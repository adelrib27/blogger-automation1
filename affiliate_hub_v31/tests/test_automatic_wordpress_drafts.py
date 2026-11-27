"""C60 — WordPress universal: Blogger/WP separam LIVE, mas compartilham R2."""
import json
import os
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
    base = (
        "Para escolher um vaso decorativo, observe as medidas do ambiente, "
        "a estabilidade, o acabamento e a rotina de limpeza. "
        "Verifique os materiais no anúncio para evitar suposições. " * 3
    )
    return [
        base + f"Na seção {i+1}, compare critérios de escolha antes de decidir."
        for i in range(8)
    ]

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
        # context=edit real fornece RAW; prévia rendered é insuficiente para
        # provar ausência de colisão SKU em artigos legados.
        result=[]
        for p in self.posts:
            title=p["title"]
            content=p["content"]
            result.append({**p,
                "title":{**title, "raw":title.get("raw", title.get("rendered", ""))},
                "content":{**content, "raw":content.get("raw", content.get("rendered", ""))}})
        return result
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

    def test_legacy_same_title_blocks_direct_writer_before_ai_or_post(self):
        wp=FakeWP()
        wp.posts.append({"id":88,"status":"draft","slug":"legacy-vaso",
                         "title":{"rendered":m._draft_title(TITLE)},
                         "content":{"rendered":"<p>Guia anterior de vaso</p>"},
                         "link":HOME+"?p=88"})
        generator_calls=[]
        def writer(**kwargs):
            generator_calls.append(True)
            return paras()
        with Catalog(self.dbpath) as cat:
            with self.assertRaisesRegex(m.WordPressAutoDraftError,
                                        "wordpress_legacy_collision_review_required"):
                m.run(site_key=KEY,execute_draft=True,wp_client=wp,
                      writer=writer,catalog=cat)
        self.assertEqual(generator_calls,[])
        self.assertEqual(wp.writes,[])

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

    def test_continuous_wp_request_has_no_three_or_24_total_cap(self):
        wp=FakeWP()
        # Muitos posts legados não devem impedir geração contínua.
        for i in range(1,29):
            wp.posts.append({"id":50+i,"status":"publish",
                             "slug":"legacy-"+str(i),
                             "title":{"rendered":"Artigo antigo "+str(i)},
                             "link":HOME+"legacy-"+str(i)+"/",
                             "content":{"rendered":"<p>Conteúdo antigo</p>"}})
        with patch.object(m,"load_requests",return_value=[
             {**REQUEST,"articles":None}]):
            with Catalog(self.dbpath) as cat:
                one=m.run(site_key=KEY,execute_draft=True,
                          wp_client=wp,writer=paras,catalog=cat)
                again=m.run(site_key=KEY,execute_draft=True,
                            wp_client=wp,writer=paras,catalog=cat)
        self.assertEqual(one["status"],"DRAFT_CREATED")
        self.assertEqual(again["status"],"NO_APPROVED_CACHED_PRODUCT_FOR_TOPIC")
        self.assertEqual(len(wp.writes),1)
        self.assertEqual(wp.writes[0]["status"],"draft")

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

    def test_slug_lookup_with_zero_pages_requires_empty_first_page(self):
        client = m.WordPressRestClient(base_url=HOME, username="editor",
                                       application_password="test-password")
        for batch in ([], [{"status": "draft"}]):
            with self.subTest(batch=batch):
                def fetch(method, path, body=None):
                    self.assertIn("slug=novo-produto", path)
                    client._last_wp_total_pages = "0"
                    return batch
                with patch.object(client, "_call", side_effect=fetch):
                    if batch:
                        with self.assertRaisesRegex(m.WordPressAutoDraftError, "pages_invalid"):
                            client.list_posts(include_unpublished=True, slug="novo-produto")
                    else:
                        self.assertEqual(client.list_posts(include_unpublished=True, slug="novo-produto"), [])

    def test_wp_exact_100_posts_single_page_uses_rest_totalpages(self):
        # Casa real tinha 43 publish +57 draft: resposta com exatamente
        # 100 itens e X-WP-TotalPages=1; não pedir página 2 inexistente.
        client=m.WordPressRestClient(base_url=HOME,username="editor",
                                     application_password="test-password")
        calls=[]
        def fetch(method,path,body=None):
            calls.append(path)
            client._last_wp_total_pages="1"
            return [{"status":"draft"}]*100
        with patch.object(client,"_call",side_effect=fetch):
            items=client.list_posts(include_unpublished=True)
        self.assertEqual(len(items),100)
        self.assertEqual(len(calls),1)

    def test_wp_multi_page_and_invalid_total_fail_closed(self):
        client=m.WordPressRestClient(base_url=HOME,username="editor",
                                     application_password="test-password")
        calls=[]
        def fetch(method,path,body=None):
            calls.append(path)
            client._last_wp_total_pages="2"
            return [{"status":"draft"}]*100 if len(calls)==1 else [{"status":"draft"}]
        with patch.object(client,"_call",side_effect=fetch):
            self.assertEqual(len(client.list_posts(include_unpublished=True)),101)
        self.assertEqual(len(calls),2)
        def bogus(method,path,body=None):
            client._last_wp_total_pages="garbage"
            return [{"status":"draft"}]*100
        with patch.object(client,"_call",side_effect=bogus):
            with self.assertRaisesRegex(m.WordPressAutoDraftError,"pages_invalid"):
                client.list_posts(include_unpublished=True)

    def test_wp_full_page_without_total_is_not_accepted(self):
        client=m.WordPressRestClient(base_url=HOME,username="editor",
                                     application_password="test-password")
        def missing_header(method,path,body=None):
            return [{"status":"draft"}]*100
        with patch.object(client,"_call",side_effect=missing_header):
            with self.assertRaisesRegex(m.WordPressAutoDraftError,"pagination_unverified"):
                client.list_posts(include_unpublished=True)

    def test_draft_title_never_cuts_word_or_ends_in_conjunction(self):
        raw = ("Escorredor de Louças Dobrável Compacto – Plástico "
               "Resistente Dr Util para Pratos, Xícaras e Talheres")
        title = m._draft_title(raw)
        self.assertTrue(title.startswith("Guia prático: Escorredor de Louças"))
        self.assertLessEqual(len(title),75)
        self.assertNotRegex(title.lower(),r"\b(?:e|de|para|com|em|ou)$")
        self.assertNotEqual(title[-1], " ")
        self.assertEqual(m._draft_title("  Vaso   decorativo para sala  "),
                         "Guia prático: Vaso decorativo para sala")
        self.assertRaises(m.WordPressAutoDraftError,
                          m._draft_title,"PalavraSemEspacos"*20)

    def test_wp_editorial_gate_accepts_distinct_cautious_paragraphs(self):
        result=m.validate_wordpress_paragraphs(paras(),product_title=TITLE)
        self.assertEqual(len(result),8)

    def test_wp_editorial_gate_rejects_duplicate_before_post(self):
        wp=FakeWP()
        invalid=lambda **kwargs: [paras()[0]]*8
        with Catalog(self.dbpath) as cat:
            with self.assertRaisesRegex(m.WordPressAutoDraftError,
                                        "duplicate_paragraph"):
                m.run(site_key=KEY,execute_draft=True,wp_client=wp,
                      writer=invalid,catalog=cat)
        self.assertEqual(wp.writes,[])

    def test_wp_editorial_gate_rejects_unverified_claim_before_post(self):
        wp=FakeWP()
        def invalid(**kwargs):
            rows=paras()
            rows[0]+=" Materiais resistentes a bactérias impedem odores."
            return rows
        with Catalog(self.dbpath) as cat:
            with self.assertRaisesRegex(m.WordPressAutoDraftError,
                                        "claim_unverified"):
                m.run(site_key=KEY,execute_draft=True,wp_client=wp,
                      writer=invalid,catalog=cat)
        self.assertEqual(wp.writes,[])

    def test_wp_editorial_gate_rejects_unverified_product_title_and_html(self):
        unsafe=paras()
        long_title="Escorredor de Louças Dobrável Compacto Plástico Resistente Dr Util"
        unsafe[2]+=" O produto é "+long_title+"."
        with self.assertRaisesRegex(m.WordPressAutoDraftError,
                                    "copied_offer_title"):
            m.validate_wordpress_paragraphs(unsafe,product_title=long_title)
        unsafe=paras()
        unsafe[1]+=' <a href="https://exemplo.com">Comprar</a>'
        with self.assertRaisesRegex(m.WordPressAutoDraftError,
                                    "html_or_sales"):
            m.validate_wordpress_paragraphs(unsafe,product_title=TITLE)

    def test_c65_casa_legacy_credentials_bridge_is_strictly_isolated(self):
        with patch.dict(os.environ, {
            "CASA_WORDPRESS_USERNAME": "casa_editor",
            "CASA_WORDPRESS_APP_PASSWORD": "test-legacy-secret",
        }):
            self.assertEqual(m.credentials_for(KEY, raw=""),
                             ("casa_editor", "test-legacy-secret"))
            with self.assertRaisesRegex(m.WordPressAutoDraftError,
                                        "wordpress_credentials_not_configured"):
                m.credentials_for("wordpress_other_site", raw="")
            with self.assertRaisesRegex(m.WordPressAutoDraftError,
                                        "wordpress_site_credentials_missing"):
                m.credentials_for("wordpress_other_site", raw=json.dumps({
                    KEY: {"username": "casa_editor",
                          "application_password": "test-legacy-secret"}
                }))

    def test_oficina_json_preserves_casa_credentials_and_isolation(self):
        oficina = "wordpress_oficina_garagem"
        mapping = {
            oficina: {"username": "oficina_editor", "application_password": "test-oficina"},
        }
        with patch.dict(os.environ, {
            "CASA_WORDPRESS_USERNAME": "casa_editor",
            "CASA_WORDPRESS_APP_PASSWORD": "test-casa",
            "V31_WORDPRESS_SITE_CREDENTIALS_JSON": json.dumps(mapping),
        }):
            self.assertEqual(m.credentials_for(KEY), ("casa_editor", "test-casa"))
            self.assertEqual(m.credentials_for(oficina), ("oficina_editor", "test-oficina"))
            with self.assertRaisesRegex(m.WordPressAutoDraftError,
                                        "wordpress_site_credentials_missing"):
                m.credentials_for(KEY, raw=json.dumps({**mapping, KEY: {}}))

    def test_ai_rewrites_rejected_wordpress_text_before_first_post(self):
        wp=FakeWP()
        rejected=[paras()[0]]*8
        with patch.object(m,"generate_original_paragraphs",
                          side_effect=[rejected,paras()]) as model:
            with Catalog(self.dbpath) as cat:
                result=m.run(site_key=KEY,execute_draft=True,
                             wp_client=wp,catalog=cat)
        self.assertEqual(result["status"],"DRAFT_CREATED")
        self.assertEqual(result["publication_calls"],0)
        self.assertEqual(model.call_count,2)
        self.assertEqual(len(wp.writes),1)
        self.assertEqual(wp.writes[0]["status"],"draft")

    def test_three_invalid_ai_outputs_fail_before_any_wordpress_post(self):
        wp=FakeWP()
        rejected=[paras()[0]]*8
        with patch.object(m,"generate_original_paragraphs",
                          return_value=rejected) as model:
            with Catalog(self.dbpath) as cat:
                with self.assertRaisesRegex(m.WordPressAutoDraftError,
                                            "duplicate_paragraph"):
                    m.run(site_key=KEY,execute_draft=True,
                          wp_client=wp,catalog=cat)
        self.assertEqual(model.call_count,3)
        self.assertEqual(wp.writes,[])

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
