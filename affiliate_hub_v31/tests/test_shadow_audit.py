"""C8: auditoria read-only realista, perfis configuráveis, falha fechada."""
import csv
import json
import tempfile
import unittest
from pathlib import Path

from affiliate_hub_v31.catalog import Catalog
from affiliate_hub_v31.shadow_audit import (
    ShadowError, audit, audit_site, load_profiles, relative_config,
)


class FakeR2:
    def __init__(self,source:Path):
        self.content=source.read_bytes()
        self.reads=0
        self.writes=0

    def restore_to(self,path):
        self.reads+=1
        Path(path).write_bytes(self.content)
        return True

    def save_from(self,path):
        self.writes+=1
        raise AssertionError("SHADOW must never save")


class ShadowTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name)
        feed=self.root/"f.csv"
        with feed.open("w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=[
                "shopId","itemId","productName","productLink","imageUrl"
            ])
            w.writeheader()
            for i,title in enumerate(["Luminária Solar LED para Jardim",
                                      "Furadeira de Impacto 12V"],1):
                w.writerow({
                    "shopId":"55","itemId":str(i),"productName":title,
                    "productLink":f"https://shopee.com.br/item-i.55.{i}",
                    "imageUrl":"https://image.example.invalid/p.png"
                })
        self.db=self.root/"catalog.sqlite3"
        with Catalog(self.db) as catalog:
            catalog.import_csv(feed,"f1")
            catalog.cache_link("shopee:55:1","casaedecoracaowp",
                "https://s.shopee.com.br/casa-test")
            catalog.cache_link("shopee:55:2","oficinawp",
                "https://s.shopee.com.br/oficina-test")

    def test_existing_profiles_are_site_registry_driven(self):
        profiles=load_profiles()
        self.assertEqual(set(profiles),{
            "wordpress_casa_decoracao","wordpress_oficina_garagem",
            "wordpress_radartechbr",
        })
        self.assertEqual(profiles["wordpress_radartechbr"]["daily_slots"],5)

    def test_shadow_does_not_modify_r2_and_reports_unready(self):
        storage=FakeR2(self.db)
        payload=audit(storage,profiles=load_profiles())
        self.assertEqual(storage.reads,1)
        self.assertEqual(storage.writes,0)
        self.assertEqual(payload["publication_calls"],0)
        self.assertEqual(payload["shopee_api_calls"],0)
        self.assertEqual(payload["profiles_evaluated"],3)
        self.assertEqual(payload["sites_shadow_ready"],0)
        bysite={x["site_key"]:x for x in payload["sites"]}
        self.assertEqual(bysite["wordpress_casa_decoracao"]["cached_links_for_campaign"],1)
        self.assertEqual(bysite["wordpress_casa_decoracao"]["target_usable_products"],9)
        self.assertEqual(bysite["wordpress_oficina_garagem"]["target_usable_products"],6)
        self.assertEqual(bysite["wordpress_radartechbr"]["target_usable_products"],15)
        self.assertEqual(len(bysite["wordpress_radartechbr"]["required_categories_missing"]),5)
        self.assertNotIn("offerLink",json.dumps(payload))
        self.assertNotIn("s.shopee.com.br",json.dumps(payload))

    def test_selection_is_site_specific(self):
        storage=FakeR2(self.db)
        value=audit(storage,"wordpress_casa_decoracao")
        self.assertEqual(value["profiles_evaluated"],1)
        self.assertEqual(value["sites"][0]["site_key"],"wordpress_casa_decoracao")
        with self.assertRaisesRegex(ShadowError,"unknown_or_unconfigured_site"):
            audit(storage,"blogger_nao_configurado")

    def test_unsafe_profile_config_is_rejected(self):
        for path in ("/etc/passwd","../outside.json","./outside.json"):
            with self.assertRaises(ShadowError):
                relative_config(path)
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            (root/"not-exist.json").write_text("{}")
            with self.assertRaises(ShadowError):
                relative_config("missing.json",root)

    def test_unknown_required_source_category_blocked(self):
        profiles=load_profiles()
        fake={**profiles["wordpress_casa_decoracao"],
              "required_source_categories":["FICTITIOUS"]}
        with self.assertRaisesRegex(ShadowError,"profile_required_categories_unknown"):
            audit_site(self.db,fake)


if __name__=="__main__":
    unittest.main()
