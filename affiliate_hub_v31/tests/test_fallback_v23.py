"""C6: fallback CSV/R2 universal para contrato de ranking e intenção v2.3."""
import csv
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from affiliate_hub_v31.catalog import Catalog
from affiliate_hub_v31.fallback_v23 import (
    FallbackUnavailable, candidates_from_catalog, emit_v23_outputs,
    semantic_score, load_configuration,
)


class FallbackV23Tests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name)
        feed=self.root/"products.csv"
        with feed.open("w",encoding="utf-8",newline="") as stream:
            w=csv.DictWriter(stream,fieldnames=["shopId","itemId","productName","productLink","imageUrl"])
            w.writeheader()
            for i,title in enumerate([
                "Luminária Solar para Jardim em LED",
                "Luminária de Mesa para Sala",
                "Capa para Liquidificador 2 Litros",
            ],1):
                w.writerow({
                    "shopId":"904","itemId":str(i),"productName":title,
                    "productLink":f"https://shopee.com.br/item-i.904.{i}",
                    "imageUrl":f"https://img.example.invalid/p{i}.jpg",
                })
        self.db=self.root/"state.sqlite3"
        with Catalog(self.db) as cat:
            cat.import_csv(feed,"feed1")
            cat.cache_link("shopee:904:1","casaedecoracaowp",
                           "https://s.shopee.com.br/verified-one")
            cat.cache_link("shopee:904:2","radarwp",
                           "https://s.shopee.com.br/radar-only")
        self.config={"categories":{
            "Area Externa":["luminaria solar jardim"],
            "Sala":["luminaria mesa"],
        }}
        self.rules={"rules":{
            "luminaria solar jardim":{
                "require_groups":[["luminaria"],["solar"],["jardim"]],
                "block_phrases":["automotiva"],
            }
        }}

    def test_valid_cached_links_only_no_fabricated_metrics(self):
        result=candidates_from_catalog(self.db,"wordpress_casa_decoracao",
                    self.config,self.rules,limit=12)
        self.assertEqual(len(result),1)
        row=result[0]
        self.assertEqual(row["itemId"],"1")
        self.assertEqual(row["offerLink"],"https://s.shopee.com.br/verified-one")
        self.assertEqual(row["intentMatchedKeywords"],["luminaria solar jardim"])
        self.assertEqual(row["categories"],["Area Externa"])
        self.assertEqual(row["sourceModes"],["csv_r2_verified_affiliate_cache"])
        self.assertIsNone(row["sales"])
        self.assertIsNone(row["ratingStar"])
        self.assertIsNone(row["commission"])

    def test_campaign_isolation_and_no_organic_productlink(self):
        config={"categories":{"Sala":["luminaria mesa"]}}
        self.assertEqual(candidates_from_catalog(self.db,"wordpress_casa_decoracao",
                         config,self.rules),[])
        radar=candidates_from_catalog(self.db,"wordpress_radartechbr",config,self.rules)
        self.assertEqual(len(radar),1)
        self.assertEqual(radar[0]["offerLink"],"https://s.shopee.com.br/radar-only")
        self.assertNotIn("item-i.904.2",radar[0]["offerLink"])

    def test_files_match_existing_intent_report_and_ranking_contract(self):
        rows=candidates_from_catalog(self.db,"wordpress_casa_decoracao",
                    self.config,self.rules,limit=12)
        output=self.root/"outputs"
        self.assertEqual(emit_v23_outputs(rows,self.config,output),1)
        rank=json.loads((output/"ranking.json").read_text(encoding="utf-8"))
        report=json.loads((output/"intent_report.json").read_text(encoding="utf-8"))
        self.assertEqual(rank["ranking"][0]["itemId"],"1")
        self.assertEqual(rank["ranking"][0]["imageUrl"],
                         "https://img.example.invalid/p1.jpg")
        self.assertEqual(report["version"],"2.3")
        self.assertEqual(report["ranking"][0]["itemId"],"1")
        self.assertEqual(report["ranking"][0]["offerLink"],
                         rank["ranking"][0]["offerLink"])
        self.assertEqual(report["ranking"][0]["intentMatchedKeywords"],
                         rank["ranking"][0]["intentMatchedKeywords"])
        self.assertTrue((output/"ranking.csv").is_file())
        self.assertTrue((output/"search_signals.json").is_file())

    def test_empty_never_writes_a_successful_output(self):
        out=self.root/"empty"
        with self.assertRaisesRegex(FallbackUnavailable,"no_verified_cached_affiliate_link"):
            emit_v23_outputs([],self.config,out)
        self.assertFalse((out/"intent_report.json").exists())

    def test_semantic_rules_block_incompatible_accessories(self):
        rule={"rules":{"furadeira":{"require_groups":[["furadeira"]],
                                   "block_phrases":["broca para furadeira"]}}}
        self.assertEqual(semantic_score("Broca para Furadeira","furadeira",rule),0.0)
        self.assertEqual(semantic_score("Furadeira 12V","furadeira",rule),1.0)

    def test_invalid_site_fails_closed(self):
        with self.assertRaisesRegex(FallbackUnavailable,"site_not_registered"):
            candidates_from_catalog(self.db,"wordpress_inventado",
                                    self.config,self.rules)

    def test_readonly_database_not_modified(self):
        before=self.db.read_bytes()
        candidates_from_catalog(self.db,"wordpress_casa_decoracao",
                                self.config,self.rules)
        after=self.db.read_bytes()
        self.assertEqual(before,after)

    def test_load_existing_shape_generic_config(self):
        config=self.root/"config.json"
        rules=self.root/"intent.json"
        config.write_text(json.dumps(self.config),encoding="utf-8")
        rules.write_text(json.dumps(self.rules),encoding="utf-8")
        cfg,doc=load_configuration(config,rules)
        self.assertEqual(cfg,self.config)
        self.assertEqual(doc,self.rules)



    def test_protected_legacy_cached_link_never_enters_wordpress_fallback(self):
        from affiliate_hub_v31.source_category_index import create_source_category_schema
        with Catalog(self.db) as cat:
            create_source_category_schema(cat)
            with cat.db:
                cat.db.execute("""
                    INSERT INTO product_source_categories
                    (product_key,source,level1,level2,level3,status)
                    VALUES(?,?,?,?,?,?)
                """,("shopee:904:1","feed","health","vitamins","","matched"))
            original=cat.cached_link("shopee:904:1","casaedecoracaowp")
            self.assertEqual(original,"https://s.shopee.com.br/verified-one")
        before=self.db.read_bytes()
        blocked=candidates_from_catalog(self.db,"wordpress_casa_decoracao",
                                        self.config,self.rules)
        after=self.db.read_bytes()
        self.assertEqual(blocked,[])
        self.assertEqual(before,after)
        radar=candidates_from_catalog(self.db,"wordpress_radartechbr",
                                      {"categories":{"Sala":["luminaria mesa"]}},
                                      self.rules)
        self.assertEqual(len(radar),1)
        self.assertEqual(radar[0]["itemId"],"2")

    def test_conflicting_source_even_with_matched_feed_rejected_for_fallback(self):
        from affiliate_hub_v31.source_category_index import create_source_category_schema
        with Catalog(self.db) as cat:
            create_source_category_schema(cat)
            with cat.db:
                cat.db.execute("""
                    INSERT INTO product_source_categories
                    (product_key,source,level1,level2,level3,status)
                    VALUES(?,?,?,?,?,?)
                """,("shopee:904:1","first","home living","decoration","","matched"))
                cat.db.execute("""
                    INSERT INTO product_source_categories
                    (product_key,source,level1,level2,level3,status)
                    VALUES(?,?,?,?,?,?)
                """,("shopee:904:1","second","home living","decoration","","conflict"))
        self.assertEqual(candidates_from_catalog(
            self.db,"wordpress_casa_decoracao",self.config,self.rules),[])

if __name__=="__main__":
    unittest.main()
