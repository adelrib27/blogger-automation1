import hashlib
import unittest
from unittest.mock import Mock, patch
from affiliate_hub_v31.autonomous_review import recover_fresh_ready, VerificationError
from affiliate_hub_v31.universal_evidence_ready import _fingerprint
from affiliate_hub_v31.d1_universal_ready import UniversalD1ReadyState, D1SafeError

KEY = "shopee:123:456"
TENANT = {"site_key":"blogger_moveis_para_cada_canto","campaign":"moveisparacadacanto"}
ROUTE = {**TENANT,"platform":"blogger","publish_enabled":False}
HOME = "https://moveisparacadacanto.blogspot.com/"
NOW = 1795578392
FP = _fingerprint(KEY,"modelo exemplo","guia exemplo")
JOB = {"fingerprint":FP,"product_key":KEY,"html_sha256":"1"*64,"evidence_sha256":"2"*64}
IMAGE = "https://example.com/image.jpg"
AFF = "https://s.shopee.com.br/example"


class ReadyRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.state = Mock()
        self.state.list_fresh_ready.return_value = [JOB]
        self.envelope = Mock()
        self.envelope.load.return_value = {"review": {
            "product_key": KEY, "evidence_sha256":JOB["evidence_sha256"],
            "site_url":HOME,"primary_query":"modelo exemplo","angle":"guia exemplo"},
            "html_content":f'<img src="{IMAGE}"><a href="{AFF}">Oferta</a>'}
        self.args = dict(state=self.state,envelope=self.envelope,catalog=Mock(),
            route=ROUTE,policy={"home":HOME},prior_keys=set(),prior_slugs=set(),
            prior_prose=set(),public_key_sha256="3"*64,now_epoch=NOW)

    @patch("affiliate_hub_v31.autonomous_review._single_verified_offer",return_value=("Produto",IMAGE,AFF))
    @patch("affiliate_hub_v31.autonomous_review.route_allows_sku",return_value=True)
    def test_recover_without_candidate_ranking_or_budget(self, scope, offer):
        result = recover_fresh_ready(**self.args)
        self.assertEqual(result["fingerprint"], FP)
        self.assertEqual(result["status"], "READY")
        self.state.list_fresh_ready.assert_called_once_with(**TENANT, now_epoch=NOW)
        self.state.claim_search_budget.assert_not_called()
        self.state.consume_one.assert_not_called()
        self.envelope.load.assert_called_once_with(**TENANT, html_sha256=JOB["html_sha256"],release_public_key_sha256="3"*64)

    def test_existing_product_not_recovered(self):
        self.args["prior_keys"].add(hashlib.sha256(KEY.encode()).hexdigest())
        self.assertIsNone(recover_fresh_ready(**self.args))
        self.envelope.load.assert_not_called()

    @patch("affiliate_hub_v31.autonomous_review.route_allows_sku",return_value=False)
    def test_out_of_scope_not_recovered(self, scope):
        self.assertIsNone(recover_fresh_ready(**self.args))
        self.envelope.load.assert_not_called()

    @patch("affiliate_hub_v31.autonomous_review._single_verified_offer",return_value=("Produto",IMAGE,AFF))
    @patch("affiliate_hub_v31.autonomous_review.route_allows_sku",return_value=True)
    def test_mismatched_commercial_content_or_binding(self, scope, offer):
        self.envelope.load.return_value["html_content"] = '<p>Sem oferta</p>'
        self.assertIsNone(recover_fresh_ready(**self.args))
        self.envelope.load.return_value["review"]["evidence_sha256"] = "4"*64
        with self.assertRaisesRegex(VerificationError,"recovered_ready_binding_mismatch"):
            recover_fresh_ready(**self.args)


class ReadyQueueTests(unittest.TestCase):
    def test_select_only_scoped_fresh_ready(self):
        query = Mock(return_value=[JOB])
        state = UniversalD1ReadyState(query)
        self.assertEqual(state.list_fresh_ready(**TENANT,now_epoch=NOW),[JOB])
        sql, params = query.call_args.args
        self.assertIn("j.status='READY'",sql)
        self.assertIn("ev.expires_epoch>?",sql)
        self.assertIn("j.site_key=? AND j.campaign=?",sql)
        self.assertEqual(params,(TENANT["site_key"],TENANT["campaign"],NOW,NOW))
        query.return_value = [JOB,JOB]
        with self.assertRaises(D1SafeError):
            state.list_fresh_ready(**TENANT,now_epoch=NOW)
