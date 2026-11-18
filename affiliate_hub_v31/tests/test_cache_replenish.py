"""C8: orçamento global, round-robin, R2, zero publicações e failover."""
import csv
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from affiliate_hub_v31.catalog import Catalog
from affiliate_hub_v31.converter import ConversionError
from affiliate_hub_v31.cache_replenish import replenish, rotated_sites
from affiliate_hub_v31.shadow_audit import load_profiles


class MemoryR2:
    def __init__(self, source: Path):
        self.data=source.read_bytes()
        self.reads=0
        self.writes=0
    def restore_to(self, path):
        self.reads+=1
        Path(path).write_bytes(self.data)
        return True
    def save_from(self, path):
        self.writes+=1
        self.data=Path(path).read_bytes()
        return {"state_saved":True,"retention_pending":False}


class ReplenishTests(unittest.TestCase):
    def setUp(self):
        folder=tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root=Path(folder.name)
        csvfile=self.root/"f.csv"
        with csvfile.open("w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=[
                "shopId","itemId","productName","productLink","imageUrl"
            ])
            w.writeheader()
            for i,title in enumerate([
                "Luminária Solar LED para Jardim",
                "Luminária Solar para Jardim Dois",
                "Furadeira de Impacto 12V",
                "Caixa de Som Bluetooth Portátil",
            ],1):
                w.writerow({
                    "shopId":"74","itemId":str(i),"productName":title,
                    "productLink":f"https://shopee.com.br/item-i.74.{i}",
                    "imageUrl":"https://image.example.invalid/p.png",
                })
        self.catalog_path=self.root/"catalog.sqlite3"
        with Catalog(self.catalog_path) as cat:
            cat.import_csv(csvfile,"f")
        self.storage=MemoryR2(self.catalog_path)
        self.profiles=load_profiles()
        self.calls=[]
        def fake_convert(catalog, product_key, campaign, app, secret):
            self.calls.append((product_key,campaign))
            link="https://s.shopee.com.br/test-"+str(len(self.calls))
            catalog.cache_link(product_key,campaign,link)
            return link,True
        self.fake_convert=fake_convert

    def test_rotation_scales_beyond_three_blogs(self):
        names=[f"site_{i}" for i in range(50)]
        seen=set()
        for d in range(17):
            seen.update(rotated_sites(names,d+1,3)[:3])
        self.assertEqual(len(seen),50)

    def test_dry_run_reads_only_and_never_calls_shopee(self):
        with patch("affiliate_hub_v31.cache_replenish.convert_one",
                   side_effect=AssertionError("must not mutate")):
            report=replenish(self.storage,"all",budget=3,execute=False,
                             ordinal=3,profiles=self.profiles)
        self.assertEqual(report["mode"],"DRY_RUN")
        self.assertEqual(report["shopee_mutation_attempts"],0)
        self.assertEqual(report["converted"],0)
        self.assertEqual(report["publication_calls"],0)
        self.assertEqual(self.storage.writes,0)
        self.assertEqual(self.storage.reads,1)
        self.assertLessEqual(sum(x["eligible_for_next_conversion"]
                                 for x in report["plan"]),3)

    def test_live_limited_to_three_attempts_and_one_snapshot(self):
        with patch("affiliate_hub_v31.cache_replenish.convert_one",
                   side_effect=self.fake_convert):
            report=replenish(self.storage,"all",budget=3,execute=True,
                             ordinal=3,profiles=self.profiles,
                             app_id="TESTID",app_secret="TESTSECRET")
        self.assertEqual(report["converted"],3)
        self.assertEqual(report["shopee_mutation_attempts"],3)
        self.assertEqual(len(self.calls),3)
        self.assertEqual(len(set(c for _,c in self.calls)),3)
        self.assertEqual(self.storage.writes,1)
        self.assertEqual(self.storage.reads,2)
        self.assertTrue(report["r2_snapshot_saved"])
        with tempfile.TemporaryDirectory() as dirname:
            path=Path(dirname)/"check.sqlite3"
            self.storage.restore_to(path)
            with Catalog(path) as cat:
                self.assertEqual(cat.stats()["cached_affiliate_links"],3)

    def test_api_error_early_circuit_breaker_persists_partial(self):
        def partial(catalog,product,campaign,a,s):
            if len(self.calls):
                raise ConversionError("graphql_error")
            return self.fake_convert(catalog,product,campaign,a,s)
        with patch("affiliate_hub_v31.cache_replenish.convert_one",
                   side_effect=partial):
            report=replenish(self.storage,"all",budget=3,execute=True,
                             ordinal=3,profiles=self.profiles,
                             app_id="ID",app_secret="SECRET")
        self.assertEqual(report["converted"],1)
        self.assertEqual(report["shopee_mutation_attempts"],2)
        self.assertTrue(report["api_interrupted"])
        self.assertEqual(self.storage.writes,1)

    def test_specific_site_can_convert_two_distinct_products(self):
        with patch("affiliate_hub_v31.cache_replenish.convert_one",
                   side_effect=self.fake_convert):
            report=replenish(self.storage,"wordpress_casa_decoracao",
                             budget=2,execute=True,ordinal=1,
                             profiles=self.profiles,
                             app_id="ID",app_secret="SECRET")
        self.assertEqual(report["converted"],2)
        self.assertEqual(len({key for key,_ in self.calls}),2)
        self.assertEqual(len({campaign for _,campaign in self.calls}),1)

    def test_no_secret_no_mutation(self):
        with self.assertRaisesRegex(ConversionError,"credentials_missing"):
            replenish(self.storage,"all",budget=1,execute=True,
                      profiles=self.profiles,app_id="",app_secret="")
        self.assertEqual(self.storage.reads,0)
        self.assertEqual(self.storage.writes,0)


if __name__=="__main__":
    unittest.main()
