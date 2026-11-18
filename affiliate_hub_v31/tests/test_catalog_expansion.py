"""C17 — histórico antigo e links não mudam, mesmo se feeds rotacionarem."""
import csv
import tempfile
import unittest
from pathlib import Path

from affiliate_hub_v31.catalog import Catalog
from affiliate_hub_v31.catalog_expansion import (
    expand, fingerprint_original, install_original_keys,
)
from affiliate_hub_v31.source_category_index import browse_source,source_inventory
from affiliate_hub_v31.title_index import rebuild_index,has_index


class FakeR2:
    def __init__(self,data:bytes):
        self.data=data
        self.writes=0

    def restore_to(self,path):
        Path(path).write_bytes(self.data)
        return True

    def save_from(self,path):
        self.data=Path(path).read_bytes()
        self.writes+=1
        return {"state_saved":True,"retention_pending":False}


class ExpansionSafeTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name)
        self.db=self.root/"state.sqlite3"
        old=self.root/"old.csv"
        self.write(old,[
            ("1","Air Fryer Original",("Home Appliances","Kitchen Appliances","Air Fryers")),
            ("9","Produto antigo só no histórico",("Home & Living","Decoration","")),
        ])
        with Catalog(self.db) as cat:
            cat.import_csv(old,"feed1")
            cat.cache_link("shopee:321:1","campaignold",
                           "https://s.shopee.com.br/old-real-affiliate")
            self.original=cat.stats()
        self.storage=FakeR2(self.db.read_bytes())
        self.feed1=self.root/"feed1.csv"
        self.feed2=self.root/"feed2.csv"
        self.write(self.feed1,[
            ("1","Furadeira Título CONFLITANTE no feed",
             ("Tools","Tools Home Improvement","Drills")),
            ("2","Guarda Roupa Casal Novo",("Home & Living","Furniture","Wardrobes")),
            ("3","Smartwatch com Pulseira",("Mobile Gadgets","Wearables","")),
        ])
        self.write(self.feed2,[
            ("2","Guarda Roupa Casal Novo",("Home & Living","Furniture","")),
            ("4","Air Fryer 6 Litros",("Home Appliances","Kitchen Appliances","")),
        ],levels=2)

    def write(self,path,items,levels=3):
        names=["shopId","itemId","productName","productLink","imageUrl"]
        meta=["globalCategory1","globalCategory2"]
        if levels==3:
            meta.append("globalCategory3")
        with path.open("w",encoding="utf-8",newline="") as f:
            writer=csv.DictWriter(f,fieldnames=names+meta)
            writer.writeheader()
            for iid,title,categories in items:
                writer.writerow({
                    **{"shopId":"321","itemId":iid,"productName":title,
                       "productLink":f"https://shopee.com.br/product/321/{iid}",
                       "imageUrl":"https://cf.shopee.com.br/file/image"},
                    **dict(zip(meta,categories))
                })

    def test_dry_run_preserves_original_data_and_r2_state(self):
        report=expand(self.storage,(self.feed1,self.feed2),execute=False)
        self.assertEqual(report["mode"],"EXPAND_DRY_RUN")
        self.assertEqual(report["previous_catalog"]["products"],2)
        self.assertEqual(report["current_catalog"]["products"],5)
        self.assertEqual(report["current_catalog"]["cached_affiliate_links"],1)
        self.assertTrue(report["existing_products_links_and_review_states_preserved"])
        self.assertFalse(report["snapshot_saved_and_restored"])
        self.assertEqual(self.storage.writes,0)
        self.assertEqual(report["source_categories"]
                         ["products_with_official_source_categories"],4)
        with Catalog(self.db) as original:
            self.assertEqual(original.stats(),self.original)
            self.assertEqual(original.db.execute(
                "SELECT title FROM products WHERE product_key='shopee:321:1'"
            ).fetchone()[0],"Air Fryer Original")

    def test_execute_once_and_restore_old_link_exactly(self):
        report=expand(self.storage,(self.feed1,self.feed2),execute=True)
        self.assertEqual(report["current_catalog"]["products"],5)
        self.assertTrue(report["snapshot_saved_and_restored"])
        self.assertEqual(self.storage.writes,1)
        recovered=self.root/"recovered.db"
        self.storage.restore_to(recovered)
        with Catalog(recovered) as cat:
            self.assertEqual(cat.cached_link("shopee:321:1","campaignold"),
                             "https://s.shopee.com.br/old-real-affiliate")
            self.assertEqual(cat.db.execute(
                "SELECT title FROM products WHERE product_key='shopee:321:1'"
            ).fetchone()[0],"Air Fryer Original")
            self.assertEqual(source_inventory(cat)
                             ["products_with_official_source_categories"],4)
            results=browse_source(cat,level1="Home & Living",level2="Furniture")
            self.assertEqual(len(results),1)
            self.assertFalse(results[0]["editorial_approved"])

    def test_incremental_refresh_rebuilds_existing_fts_index(self):
        with Catalog(self.db) as catalog:
            rebuild_index(catalog)
        self.storage=FakeR2(self.db.read_bytes())
        result=expand(self.storage,(self.feed1,self.feed2),execute=True)
        self.assertTrue(result["search_index_updated"])
        check=self.root/"searchable-restored.sqlite3"
        self.storage.restore_to(check)
        with Catalog(check) as catalog:
            self.assertTrue(has_index(catalog))
            self.assertEqual(catalog.db.execute(
                "SELECT COUNT(*) FROM v31_catalog_fts"
            ).fetchone()[0],5)
            matches=catalog.db.execute("""
                SELECT product_key FROM v31_catalog_fts
                WHERE v31_catalog_fts MATCH ?
            """,('"guarda" OR "roupa"',)).fetchall()
            self.assertIn(("shopee:321:2",),matches)
            self.assertEqual(catalog.cached_link("shopee:321:1","campaignold"),
                             "https://s.shopee.com.br/old-real-affiliate")

    def test_refresh_builds_separate_universal_sidecar_without_bloating_catalog(self):
        report=expand(self.storage,(self.feed1,self.feed2),execute=True)
        self.assertEqual(report["universal_inventory"]["products_indexed"],5)
        self.assertEqual(report["universal_inventory"]["new_approvals"],0)
        self.assertEqual(report["universal_index_location"],"R2_SIDECAR")
        restored=self.root/"base_check.sqlite3"
        self.storage.restore_to(restored)
        with Catalog(restored) as cat:
            self.assertEqual(cat.db.execute("""
              SELECT count(*) FROM sqlite_master
              WHERE type='table' AND name='v31_universal_inventory'
            """).fetchone()[0],0)
            self.assertEqual(cat.db.execute("""
              SELECT moderation FROM products WHERE product_key='shopee:321:9'
            """).fetchone()[0],"review")
            self.assertEqual(cat.db.execute(
                "SELECT count(*) FROM affiliate_links").fetchone()[0],1)
        self.assertEqual(self.storage.writes,1)

    def test_second_run_does_not_add_duplicate_products(self):
        expand(self.storage,(self.feed1,self.feed2),execute=True)
        again=expand(self.storage,(self.feed1,self.feed2),execute=False)
        self.assertEqual(again["current_catalog"]["products"],5)
        self.assertEqual(sum(x["new_products"] for x in again["feeds"]),0)
        self.assertEqual(self.storage.writes,1)


if __name__=="__main__":
    unittest.main()
