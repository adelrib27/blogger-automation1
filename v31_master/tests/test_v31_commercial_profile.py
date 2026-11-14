import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import shopee_r2_safe as store

PROFILE = ROOT / "profiles" / "cadeira_certa_commercial_safe.json"


class TestCommercialProfile(unittest.TestCase):
    def test_pilot_exports_only_eligible_offers_for_its_own_destination(self):
        profile = store.load_commercial_profile(PROFILE)
        categories = profile["store"]["categories"]

        def query(keyword, app_id, secret):
            index, category = next((i, c) for i, c in enumerate(categories) if keyword in c["terms"])
            base = {
                "productName": category["include"][0] + " modelo teste",
                "offerLink": "https://s.shopee.com.br/teste",
                "imageUrl": "https://img.susercontent.com/teste.jpg",
                "priceMin": "550.00",
                "shopId": str(index + 1),
                "commissionRate": "0.0001",
            }
            return [
                dict(base, itemId=str(index * 10 + 1), commissionRate="0"),
                dict(base, itemId=str(index * 10 + 5), productName="Capa para " + base["productName"]),
                *(dict(base, itemId=str(index * 10 + j)) for j in range(1, 5)),
            ]

        with tempfile.TemporaryDirectory() as directory:
            args = ["shopee_r2_safe.py", "--commercial-profile", str(PROFILE), "--out-dir", directory]
            with patch.object(sys, "argv", args), patch.dict("os.environ", {
                "SHOPEE_APP_ID": "1234", "SHOPEE_SECRET": "mock-only",
            }), patch.object(store, "signed_query", side_effect=query) as signed_query:
                self.assertEqual(store.main(), 0)
            self.assertEqual(signed_query.call_count, 4)
            catalog = json.loads((Path(directory) / "v31_r2_products.json").read_text())
            self.assertEqual(catalog["blog_id"], "7163624325768776034")
            self.assertEqual(catalog["page_id"], "5014986967420563988")
            self.assertEqual({p["item_id"] for p in catalog["products"]},
                             {str(i * 10 + j) for i in range(4) for j in range(1, 5)})
            page = (Path(directory) / "v31_r2_store.html").read_text()
            self.assertEqual(page.count('rel="nofollow sponsored noopener"'), 32)

    def test_duplicate_category_cannot_pass_preflight(self):
        profile = json.loads(PROFILE.read_text())
        profile["store"]["categories"][1]["name"] = "CADEIRAS ERGONOMICAS"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "profile.json"
            path.write_text(json.dumps(profile))
            with self.assertRaisesRegex(store.GateError, "duplicada"):
                store.load_commercial_profile(path)

    def test_transient_graphql_error_retries_once_and_discards_partial_data(self):
        transient = store.ShopeeGraphQLError([{"extensions": {"code": "10000"}}])
        with patch.object(store, "signed_query", side_effect=[transient, []]) as request, \
                patch.object(store.time, "sleep") as sleep:
            self.assertEqual(store.query_commercial("cadeira", "123", "mock"), [])
            self.assertEqual(request.call_count, 2)
            sleep.assert_called_once_with(8)
        with patch.object(store, "signed_query", side_effect=transient) as request, \
                patch.object(store.time, "sleep"):
            with self.assertRaises(store.ShopeeGraphQLError):
                store.query_commercial("cadeira", "123", "mock")
            self.assertEqual(request.call_count, 2)

    def test_non_transient_error_is_not_retried(self):
        error = store.ShopeeGraphQLError([{"code": 10020}])
        with patch.object(store, "signed_query", side_effect=error) as request, \
                patch.object(store.time, "sleep") as sleep:
            with self.assertRaises(store.ShopeeGraphQLError):
                store.query_commercial("cadeira", "123", "mock")
            request.assert_called_once()
            sleep.assert_not_called()
