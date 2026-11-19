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

    def test_continuous_request_not_blocked_after_three_existing_live(self):
        request={**m.load_requests()[0],"articles":None}
        with Catalog(self.path) as cat:
            result=m.select_next(cat,site_key=KEY,request=request,
                 existing_posts=article_list(30))
        self.assertEqual(result["status"],"READY_FOR_ORIGINAL_DRAFT_REVIEW")

    def test_continuous_writer_can_make_fourth_draft_never_live(self):
        # Três LIVE já existentes não significam quota esgotada.
        self.p4.stop()
        patcher=patch.object(m,"load_requests",return_value=[
            {"site_key":KEY,"platform":"blogger","topic":"sofá retrátil",
             "articles":None,"enabled":True}])
        patcher.start()
        self.addCleanup(patcher.stop)
        api=self._service(3)
        with Catalog(self.path) as cat:
            result=m.draft_next(site_key=KEY,execute=True,
                blogger_service=api,catalog=cat,workers_writer=worker_paragraphs)
        self.assertEqual(result["status"],"DRAFT_CREATED")
        self.assertEqual(result["publication_calls"],0)
        api.posts.return_value.insert.assert_called_once()
        self.assertTrue(api.posts.return_value.insert.call_args.kwargs["isDraft"])

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

    def test_blogger_rejects_full_commercial_product_title_in_body(self):
        long_name=("Guarda-Roupa Casal 6 Portas 2 Gavetas Peroba/Off White "
                   "RP154 Rei Móveis")
        clean=worker_paragraphs()
        payload=json.dumps({"paragraphs":clean},ensure_ascii=False)
        self.assertEqual(len(m.validate_generated_paragraphs(
            payload,keyword="sofá",product_name=long_name)),7)
        bad=list(clean)
        bad[0]+=" Antes de escolher, confira "+long_name+"."
        copied=json.dumps({"paragraphs":bad},ensure_ascii=False)
        with self.assertRaisesRegex(m.AutoDraftError,
                                    "product_title_copied_into_editorial_body"):
            m.validate_generated_paragraphs(
                copied,keyword="sofá",product_name=long_name)
        with Catalog(self.path) as cat:
            plan=m.select_next(cat,site_key=KEY,
                request=m.load_requests()[0],existing_posts=article_list(2))
        plan["product_title"]=long_name
        with self.assertRaisesRegex(m.AutoDraftError,
                                    "product_title_copied_into_editorial_body"):
            m.compose_draft_html(plan,bad,blog_home_url=URL,
                                 published_posts=article_list(2))

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

    def test_real_blogger_listing_without_item_status_still_has_live_links(self):
        # A API Google pode omitir status em cada post apesar de filtrar LIVE.
        api=Mock()
        def listing(**params):
            resp=Mock()
            if "LIVE" in params["status"]:
                items=[{k:v for k,v in post.items() if k!="status"}
                       for post in article_list(3)]
            else:
                items=[]
            resp.execute.return_value={"items":items}
            return resp
        api.posts.return_value.list.side_effect=listing
        history=m._list_posts(api,ROUTE["identifier"])
        self.assertEqual(len(history),3)
        self.assertTrue(all(p["status"]=="live" for p in history))
        links=m.relevant_live_links(history,blog_home_url=URL,
                   current_title="Guia de compra novo",limit=2)
        self.assertEqual(len(links),2)
        self.assertTrue(all(link[1].startswith(URL) for link in links))

    def test_inconsistent_api_status_fails_closed(self):
        api=Mock()
        response=Mock()
        response.execute.return_value={"items":[{**article_list(1)[0],
                                                "status":"draft"}]}
        api.posts.return_value.list.return_value=response
        with self.assertRaisesRegex(m.AutoDraftError,"status_mismatch"):
            m._list_posts(api,ROUTE["identifier"])

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
