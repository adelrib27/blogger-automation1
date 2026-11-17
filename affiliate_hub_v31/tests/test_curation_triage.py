"""C21 — contratos de curadoria em 7 lanes e bloqueio de conflito entre fontes."""
import json
import tempfile
import unittest
from pathlib import Path

from affiliate_hub_v31.catalog import Catalog
from affiliate_hub_v31.curation_triage import (
    LANES, TriageError, lane_for_record, triage_backlog,
)
from affiliate_hub_v31.product_discovery import discover, suggest_category_paths
from affiliate_hub_v31.source_category_index import create_source_category_schema
from affiliate_hub_v31.title_index import rebuild_index


class CurationTriageTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.db = Path(tmp.name) / "catalog.sqlite3"
        items = [
            # id, title, mod, tax, l1, l2, shop, origin_good, source_status
            ("1", "Air Fryer Digital 5 litros", "eligible", "matched",
             "home appliances", "kitchen appliances", "101", True, "matched"),
            ("2", "Guarda Roupa Casal 4 Portas", "review", "review",
             "home living", "furniture", "202", True, "matched"),
            ("3", "Guarda Roupa Solteiro 3 Portas", "review", "matched",
             "home living", "furniture", "303", True, "matched"),
            ("4", "Produto Peculiar Sem Categoria", "review", "review",
             "", "", "404", True, None),
            ("5", "Suplemento Produto Revisao", "review", "review",
             "health", "vitamins", "505", True, "matched"),
            ("6", "Produto Sem URL Correta", "review", "review",
             "home living", "furniture", "606", False, "matched"),
            ("7", "Air Fryer Dados Inconsistentes", "review", "review",
             "home appliances", "kitchen appliances", "707", True, "matched"),
            ("8", "Air Fryer Produto Fonte Protegida", "eligible", "matched",
             "health", "vitamins", "808", True, "matched"),
            ("9", "Air Fryer Digital Conflito Source", "eligible", "matched",
             "home appliances", "kitchen appliances", "909", True, "matched"),
            ("10", "Produto Sem Loja", "review", "review",
             "home living", "furniture", "", True, "matched"),
        ]
        with Catalog(self.db) as cat:
            create_source_category_schema(cat)
            with cat.db:
                for ident, title, mod, tax, l1, l2, shop, valid, src_status in items:
                    key = "shopee:" + (shop or "0") + ":" + ident
                    cat.db.execute("""
                        INSERT INTO products
                        (product_key,shop_id,item_id,title,description,origin_url,
                         image_url,moderation,moderation_reason,first_source,last_seen_utc)
                        VALUES(?,?,?,?,?,?,?,?,?,?,?)
                    """, (key,shop,ident,title,"Descrição editorial não comercial",
                          f"https://shopee.com.br/product/{shop or '0'}/{ident}"
                          if valid else "https://invalid.example/1",
                          "https://cf.shopee.com.br/file/test",mod,
                          "categoria_sensivel" if ident == "5" else "",
                          "first","2026-11-17T00:00:00Z"))
                    cat.db.execute("""
                        INSERT INTO product_taxonomy
                        (product_key,category,niche,status,reason,version)
                        VALUES(?,?,?,?,?,?)
                    """,(key,"home","appliance",tax,
                          "exact_phrase" if tax == "matched" else "unclassified",
                          "v31-editorial-taxonomy-fixture"))
                    if src_status:
                        cat.db.execute("""
                            INSERT INTO product_source_categories
                            (product_key,source,level1,level2,level3,status)
                            VALUES(?,?,?,?,?,?)
                        """,(key,"first",l1,l2,"",src_status))
                for ident,shop in (("7","707"),("9","909")):
                    cat.db.execute("""
                        INSERT INTO product_source_categories
                        (product_key,source,level1,level2,level3,status)
                        VALUES(?,?,?,?,?,?)
                    """,(f"shopee:{shop}:{ident}","second",
                          "home appliances","kitchen appliances","","conflict"))
            cat.cache_link("shopee:101:1", "blogantigo",
                           "https://s.shopee.com.br/existing-real-link")

    def test_all_pending_have_exactly_one_lane_and_legacy_protected_stays_out(self):
        with Catalog(self.db) as cat:
            before=cat.stats()
            report=triage_backlog(cat)
            after=cat.stats()
        self.assertEqual(before,after)
        self.assertEqual(report["products"],10)
        self.assertEqual(report["previously_approved"],3)
        self.assertEqual(report["pending_review"],7)
        self.assertEqual(report["sum_review_lanes"],7)
        self.assertEqual(report["existing_affiliate_links"],1)
        self.assertEqual(report["prior_approvals_with_protected_or_conflicting_source"],2)
        self.assertEqual(report["lane_counts"],{
            "SOURCE_CONFLICT":1, "POLICY_REVIEW":1,"DATA_REPAIR":2,
            "NO_OFFICIAL_CATEGORY":1,"TAXONOMY_REVIEW":1,
            "MODERATION_REVIEW":1,"OTHER_HOLD":0,
        })
        self.assertEqual(set(report["lane_counts"]), set(LANES))
        self.assertEqual(report["publication_calls"],0)
        self.assertEqual(report["r2_writes"],0)
        self.assertEqual(report["new_approvals"],0)
        self.assertFalse(report["can_publish"])

    def test_ranked_manual_paths_use_source_evidence_and_distinct_shops(self):
        with Catalog(self.db) as cat:
            report=triage_backlog(cat)
        self.assertEqual(report["review_opportunity_paths"][0]["category_l1"],"home living")
        self.assertEqual(report["review_opportunity_paths"][0]["category_l2"],"furniture")
        self.assertEqual(report["review_opportunity_paths"][0]["pending_for_manual_review"],2)
        self.assertEqual(report["review_opportunity_paths"][0]["distinct_shops"],2)
        self.assertFalse(report["review_opportunity_paths"][0]["publication_approved"])
        self.assertIsNone(report["review_opportunity_paths"][0]["estimated_sales_or_commission"])

    def test_source_conflict_never_in_approved_discovery_before_or_after_fts(self):
        with Catalog(self.db) as cat:
            before=discover(cat,topic="Air Fryer",include_review=False)
            paths_before=suggest_category_paths(cat,topic="Air Fryer")
            rebuild_index(cat)
            after=discover(cat,topic="Air Fryer",include_review=False)
            paths_after=suggest_category_paths(cat,topic="Air Fryer")
        keys={x["product_key"] for x in before}
        self.assertIn("shopee:101:1",keys)
        self.assertNotIn("shopee:909:9",keys)
        self.assertNotIn("shopee:707:7",keys)
        self.assertNotIn("shopee:808:8",keys)  # raiz protegida
        self.assertEqual(before,after)
        self.assertEqual(paths_before,paths_after)
        self.assertTrue(all(not x["can_publish"] for x in before))

    def test_conflict_also_disappears_from_review_candidates(self):
        with Catalog(self.db) as cat:
            full=discover(cat,topic="Air Fryer",include_review=True)
        keys={x["product_key"] for x in full}
        self.assertNotIn("shopee:909:9",keys)
        self.assertNotIn("shopee:707:7",keys)

    def test_logs_contain_only_aggregates_not_products_or_campaigns(self):
        with Catalog(self.db) as cat:
            raw=json.dumps(triage_backlog(cat),ensure_ascii=False)
        for secret in ("Guarda Roupa Casal","shopee:", "existing-real-link",
                       "blogantigo","/product/"):
            self.assertNotIn(secret,raw)
        self.assertIn("distinct_shops",raw)

    def test_invalid_limits_and_policy_precedence_fail_closed(self):
        with Catalog(self.db) as cat:
            for bad in (0,31,-1,True,"12"):
                with self.subTest(bad=bad),self.assertRaises(TriageError):
                    triage_backlog(cat,max_categories=bad)
        opts=dict(title="Produto",shop_id="1",
                  origin_url="https://shopee.com.br/product/1/1",
                  image_url="https://cf.shopee.com.br/file/a",
                  moderation="review",moderation_reason="",
                  taxonomy_status="review",source_l1="home living",
                  source_record_count=1,branches=1,leaves=0,invalid_sources=0)
        self.assertEqual(lane_for_record(**opts),"TAXONOMY_REVIEW")
        self.assertEqual(lane_for_record(**{**opts,"invalid_sources":1}),
                         "SOURCE_CONFLICT")
        self.assertEqual(lane_for_record(**{**opts,"source_l1":"health"}),
                         "POLICY_REVIEW")
        self.assertEqual(lane_for_record(**{**opts,"origin_url":"http://bad"}),
                         "DATA_REPAIR")
        self.assertEqual(lane_for_record(**{**opts,"source_record_count":0,
                                            "source_l1":""}),"NO_OFFICIAL_CATEGORY")


if __name__=="__main__":
    unittest.main()
