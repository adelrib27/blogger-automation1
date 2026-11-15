"""Regressões da importação atômica, feed URL e persistência R2 fake."""
import csv
import io
import os
import json
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from affiliate_hub_v31.catalog import Catalog
from affiliate_hub_v31.feed_download import check_feed_url
from affiliate_hub_v31.ingest import ingest_two
from affiliate_hub_v31 import ingest_cli
from affiliate_hub_v31.r2_state import R2State, StorageError, POINTER, validate_manifest


def feed(path: Path, titles):
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["shopId","itemId","productName","productLink","imageUrl"])
        writer.writeheader()
        for item, title in titles:
            writer.writerow({"shopId":"900","itemId":str(item),"productName":title,
                             "productLink":f"https://shopee.com.br/produto-i.900.{item}",
                             "imageUrl":"https://cdn.example/image.png"})


class FakeS3Error(Exception):
    def __init__(self, code):
        self.response={"Error":{"Code":code}}


class FakeS3:
    def __init__(self):
        self.objects={}
        self.metadata={}

    def get_object(self, *, Bucket, Key):
        if Key not in self.objects:
            raise FakeS3Error("NoSuchKey")
        return {"Body":io.BytesIO(self.objects[Key])}

    def put_object(self, *, Bucket, Key, Body, **_):
        self.objects[Key]=Body

    def upload_file(self, source, bucket, key, ExtraArgs):
        self.objects[key]=Path(source).read_bytes()
        self.metadata[key]=ExtraArgs["Metadata"]

    def head_object(self, *, Bucket, Key):
        return {"Metadata":self.metadata[Key]}

    def download_file(self, bucket, key, destination):
        Path(destination).write_bytes(self.objects[key])


class IngestAndStorageTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root=Path(temp.name)

    def test_two_feeds_dedup_atomic_and_preserve_cached_affiliate(self):
        one=self.root/"one.csv"
        two=self.root/"two.csv"
        db=self.root/"state.sqlite3"
        feed(one,[(1,"Organizador de Cozinha"),(2,"Air Fryer")])
        feed(two,[(2,"Air Fryer"),(3,"Parafusadeira")])
        stats=ingest_two(db,one,two)
        self.assertEqual(stats["input_rows"],4)
        self.assertEqual(stats["input_duplicates_or_existing"],1)
        self.assertEqual(stats["catalog"]["products"],3)
        self.assertEqual(stats["catalog"]["eligible"],3)
        with Catalog(db) as cat:
            self.assertTrue(cat.cache_link("shopee:900:1","blogger","https://s.shopee.com.br/abc"))
        stats2=ingest_two(db,one,two)
        self.assertEqual(stats2["catalog"]["products"],3)
        self.assertEqual(stats2["catalog"]["cached_affiliate_links"],1)

    def test_malformed_second_feed_does_not_replace_first_db(self):
        one=self.root/"one.csv"
        two=self.root/"two.csv"
        db=self.root/"state.sqlite3"
        feed(one,[(1,"Organizador de Cozinha")])
        feed(two,[(2,"Parafusadeira")])
        ingest_two(db,one,two)
        original=db.read_bytes()
        two.write_text("productName,productLink\nParafusadeira\n",encoding="utf-8")
        with self.assertRaises(ValueError):
            ingest_two(db,one,two)
        self.assertEqual(db.read_bytes(),original)

    def test_feed_url_cannot_redirect_to_foreign_host(self):
        good="https://affiliate.shopee.com.br/api/v1/datafeed/download?id=" + "aB09_" * 10
        check_feed_url(good)
        for invalid in [
            good.replace("https://","http://"),
            good.replace("affiliate.shopee.com.br","affiliate.shopee.com.br.evil.test"),
            good.replace("/api/v1/datafeed/download","/admin"),
            good+"&redirect=https://example.com",
            "https://evil.test/api/v1/datafeed/download?id="+"a"*32,
            "https://affiliate.shopee.com.br/api/v1/datafeed/download?id=x",
        ]:
            with self.subTest(invalid=invalid.split("?")[0]):
                with self.assertRaises(ValueError):
                    check_feed_url(invalid)

    def test_r2_snapshot_roundtrip_no_real_cloud(self):
        feed1=self.root/"a.csv";feed2=self.root/"b.csv"
        feed(feed1,[(1,"Organizador de Cozinha")])
        feed(feed2,[(2,"Air Fryer")])
        db=self.root/"state.sqlite3"
        ingest_two(db,feed1,feed2)
        cloud=FakeS3()
        state=R2State(cloud,"v31-private-hub")
        self.assertFalse(state.restore_to(self.root/"missing.sqlite3"))
        uploaded=state.save_from(db)
        self.assertTrue(uploaded["state_saved"])
        self.assertIn(POINTER,cloud.objects)
        restored=self.root/"restored.sqlite3"
        self.assertTrue(state.restore_to(restored))
        with Catalog(restored) as cat:
            self.assertEqual(cat.stats()["products"],2)
            self.assertTrue(cat.integrity())

    def test_r2_snapshot_tampering_detected(self):
        f1=self.root/"a.csv";f2=self.root/"b.csv"
        feed(f1,[(1,"Organizador de Cozinha")]);feed(f2,[(2,"Air Fryer")])
        db=self.root/"state.sqlite3"
        ingest_two(db,f1,f2)
        cloud=FakeS3();state=R2State(cloud,"v31-private-hub")
        state.save_from(db)
        pointer=json.loads(cloud.objects[POINTER])
        cloud.objects[pointer["key"]]=b"broken state bytes"
        target=self.root/"corrupt.sqlite3"
        with self.assertRaises(StorageError):
            state.restore_to(target)
        self.assertFalse(target.exists())

    def test_invalid_or_hostile_snapshot_pointer_rejected(self):
        with self.assertRaises(StorageError):
            validate_manifest({"schema":"v31-editorial-state/v1",
                               "key":"../private/secrets.json",
                               "sha256":"a"*64,
                               "created_utc":"2026-11-15"})
        with self.assertRaises(ValueError):
            R2State(FakeS3(),"../bucket")


    def test_empty_second_feed_preserves_existing_catalog(self):
        first=self.root/"first.csv";second=self.root/"second.csv"
        db=self.root/"database.sqlite3"
        feed(first,[(1,"Air Fryer")])
        feed(second,[(2,"Liquidificador")])
        ingest_two(db,first,second)
        baseline=db.read_bytes()
        feed(second,[])
        with self.assertRaises(ValueError):
            ingest_two(db,first,second)
        self.assertEqual(db.read_bytes(),baseline)

    def test_r2_missing_pointer_needs_explicit_first_run_approval(self):
        cloud=FakeS3()
        state=R2State(cloud,"v31-private-hub")
        urls={"V31_EDITORIAL_DATAFEED_URL_1":
              "https://affiliate.shopee.com.br/api/v1/datafeed/download?id="+"a"*40,
              "V31_EDITORIAL_DATAFEED_URL_2":
              "https://affiliate.shopee.com.br/api/v1/datafeed/download?id="+"b"*40}
        def fake_download(_url, destination):
            target=Path(destination)
            feed(target, [(1 if target.name=="first.csv" else 2,
                           "Air Fryer" if target.name=="first.csv" else "Liquidificador")])
            return target.stat().st_size
        with patch.dict(os.environ, urls, clear=True), \
             patch.object(ingest_cli.R2State, "from_env", return_value=state), \
             patch.object(ingest_cli, "download_feed", side_effect=fake_download):
            with self.assertRaisesRegex(ValueError,"initialization_not_authorized"):
                ingest_cli.run_cloud()
            self.assertNotIn(POINTER,cloud.objects)
        urls["V31_EDITORIAL_R2_ALLOW_INIT"]="CONFIRM_NEW_PRIVATE_CATALOG"
        with patch.dict(os.environ, urls, clear=True), \
             patch.object(ingest_cli.R2State, "from_env", return_value=state), \
             patch.object(ingest_cli, "download_feed", side_effect=fake_download):
            result=ingest_cli.run_cloud()
            self.assertEqual(result["catalog"]["products"],2)
            self.assertTrue(result["state_saved"])
            self.assertIn(POINTER,cloud.objects)


if __name__=="__main__":
    unittest.main()
