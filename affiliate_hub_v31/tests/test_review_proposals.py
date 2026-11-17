"""C22: propostas auditáveis, nunca aprovações, com source facet + texto."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from affiliate_hub_v31.catalog import Catalog
from affiliate_hub_v31.editorial import EditorialError, EditorialLedger
from affiliate_hub_v31.review_proposals import (
    ProposalError, propose_review_batch, summarize_review_batch,
)
from affiliate_hub_v31.source_category_index import create_source_category_schema


class ReviewProposalsTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.db=Path(temp.name)/"state.sqlite3"
        with Catalog(self.db) as cat:
            create_source_category_schema(cat)
            rows=[
                ("1","100","Organizador de Cozinha Aço Inox","review","review",
                 "home living","kitchenware","matched","",True),
                ("2","200","Copo Jarra de Vidro Transparente","review","review",
                 "home living","kitchenware","matched","",True),
                ("3","300","Organizador de Cozinha Antigo","eligible","matched",
                 "home living","kitchenware","matched","",True),
                ("4","400","Organizador de Cozinha Conflito","review","review",
                 "home living","kitchenware","conflict","",True),
                ("5","500","Organizador de Cozinha Sensivel","review","review",
                 "health","vitamins","matched","categoria_sensivel",True),
                ("6","600","Organizador de Cozinha Sem Link Seguro","review","review",
                 "home living","kitchenware","matched","",False),
                ("7","100","Organizador de Cozinha Segunda Loja Repetida","review","review",
                 "home living","kitchenware","matched","",True),
                ("8","800","Organizador de Porta Malas","review","review",
                 "spare parts and accessories for vehicles",
                 "internal accessories for automobiles","matched","",True),
            ]
            with cat.db:
                for ident,shop,title,moderation,tax,l1,l2,status,reason,safe in rows:
                    key=f"shopee:{shop}:{ident}"
                    cat.db.execute("""
                        INSERT INTO products
                        (product_key,shop_id,item_id,title,description,origin_url,image_url,
                         moderation,moderation_reason,first_source,last_seen_utc)
                        VALUES(?,?,?,?,?,?,?,?,?,?,?)
                    """,(key,shop,ident,title,"",
                         f"https://shopee.com.br/product/{shop}/{ident}"
                         if safe else "https://invalid.example/1",
                         "https://cf.shopee.com.br/file/image",moderation,reason,
                         "fixture","2026-11-17T00:00:00Z"))
                    cat.db.execute("""
                        INSERT INTO product_taxonomy
                        (product_key,category,niche,status,reason,version)
                        VALUES(?,?,?,?,?,?)
                    """,(key,"cozinha","organizacao_utensilios",tax,
                         "fixture","v31-test"))
                    cat.db.execute("""
                        INSERT INTO product_source_categories
                        (product_key,source,level1,level2,level3,status)
                        VALUES(?,?,?,?,?,?)
                    """,(key,"feed1",l1,l2,"",status))

    def test_proposals_never_promote_and_have_explainable_evidence(self):
        with Catalog(self.db) as cat:
            before=cat.stats()
            result=propose_review_batch(cat,category_l1="Home & Living",
                                        category_l2="Kitchenware",limit=10)
            after=cat.stats()
        self.assertEqual(before,after)
        keys={r["product_key"] for r in result["candidates"]}
        self.assertIn("shopee:100:1",keys)
        self.assertIn("shopee:200:2",keys)
        self.assertNotIn("shopee:300:3",keys)
        self.assertNotIn("shopee:400:4",keys)
        self.assertNotIn("shopee:600:6",keys)
        self.assertNotIn("shopee:100:7",keys)  # shop repeated, default max1
        self.assertEqual(len(keys),2)
        self.assertEqual(result["new_approvals"],0)
        self.assertEqual(result["conversion_calls"],0)
        self.assertEqual(result["publication_calls"],0)
        self.assertEqual(result["r2_writes"],0)
        self.assertFalse(result["can_publish"])
        first=next(x for x in result["candidates"]
                   if x["product_key"]=="shopee:100:1")
        self.assertEqual(first["suggested_editorial_route"],
                         "cozinha/organizacao_utensilios")
        second=next(x for x in result["candidates"]
                    if x["product_key"]=="shopee:200:2")
        self.assertIsNone(second["suggested_editorial_route"])
        self.assertTrue(all(x["review_required"] and
                            x["affiliate_url"] is None for x in result["candidates"]))

    def test_technical_branch_is_not_approved_for_automatic_publishing(self):
        with Catalog(self.db) as cat:
            report=propose_review_batch(
                cat,category_l1="Spare Parts and Accessories for Vehicles",
                category_l2="Internal Accessories for Automobiles")
        self.assertEqual(len(report["candidates"]),1)
        self.assertTrue(report["candidates"][0]["manual_technical_review"])
        self.assertEqual(report["candidates"][0]["suggested_editorial_route"],
                         "automotivo/acessorios")
        self.assertFalse(report["candidates"][0]["can_convert"])

    def test_summary_exposes_no_product_identifier_title_or_commercial_link(self):
        with Catalog(self.db) as cat:
            report=propose_review_batch(
                cat,category_l1="Home Living",category_l2="Kitchenware")
        aggregate=summarize_review_batch(report)
        raw=json.dumps(aggregate,ensure_ascii=False)
        for forbidden in ("shopee:","Organizador","Copo Jarra","product/",
                          "amazon","s.shopee.com.br"):
            self.assertNotIn(forbidden,raw)
        self.assertEqual(aggregate["review_candidates"],2)
        self.assertEqual(aggregate["distinct_shops"],2)
        self.assertEqual(aggregate["title_and_source_supported_route_suggestions"],1)
        self.assertEqual(aggregate["source_only_needs_editor_review"],1)

    def test_protected_roots_bad_args_and_untrusted_aggregate_fail_closed(self):
        with Catalog(self.db) as cat:
            with self.assertRaisesRegex(ProposalError,"protected_root"):
                propose_review_batch(cat,category_l1="Health",category_l2="Vitamins")
            for bad in (0,100,True,"12"):
                with self.subTest(limit=bad),self.assertRaises(ProposalError):
                    propose_review_batch(cat,category_l1="home living",
                                         category_l2="kitchenware",limit=bad)
            with self.assertRaises(ProposalError):
                propose_review_batch(cat,category_l1="",
                                     category_l2="kitchenware")
            with self.assertRaises(ProposalError):
                propose_review_batch(cat,category_l1="home living",
                                     category_l2="kitchenware",max_per_shop=0)
        with self.assertRaises(ProposalError):
            summarize_review_batch({"mode":"LIVE"})
        with Catalog(self.db) as cat:
            report=propose_review_batch(cat,category_l1="home living",
                                        category_l2="kitchenware")
            report["candidates"][0]["affiliate_url"]="https://s.shopee.com.br/leak"
            with self.assertRaises(ProposalError):
                summarize_review_batch(report)

    def test_ledger_direct_product_cannot_bypass_protected_source(self):
        with Catalog(self.db) as cat:
            with cat.db:
                cat.db.execute("""
                    INSERT INTO products
                    (product_key,shop_id,item_id,title,description,origin_url,image_url,
                     moderation,moderation_reason,first_source,last_seen_utc)
                    VALUES(?,?,?,?,?,?,?,?,?,?,?)
                """,("shopee:900:9","900","9","Air Fryer Digital 4 litros","",
                     "https://shopee.com.br/product/900/9",
                     "https://cf.shopee.com.br/file/img","eligible","",
                     "feed","2026-11-17T00:00:00Z"))
                cat.db.execute("""
                    INSERT INTO product_taxonomy
                    (product_key,category,niche,status,reason,version)
                    VALUES(?,?,?,?,?,?)
                """,("shopee:900:9","cozinha","air_fryers",
                     "matched","fixture","v31-test"))
                cat.db.execute("""
                    INSERT INTO product_source_categories
                    (product_key,source,level1,level2,level3,status)
                    VALUES(?,?,?,?,?,?)
                """,("shopee:900:9","feed","health","nutrition","","matched"))
            ledger=EditorialLedger(cat)
            with self.assertRaisesRegex(EditorialError,"product_source_policy_blocked"):
                ledger.next_brief("blogger_air_fryers","shopee:900:9")
            self.assertEqual(ledger.statistics(),{})
            self.assertEqual(cat.stats()["cached_affiliate_links"],0)

    def test_requires_real_source_table_and_never_modifies_legacy(self):
        with tempfile.TemporaryDirectory() as folder, Catalog(
                Path(folder)/"legacy.sqlite3") as cat:
            with self.assertRaisesRegex(ProposalError,"official_source"):
                propose_review_batch(cat,category_l1="home living",
                                     category_l2="kitchenware")
            names={x[0] for x in cat.db.execute(
                "SELECT name FROM sqlite_master WHERE type='table'")}
            self.assertNotIn("product_source_categories",names)


if __name__=="__main__":
    unittest.main()
