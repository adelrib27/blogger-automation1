"""C60 — WordPress universal: Blogger/WP separam LIVE, mas compartilham R2."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from affiliate_hub_v31.catalog import Catalog
from affiliate_hub_v31 import automatic_wordpress_drafts as m


KEY="wordpress_casa_decoracao"
ROUTE={"site_key":KEY,"platform":"wordpress",
       "identifier":"https://casaedecoracao.radartechbr.com.br/",
       "campaign":"casaedecoracaowp",
       "allowed_niches":["casa/decoracao"],"publish_enabled":False}
PRODUCT="shopee:12345678:87654321"
TITLE="Vaso Decorativo para Sala em Cerâmica"
LINK="https://s.shopee.com.br/Validated_Casa123"
IMAGE="https://cf.shopee.com.br/file/sku-casa-real"
HOME=ROUTE["identifier"]
REQUEST={"site_key":KEY,"topic":"vaso decorativo","platform":"wordpress",
         "articles":1,"enabled":True}


def paras(**kwargs):
    return [(
        "Para escolher um vaso decorativo, observe as medidas do ambiente, "
        "a estabilidade, o acabamento e a rotina de limpeza. "
        "Verifique os materiais no anúncio para evitar suposições. "*3
    )]*8


class FakeWP:
    def __init__(self):
        self.posts=[
            {"id":31,"status":"publish","slug":"decorar-sala",
             "title":{"rendered":"Dicas para decorar a sala"},
             "link":HOME+"dicas-decoracao-sala/",
             "content":{"rendered":"<p>Um texto original da casa.</p>"}},
            {"id":32,"status":"publish","slug":"organizar-estantes",
             "title":{"rendered":"Organizando a estante"},
             "link":HOME+"organizacao-de-estante/",
             "content":{"rendered":"<p>Mais um guia.</p>"}},
        ]
        self.writes=[]
        self.url=HOME
    def site_settings(self):
        return {"url":self.url}
    def list_posts(self,*,include_unpublished):
        return list(self.posts)
    def create_draft(self,*,title,slug,content):
        self.writes.append({"title":title,"slug":slug,"content":content,
                            "status":"draft"})
        new={"id":9871,"title":{"raw":title},"slug":slug,
             "content":{"raw":content},"status":"draft",
             "link":HOME+"?p=9871"}
        self.posts.append(new)
        return new
    def get_post(self,post_id):
        return next(x for x in self.posts if x["id"]==post_id)


class WordPressUniversalDraftTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.dbpath=Path(t.name)/"catalog.sqlite3"
        with Catalog(self.dbpath) as cat:
            with cat.db:
                cat.db.execute("""
                  INSERT INTO products(product_key,shop_id,item_id,title,
                  description,origin_url,image_url,moderation,
                  moderation_reason,first_source,last_seen_utc)
                  VALUES(?,?,?,?,?,?,?,?,?,?,?)
                """,(PRODUCT,"12345678","87654321",TITLE,"",
                    "https://shopee.com.br/product/12345678/87654321",
                    IMAGE,"eligible","","feed","2026-11-18T00:00:00Z"))
                cat.db.execute("""
                  INSERT INTO product_taxonomy
                  (product_key,category,niche,status,reason,version)
                  VALUES(?,?,?,?,?,?)
                """,(PRODUCT,"casa","decoracao","matched","fixture","v31"))
            cat.cache_link(PRODUCT,ROUTE["campaign"],LINK)
        self.mock_r=patch.object(m,"sites",return_value={KEY:ROUTE})
        self.mock_launch=patch.object(m,"preview_site_launch",
            return_value={"registered_site":True,"can_publish":False,
            "campaign":ROUTE["campaign"],
            "approved_catalog_candidates":[{
                "product_key":PRODUCT,"title":TITLE,
                "affiliate_url":LINK,"affiliate_status":"verified_for_campaign"
            }]})
        self.mock_requests=patch.object(m,"load_requests",
            return_value=[REQUEST])
        self.mock_offer=patch("affiliate_hub_v31.article_commerce.sites",
            return_value={KEY:ROUTE})
        for tool in (self.mock_r,self.mock_launch,self.mock_requests,
                     self.mock_offer):
            tool.start()
            self.addCleanup(tool.stop)

    def test_preview_no_post_and_real_photo_link_cta(self):
        wp=FakeWP()
        with Catalog(self.dbpath) as cat:
            result=m.run(site_key=KEY,execute_draft=False,
                         wp_client=wp,catalog=cat)
        self.assertEqual(result["status"],"READY_FOR_DRAFT_REVIEW")
        self.assertTrue(result["real_product_image"])
        self.assertTrue(result["exact_campaign"])
        self.assertEqual(result["internal_links"],2)
        self.assertEqual(result["wordpress_posts_created"],0)
        self.assertEqual(len(wp.writes),0)

    def test_creates_only_draft_after_real_request_and_verifies_readback(self):
        wp=FakeWP()
        with Catalog(self.dbpath) as cat:
            result=m.run(site_key=KEY,execute_draft=True,wp_client=wp,
                         writer=paras,catalog=cat)
            repeated=m.run(site_key=KEY,execute_draft=True,wp_client=wp,
                           writer=paras,catalog=cat)
        self.assertEqual(result["status"],"DRAFT_CREATED")
        self.assertEqual(result["publication_calls"],0)
        self.assertEqual(repeated["status"],"OWNER_QUOTA_REACHED")
        self.assertEqual(len(wp.writes),1)
        body=wp.writes[0]
        self.assertEqual(body["status"],"draft")
        self.assertTrue(body["slug"].startswith("v31-"))
        self.assertIn(IMAGE,body["content"])
        self.assertIn(LINK,body["content"])
        self.assertIn("Ver produto na Shopee",body["content"])
        self.assertIn('data-v31-related="1"',body["content"])
        self.assertEqual(body["content"].count("<li>"),2)

    def test_without_real_request_execution_fails_closed(self):
        wp=FakeWP()
        with patch.object(m,"load_requests",return_value=[]):
            with Catalog(self.dbpath) as cat:
                with self.assertRaisesRegex(m.WordPressAutoDraftError,
                                            "enabled_owner_request_required"):
                    m.run(site_key=KEY,execute_draft=True,wp_client=wp,
                          writer=paras,catalog=cat)
        self.assertEqual(wp.writes,[])

    def test_site_identity_mismatch_blocks_before_writes(self):
        wp=FakeWP()
        wp.url="https://outrosite.exemplo.com.br/"
        with Catalog(self.dbpath) as cat:
            with self.assertRaisesRegex(m.WordPressAutoDraftError,
                                        "wordpress_identity_mismatch|registered_site_mismatch"):
                m.run(site_key=KEY,execute_draft=True,wp_client=wp,
                      writer=paras,catalog=cat)
        self.assertEqual(wp.writes,[])

    def test_product_campaign_mismatch_stops_before_post(self):
        wp=FakeWP()
        with Catalog(self.dbpath) as cat:
            with cat.db:
                cat.db.execute("DELETE FROM affiliate_links WHERE campaign=?",
                               (ROUTE["campaign"],))
            result=m.run(site_key=KEY,execute_draft=True,
                         wp_client=wp,writer=paras,catalog=cat)
        self.assertEqual(result["status"],"NO_APPROVED_CACHED_PRODUCT_FOR_TOPIC")
        self.assertEqual(wp.writes,[])

    def test_reuses_no_product_link_already_present_on_blog(self):
        wp=FakeWP()
        wp.posts[0]["content"]["rendered"]='<a href="'+LINK+'">Produto</a>'
        with Catalog(self.dbpath) as cat:
            result=m.run(site_key=KEY,execute_draft=True,
                         wp_client=wp,writer=paras,catalog=cat)
        self.assertEqual(result["status"],"NO_APPROVED_CACHED_PRODUCT_FOR_TOPIC")
        self.assertEqual(wp.writes,[])

    def test_wrong_identity_or_credentials_are_not_authorized(self):
        with self.assertRaises(m.WordPressAutoDraftError):
            m.site_route("wordpress_inventado")
        with self.assertRaises(m.WordPressAutoDraftError):
            m.credentials_for(KEY,raw="")
        with self.assertRaises(m.WordPressAutoDraftError):
            m.credentials_for(KEY,raw='{"other":{"username":"x","application_password":"y"}}')
        user,password=m.credentials_for(
            KEY,raw=json.dumps({KEY:{"username":"editor",
                          "application_password":"fake-test-secret"}}))
        self.assertEqual(user,"editor")
        self.assertEqual(password,"fake-test-secret")

    def test_rest_client_posts_only_draft(self):
        client=m.WordPressRestClient(base_url=HOME,
            username="editor",application_password="fake-test-secret")
        calls=[]
        def fake(method,path,body=None):
            calls.append((method,path,body))
            return {"id":99,"status":"draft"}
        with patch.object(client,"_call",side_effect=fake):
            result=client.create_draft(
                title="Como escolher um vaso decorativo para casa",
                slug=m._product_slug(KEY,PRODUCT),
                content='<section data-v31-product-key="'+PRODUCT+
                    '"> <a rel="nofollow sponsored">Ver produto na Shopee</a></section>')
        self.assertEqual(result["status"],"draft")
        self.assertEqual(calls[0][0],"POST")
        self.assertEqual(calls[0][2]["status"],"draft")
        self.assertNotIn("publish",json.dumps(calls[0][2]))

if __name__=="__main__":
    unittest.main()
