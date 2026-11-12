#!/usr/bin/env python3
"""SAFE/LAB only: regressao dos filtros flexibilizados sem API real nem escrita Blogger."""
from __future__ import annotations
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import shopee_r2_safe as selection
from replication_safe import GateError

CATEGORIES = ("Casa e Organização", "Cozinha", "Tecnologia", "Utilidades")
NAMES = ("Organizadores compactos", "Cafeteiras elétricas", "Mouse USB", "Garrafas térmicas")


def item(item_id: str, title: str, *, rating="3.7", shop="1", price="29.90"):
    return {
        "itemId": item_id,
        "productName": title,
        "offerLink": "https://s.shopee.com.br/123abc",
        "imageUrl": "https://down-br.img.susercontent.com/abc",
        "priceMin": price,
        "ratingStar": rating,
        "shopId": shop,
        "sales": 10,
    }


def offers_by_category():
    return {
        cat: [item(str(1000000 + ci * 4 + j), NAMES[ci], shop=str(ci + 1))
              for j in range(4)]
        for ci, cat in enumerate(CATEGORIES)
    }


def profile():
    return {"store": {"categories": [{"name": c} for c in CATEGORIES]}}


class TestRelaxedFiltersSafe(unittest.TestCase):
    def test_rating_37_passes_lab(self):
        self.assertIsNotNone(selection.normalize(item("1000001", "Mouse USB", rating="3.7"), "Tecnologia"))

    def test_rating_below_35_rejected(self):
        self.assertIsNone(selection.normalize(item("1000001", "Mouse USB", rating="3.4"), "Tecnologia"))

    def test_rating_above_5_rejected(self):
        self.assertIsNone(selection.normalize(item("1000001", "Mouse USB", rating="5.1"), "Tecnologia"))

    def test_eight_characters_or_more(self):
        self.assertIsNotNone(selection.normalize(item("1000001", "Mouse USB"), "Tecnologia"))
        self.assertIsNone(selection.normalize(item("1000001", "USB"), "Tecnologia"))

    def test_accent_and_plural(self):
        self.assertIsNotNone(selection.normalize(item("1000001", "Garrafas térmicas"), "Utilidades"))
        self.assertIsNotNone(selection.normalize(item("1000001", "Cafeteiras elétricas"), "Cozinha"))

    def test_still_reject_wrong_category(self):
        self.assertIsNone(selection.normalize(item("1000001", "Ração para cães"), "Tecnologia"))

    def test_still_reject_untrusted_affiliate_link(self):
        p = item("1000001", "Mouse USB")
        p["offerLink"] = "https://s.shopee.com.br.evil.example/fake"
        self.assertIsNone(selection.normalize(p, "Tecnologia"))

    def test_still_reject_untrusted_image(self):
        p = item("1000001", "Mouse USB")
        p["imageUrl"] = "http://down-br.img.susercontent.com/abc"
        self.assertIsNone(selection.normalize(p, "Tecnologia"))

    def test_still_reject_bad_price(self):
        self.assertIsNone(selection.normalize(item("1000001", "Mouse USB", price="0.99"), "Tecnologia"))

    def test_still_reject_bad_item_id(self):
        self.assertIsNone(selection.normalize(item("fake", "Mouse USB"), "Tecnologia"))

    def test_16_distinct_products_and_4_per_category(self):
        chosen = selection.choose(profile(), offers_by_category())
        self.assertEqual(len(chosen), 16)
        self.assertEqual(len({x["item_id"] for x in chosen}), 16)
        self.assertEqual([sum(p["category"] == c for p in chosen) for c in CATEGORIES], [4] * 4)
        html = selection.render(chosen, lab_url="https://example.invalid/")
        self.assertEqual(html.count('class="ub-product-card"'), 16)
        self.assertEqual(html.count('rel="nofollow sponsored noopener"'), 32)
        self.assertEqual(html.count('data-lab-only="true"'), 1)

    def test_15_products_still_blocked(self):
        pool = offers_by_category()
        pool[CATEGORIES[0]].pop()
        with self.assertRaises(GateError):
            selection.choose(profile(), pool)

    def test_duplicate_ids_still_blocked(self):
        pool = offers_by_category()
        pool[CATEGORIES[1]][0]["itemId"] = pool[CATEGORIES[0]][0]["itemId"]
        with self.assertRaises(GateError):
            selection.choose(profile(), pool)

    def test_graphql_error_still_fail_closed(self):
        response = MagicMock()
        response.status = 200
        response.read.return_value = json.dumps({"errors": [{"code": 10000, "message": "System Error"}]}).encode()
        handle = MagicMock()
        handle.__enter__.return_value = response
        with patch.object(selection.urllib.request, "urlopen", return_value=handle):
            with self.assertRaises(GateError):
                selection.signed_query("mouse", "123456", "fake-test-secret")

    def test_no_credentials_or_blogger_write_required_for_offline_test(self):
        selected = selection.choose(profile(), offers_by_category())
        self.assertEqual(len(selected), 16)


    def test_strict_vs_relaxed_same_fixture(self):
        from lab_shopee_filters_probe import strict_eligible
        pool = offers_by_category()
        strict_count = sum(1 for rows in pool.values() for raw in rows if strict_eligible(raw))
        relaxed_count = len(selection.choose(profile(), pool))
        self.assertEqual(strict_count, 0)
        self.assertEqual(relaxed_count, 16)

    def test_rotation_candidate_staged_without_write(self):
        import r57_store_policy as gate
        before_pool = offers_by_category()
        after_pool = offers_by_category()
        for rows in after_pool.values():
            for raw in rows:
                raw["itemId"] = str(int(raw["itemId"]) + 100000)
        before = selection.render(selection.choose(profile(), before_pool), lab_url="https://example.invalid/")
        after = selection.render(selection.choose(profile(), after_pool), lab_url="https://example.invalid/")
        old = gate.validate_store_html(before)
        gate.validate_store_html(after)
        state = {
            "schema": gate.SCHEMA, "blog_id": gate.BLOG_ID, "page_id": gate.PAGE_ID, "url": gate.STORE_URL,
            "card_count": 16, "affiliate_link_count": 32,
            "item_ids": old["items"], "html_sha256": old["sha256"],
            "allow_auto_write": False,
            "guards": {
                "blogger_page_exact": True, "no_runner_files_write": True,
                "no_theme_install": True, "no_new_post_or_page": True,
                "public_pass_before_state_update": True,
            },
        }
        outcome = gate.decision(before, after, state)
        self.assertEqual(outcome["status"], "R57_CANDIDATE_SAFE_NOT_AUTHORIZED")
        self.assertFalse(outcome["writes"])
        self.assertEqual(outcome["new_item_count"], 16)
        unchanged = gate.decision(before, before, state)
        self.assertEqual(unchanged["status"], "R57_NO_CHANGE")
        self.assertFalse(unchanged["writes"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
