"""C4 piloto sem APIs externas; mock de Shopee e storage R2."""
import csv
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from affiliate_hub_v31.catalog import Catalog
from affiliate_hub_v31.conversion_pilot import pilot


class MemoryState:
    def __init__(self, initial: Path):
        self.contents=initial.read_bytes()
        self.saves=0

    def restore_to(self, destination: Path):
        destination.write_bytes(self.contents)
        return True

    def save_from(self, path: Path):
        self.contents=path.read_bytes()
        self.saves += 1
        return {"state_saved":True,"retention_pending":False}


class Response:
    status=200
    def __enter__(self): return self
    def __exit__(self,*_): return False
    def read(self,*_):
        return json.dumps({"data":{"generateShortLink":{
            "shortLink":"https://s.shopee.com.br/pilot-test"}}}).encode()


class ConversionPilotTests(unittest.TestCase):
    def test_pilot_saves_one_and_second_run_uses_cache(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            file=root/"feed.csv"
            with file.open("w",encoding="utf-8",newline="") as stream:
                writer=csv.DictWriter(stream,fieldnames=["shopId","itemId","productName","productLink","imageUrl"])
                writer.writeheader()
                writer.writerow({"shopId":"123","itemId":"456",
                    "productName":"Air Fryer Modelo A","productLink":"https://shopee.com.br/product-i.123.456",
                    "imageUrl":"https://img.example.invalid/a.jpg"})
            local=root/"catalog.sqlite3"
            with Catalog(local) as cat:
                cat.import_csv(file,"feed")
            store=MemoryState(local)
            with patch("affiliate_hub_v31.converter.urllib.request.urlopen",return_value=Response()) as mocked:
                result=pilot(store,"APPID","SECRET")
                self.assertTrue(result["created_now"])
                self.assertTrue(result["restored_and_verified"])
                self.assertEqual(mocked.call_count,1)
                repeat=pilot(store,"APPID","SECRET")
                self.assertTrue(repeat["reused_from_cache"])
                self.assertEqual(mocked.call_count,1)
                self.assertEqual(store.saves,1)


if __name__=="__main__":
    unittest.main()
