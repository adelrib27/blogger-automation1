"""C2.2 — anti-canibalização editorial e preservação da palavra-chave."""
import csv
import tempfile
import unittest
from affiliate_hub_v31.tests.synthetic_site_routes import synthetic_routes
from pathlib import Path
from affiliate_hub_v31.catalog import Catalog
from affiliate_hub_v31.editorial import (
    ANGLES, EditorialError, EditorialLedger, fold, make_brief, title_key
)


class EditorialTests(unittest.TestCase):
    def setUp(self):
        ctx=synthetic_routes()
        ctx.__enter__()
        self.addCleanup(ctx.__exit__,None,None,None)
        temp=tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root=Path(temp.name)
        filename=self.root/"products.csv"
        with filename.open("w",encoding="utf-8",newline="") as output:
            writer=csv.DictWriter(output,fieldnames=["shopId","itemId","productName","productLink","imageUrl"])
            writer.writeheader()
            for idx,name in enumerate(("Air Fryer Digital 5 L", "Air Fryer Compacta 3 L",
                                        "Liquidificador Turbo 1000 W","Produto Sem Categoria"), 1):
                writer.writerow({"shopId":"77","itemId":str(idx),"productName":name,
                                 "productLink":f"https://shopee.com.br/item-i.77.{idx}",
                                 "imageUrl":"https://img.example.invalid/test.jpg"})
        self.catalog=Catalog(self.root/"catalog.sqlite3")
        self.addCleanup(self.catalog.close)
        self.catalog.import_csv(filename,"feed1")
        self.ledger=EditorialLedger(self.catalog)

    def test_same_product_multiple_topics_but_no_repeat(self):
        one,ref1=self.ledger.next_brief("test_blogger_air_fryers","shopee:77:1")
        two,ref2=self.ledger.next_brief("test_blogger_air_fryers","shopee:77:1")
        self.assertEqual(one.product_key,two.product_key)
        self.assertNotEqual(ref1,ref2)
        self.assertNotEqual(one.title,two.title)
        self.assertNotEqual(one.angle,two.angle)
        self.assertNotEqual(one.topic,two.topic)
        self.assertIn("air fryer",fold(one.title))
        self.assertIn("air fryer",fold(two.title))
        self.assertEqual(one.status,"REVIEW_REQUIRED")
        self.assertEqual(self.ledger.statistics()["REVIEW_REQUIRED"],2)

    def test_prevent_same_subject_in_different_blogs_even_for_same_product(self):
        one,ref=self.ledger.next_brief("test_blogger_air_fryers","shopee:77:1")
        same=make_brief("blogger_cozinha_sem_complicacao","shopee:77:1",
                        "Air Fryer Digital 5 L","cozinha","air_fryers",one.angle)
        with self.assertRaisesRegex(EditorialError,"duplicate_title_or_subject"):
            self.ledger.reserve(same)
        different,other=self.ledger.next_brief("blogger_cozinha_sem_complicacao","shopee:77:1")
        self.assertNotEqual(one.title,different.title)
        self.assertNotEqual(one.angle,different.angle)
        self.assertNotEqual(ref,other)

    def test_duplicated_catalog_name_can_still_be_a_different_article(self):
        one,ref=self.ledger.next_brief("test_blogger_air_fryers","shopee:77:1")
        two,ref2=self.ledger.next_brief("test_blogger_air_fryers","shopee:77:2")
        self.assertNotEqual(one.title,two.title)
        self.assertNotEqual(one.topic,two.topic)
        self.assertNotEqual(ref,ref2)

    def test_prevent_exact_duplicate_reservation_and_title(self):
        brief,key=self.ledger.next_brief("test_blogger_air_fryers","shopee:77:1")
        with self.assertRaisesRegex(EditorialError,"duplicate_title_or_subject"):
            self.ledger.reserve(brief)
        self.assertEqual(self.ledger.statistics()["REVIEW_REQUIRED"],1)

    def test_no_unknown_product_or_blog(self):
        with self.assertRaisesRegex(EditorialError,"product_not_eligible"):
            self.ledger.next_brief("test_blogger_air_fryers","shopee:77:4")
        with self.assertRaisesRegex(EditorialError,"unknown_site"):
            self.ledger.next_brief("blogger_inventado","shopee:77:1")

    def test_keyword_locked_and_title_is_not_generic(self):
        brief=make_brief("test_blogger_liquidificadores","shopee:77:3",
                         "Liquidificador Turbo 1000 W","cozinha","liquidificadores","comparacao")
        self.assertIn("liquidificador",fold(brief.title))
        self.assertIn("como comparar",fold(brief.title))
        self.assertTrue(brief.slug)
        with self.assertRaisesRegex(EditorialError,"niche_outside_site"):
            make_brief("test_blogger_air_fryers","shopee:77:3",
                       "Liquidificador Turbo 1000 W","cozinha","liquidificadores","comparacao")
        with self.assertRaisesRegex(EditorialError,"unknown_angle"):
            make_brief("test_blogger_liquidificadores","shopee:77:3",
                       "Liquidificador Turbo 1000 W","cozinha","liquidificadores","angle_999")

    def test_requires_review_and_state_transitions(self):
        brief,key=self.ledger.next_brief("test_blogger_air_fryers","shopee:77:1")
        with self.assertRaisesRegex(EditorialError,"invalid_transition"):
            self.ledger.update_status(key,"PUBLISHED")
        self.ledger.update_status(key,"APPROVED")
        self.ledger.update_status(key,"DRAFT_CREATED",remote_id="draft-test-123")
        with self.assertRaisesRegex(EditorialError,"invalid_transition"):
            self.ledger.update_status(key,"APPROVED")
        self.ledger.update_status(key,"SCHEDULED")
        self.ledger.update_status(key,"PUBLISHED")
        self.assertEqual(self.ledger.statistics()["PUBLISHED"],1)

    def test_ledger_survives_reopening_catalog(self):
        first,key=self.ledger.next_brief("test_blogger_air_fryers","shopee:77:1")
        with Catalog(self.root/"catalog.sqlite3") as reopened:
            ledger=EditorialLedger(reopened)
            second,key2=ledger.next_brief("test_blogger_air_fryers","shopee:77:1")
            self.assertNotEqual(first.angle,second.angle)
            self.assertNotEqual(key,key2)

    def test_all_angles_unique(self):
        self.assertEqual(len(set(x[0] for x in ANGLES)),len(ANGLES))
        self.assertEqual(title_key("Air Fryer: comprar"),title_key("AIR-FRYER, Comprar"))
        self.assertNotEqual(title_key("Air Fryer: comprar"),title_key("Air Fryer: manutenção"))

if __name__=="__main__":
    unittest.main()
