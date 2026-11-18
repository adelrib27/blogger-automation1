"""O índice de 203k SKUs usa objeto R2 próprio, sem inflar SQLite principal."""
import io
import sqlite3
import tempfile
import unittest
from pathlib import Path

from affiliate_hub_v31.catalog import Catalog
from affiliate_hub_v31.r2_state import R2State, StorageError
from affiliate_hub_v31.universal_index_storage import UniversalIndexStorage, POINTER
from affiliate_hub_v31.universal_inventory import rebuild_universal_inventory
from affiliate_hub_v31.source_category_index import create_source_category_schema


class NotFound(Exception):
    response={"Error":{"Code":"NoSuchKey"}}


class FakeS3:
    def __init__(self):
        self.objects={}
        self.meta={}
    def get_object(self,*,Bucket,Key):
        if Key not in self.objects:
            raise NotFound()
        return {"Body":io.BytesIO(self.objects[Key])}
    def upload_file(self,filepath,bucket,key,ExtraArgs=None):
        self.objects[key]=Path(filepath).read_bytes()
        self.meta[key]=(ExtraArgs or {}).get("Metadata",{})
    def head_object(self,*,Bucket,Key):
        return {"Metadata":self.meta[Key]}
    def put_object(self,*,Bucket,Key,Body,**kwargs):
        self.objects[Key]=Body
    def download_file(self,bucket,key,filepath):
        Path(filepath).write_bytes(self.objects[key])
    def list_objects_v2(self,*,Bucket,Prefix,MaxKeys,**kwargs):
        return {"Contents":[{"Key":x} for x in self.objects if x.startswith(Prefix)],
                "IsTruncated":False}
    def delete_object(self,*,Bucket,Key):
        self.objects.pop(Key,None)


class UniversalSidecarTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name)
        self.catalog=self.root/"catalog.sqlite3"
        with Catalog(self.catalog) as cat:
            create_source_category_schema(cat)
            with cat.db:
                for index,approved in ((1,True),(2,False)):
                    key=f"shopee:100:{index}"
                    cat.db.execute("""
                      INSERT INTO products(product_key,shop_id,item_id,title,
                          description,origin_url,image_url,moderation,
                          moderation_reason,first_source,last_seen_utc)
                      VALUES(?,?,?,?,?,?,?,?,?,?,?)
                    """,(key,"100",str(index),
                         "Air Fryer Digital" if approved else "Organizador",
                         "",f"https://shopee.com.br/product/100/{index}",
                         "https://cf.shopee.com.br/file/p",
                         "eligible" if approved else "review",
                         "" if approved else "taxonomy_unclassified",
                         "test","2026-11-18T00:00:00Z"))
                    cat.db.execute("""
                      INSERT INTO product_taxonomy
                      (product_key,category,niche,status,reason,version)
                      VALUES(?,?,?,?,?,?)
                    """,(key,"cozinha","air_fryers",
                         "matched" if approved else "review","test","test"))
                    cat.db.execute("""
                      INSERT INTO product_source_categories
                      (product_key,source,level1,level2,level3,status)
                      VALUES(?,?,?,?,?,?)
                    """,(key,"feed1","home appliances","kitchen appliances",
                         "","matched"))
            cat.cache_link("shopee:100:1","campanha_existente",
                "https://s.shopee.com.br/cached-link")
        self.s3=FakeS3()
        self.store=UniversalIndexStorage(R2State(self.s3,"test-bucket"))

    def test_sidecar_build_does_not_add_table_or_mutate_catalog(self):
        before=self.catalog.read_bytes()
        sidecar=self.root/"sidecar.sqlite3"
        with Catalog(self.catalog) as cat:
            with sqlite3.connect(sidecar) as index:
                result=rebuild_universal_inventory(cat,sidecar=index)
            self.assertEqual(cat.db.execute("""
              SELECT count(*) FROM sqlite_master
              WHERE name='v31_universal_inventory'
            """).fetchone()[0],0)
            self.assertEqual(cat.db.execute(
                "SELECT count(*) FROM affiliate_links").fetchone()[0],1)
        self.assertEqual(self.catalog.read_bytes(),before)
        self.assertEqual(result["products_indexed"],2)
        self.assertEqual(result["inventory_approved_preexisting"],1)
        self.assertEqual(result["inventory_review_required"],1)
        self.assertEqual(self.store.save_from(sidecar,product_count=2)["index_saved"],True)
        restored=self.root/"restored.sqlite3"
        self.assertTrue(self.store.restore_to(restored,expected_product_count=2))
        with sqlite3.connect(restored) as db:
            self.assertEqual(db.execute(
                "SELECT count(*) FROM v31_universal_inventory").fetchone()[0],2)
        self.assertIn(POINTER,self.s3.objects)

    def test_expected_product_count_refuses_stale_index(self):
        sidecar=self.root/"sidecar.sqlite3"
        with Catalog(self.catalog) as cat,sqlite3.connect(sidecar) as i:
            rebuild_universal_inventory(cat,sidecar=i)
        self.store.save_from(sidecar,product_count=2)
        with self.assertRaises(StorageError):
            self.store.restore_to(self.root/"stale.sqlite3",
                                  expected_product_count=3)

    def test_review_hint_count_is_verified_after_restore(self):
        sidecar=self.root/"hint-index.sqlite3"
        with Catalog(self.catalog) as cat, sqlite3.connect(sidecar) as db:
            rebuild_universal_inventory(cat,sidecar=db)
            db.execute("""
              CREATE TABLE v31_unclassified_review_hints(
                product_key TEXT PRIMARY KEY,review_only INTEGER NOT NULL
                CHECK(review_only=1))
            """)
            db.execute("""
              INSERT INTO v31_unclassified_review_hints VALUES(?,1)
            """,("shopee:100:2",))
        self.store.save_from(sidecar,product_count=2)
        good=self.root/"hint-good.sqlite3"
        self.assertTrue(self.store.restore_to(
            good,expected_product_count=2,expected_review_hint_count=1))
        with self.assertRaisesRegex(StorageError,
                                    "universal_index_hint_count_mismatch"):
            self.store.restore_to(
                self.root/"hint-wrong.sqlite3",
                expected_product_count=2,expected_review_hint_count=2)
        self.assertFalse((self.root/"hint-wrong.sqlite3").exists())

    def test_explicit_hint_expectation_rejects_legacy_without_table(self):
        sidecar=self.root/"legacy-index.sqlite3"
        with Catalog(self.catalog) as cat, sqlite3.connect(sidecar) as db:
            rebuild_universal_inventory(cat,sidecar=db)
        self.store.save_from(sidecar,product_count=2)
        with self.assertRaisesRegex(StorageError,
                                    "universal_index_invalid_schema"):
            self.store.restore_to(
                self.root/"legacy-hints.sqlite3",
                expected_product_count=2,expected_review_hint_count=0)

    def test_restore_hash_tamper_is_blocked(self):
        sidecar=self.root/"sidecar.sqlite3"
        with Catalog(self.catalog) as cat,sqlite3.connect(sidecar) as i:
            rebuild_universal_inventory(cat,sidecar=i)
        self.store.save_from(sidecar,product_count=2)
        key=next(k for k in self.s3.objects if "snapshots/" in k)
        self.s3.objects[key]=b"tampered"
        with self.assertRaises(StorageError):
            self.store.restore_to(self.root/"tampered.sqlite3",
                                  expected_product_count=2)


if __name__=="__main__":
    unittest.main()
