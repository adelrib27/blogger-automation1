"""C15: pool de pré-conversão independente de nichos dos blogs atuais.

Nenhuma API real, senha ou R2 real. Usa cópias SQLite locais no teste.
"""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from affiliate_hub_v31.catalog import Catalog
from affiliate_hub_v31.converter import ConversionError
from affiliate_hub_v31.library_pool import (
    LibraryPoolError, coverage, library_candidates, replenish_library,
)


class FakeR2:
    def __init__(self, content: bytes):
        self.state=content
        self.saves=0

    def restore_to(self, path):
        Path(path).write_bytes(self.state)
        return True

    def save_from(self, path):
        self.state=Path(path).read_bytes()
        self.saves+=1
        return {"state_saved":True,"retention_pending":False}


class UniversalLibraryTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name)
        self.file=self.root/"library.sqlite3"
        with Catalog(self.file) as catalog:
            with catalog.db:
                for i,(cat,niche) in enumerate([
                    ("tecnologia","audio"),("tecnologia","audio"),
                    ("decoracao","iluminacao"),("decoracao","iluminacao"),
                    ("beleza","cabelos"),("beleza","cabelos"),
                ],1):
                    key=f"shopee:{900+i}:{800+i}"
                    catalog.db.execute("""
                        INSERT INTO products(product_key,shop_id,item_id,title,
                            description,origin_url,image_url,moderation,
                            moderation_reason,first_source,last_seen_utc)
                        VALUES(?,?,?,?,?,?,?,?,?,?,?)
                    """,(key,str(900+i),str(800+i),f"Produto exemplo {i}","",
                         f"https://shopee.com.br/product/{900+i}/{800+i}",
                         "https://cf.shopee.com.br/file/test","eligible","",
                         "feed_110k","2026-11-17T00:00:00Z"))
                    catalog.db.execute("""
                        INSERT INTO product_taxonomy
                            (product_key,category,niche,status,reason,version)
                        VALUES(?,?,?,?,?,?)
                    """,(key,cat,niche,"matched","test","v31-test"))
                # Produto de nicho que AINDA NÃO foi classificado; manter no
                # acervo para futuro blog, mas nunca criar link sem revisão.
                catalog.db.execute("""
                    INSERT INTO products(product_key,shop_id,item_id,title,
                        description,origin_url,image_url,moderation,
                        moderation_reason,first_source,last_seen_utc)
                    VALUES(?,?,?,?,?,?,?,?,?,?,?)
                """,("shopee:999:999","999","999","Nicho futuro desconhecido","",
                     "https://shopee.com.br/product/999/999",
                     "https://cf.shopee.com.br/file/test",
                     "review","taxonomy_unclassified","feed_110k",
                     "2026-11-17T00:00:00Z"))
                catalog.db.execute("""
                    INSERT INTO product_taxonomy
                        (product_key,category,niche,status,reason,version)
                    VALUES(?,?,?,?,?,?)
                """,("shopee:999:999","","","review","unclassified","v31-test"))
        self.storage=FakeR2(self.file.read_bytes())

    def test_pool_without_any_site_profiles_covers_unrelated_categories(self):
        with Catalog(self.file) as catalog:
            selected=library_candidates(catalog,"librarybase",3,rotation=0)
            cats=[catalog.db.execute(
                "SELECT category FROM product_taxonomy WHERE product_key=?",
                (key,)).fetchone()[0] for key in selected]
            self.assertEqual(len(selected),3)
            self.assertEqual(set(cats),{"beleza","decoracao","tecnologia"})
            self.assertNotIn("shopee:999:999",selected)
            self.assertEqual(coverage(catalog,"librarybase")
                             ["products_in_universal_catalog"],7)
            self.assertEqual(coverage(catalog,"librarybase")
                             ["products_pending_or_under_review"],1)
            self.assertEqual(coverage(catalog,"librarybase")
                             ["blog_profiles_used_for_selection"],0)

    def test_rotates_category_start_and_avoids_reconverting_same_campaign(self):
        with Catalog(self.file) as catalog:
            first=library_candidates(catalog,"librarybase",3,rotation=0)
            second=library_candidates(catalog,"librarybase",3,rotation=1)
            self.assertNotEqual(first[0],second[0])
            catalog.cache_link(first[0],"librarybase",
                               "https://s.shopee.com.br/library-converted")
            new=library_candidates(catalog,"librarybase",3,rotation=0)
            self.assertNotIn(first[0],new)
            self.assertIn(first[0],library_candidates(
                catalog,"newblogcampaign",3,rotation=0))
            self.assertIsNone(catalog.cached_link(first[0],"newblogcampaign"))

    def test_dryrun_has_zero_shopee_or_r2_mutations(self):
        with patch("affiliate_hub_v31.library_pool.convert_one",
                   side_effect=AssertionError("network forbidden")):
            report=replenish_library(self.storage,"librarybase",
                                     budget=3,execute=False,rotation=0)
        self.assertEqual(report["planned"],3)
        self.assertEqual(report["attempts"],0)
        self.assertEqual(report["converted"],0)
        self.assertEqual(self.storage.saves,0)
        self.assertEqual(report["publication_calls"],0)

    def test_execute_saves_and_restores_one_snapshot_only(self):
        def fake_convert(catalog,key,campaign,_id,_secret):
            added=catalog.cache_link(key,campaign,
                  "https://s.shopee.com.br/verified-by-shopee")
            return "https://s.shopee.com.br/verified-by-shopee",added
        with patch("affiliate_hub_v31.library_pool.convert_one",
                   side_effect=fake_convert):
            report=replenish_library(self.storage,"librarybase",
                       budget=3,execute=True,rotation=0,
                       app_id="TEST",app_secret="TEST")
        self.assertEqual(report["attempts"],3)
        self.assertEqual(report["converted"],3)
        self.assertEqual(report["r2_snapshot_saved"],True)
        self.assertEqual(self.storage.saves,1)
        self.assertEqual(report["links_copied_across_campaigns"],0)
        with Catalog(self.file) as original:
            self.assertEqual(coverage(original,"librarybase")
                             ["pool_campaign_links_converted"],0)

    def test_api_failure_stops_further_calls(self):
        with patch("affiliate_hub_v31.library_pool.convert_one",
                   side_effect=ConversionError("graphql_error")) as patched:
            report=replenish_library(self.storage,"librarybase",
                       budget=3,execute=True,rotation=0,
                       app_id="TEST",app_secret="TEST")
        self.assertEqual(patched.call_count,1)
        self.assertEqual(report["attempts"],1)
        self.assertTrue(report["api_interrupted"])
        self.assertEqual(report["converted"],0)
        self.assertEqual(self.storage.saves,0)

    def test_unconfigured_campaign_rejected(self):
        with self.assertRaises(ValueError):
            replenish_library(self.storage,"",budget=3)
        with self.assertRaises(LibraryPoolError):
            replenish_library(self.storage,"librarybase",budget=4)


if __name__=="__main__":
    unittest.main()
