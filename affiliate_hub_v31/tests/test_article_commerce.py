"""V31 C54: fotos reais, links internos e CTA da campanha correta."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from affiliate_hub_v31.catalog import Catalog
from affiliate_hub_v31.article_commerce import (
    CommerceArticleError, valid_product_photo, product_offer_html,
    related_articles_html, enhance_existing_article_html,
)


ROUTES={
 "blogger_moveis_para_cada_canto":{
    "site_key":"blogger_moveis_para_cada_canto",
    "platform":"blogger","identifier":"1439741542627895062",
    "campaign":"moveisparacadacanto",
    "allowed_niches":["casa/moveis"],"publish_enabled":False,
 },
 "outro_blog":{
    "site_key":"outro_blog","platform":"blogger","identifier":"111222333444555",
    "campaign":"outracampanha","allowed_niches":["casa/moveis"],
    "publish_enabled":False,
 }
}

HOME="https://moveisparacadacanto.blogspot.com/"
RELATED=[
 ("Sofá para sala pequena",
  "https://moveisparacadacanto.blogspot.com/2026/11/sofa-para-sala-pequena-como-escolher.html"),
 ("Guarda-roupa para quarto",
  "https://moveisparacadacanto.blogspot.com/2026/11/guarda-roupa-para-quarto-portas-medidas.html"),
]


class CommerceArticleTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.path=Path(t.name)/"catalog.sqlite3"
        self.key="shopee:123:456"
        with Catalog(self.path) as cat:
            with cat.db:
                cat.db.execute("""
                    INSERT INTO products(product_key,shop_id,item_id,title,
                     description,origin_url,image_url,moderation,
                     moderation_reason,first_source,last_seen_utc)
                    VALUES(?,?,?,?,?,?,?,?,?,?,?)
                """,(self.key,"123","456",
                     'Sofá Retrátil 2 lugares <suede>','',
                     "https://shopee.com.br/product/123/456",
                     "https://cf.shopee.com.br/file/img-real",
                     "eligible","","feed1","2026-11-18T00:00:00Z"))
                cat.db.execute("""
                  INSERT INTO product_taxonomy(
                     product_key,category,niche,status,reason,version)
                  VALUES(?,?,?,?,?,?)
                """,(self.key,"casa","moveis","matched","test","v31"))
            cat.cache_link(self.key,"moveisparacadacanto",
                           "https://s.shopee.com.br/CampanhaReal")
            cat.cache_link(self.key,"outracampanha",
                           "https://s.shopee.com.br/OutroBlog")
        p=patch("affiliate_hub_v31.article_commerce.sites",
                return_value=ROUTES)
        p.start()
        self.addCleanup(p.stop)

    def test_verified_product_photo_keyword_link_and_two_sponsored_ctas(self):
        with Catalog(self.path) as cat:
            before=cat.stats()
            html=product_offer_html(
                cat,site_key="blogger_moveis_para_cada_canto",
                product_key=self.key,topic="sofá retrátil")
            self.assertEqual(before,cat.stats())
        self.assertIn('src="https://cf.shopee.com.br/file/img-real"',html)
        self.assertIn('alt="Foto real do anúncio:',html)
        self.assertIn('s.shopee.com.br/CampanhaReal',html)
        self.assertNotIn('s.shopee.com.br/OutroBlog',html)
        self.assertIn('>sofá retrátil</a>',html)
        self.assertIn('>Ver produto na Shopee</a>',html)
        self.assertIn('rel="sponsored nofollow noopener noreferrer"',html)
        self.assertIn('target="_blank"',html)
        self.assertIn('&lt;suede&gt;',html)
        self.assertNotIn('<suede>',html)
        self.assertNotIn("R$",html)

    def test_photo_domain_whitelist(self):
        self.assertTrue(valid_product_photo(
            "https://cf.shopee.com.br/file/br-111342"))
        self.assertTrue(valid_product_photo(
            "https://down-br.img.susercontent.com/file/abc"))
        for url in ("http://cf.shopee.com.br/file/abc",
                    "https://cf.shopee.com.br.evil.test/file/a",
                    "https://example.com/file/a",
                    "javascript:alert(1)",
                    "https://user:pass@cf.shopee.com.br/file/a",
                    "https://cf.shopee.com.br/"):
            with self.subTest(url=url):
                self.assertFalse(valid_product_photo(url))

    def test_without_exact_campaign_link_fails(self):
        with Catalog(self.path) as cat:
            cat.db.execute("""
             DELETE FROM affiliate_links WHERE campaign=?
            """,("moveisparacadacanto",))
            with self.assertRaisesRegex(CommerceArticleError,
                                        "exact_campaign_affiliate_link_required"):
                product_offer_html(cat,
                    site_key="blogger_moveis_para_cada_canto",
                    product_key=self.key,topic="sofá")

    def test_review_product_never_gets_shopping_button(self):
        with Catalog(self.path) as cat:
            with cat.db:
                cat.db.execute(
                    "UPDATE products SET moderation='review' WHERE product_key=?",
                    (self.key,))
            with self.assertRaisesRegex(CommerceArticleError,
                                        "product_not_approved"):
                product_offer_html(cat,
                    site_key="blogger_moveis_para_cada_canto",
                    product_key=self.key,topic="sofá")

    def test_nonexistent_product_or_wrong_site_fails(self):
        with Catalog(self.path) as cat:
            with self.assertRaises(CommerceArticleError):
                product_offer_html(cat,site_key="invalid_site",
                                   product_key=self.key,topic="sofá")
            with self.assertRaises(CommerceArticleError):
                product_offer_html(cat,
                    site_key="blogger_moveis_para_cada_canto",
                    product_key="shopee:99:99",topic="sofá")

    def test_related_links_same_real_host_and_escape(self):
        links=related_articles_html(
            [("Como escolher <sofá>?",RELATED[0][1]),RELATED[1]],
            blog_home_url=HOME)
        self.assertIn('&lt;sofá&gt;',links)
        self.assertIn('data-v31-related="1"',links)
        self.assertEqual(links.count("<li>"),2)
        for url in ("https://moveisparacadacanto.blogspot.com.evil.test/f.html",
                    "http://moveisparacadacanto.blogspot.com/x.html",
                    "https://shopee.com.br/product/123/456",
                    "https://moveisparacadacanto.blogspot.com/x.html?redirect=1"):
            with self.subTest(url=url),self.assertRaises(CommerceArticleError):
                related_articles_html([("Fraude",url)],blog_home_url=HOME)

    def test_current_url_is_not_linked_to_itself(self):
        links=related_articles_html(RELATED,blog_home_url=HOME,
            current_url=RELATED[0][1])
        self.assertEqual(links.count("<li>"),1)

    def test_existing_post_kept_and_second_update_idempotent(self):
        original="<article><h2>Texto editorial original</h2><p>Corpo</p></article>"
        with Catalog(self.path) as cat:
            offer=product_offer_html(cat,
                site_key="blogger_moveis_para_cada_canto",
                product_key=self.key,topic="sofá")
        related=related_articles_html(RELATED,blog_home_url=HOME)
        enriched=enhance_existing_article_html(
            original,offer=offer,related=related)
        self.assertIn("<h2>Texto editorial original</h2>",enriched)
        self.assertIn("data-v31-product-key",enriched)
        self.assertIn("data-v31-related",enriched)
        self.assertEqual(enhance_existing_article_html(
            enriched,offer=offer,related=related),enriched)
        with self.assertRaisesRegex(CommerceArticleError,
                                    "existing_commercial_section_requires_review"):
            enhance_existing_article_html(
                enriched,offer=offer.replace("CampanhaReal","OutroBlog"),
                related=related)

    def test_existing_post_without_article_element_fails_closed(self):
        with self.assertRaises(CommerceArticleError):
            enhance_existing_article_html(
                "<p>sem fechamento</p>",offer="<section>abc</section>")


if __name__ == "__main__":
    unittest.main()
