"""C55 — auto draft Blogger, bounded by owner quota and never LIVE."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from affiliate_hub_v31.catalog import Catalog
from affiliate_hub_v31 import automatic_blogger_drafts as m

KEY="blogger_moveis_para_cada_canto"
ROUTE={"site_key":KEY,"platform":"blogger",
       "identifier":"1439741542627895062",
       "campaign":"moveisparacadacanto","publish_enabled":False,
       "allowed_niches":["casa/moveis"],
       "allowed_source_paths":["home living/furniture"]}
URL="https://moveisparacadacanto.blogspot.com/"
LINK="https://s.shopee.com.br/CampanhaReal"
PRODUCT="shopee:123:456"
NAME="Sofá Retrátil 2 Lugares Suede Cinza"

def article_list(n=3):
    return [{"id":str(i+100),"title":f"Artigo {i}",
             "url":URL+f"2026/11/artigo-{i}.html",
             "status":"live","content":"<article>Original</article>"}
            for i in range(n)]

def worker_paragraphs(**_):
    sentence=("Para escolher sofá retrátil, confira medidas, "
      "profundidade de abertura, materiais de estofamento, "
      "recomendações de conservação e condições de entrega. "
      "Verifique especificações no anúncio antes de comparar modelos. ")
    return [sentence*4]*7

class AutoBloggerDraftTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.path=Path(t.name)/"db.sqlite3"
        with Catalog(self.path) as c:
            with c.db:
                c.db.execute("""
                  INSERT INTO products(product_key,shop_id,item_id,title,
                  description,origin_url,image_url,moderation,
                  moderation_reason,first_source,last_seen_utc)
                  VALUES(?,?,?,?,?,?,?,?,?,?,?)
                """,(PRODUCT,"123","456",NAME,"",
                   "https://shopee.com.br/product/123/456",
                   "https://cf.shopee.com.br/file/real",
                   "eligible","","feed1","2026-11-18T00:00:00Z"))
                c.db.execute("""
                  INSERT INTO product_taxonomy
                  (product_key,category,niche,status,reason,version)
                  VALUES(?,?,?,?,?,?)
                """,(PRODUCT,"casa","moveis","matched","fixture","v31"))
            c.cache_link(PRODUCT,ROUTE["campaign"],LINK)
        self.p1=patch.object(m,"sites",return_value={KEY:ROUTE})
        self.p2=patch("affiliate_hub_v31.article_commerce.sites",
                      return_value={KEY:ROUTE})
        self.p3=patch.object(m,"preview_site_launch",return_value={
            "registered_site":True,"can_publish":False,
            "approved_catalog_candidates":[
                {"product_key":PRODUCT,"title":NAME,
                 "affiliate_url":LINK,
                 "affiliate_status":"verified_for_campaign"}
            ]})
        self.p4=patch.object(m,"load_requests",return_value=[{
             "site_key":KEY,"platform":"blogger","topic":"sofá retrátil",
             "articles":3,"enabled":True}])
        for patcher in (self.p1,self.p2,self.p3,self.p4):
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_existing_three_live_articles_block_more_auto_drafts(self):
        with Catalog(self.path) as cat:
            result=m.select_next(cat,site_key=KEY,
                request=m.load_requests()[0],existing_posts=article_list(3))
        self.assertEqual(result["status"],"OWNER_QUOTA_REACHED")
        self.assertEqual(result["draft_creation_calls"],0)

    def test_original_html_includes_exact_photo_cta_and_two_internal_links(self):
        with Catalog(self.path) as cat:
            plan=m.select_next(cat,site_key=KEY,
                request=m.load_requests()[0],existing_posts=article_list(2))
        self.assertEqual(plan["status"],"READY_FOR_ORIGINAL_DRAFT_REVIEW")
        built=m.compose_draft_html(plan,worker_paragraphs(),
                blog_home_url=URL,published_posts=article_list(2))
        self.assertIn("https://cf.shopee.com.br/file/real",built)
        self.assertIn(LINK,built)
        self.assertIn("Ver produto na Shopee",built)
        self.assertIn("data-v31-product-key",built)
        self.assertEqual(built.count("<li>"),2)
        self.assertNotIn("Compre agora por R$",built)
        self.assertIn('rel="nofollow sponsored',built)

    def test_used_product_never_generated_twice(self):
        old=article_list(1)
        old[0]["content"]="<section data-v31-product-key=\""+PRODUCT+"\">"
        with Catalog(self.path) as cat:
            result=m.select_next(cat,site_key=KEY,
                request=m.load_requests()[0],existing_posts=old)
        self.assertEqual(result["status"],"NO_VERIFIED_CAMPAIGN_PRODUCT_YET")

    def test_other_campaign_link_is_not_silently_used(self):
        with Catalog(self.path) as cat:
            with cat.db:
                cat.db.execute("""
                  DELETE FROM affiliate_links WHERE product_key=? AND campaign=?
                """,(PRODUCT,ROUTE["campaign"]))
            result=m.select_next(cat,site_key=KEY,
                request=m.load_requests()[0],existing_posts=article_list(1))
        self.assertEqual(result["status"],"NO_VERIFIED_CAMPAIGN_PRODUCT_YET")

    def test_worker_json_mode_parsed_response_and_supported_model(self):
        self.assertEqual(m.WORKERS_MODEL,
            "@cf/meta/llama-3.3-70b-instruct-fp8-fast")
        response={"result":{"response":{
            "paragraphs":worker_paragraphs()
        }}}
        text=m._ai_response_text(response)
        paragraphs=m.validate_generated_paragraphs(
            text,keyword="sofá retrátil")
        self.assertEqual(len(paragraphs),7)

    def test_validates_blogger_id_and_blog_url(self):
        good={"id":ROUTE["identifier"],"url":URL}
        self.assertEqual(m.validate_remote_identity(ROUTE,good),URL)
        with self.assertRaisesRegex(m.AutoDraftError,"blogger_identity_invalid"):
            m.validate_remote_identity(ROUTE,{**good,"id":"00000000"})
        with self.assertRaisesRegex(m.AutoDraftError,"blogger_url_unverified"):
            m.validate_remote_identity(ROUTE,{**good,"url":"http://other.com/"})

    def test_rejects_ai_markdown_html_and_commercial_hallucination(self):
        payload=json.dumps({"paragraphs":worker_paragraphs()},ensure_ascii=False)
        self.assertEqual(len(m.validate_generated_paragraphs(
            payload,keyword="sofá")),7)
        with self.assertRaises(m.AutoDraftError):
            m.validate_generated_paragraphs("texto solto",keyword="sofá")
        with self.assertRaises(m.AutoDraftError):
            m.validate_generated_paragraphs(payload.replace(
                "Para escolher","R$ 9,99 Para escolher"),
                keyword="sofá")
        with self.assertRaises(m.AutoDraftError):
            m.validate_generated_paragraphs(payload.replace(
                "Para escolher","https://malicious.example Para escolher"),
                keyword="sofá")

    def _service(self,count=3):
        service=Mock()
        service.blogs.return_value.get.return_value.execute.return_value={
            "id":ROUTE["identifier"],"url":URL}
        def listings(**params):
            resp=Mock()
            st=params["status"]
            resp.execute.return_value={"items":article_list(count)
                if "LIVE" in st else []}
            return resp
        service.posts.return_value.list.side_effect=listings
        service.posts.return_value.insert.return_value.execute.return_value={
            "id":"987654321","status":"draft"}
        return service

    def test_dry_run_respects_owner_quota_and_no_api_writes(self):
        api=self._service(3)
        with Catalog(self.path) as cat:
            result=m.draft_next(site_key=KEY,execute=False,
                blogger_service=api,catalog=cat)
        self.assertEqual(result["status"],"OWNER_QUOTA_REACHED")
        self.assertEqual(result["draft_creation_calls"],0)
        api.posts.return_value.insert.assert_not_called()

    def test_scheduled_execute_still_skips_when_three_already_published(self):
        api=self._service(3)
        with Catalog(self.path) as cat:
            result=m.draft_next(site_key=KEY,execute=True,
                blogger_service=api,catalog=cat,
                workers_writer=worker_paragraphs)
        self.assertEqual(result["status"],"OWNER_QUOTA_REACHED")
        api.posts.return_value.insert.assert_not_called()

    def test_future_incremental_quota_creates_draft_not_live(self):
        api=self._service(2)
        with Catalog(self.path) as cat:
            result=m.draft_next(site_key=KEY,execute=True,
                blogger_service=api,catalog=cat,
                workers_writer=worker_paragraphs)
        self.assertEqual(result["status"],"DRAFT_CREATED")
        self.assertEqual(result["draft_creation_calls"],1)
        self.assertEqual(result["publication_calls"],0)
        args=api.posts.return_value.insert.call_args.kwargs
        self.assertTrue(args["isDraft"])
        self.assertEqual(args["blogId"],ROUTE["identifier"])
        self.assertIn('data-v31-product-key',args["body"]["content"])
        self.assertIn("https://cf.shopee.com.br/file/real",
                      args["body"]["content"])
        self.assertIn(LINK,args["body"]["content"])
        self.assertEqual(args["body"]["labels"],["Guias de compra","Produtos"])

if __name__=="__main__":
    unittest.main()
