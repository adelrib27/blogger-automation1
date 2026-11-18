"""Rotas separadas por blog e plataforma; C2 não faz publicação."""
import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import affiliate_hub_v31.routing as routing

from affiliate_hub_v31.catalog import Catalog
from affiliate_hub_v31.routing import plan_site, sites


class RouteTests(unittest.TestCase):
    def test_routes_cover_blogger_and_wordpress_by_verified_ids(self):
        mapping=sites()
        # O catálogo universal aceita novos blogs declarativos.
        # Não fixar a quantidade histórica (18 Blogger + 3 WordPress).
        base=json.loads(routing.ROUTES_PATH.read_text(encoding="utf-8"))["sites"]
        extras=list(routing.SITES_DIRECTORY.glob("*.json"))
        self.assertEqual(len(mapping),len(base)+len(extras))
        self.assertGreaterEqual(
            sum(x["platform"]=="blogger" for x in mapping.values()),18)
        self.assertGreaterEqual(
            sum(x["platform"]=="wordpress" for x in mapping.values()),3)
        self.assertTrue(all(x["publish_enabled"] is False for x in mapping.values()))
        self.assertEqual(mapping["blogger_air_fryers"]["identifier"],"9113728635217260884")
        self.assertEqual(mapping["blogger_liquidificadores"]["identifier"],"5271798990390532475")
        self.assertEqual(mapping["wordpress_casa_decoracao"]["identifier"],
                         "https://casaedecoracao.radartechbr.com.br/")

    def test_liquidificador_not_routed_to_air_fryers_and_vice_versa(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            feed=root/"f.csv"
            with feed.open("w",encoding="utf-8",newline="") as f:
                w=csv.DictWriter(f,fieldnames=["shopId","itemId","productName","productLink","imageUrl"])
                w.writeheader()
                for idx,title in enumerate(["Liquidificador potente","Air Fryer digital","Furadeira 12V","Produto Premium"],1):
                    w.writerow({"shopId":"20","itemId":str(idx),"productName":title,
                                "productLink":f"https://shopee.com.br/item-i.20.{idx}",
                                "imageUrl":"https://cdn.example/image.jpg"})
            with Catalog(root/"db.sqlite3") as cat:
                cat.import_csv(feed,"feed")
                air=plan_site(cat,"blogger_air_fryers")
                liq=plan_site(cat,"blogger_liquidificadores")
                wp=plan_site(cat,"wordpress_radartechbr")
                self.assertEqual(air["product_keys"],["shopee:20:2"])
                self.assertEqual(liq["product_keys"],["shopee:20:1"])
                self.assertIn("shopee:20:3",wp["product_keys"])
                wp_diverse=plan_site(cat,"wordpress_radartechbr",limit=2)
                self.assertIn("shopee:20:3",wp_diverse["product_keys"])
                self.assertEqual(len(wp_diverse["product_keys"]),2)
                self.assertTrue(any(p in wp_diverse["product_keys"]
                                    for p in ("shopee:20:1","shopee:20:2")))

                self.assertEqual(air["mode"],"SAFE_NO_PUBLICATION")
                self.assertNotIn("shopee:20:4",air["product_keys"])
                self.assertNotEqual(air["campaign"],liq["campaign"])
                # A seleção editorial DEVE reaproveitar o link convertido.
                self.assertTrue(cat.cache_link("shopee:20:2",air["campaign"],
                                               "https://s.shopee.com.br/PRECONVERTED"))
                air_again=plan_site(cat,"blogger_air_fryers")
                self.assertEqual(air_again["product_keys"],["shopee:20:2"])
                self.assertEqual(air_again["cached_affiliate_links"],1)
                self.assertEqual(air_again["requiring_conversion"],0)
                self.assertEqual(cat.candidates(air["campaign"],category="cozinha",
                                                niche="air_fryers"),[])


    def test_add_60_future_blogs_using_only_json_without_python_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for number in range(60):
                record={
                    "site_key":f"wordpress_novo_{number:03d}",
                    "platform":"wordpress",
                    "identifier":f"https://blog-{number}.example.test/",
                    "campaign":f"novo{number:03d}",
                    "allowed_niches":["tecnologia/gadgets"],
                    "publish_enabled":False
                }
                (root/f"novo-{number:03d}.json").write_text(
                    json.dumps(record),encoding="utf-8")
            routing.sites.cache_clear()
            try:
                with patch.object(routing,"SITES_DIRECTORY",root):
                    mapping=routing.sites()
                    self.assertEqual(len(mapping),80)
                    self.assertIn("wordpress_novo_059",mapping)
                    self.assertEqual(mapping["wordpress_novo_059"]["campaign"],"novo059")
            finally:
                routing.sites.cache_clear()

    def test_duplicate_registration_rejected_safely(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            route={
                "site_key":"wordpress_casa_decoracao",
                "platform":"wordpress",
                "identifier":"https://other.example.test/",
                "campaign":"uniquecamp",
                "allowed_niches":["tecnologia/gadgets"],
                "publish_enabled":False
            }
            (root/"duplicate.json").write_text(json.dumps(route),encoding="utf-8")
            routing.sites.cache_clear()
            try:
                with patch.object(routing,"SITES_DIRECTORY",root):
                    with self.assertRaisesRegex(ValueError,"Rota ou campanha repetida"):
                        routing.sites()
            finally:
                routing.sites.cache_clear()

    def test_unknown_site_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp, Catalog(Path(tmp)/"state.db") as cat:
            with self.assertRaises(ValueError):
                plan_site(cat,"unknown_blog")
            with self.assertRaises(ValueError):
                plan_site(cat,"blogger_air_fryers",limit=0)


if __name__=="__main__":
    unittest.main()
