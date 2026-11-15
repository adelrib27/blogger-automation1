"""Teste de conversão mockada; este arquivo nunca chama a Shopee real."""
import csv
import json
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

from affiliate_hub_v31.catalog import Catalog
from affiliate_hub_v31.converter import (
    ConversionError, convert_one, generate_shortlink, make_payload, planned_candidates,
)


class FakeResponse:
    status = 200
    def __init__(self, data):
        self.payload = json.dumps(data).encode() if isinstance(data, dict) else data
    def __enter__(self):
        return self
    def __exit__(self, *_):
        return False
    def read(self, *_):
        return self.payload


class ConverterTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        path = root / "feed.csv"
        with path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "productName","shopId","itemId","productLink","imageUrl"])
            writer.writeheader()
            for idx, title in enumerate(("Organizador de Cozinha", "Parafusadeira", "Produto Desconhecido"),1):
                writer.writerow({
                    "productName":title,"shopId":"501","itemId":str(idx),
                    "productLink":f"https://shopee.com.br/item-i.501.{idx}",
                    "imageUrl":"https://cdn.example/img.jpg",
                })
        self.catalog = Catalog(root/"state.sqlite3")
        self.addCleanup(self.catalog.close)
        self.catalog.import_csv(path, "feed1")

    def test_graphql_payload_escapes_values_and_uses_derived_subid(self):
        url="https://shopee.com.br/x-i.501.1?foo=bar&baz=true"
        body = json.loads(make_payload(url,"blogger_casa"))
        self.assertEqual(body["operationName"],"V31EditorialGenerateLink")
        self.assertIn("generateShortLink(input:",body["query"])
        self.assertIn(json.dumps(url), body["query"])
        self.assertIn('"BLOGGERCASA"', body["query"])
        with self.assertRaises(ValueError):
            make_payload("https://shopee.com.br.evil.test/x","blogger")

    def test_plan_counts_and_isolated_niches_without_network(self):
        p=planned_candidates(self.catalog,"blogger_casa","cozinha","organizacao_utensilios")
        self.assertEqual(p["count"],1)
        self.assertEqual(p["keys"],["shopee:501:1"])
        self.assertEqual(self.catalog.stats()["cached_affiliate_links"],0)
        self.assertEqual(planned_candidates(self.catalog,"wordpress","ferramentas")["count"],1)
        self.assertEqual(planned_candidates(self.catalog,"wordpress","tecnologia")["count"],0)

    def test_conversion_cache_and_campaign_isolation(self):
        success = FakeResponse({"data":{"generateShortLink":{"shortLink":"https://s.shopee.com.br/A123"}}})
        with patch("affiliate_hub_v31.converter.urllib.request.urlopen",return_value=success) as mock:
            link, created = convert_one(self.catalog,"shopee:501:1","blogger_casa","ID","SECRET")
            self.assertTrue(created)
            self.assertEqual(link,"https://s.shopee.com.br/A123")
            request=mock.call_args.args[0]
            self.assertEqual(request.method,"POST")
            self.assertNotIn(b"SECRET",request.data)
            self.assertEqual(request.full_url,"https://open-api.affiliate.shopee.com.br/graphql")
        with patch("affiliate_hub_v31.converter.urllib.request.urlopen",side_effect=AssertionError("should not call")):
            self.assertEqual(convert_one(self.catalog,"shopee:501:1","blogger_casa","",""), (link,False))
        with patch("affiliate_hub_v31.converter.urllib.request.urlopen",return_value=FakeResponse({
            "data":{"generateShortLink":{"shortLink":"https://shope.ee/W456"}}
        })):
            other,created=convert_one(self.catalog,"shopee:501:1","wordpress_radar","ID","SECRET")
            self.assertTrue(created)
            self.assertNotEqual(other,link)
        self.assertEqual(self.catalog.stats()["cached_affiliate_links"],2)

    def test_unclassified_cannot_call_api(self):
        with patch("affiliate_hub_v31.converter.urllib.request.urlopen",side_effect=AssertionError("unsafe call")):
            with self.assertRaises(ConversionError):
                convert_one(self.catalog,"shopee:501:3","blogger","ID","SECRET")

    def test_api_graphql_error_and_hostile_domain_never_persist(self):
        for response,code in (
            ({"errors":[{"message":"PRIVATE API ERROR"}]}, "graphql_error"),
            ({"data":{"generateShortLink":{"shortLink":"https://shopee.com.br.evil.test/abc"}}},
                "untrusted_or_missing_affiliate_link"),
            ({"data":{"generateShortLink":{"shortLink":""}}}, "untrusted_or_missing_affiliate_link"),
        ):
            with self.subTest(code=code),patch("affiliate_hub_v31.converter.urllib.request.urlopen",
                                                return_value=FakeResponse(response)):
                with self.assertRaises(ConversionError) as e:
                    convert_one(self.catalog,"shopee:501:1","blogger","ID","SECRET")
                self.assertEqual(str(e.exception),code)
                self.assertIsNone(self.catalog.cached_link("shopee:501:1","blogger"))

    def test_http_error_is_sanitized_and_does_not_auto_retry(self):
        exc=urllib.error.HTTPError("https://open-api.affiliate.shopee.com.br/graphql",429,
                                   "secret in remote body",{},None)
        with patch("affiliate_hub_v31.converter.urllib.request.urlopen",side_effect=exc) as mock:
            with self.assertRaisesRegex(ConversionError,"http_error_429"):
                generate_shortlink("https://shopee.com.br/item-i.501.1","blogger","ID","SECRET")
            self.assertEqual(mock.call_count,1)

    def test_bad_campaign_rejected(self):
        with self.assertRaises(ValueError):
            planned_candidates(self.catalog,"../../etc/passwd")
        with self.assertRaises(ValueError):
            make_payload("https://shopee.com.br/item-i.501.1","BAD SPACE")


if __name__ == "__main__":
    unittest.main()
