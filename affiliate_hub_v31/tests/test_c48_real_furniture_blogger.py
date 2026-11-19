"""C48: blog de móveis REAL, campanha própria e nenhum LIVE automático."""
import json
import unittest

from affiliate_hub_v31.routing import sites
from affiliate_hub_v31.converter import valid_campaign, make_payload
from affiliate_hub_v31.site_request_queue import load_requests

KEY = "blogger_moveis_para_cada_canto"
ID = "1439741542627895062"
CAMPAIGN = "moveisparacadacanto"


class FurnitureBloggerLaunchTests(unittest.TestCase):
    def test_real_blogger_is_registered_in_universal_router(self):
        routes = sites()
        blog = routes[KEY]
        self.assertEqual(blog["platform"], "blogger")
        self.assertEqual(blog["identifier"], ID)
        self.assertEqual(blog["campaign"], CAMPAIGN)
        self.assertEqual(blog["allowed_niches"], ["casa/moveis"])
        self.assertEqual(blog["allowed_source_paths"], ["home living/furniture"])
        self.assertIs(blog["publish_enabled"], False)
        self.assertEqual(sum(x["identifier"] == ID for x in routes.values()), 1)
        self.assertEqual(sum(x["campaign"] == CAMPAIGN for x in routes.values()), 1)

    def test_affiliate_subid_is_exclusively_this_campaign(self):
        self.assertEqual(valid_campaign(CAMPAIGN), "MOVEISPARACADACANTO")
        payload = json.loads(make_payload(
            "https://shopee.com.br/product/123/456", CAMPAIGN))
        query = payload["query"]
        self.assertIn('subIds: ["MOVEISPARACADACANTO"]', query)
        self.assertNotIn("CASAED", query)
        self.assertIn("generateShortLink", query)

    def test_real_blog_request_now_continuous_cache_only(self):
        # C49 histórico: 3 LIVE iniciais entregues. C61 autorização atual
        # é contínua; a fila só cacheia links, nunca publica posts.
        requests=[x for x in load_requests() if x["site_key"] == KEY]
        self.assertEqual(len(requests),1)
        request=requests[0]
        self.assertIsNone(request["articles"])
        self.assertEqual(request["platform"],"blogger")
        self.assertTrue(request["enabled"])
        for keyword in ("sofá","guarda-roupa","mesa","escritório"):
            self.assertIn(keyword,request["topic"])
        self.assertIs(sites()[KEY]["publish_enabled"],False)


if __name__ == "__main__":
    unittest.main()
