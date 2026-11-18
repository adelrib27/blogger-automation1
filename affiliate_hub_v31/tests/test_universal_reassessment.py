"""C33: inventário universal de evidências, sempre só revisão."""
import json
import tempfile
import unittest
from pathlib import Path

from affiliate_hub_v31.catalog import Catalog
from affiliate_hub_v31.source_category_index import create_source_category_schema
from affiliate_hub_v31.universal_reassessment import (
    ReassessmentError, plan_universal_reassessment,
)

# (title, moderation, taxonomy, source_l1, source_l2, source_status, reason, url_ok)
ROWS = [
    ("Air Fryer Digital 5L", "eligible", "matched",
     "home appliances", "kitchen appliances", "matched", "", True),
    ("Air Fryer Digital Premium", "review", "review",
     "home appliances", "kitchen appliances", "matched", "", True),
    ("Air Fryer Inox Nova", "review", "review",
     "", "", None, "", True),
    ("Air Fryer de Teste", "review", "review",
     "health", "vitamins", "matched", "", True),
    ("Air Fryer em Conflito", "review", "review",
     "home appliances", "kitchen appliances", "conflict", "", True),
    ("Objeto Desconhecido", "review", "review",
     "home living", "kitchenware", "matched", "", True),
    ("Air Fryer Sem Correspondencia Oficial", "review", "review",
     "home living", "furniture", "matched", "", True),
    ("Air Fryer Com URL Invalida", "review", "review",
     "home appliances", "kitchen appliances", "matched", "", False),
    ("Air Fryer Moderacao Antiga", "review", "matched",
     "home appliances", "kitchen appliances", "matched", "", True),
    ("Air Fryer Risco", "review", "review",
     "home appliances", "kitchen appliances", "matched",
     "categoria_sensivel", True),
]


class UniversalReassessmentTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.path = Path(temp.name)/"catalog.sqlite3"
        with Catalog(self.path) as cat:
            create_source_category_schema(cat)
            with cat.db:
                for i,(title,mod,tax,l1,l2,src_status,reason,valid) in enumerate(ROWS):
                    shop=str(100+i)
                    key=f"shopee:{shop}:{i+1}"
                    cat.db.execute("""
                      INSERT INTO products
                      (product_key,shop_id,item_id,title,description,
                       origin_url,image_url,moderation,moderation_reason,
                       first_source,last_seen_utc)
                      VALUES(?,?,?,?,?,?,?,?,?,?,?)
                    """,(key,shop,str(i+1),title,"",
                          f"https://shopee.com.br/product/{shop}/{i+1}"
                          if valid else "https://bad.example/p",
                          "https://cf.shopee.com.br/file/test",mod,reason,
                          "fixture","2026-11-18T00:00:00Z"))
                    cat.db.execute("""
                      INSERT INTO product_taxonomy
                      (product_key,category,niche,status,reason,version)
                      VALUES(?,?,?,?,?,?)
                    """,(key,"cozinha","air_fryers",tax,"fixture","test"))
                    if src_status is not None:
                        cat.db.execute("""
                          INSERT INTO product_source_categories
                          (product_key,source,level1,level2,level3,status)
                          VALUES(?,?,?,?,?,?)
                        """,(key,"feed1",l1,l2,"",src_status))
            cat.cache_link("shopee:100:1","firstblog",
                           "https://s.shopee.com.br/existing-link")

    def test_entire_backlog_is_accounted_for_without_approvals(self):
        with Catalog(self.path) as cat:
            before=cat.stats()
            result=plan_universal_reassessment(cat)
            after=cat.stats()
        self.assertEqual(before,after)
        self.assertEqual(result["products"],len(ROWS))
        self.assertEqual(result["previously_approved"],1)
        self.assertEqual(result["pending_review"],9)
        counts=result["evidence_counts"]
        self.assertEqual(counts["TITLE_AND_OFFICIAL_PATH"],2)
        self.assertEqual(counts["TITLE_WITHOUT_OFFICIAL_FACET"],1)
        self.assertEqual(counts["OFFICIAL_FACET_WITHOUT_TITLE_ROUTE"],1)
        self.assertEqual(counts["TITLE_ONLY_UNVALIDATED_PATH"],1)
        self.assertEqual(counts["SOURCE_CONFLICT_BLOCKED"],1)
        self.assertEqual(counts["POLICY_REVIEW_BLOCKED"],2)
        self.assertEqual(counts["DATA_REPAIR_BLOCKED"],1)
        self.assertEqual(sum(counts.values()),9)
        self.assertEqual(result["new_approvals"],0)
        self.assertEqual(result["affiliate_conversion_calls"],0)
        self.assertEqual(result["publication_calls"],0)
        self.assertEqual(result["r2_writes"],0)
        self.assertFalse(result["can_publish"])
        self.assertTrue(result["review_proposal_only"])
        self.assertEqual(result["review_lane_counts"]["MODERATION_REVIEW"],1)

    def test_official_and_title_group_is_explainable_not_autoapproved(self):
        with Catalog(self.path) as cat:
            report=plan_universal_reassessment(cat)
        group=next(x for x in report["priority_review_paths"]
                   if x["category_l1"]=="home appliances")
        self.assertEqual(group["title_and_official_evidence"],2)
        self.assertEqual(group["distinct_shops_with_both_signals"],2)
        self.assertFalse(group["can_autoapprove"])

    def test_summary_never_exposes_product_identifiers_titles_or_links(self):
        with Catalog(self.path) as cat:
            report=plan_universal_reassessment(cat)
        output=json.dumps(report,ensure_ascii=False)
        for secret in ("shopee:", "s.shopee.com.br", "Air Fryer",
                       "firstblog", "cf.shopee.com.br", "100:1", "Premium"):
            self.assertNotIn(secret,output)

    def test_missing_official_index_fails_closed_without_creating_table(self):
        with tempfile.TemporaryDirectory() as td:
            with Catalog(Path(td)/"legacy.sqlite3") as cat:
                with self.assertRaises(ReassessmentError):
                    plan_universal_reassessment(cat)
                count=cat.db.execute("""
                  SELECT COUNT(*) FROM sqlite_master
                  WHERE name='product_source_categories'
                """).fetchone()[0]
                self.assertEqual(count,0)

    def test_limit_rejects_invalid_values(self):
        with Catalog(self.path) as cat:
            for bad in (0,101,-1,True,False,1.3,"10"):
                with self.subTest(bad=bad),self.assertRaises(ReassessmentError):
                    plan_universal_reassessment(cat,max_paths=bad)

    def test_limited_group_list_does_not_truncate_backlog_counts(self):
        with Catalog(self.path) as cat:
            full=plan_universal_reassessment(cat,max_paths=20)
            one=plan_universal_reassessment(cat,max_paths=1)
        self.assertEqual(one["pending_review"],full["pending_review"])
        self.assertEqual(one["evidence_counts"],full["evidence_counts"])
        self.assertEqual(len(one["priority_review_paths"]),1)
        self.assertGreater(full["source_paths_awaiting_review"],1)


if __name__=="__main__":
    unittest.main()
