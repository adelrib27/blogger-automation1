"""C46: pistas agregadas nunca tornam produtos sem faceta publicáveis."""
import json
import sqlite3
import unittest

from affiliate_hub_v31.unclassified_review_hints import (
    ReviewHintsError, build_review_path_hints, suggested_path_counts, review_dashboard,
)


class ReviewHintsTests(unittest.TestCase):
    def setUp(self):
        self.db=sqlite3.connect(":memory:")
        self.side=sqlite3.connect(":memory:")
        self.addCleanup(self.db.close)
        self.addCleanup(self.side.close)
        self.db.execute("""
          CREATE TABLE products(
             product_key TEXT PRIMARY KEY, title TEXT, moderation TEXT)
        """)
        self.side.executescript("""
          CREATE TABLE v31_universal_inventory(
            product_key TEXT PRIMARY KEY, source_l1 TEXT,
            review_lane TEXT, decision TEXT, can_convert INTEGER);
          CREATE TABLE v31_universal_title_lexicon(
            source_l1 TEXT, source_l2 TEXT, term TEXT,
            product_count INTEGER, shop_count_floor INTEGER,
            review_only INTEGER);
        """)
        products=[
            ("p1","Mesa jantar madeira robusta","review",
             "NO_OFFICIAL_CATEGORY","review_required"),
            ("p2","Kit mesa","review",
             "NO_OFFICIAL_CATEGORY","review_required"),
            ("p3","Pistola mesa jantar madeira","review",
             "NO_OFFICIAL_CATEGORY","review_required"),
            ("p4","Pneu moto aro 17","review",
             "NO_OFFICIAL_CATEGORY","review_required"),
            ("p5","Mesa jantar pneu moto","review",
             "NO_OFFICIAL_CATEGORY","review_required"),
            ("p6","Mesa jantar madeira","review",
             "POLICY_REVIEW","review_required"),
            ("p7","Mesa jantar madeira","eligible",
             "APPROVED","approved"),
            ("p8","Mesa jantar madeira","review",
             "SOURCE_CONFLICT","review_required"),
        ]
        for key,title,mod,lane,decision in products:
            self.db.execute("INSERT INTO products VALUES(?,?,?)",
                            (key,title,mod))
            self.side.execute("""
              INSERT INTO v31_universal_inventory VALUES(?,?,?,?,?)
            """,(key,"sem_categoria_oficial",lane,decision,0))
        groups={
            ("home living","furniture"):
                ["mesa","jantar","mesa jantar","madeira"],
            ("vehicles","motorcycle accessories"):
                ["pneu","moto","pneu moto"],
            ("health","vitamins"):["mesa","jantar","mesa jantar"],
        }
        for (l1,l2),terms in groups.items():
            for term in terms:
                self.side.execute("""
                  INSERT INTO v31_universal_title_lexicon VALUES
                  (?,?,?,?,?,1)
                """,(l1,l2,term,40,9))

    def test_only_eligible_review_lane_gets_nonpublishing_hints(self):
        result=build_review_path_hints(self.db,self.side)
        self.assertEqual(result["unclassified_review_scanned"],5)
        self.assertEqual(result["review_path_hints_created"],2)
        self.assertEqual(result["sensitive_or_invalid_title_held"],1)
        self.assertEqual(result["ambiguous_evidence_held"],1)
        self.assertEqual(result["insufficient_evidence_held"],1)
        self.assertEqual(result["distinct_official_paths_suggested"],2)
        self.assertTrue(result["review_only"])
        self.assertEqual(result["new_approvals"],0)
        self.assertEqual(result["affiliate_conversion_calls"],0)
        self.assertEqual(result["publication_calls"],0)
        matches=self.side.execute("""
          SELECT product_key,suggested_l1,review_only
          FROM v31_unclassified_review_hints ORDER BY product_key
        """).fetchall()
        self.assertEqual([r[0] for r in matches],["p1","p4"])
        self.assertTrue(all(row[2]==1 for row in matches))

    def test_idempotent_rebuild_does_not_accumulate_old_hints(self):
        one=build_review_path_hints(self.db,self.side)
        two=build_review_path_hints(self.db,self.side)
        self.assertEqual(one,two)
        self.assertEqual(self.side.execute("""
          SELECT COUNT(*) FROM v31_unclassified_review_hints
        """).fetchone()[0],2)
        counts=suggested_path_counts(self.side)
        self.assertEqual(len(counts),2)
        self.assertTrue(all(x["approved_for_publication"] is False
                            for x in counts))
        self.assertNotIn("p1",json.dumps(counts))

    def test_aggregated_dashboard_has_no_skus_or_campaigns(self):
        build_review_path_hints(self.db,self.side)
        report=review_dashboard(self.side,limit=10)
        self.assertEqual(report["unclassified_review_products"],5)
        self.assertEqual(report["review_path_hint_products"],2)
        self.assertEqual(report["remaining_without_safe_hint"],3)
        self.assertEqual(report["publication_calls"],0)
        self.assertEqual(report["r2_writes"],0)
        self.assertEqual(report["new_approvals"],0)
        self.assertTrue(report["review_only"])
        for key in ("p1","p4","Pistola","s.shopee.com.br"):
            self.assertNotIn(key,json.dumps(report))

    def test_empty_lexicon_yields_zero_approvals_or_hints(self):
        self.side.execute("DELETE FROM v31_universal_title_lexicon")
        report=build_review_path_hints(self.db,self.side)
        self.assertEqual(report["review_path_hints_created"],0)
        self.assertEqual(report["still_without_confident_hint"],5)
        self.assertEqual(report["new_approvals"],0)

    def test_lexicon_requires_table_and_review_only(self):
        self.side.execute("DROP TABLE v31_universal_title_lexicon")
        with self.assertRaises(ReviewHintsError):
            build_review_path_hints(self.db,self.side)

    def test_divergent_core_fails_closed(self):
        self.db.execute("DELETE FROM products WHERE product_key='p1'")
        with self.assertRaisesRegex(ReviewHintsError,
                                    "review_inventory_core_divergence"):
            build_review_path_hints(self.db,self.side)

    def test_path_counts_rejects_unbounded_limits(self):
        build_review_path_hints(self.db,self.side)
        for value in (0,-1,101,True,"50"):
            with self.subTest(value=value),self.assertRaises(ReviewHintsError):
                suggested_path_counts(self.side,limit=value)


if __name__=="__main__":
    unittest.main()
