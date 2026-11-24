"""C147 — conversão em tempo real com limite D1 e R2 readback.

Todos os testes usam SQLite local e substituem API/R2; nenhuma mutação real.
"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from affiliate_hub_v31.catalog import Catalog
from affiliate_hub_v31.converter import ConversionError
from affiliate_hub_v31.on_demand_conversion import (
    OnDemandConversionError, convert_for_review,
)
from affiliate_hub_v31.routing import sites


SKU = "shopee:887799:551177"
LINK = "https://s.shopee.com.br/1gKKtbXPHn"


class FakeR2:
    def __init__(self, *, broken_save=False, broken_restore=False, stale=False):
        self.saved = None
        self.writes = 0
        self.reads = 0
        self.broken_save = broken_save
        self.broken_restore = broken_restore
        self.stale = stale

    def save_from(self, path):
        self.writes += 1
        if self.broken_save:
            return {"state_saved": False}
        self.saved = Path(path).read_bytes()
        return {"state_saved": True}

    def restore_to(self, path):
        self.reads += 1
        if self.broken_restore:
            return False
        Path(path).write_bytes(self.saved)
        if self.stale:
            # Simula perda da escrita no snapshot: a função externa de
            # readback deve bloquear, nunca considerar conversão concluída.
            with Catalog(path) as catalog:
                catalog.db.execute(
                    "DELETE FROM affiliate_links WHERE product_key=?",
                    (SKU,))
                catalog.db.commit()
        return True


class OnDemandConversionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="v31-c147-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.catalog = Catalog(self.root / "current.sqlite3")
        self.addCleanup(self.catalog.close)
        self.route = sites()["wordpress_casa_decoracao"]
        self.storage = FakeR2()
        self.reservations = []
        with self.catalog.db:
            self.catalog.db.execute("""
              INSERT INTO products
              (product_key,shop_id,item_id,title,description,origin_url,
               image_url,moderation,moderation_reason,first_source,last_seen_utc)
              VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """, (SKU,"887799","551177","Vaso decorativo","Vaso decorativo original",
                  "https://shopee.com.br/product/887799/551177",
                  "https://cf.shopee.com.br/file/sg-11134201-c147",
                  "eligible","","fixture","2026-11-24T00:00:00Z"))
            self.catalog.db.execute("""
              INSERT INTO product_taxonomy
              (product_key,category,niche,status,reason,version)
              VALUES (?,?,?,?,?,?)
            """, (SKU,"casa","decoracao","matched","","test"))

    def reserve(self, campaign, product_key):
        self.reservations.append((campaign,product_key))
        return True

    def invoke(self, **overrides):
        opts = dict(
            catalog=self.catalog,
            storage=self.storage,
            route=self.route,
            product_key=SKU,
            app_id="sampleapp",
            app_secret="samplesecret",
            reserve_attempt=self.reserve,
            verification_path=self.root / "verified.sqlite3",
        )
        opts.update(overrides)
        return convert_for_review(**opts)

    def fake_convert(self, catalog, sku, campaign, app_id, app_secret):
        self.assertEqual(sku, SKU)
        self.assertEqual(campaign, self.route["campaign"])
        self.assertEqual((app_id, app_secret), ("sampleapp", "samplesecret"))
        self.assertIsNone(catalog.cached_link(SKU, campaign))
        self.assertTrue(catalog.cache_link(sku, campaign, LINK))
        return LINK, True

    def test_real_time_converts_and_confirms_r2_exact_campaign_link(self):
        with patch("affiliate_hub_v31.on_demand_conversion.convert_one",
                   side_effect=self.fake_convert) as call:
            self.assertEqual(self.invoke(), "CONVERTED")
        self.assertEqual(call.call_count, 1)
        self.assertEqual(self.reservations, [(self.route["campaign"],SKU)])
        self.assertEqual(self.storage.writes, 1)
        self.assertEqual(self.storage.reads, 1)
        self.assertEqual(self.catalog.cached_link(SKU, self.route["campaign"]), LINK)

    def test_reuses_cached_link_without_api_or_budget(self):
        self.catalog.cache_link(SKU, self.route["campaign"], LINK)
        with patch("affiliate_hub_v31.on_demand_conversion.convert_one") as call:
            self.assertEqual(self.invoke(), "CACHED")
            call.assert_not_called()
        self.assertEqual(self.reservations, [])
        self.assertEqual(self.storage.writes, 0)

    def test_budget_denied_without_shopee_or_r2(self):
        with patch("affiliate_hub_v31.on_demand_conversion.convert_one") as call:
            self.assertEqual(self.invoke(reserve_attempt=lambda a,b:False), "BUDGET_DENIED")
            call.assert_not_called()
        self.assertEqual(self.storage.writes, 0)

    def test_credentials_missing_before_consuming_d1(self):
        with self.assertRaisesRegex(OnDemandConversionError,
                                    "on_demand_shopee_credentials_missing"):
            self.invoke(app_secret="")
        self.assertEqual(self.reservations, [])

    def test_no_conversion_for_unapproved_product(self):
        self.catalog.db.execute(
            "UPDATE products SET moderation='review' WHERE product_key=?", (SKU,))
        self.catalog.db.commit()
        with self.assertRaisesRegex(OnDemandConversionError,
                                    "on_demand_product_not_eligible"):
            self.invoke()
        self.assertEqual(self.reservations, [])

    def test_no_conversion_for_wrong_blog_niche(self):
        wrong = dict(self.route,allowed_niches=["tecnologia/gadgets"],
                     allowed_source_paths=[])
        with self.assertRaisesRegex(OnDemandConversionError,
                                    "on_demand_product_not_eligible"):
            self.invoke(route=wrong)
        self.assertEqual(self.reservations, [])

    def test_existing_link_of_other_campaign_does_not_satisfy_route(self):
        self.catalog.cache_link(SKU,"othercampaign",LINK)
        with patch("affiliate_hub_v31.on_demand_conversion.convert_one",
                   side_effect=self.fake_convert):
            self.assertEqual(self.invoke(),"CONVERTED")
        self.assertEqual(self.catalog.cached_link(SKU,"othercampaign"), LINK)
        self.assertEqual(self.catalog.cached_link(SKU,self.route["campaign"]), LINK)

    def test_shopee_network_error_fails_closed_without_retry_or_r2(self):
        with patch("affiliate_hub_v31.on_demand_conversion.convert_one",
                   side_effect=ConversionError("network_error")) as call:
            with self.assertRaisesRegex(OnDemandConversionError,
                                        "on_demand_shopee_failed_closed"):
                self.invoke()
        self.assertEqual(call.call_count,1)
        self.assertEqual(len(self.reservations),1)
        self.assertEqual(self.storage.writes,0)

    def test_failed_r2_persistence_blocks_review(self):
        self.storage = FakeR2(broken_save=True)
        with patch("affiliate_hub_v31.on_demand_conversion.convert_one",
                   side_effect=self.fake_convert):
            with self.assertRaisesRegex(OnDemandConversionError,
                                        "on_demand_r2_persistence_unverified"):
                self.invoke()
        self.assertEqual(self.storage.writes,1)

    def test_failed_r2_readback_blocks_review(self):
        self.storage = FakeR2(broken_restore=True)
        with patch("affiliate_hub_v31.on_demand_conversion.convert_one",
                   side_effect=self.fake_convert):
            with self.assertRaisesRegex(OnDemandConversionError,
                                        "on_demand_r2_restore_unverified"):
                self.invoke()

    def test_r2_readback_missing_exact_sku_link_blocks_review(self):
        self.storage = FakeR2(stale=True)
        with patch("affiliate_hub_v31.on_demand_conversion.convert_one",
                   side_effect=self.fake_convert):
            with self.assertRaisesRegex(OnDemandConversionError,
                                        "on_demand_r2_exact_link_unverified"):
                self.invoke()

    def test_untrusted_budget_response_is_fail_closed(self):
        with self.assertRaisesRegex(OnDemandConversionError,
                                    "on_demand_budget_untrusted"):
            self.invoke(reserve_attempt=lambda a,b:1)
        self.assertEqual(self.storage.writes,0)

    def test_budget_exception_never_attempts_shopee(self):
        def broken(a,b):
            raise RuntimeError("sensitive data")
        with patch("affiliate_hub_v31.on_demand_conversion.convert_one") as call:
            with self.assertRaisesRegex(OnDemandConversionError,
                                        "on_demand_budget_unverified"):
                self.invoke(reserve_attempt=broken)
            call.assert_not_called()

    def test_on_demand_never_uses_existing_file_as_restore_target(self):
        with self.assertRaisesRegex(OnDemandConversionError,
                                    "on_demand_restore_path_invalid"):
            self.invoke(verification_path=self.catalog.path)
        self.assertEqual(self.reservations, [])

    def test_route_must_be_draft_only(self):
        bad = dict(self.route,publish_enabled=True)
        with self.assertRaisesRegex(OnDemandConversionError,
                                    "on_demand_route_or_budget_invalid"):
            self.invoke(route=bad)
        self.assertEqual(self.reservations, [])


if __name__ == "__main__":
    unittest.main()
