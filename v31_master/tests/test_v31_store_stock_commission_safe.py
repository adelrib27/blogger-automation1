#!/usr/bin/env python3
"""SAFE: testes comerciais e de estoque inteiramente offline (sem PUT)."""
from __future__ import annotations
import sys
import unittest
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import store_stock_commission_safe as policy
from replication_safe import GateError

NOW = datetime(2026, 11, 12, 14, 0, tzinfo=timezone.utc)
CATEGORIES = tuple(policy.KEYWORDS.keys())
NAMES = {
    "Casa e Organização": "Organizador de casa compacto",
    "Cozinha": "Cafeteira de cozinha com filtro",
    "Tecnologia": "Mouse USB sem fio",
    "Utilidades": "Garrafa termica de inox",
}


def raw(item_id, category, *, rate="0.005", seller_extra=None, price="1500"):
    row = {
        "itemId": str(item_id), "productName": NAMES[category],
        "offerLink": "https://s.shopee.com.br/abc", "imageUrl": "https://down-br.img.susercontent.com/abc",
        "priceMin": price, "shopId": str(item_id), "ratingStar": "3.9", "sales": 17,
        "commissionRate": rate,
    }
    if seller_extra is not None:
        row["sellerCommissionRate"] = seller_extra
    return row


def inventory(item_id, when, stock, *, run="check-001", source=policy.INVENTORY_SOURCE,
              ok=True, authenticated=True):
    return {
        "item_id": str(item_id), "observed_at": when.isoformat(),
        "stock_units": stock, "run_id": run,
        "source": source, "success": ok, "authenticated": authenticated,
    }


def existing():
    return [
        {"item_id": str(1000000 + catidx * 4 + index),
         "title": NAMES[category], "offer_link": "https://s.shopee.com.br/abc",
         "image": "https://down-br.img.susercontent.com/abc", "price": "1500",
         "category": category, "shop_id": str(catidx + 1), "rating": "3.9", "sales": 17}
        for catidx, category in enumerate(CATEGORIES)
        for index in range(4)
    ]


def offers(*, alt=True):
    return {
        category: ([raw(2000000 + catidx * 4 + n, category) for n in range(4)] if alt else [])
        for catidx, category in enumerate(CATEGORIES)
    }


def profile():
    return {"store": {"categories": [{"name": cat} for cat in CATEGORIES]}}


def two_zero(item_id):
    return [
        inventory(item_id, NOW - timedelta(minutes=35), 0, run="check-early"),
        inventory(item_id, NOW - timedelta(minutes=3), 0, run="check-later"),
    ]


class TestNewCommercialPolicy(unittest.TestCase):
    def test_commission_half_percent_allowed(self):
        self.assertTrue(policy.commission_eligible(raw(1, "Cozinha", rate="0.005"),
                                                  verified_affiliate_response=True))

    def test_commission_below_three_percent_allowed(self):
        self.assertTrue(policy.commission_eligible(raw(1, "Cozinha", rate="0.01"),
                                                  verified_affiliate_response=True))

    def test_seller_extra_not_required(self):
        self.assertTrue(policy.commission_eligible(raw(1, "Cozinha", rate="0.01", seller_extra="0"),
                                                  verified_affiliate_response=True))

    def test_only_seller_extra_is_not_verified_total(self):
        p = raw(1, "Cozinha", rate=None, seller_extra="0.1")
        self.assertFalse(policy.commission_eligible(p, verified_affiliate_response=True))

    def test_amount_in_reais_positive_accepted(self):
        p = raw(1, "Cozinha", rate=None)
        p["commission"] = "0.12"
        self.assertTrue(policy.commission_eligible(p, verified_affiliate_response=True))

    def test_commission_zero_rejected(self):
        self.assertFalse(policy.commission_eligible(raw(1, "Cozinha", rate="0"),
                                                    verified_affiliate_response=True))

    def test_unknown_commission_rejected(self):
        self.assertFalse(policy.commission_eligible(raw(1, "Cozinha", rate=None),
                                                    verified_affiliate_response=True))

    def test_negative_or_nan_rejected(self):
        for value in ("-0.01", "NaN", "Infinity", True):
            with self.subTest(value=value):
                self.assertFalse(policy.commission_eligible(raw(1, "Cozinha", rate=value),
                                                            verified_affiliate_response=True))

    def test_unverified_api_origin_rejected(self):
        self.assertFalse(policy.commission_eligible(raw(1, "Cozinha"),
                                                    verified_affiliate_response=False))

    def test_conflicting_commission_rate_and_amount_rejected(self):
        p = raw(1, "Cozinha", rate="0")
        p["commission"] = "45"
        self.assertFalse(policy.commission_eligible(p, verified_affiliate_response=True))

    def test_select_16_with_low_positive_commission(self):
        selected = policy.select_verified(profile(), offers(), now=NOW)
        self.assertEqual(len(selected), 16)
        self.assertEqual(len(set(p["item_id"] for p in selected)), 16)

    def test_select_missing_commercial_evidence_fail_closed(self):
        bad = offers()
        bad[CATEGORIES[0]] = [dict(x, commissionRate=None) for x in bad[CATEGORIES[0]]]
        with self.assertRaises(GateError):
            policy.select_verified(profile(), bad, now=NOW)

    def test_still_reject_bad_link(self):
        bad = offers()
        bad[CATEGORIES[0]][0]["offerLink"] = "https://s.shopee.com.br.evil.example/"
        with self.assertRaises(GateError):
            policy.select_verified(profile(), bad, now=NOW)


class TestInventoryStock(unittest.TestCase):
    ITEM = "1000000"

    def test_two_independent_zero_confirm_oos(self):
        self.assertEqual(policy.stock_status(self.ITEM, two_zero(self.ITEM), now=NOW), policy.OOS)

    def test_one_zero_means_unknown(self):
        self.assertEqual(policy.stock_status(self.ITEM, two_zero(self.ITEM)[:1], now=NOW), policy.UNKNOWN)

    def test_same_run_twice_not_confirmation(self):
        samples = two_zero(self.ITEM)
        samples[1]["run_id"] = samples[0]["run_id"]
        self.assertEqual(policy.stock_status(self.ITEM, samples, now=NOW), policy.UNKNOWN)

    def test_two_zeros_too_close_are_unknown(self):
        samples = [
            inventory(self.ITEM, NOW - timedelta(minutes=8), 0, run="check-a"),
            inventory(self.ITEM, NOW - timedelta(minutes=2), 0, run="check-b"),
        ]
        self.assertEqual(policy.stock_status(self.ITEM, samples, now=NOW), policy.UNKNOWN)

    def test_positive_latest_wins(self):
        samples = two_zero(self.ITEM) + [inventory(self.ITEM, NOW - timedelta(minutes=1), 2, run="check-final")]
        self.assertEqual(policy.stock_status(self.ITEM, samples, now=NOW), policy.IN_STOCK)

    def test_stale_inventory_is_unknown(self):
        samples = [
            inventory(self.ITEM, NOW - timedelta(hours=49), 0, run="check-a"),
            inventory(self.ITEM, NOW - timedelta(hours=30), 0, run="check-b"),
        ]
        self.assertEqual(policy.stock_status(self.ITEM, samples, now=NOW), policy.UNKNOWN)

    def test_missing_stock_is_unknown_not_zero(self):
        samples = two_zero(self.ITEM)[:1]
        samples.append(inventory(self.ITEM, NOW - timedelta(minutes=2), None, run="check-failed"))
        self.assertEqual(policy.stock_status(self.ITEM, samples, now=NOW), policy.UNKNOWN)

    def test_failed_api_after_zero_prevents_oos(self):
        samples = two_zero(self.ITEM) + [inventory(self.ITEM, NOW - timedelta(minutes=1), 0,
                                                   run="check-error", ok=False)]
        self.assertEqual(policy.stock_status(self.ITEM, samples, now=NOW), policy.UNKNOWN)

    def test_source_not_verified_never_confirms(self):
        samples = two_zero(self.ITEM)
        for sample in samples:
            sample["source"] = "web_search"
        self.assertEqual(policy.stock_status(self.ITEM, samples, now=NOW), policy.UNKNOWN)

    def test_source_not_authenticated_never_confirms(self):
        samples = two_zero(self.ITEM)
        for sample in samples:
            sample["authenticated"] = False
        self.assertEqual(policy.stock_status(self.ITEM, samples, now=NOW), policy.UNKNOWN)

    def test_false_boolean_not_zero(self):
        samples = two_zero(self.ITEM)
        for sample in samples:
            sample["stock_units"] = False
        self.assertEqual(policy.stock_status(self.ITEM, samples, now=NOW), policy.UNKNOWN)

    def test_no_stock_data_unknown(self):
        self.assertEqual(policy.stock_status(self.ITEM, [], now=NOW), policy.UNKNOWN)

    def test_invalid_ids_rejected(self):
        with self.assertRaises(GateError):
            policy.stock_status("invalid", [], now=NOW)

    def test_out_of_stock_candidate_never_selected(self):
        bad = offers()
        candidate_id = bad[CATEGORIES[0]][0]["itemId"]
        with self.assertRaises(GateError):
            policy.select_verified(profile(), bad, observations=two_zero(candidate_id), now=NOW)
        
    def test_rotation_one_oos_replaces_only_that_product(self):
        old = existing()
        current_id = old[0]["item_id"]
        p = policy.plan_oos_rotation(old, offers(), two_zero(current_id), now=NOW)
        self.assertFalse(p["writes"])
        self.assertEqual(p["status"], "OOS_REPLACEMENT_CANDIDATE_SAFE_REVIEW")
        self.assertEqual(p["new_item_count"], 1)
        self.assertNotEqual(old[0]["item_id"], p["products"][0]["item_id"])
        self.assertEqual(old[1:], p["products"][1:])
        self.assertEqual(p["candidate_html"].count('class="ub-product-card"'), 16)

    def test_rotation_no_verified_oos_no_change(self):
        old = existing()
        p = policy.plan_oos_rotation(old, offers(), [], now=NOW)
        self.assertEqual(p["status"], "NO_CONFIRMED_STOCK_CHANGE")
        self.assertFalse(p["writes"])
        self.assertEqual(p["products"], old)

    def test_rotation_oos_but_no_replacement_preserves_state(self):
        old = existing()
        p = policy.plan_oos_rotation(old, offers(alt=False), two_zero(old[0]["item_id"]), now=NOW)
        self.assertEqual(p["status"], "BLOCK_NO_VERIFIED_REPLACEMENT")
        self.assertEqual(p["products"], old)

    def test_rotation_replacement_with_zero_commission_blocked(self):
        old = existing()
        choices = offers()
        choices[CATEGORIES[0]] = [dict(x, commissionRate="0") for x in choices[CATEGORIES[0]]]
        p = policy.plan_oos_rotation(old, choices, two_zero(old[0]["item_id"]), now=NOW)
        self.assertEqual(p["status"], "BLOCK_NO_VERIFIED_REPLACEMENT")

    def test_rotation_does_not_cross_category(self):
        old = existing()
        choices = offers(alt=False)
        choices[CATEGORIES[1]] = [raw(2000002, CATEGORIES[1])]
        p = policy.plan_oos_rotation(old, choices, two_zero(old[0]["item_id"]), now=NOW)
        self.assertEqual(p["status"], "BLOCK_NO_VERIFIED_REPLACEMENT")

    def test_rotation_fails_on_duplicate_current_ids(self):
        old = existing()
        old[0]["item_id"] = old[1]["item_id"]
        with self.assertRaises(GateError):
            policy.plan_oos_rotation(old, offers(), [], now=NOW)


if __name__ == "__main__":
    unittest.main(verbosity=2)
