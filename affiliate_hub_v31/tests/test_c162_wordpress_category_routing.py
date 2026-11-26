import hashlib
import hmac
import json
import unittest
from unittest.mock import Mock, patch

from affiliate_hub_v31 import wordpress_category_routing as r
from affiliate_hub_v31.routing import sites
from affiliate_hub_v31.reviewed_ready_promotion import review_payload
from affiliate_hub_v31.review_signatures import configured_signing_keys, sign_release, verify_release
from affiliate_hub_v31.automatic_wordpress_drafts import WordPressRestClient
from affiliate_hub_v31.reviewed_draft_delivery import _wordpress_draft

ROUTE=sites()["wordpress_radartechbr"]
SKU="shopee:100:200"
BIND={"id":20,"parent":3,"slug":"ar-condicionado","taxonomy_path":"climatizacao/ar_condicionado"}
HTML='<p data-v31-product-key="'+SKU+'">Produto</p><a rel="nofollow sponsored" href="https://s.shopee.com.br/test">Ver produto na Shopee</a>'
TITLE="Guia de compra com categoria verificada"

class CategoryTests(unittest.TestCase):
    def client(self):
        client=Mock()
        client.site_settings.return_value={"url":ROUTE["identifier"]}
        client.get_category.side_effect=lambda n: {"id":n,"parent":3 if n==20 else 0,"slug":"ar-condicionado" if n==20 else "tecnologia"}
        client.list_posts.return_value=[]
        client.create_draft.return_value={"id":42,"status":"draft"}
        from affiliate_hub_v31.automatic_wordpress_drafts import _product_slug
        client.get_post.return_value={"id":42,"status":"draft","slug":_product_slug(ROUTE["site_key"],SKU),"title":{"raw":TITLE},"content":{"raw":HTML},"categories":[20]}
        return client

    def test_route_map_uses_real_ids_and_no_legacy_archive(self):
        mapping=r.category_map(ROUTE)
        self.assertEqual(mapping["climatizacao/ar_condicionado"],BIND)
        self.assertEqual({x["id"] for x in mapping.values()},{3,20})
        self.assertIsNone(r.category_map(sites()["wordpress_casa_decoracao"]))

    def test_category_selected_from_exact_product_taxonomy(self):
        catalog=Mock()
        catalog.db.execute.return_value.fetchone.return_value=("climatizacao","ar_condicionado")
        with patch("affiliate_hub_v31.verified_supply.route_allows_sku",return_value=True):
            self.assertEqual(r.category_for_product(catalog,ROUTE,SKU),BIND)
            catalog.db.execute.return_value.fetchone.return_value=("casa","decoracao")
            with self.assertRaises(ValueError):
                r.category_for_product(catalog,ROUTE,SKU)

    def test_hierarchy_rechecked_before_authorize(self):
        client=self.client()
        review={"site_url":ROUTE["identifier"],"product_key":SKU,"article_title":TITLE,"wordpress_category":BIND}
        auth=Mock(return_value=True)
        client.get_category.side_effect=lambda n: {"id":n,"parent":0,"slug":"ar-condicionado"}
        with self.assertRaises(ValueError):
            _wordpress_draft(route=ROUTE,review=review,content=HTML,authorize=auth,client=client)
        auth.assert_not_called()
        client.create_draft.assert_not_called()

    def test_category_sent_and_readback_checked(self):
        client=self.client()
        review={"site_url":ROUTE["identifier"],"product_key":SKU,"article_title":TITLE,"wordpress_category":BIND}
        auth=Mock(return_value=True)
        with patch("affiliate_hub_v31.reviewed_draft_delivery.audit_candidate_history",return_value={"status":"NO_DETECTED_COLLISION"}):
            self.assertEqual(_wordpress_draft(route=ROUTE,review=review,content=HTML,authorize=auth,client=client),"42")
            client.create_draft.assert_called_once_with(title=TITLE,slug=client.get_post.return_value["slug"],content=HTML,categories=[20])
            client.get_post.return_value["categories"]=[1]
            with self.assertRaises(ValueError):
                _wordpress_draft(route=ROUTE,review=review,content=HTML,authorize=auth,client=client)

    def test_missing_signed_category_denied_before_post(self):
        client=self.client()
        auth=Mock(return_value=True)
        with self.assertRaises(ValueError):
            _wordpress_draft(route=ROUTE,review={"site_url":ROUTE["identifier"],"product_key":SKU,"article_title":TITLE},content=HTML,authorize=auth,client=client)
        auth.assert_not_called()
        client.create_draft.assert_not_called()

    def test_replay_never_posts_and_verifies_category(self):
        client=self.client()
        client.list_posts.return_value=[{"id":42,"slug":client.get_post.return_value["slug"]}]
        review={"site_url":ROUTE["identifier"],"product_key":SKU,"article_title":TITLE,"wordpress_category":BIND}
        auth=Mock(return_value=False)
        self.assertEqual(_wordpress_draft(route=ROUTE,review=review,content=HTML,authorize=auth,client=client),"42")
        client.create_draft.assert_not_called()
        client.get_post.return_value["categories"]=[3]
        with self.assertRaises(ValueError):
            _wordpress_draft(route=ROUTE,review=review,content=HTML,authorize=auth,client=client)
        client.create_draft.assert_not_called()

    def test_category_is_part_of_signed_v2_payload(self):
        args=dict(site_key=ROUTE["site_key"],campaign=ROUTE["campaign"],product_key=SKU,site_url=ROUTE["identifier"],article_url=ROUTE["identifier"]+"test/",article_title=TITLE,primary_query="ar condicionado",angle="guia seguro",html_sha256="a"*64,evidence_sha256="b"*64,seo_context_sha256="c"*64,reviewed_text_hashes=[])
        legacy=review_payload(**args)
        self.assertEqual(legacy["version"],1)
        payload=review_payload(**args,wordpress_category=BIND)
        self.assertEqual(payload["version"],2)
        key,_,pub=configured_signing_keys(private_key="a"*64,receipt_key="b"*64)
        att={"payload":payload,"signature":"c"*64}
        sig=sign_release(att,private_key=key)
        verify_release(att,signature=sig,public_key=pub)
        tampered={"payload":{**payload,"wordpress_category":{**BIND,"id":3}},"signature":"c"*64}
        with self.assertRaises(ValueError):
            verify_release(tampered,signature=sig,public_key=pub)

    def test_client_post_contains_categories(self):
        client=WordPressRestClient(base_url=ROUTE["identifier"],username="x",application_password="y")
        with patch.object(client,"_call",return_value={"id":42,"status":"draft"}) as call:
            client.create_draft(title=TITLE,slug="v31-abcdef012345-200",content=HTML,categories=[20])
            self.assertEqual(call.call_args.args[2]["categories"],[20])

if __name__=="__main__":
    unittest.main()
