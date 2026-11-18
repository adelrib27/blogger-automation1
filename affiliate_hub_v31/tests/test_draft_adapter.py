"""Adaptadores SEO de rascunho sem acesso a Blogger ou WordPress."""
import csv
import tempfile
import unittest
from pathlib import Path

from affiliate_hub_v31.catalog import Catalog
from affiliate_hub_v31.editorial import EditorialLedger
from affiliate_hub_v31.draft_adapter import prepare_draft, DraftError


def paragraphs(keyword):
    sentence = f"Antes de escolher {keyword}, confira as características informadas pelo vendedor, as medidas, a compatibilidade e os detalhes de garantia anunciados. "
    return [(sentence * 9).strip()] * 5


class DraftAdapterTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        base=Path(temp.name)
        feed=base/"feed.csv"
        with feed.open("w",encoding="utf-8",newline="") as out:
            writer=csv.DictWriter(out,fieldnames=["shopId","itemId","productName","productLink","imageUrl"])
            writer.writeheader()
            writer.writerow({"shopId":"10","itemId":"45","productName":"Air Fryer 5L",
                             "productLink":"https://shopee.com.br/item-i.10.45",
                             "imageUrl":"https://cf.shopee.com.br/file/valid-product-photo"})
            writer.writerow({"shopId":"10","itemId":"46","productName":"Liquidificador 1000W",
                             "productLink":"https://shopee.com.br/item-i.10.46",
                             "imageUrl":"https://cf.shopee.com.br/file/valid-product-photo"})
        self.cat=Catalog(base/"state.sqlite3")
        self.addCleanup(self.cat.close)
        self.cat.import_csv(feed,"feed1")
        self.ledger=EditorialLedger(self.cat)

    def test_blogger_draft_requires_approval_and_affiliate(self):
        brief,key=self.ledger.next_brief("blogger_air_fryers","shopee:10:45")
        with self.assertRaisesRegex(DraftError,"brief_not_approved"):
            prepare_draft(self.cat,"blogger_air_fryers",key,paragraphs("air fryer"))
        self.ledger.update_status(key,"APPROVED")
        with self.assertRaisesRegex(DraftError,"affiliate_link_not_verified"):
            prepare_draft(self.cat,"blogger_air_fryers",key,paragraphs("air fryer"))
        self.cat.cache_link("shopee:10:45","airfryers","https://s.shopee.com.br/example")
        draft=prepare_draft(self.cat,"blogger_air_fryers",key,paragraphs("air fryer"))
        self.assertEqual(draft.platform,"blogger")
        self.assertTrue(draft.meta["isDraft"])
        self.assertIn('rel="nofollow sponsored',draft.content_html)
        self.assertEqual(draft.meta["blog"]["id"],"9113728635217260884")
        self.assertEqual(draft.status,"draft")

    def test_wordpress_draft_is_always_draft_and_escaped(self):
        brief,key=self.ledger.next_brief("wordpress_radartechbr","shopee:10:45")
        self.ledger.update_status(key,"APPROVED")
        self.cat.cache_link("shopee:10:45","radarwp","https://s.shopee.com.br/example2")
        text=paragraphs("air fryer")
        text[0]="<script>alert('x')</script> "+text[0]
        draft=prepare_draft(self.cat,"wordpress_radartechbr",key,text)
        self.assertEqual(draft.meta["status"],"draft")
        self.assertNotIn("<script>",draft.content_html)
        self.assertIn("&lt;script&gt;",draft.content_html)
        self.assertIn('nofollow sponsored',draft.content_html)
        self.assertNotIn("https://shopee.com.br/item",draft.content_html)

    def test_missing_affiliate_and_keyword_blocks(self):
        brief,key=self.ledger.next_brief("blogger_liquidificadores","shopee:10:46")
        self.ledger.update_status(key,"APPROVED")
        self.cat.cache_link("shopee:10:46","liquidificadores","https://s.shopee.com.br/abc")
        with self.assertRaisesRegex(DraftError,"seo_keyword_missing_from_body"):
            prepare_draft(self.cat,"blogger_liquidificadores",key,paragraphs("utensílio"))
        with self.assertRaisesRegex(DraftError,"body_not_ready"):
            prepare_draft(self.cat,"blogger_liquidificadores",key,["apenas um parágrafo"])

if __name__=="__main__":
    unittest.main()
