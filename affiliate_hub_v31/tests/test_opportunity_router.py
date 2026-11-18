"""Contrato de roteamento API Shopee -> fallback R2 em erro 1000, sem rede."""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from affiliate_hub_v31 import opportunity_router as router
from affiliate_hub_v31.fallback_v23 import emit_v23_outputs


class ObserverTests(unittest.TestCase):
    def test_only_explicit_code_1000_triggers_fallback(self):
        self.assertTrue(router.is_api_error_1000({
            "errors":[{"extensions":{"code":1000},"message":"temporarily unavailable"}]
        }))
        self.assertTrue(router.is_api_error_1000({
            "errors":[{"extensions":{"code":"1000"},"message":"temporarily unavailable"}]
        }))
        self.assertTrue(router.is_api_error_1000({"errors":[{"message":"Erro 1000"}]}))
        self.assertFalse(router.is_api_error_1000({"errors":[{"extensions":{"code":10030}}]}))
        self.assertFalse(router.is_api_error_1000({"errors":[{"message":"Produto 1000W"}]}))
        self.assertFalse(router.is_api_error_1000({"data":{"productOfferV2":{"nodes":[]}}}))

    def test_circuit_breaker_stops_api_on_first_1000(self):
        calls=[]
        def source(*args,**kwargs):
            calls.append(1)
            return {"errors":[{"extensions":{"code":1000}}]}
        observer=router.ErrorObserver(source)
        with self.assertRaises(router.ApiError1000Detected):
            observer("ignored")
        self.assertEqual(observer.calls,1)
        self.assertEqual(len(calls),1)
        self.assertTrue(observer.error_1000)

    def test_api_first_and_fail_closed(self):
        self.assertEqual(router.choose_source(4,False),"API")
        self.assertEqual(router.choose_source(4,True),"API")
        self.assertEqual(router.choose_source(0,True),"CSV_R2")
        with self.assertRaisesRegex(router.RoutingError,"api_unavailable_without_confirmed_1000"):
            router.choose_source(0,False)

    def test_observer_preserves_original_response(self):
        calls=[]
        def legacy(*a,**k):
            calls.append((a,k))
            return {"errors":[{"extensions":{"code":"1000"}}]}
        watch=router.ErrorObserver(legacy)
        with self.assertRaises(router.ApiError1000Detected):
            watch("foo",timeout=3)
        self.assertTrue(watch.error_1000)
        self.assertEqual(watch.calls,1)
        self.assertEqual(calls[0],(("foo",),{"timeout":3}))


class RouterIntegrationTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root=Path(temp.name)
        self.config=self.root/"conf.json"
        self.rules=self.root/"rules.json"
        self.config.write_text(json.dumps({"categories":{"Decoracao":["luminaria"]}}),encoding="utf-8")
        self.rules.write_text(json.dumps({"rules":{}}),encoding="utf-8")
        self.output=self.root/"opportunities"
        self.fake_scanner=self.root/"scanner.py"
        self.fake_scanner.write_text("""
import json, os
from pathlib import Path
import shopee_oportunidades as base
parsed=base.post_graphql('unused','unused','query')
if not parsed.get('errors'):
    p=Path(os.environ['SHOPEE_OUTPUT_DIR'])
    p.mkdir(parents=True,exist_ok=True)
    product={'itemId':'42','productName':'Luminaria de Mesa',
             'offerLink':'https://s.shopee.com.br/verified','imageUrl':'https://img.example.invalid/p.png'}
    (p/'ranking.json').write_text(json.dumps({'ranking':[product]}))
    (p/'intent_report.json').write_text(json.dumps({'version':'2.3','ranking':[product]}))
    (p/'ranking.csv').write_text('itemId,productName\\n42,Luminaria')
    (p/'search_signals.json').write_text('{}')
""",encoding="utf-8")
        sys.path.insert(0,str(router.ROOT/"src"))
        import shopee_oportunidades as base
        self.base=base
        self.addCleanup(sys.path.remove,str(router.ROOT/"src"))

    def _run(self):
        with patch.object(router,"validate_scanner",return_value=self.fake_scanner):
            return router.run_router("wordpress_casa_decoracao",
                "mock.py",str(self.config),str(self.rules),str(self.output),limit=3)

    def test_api_success_never_calls_fallback(self):
        with patch.object(self.base,"post_graphql",return_value={"data":{"productOfferV2":{}}}), \
             patch.object(router,"run_cloud",side_effect=AssertionError("R2 should not be used")):
            self.assertEqual(self._run(),"API")
        out=json.loads((self.output/"ranking.json").read_text(encoding="utf-8"))
        self.assertEqual(out["ranking"][0]["itemId"],"42")

    def test_api_error_1000_uses_cached_fallback_contract(self):
        calls=[]
        def fake_r2(site,config,rules,stage,limit):
            calls.append(site)
            return emit_v23_outputs([{
                "itemId":"43","productName":"Luminária Solar",
                "offerLink":"https://s.shopee.com.br/cache",
                "imageUrl":"https://img.example.invalid/43.jpg",
                "intentMatchedKeywords":["luminaria"],
                "keywords":["luminaria"],"categories":["Decoracao"],
                "sourceModes":["csv_r2_verified_affiliate_cache"],
                "priorityTier":"CSV_R2_CACHE",
                "semanticIntentScore":1.0,
            }],{"categories":{"Decoracao":["luminaria"]}},stage)
        with patch.object(self.base,"post_graphql",
                          return_value={"errors":[{"extensions":{"code":1000}}]}), \
             patch.object(router,"run_cloud",side_effect=fake_r2):
            self.assertEqual(self._run(),"CSV_R2")
        self.assertEqual(calls,["wordpress_casa_decoracao"])
        result=json.loads((self.output/"intent_report.json").read_text(encoding="utf-8"))
        self.assertEqual(result["ranking"][0]["itemId"],"43")
        self.assertEqual(result["ranking"][0]["offerLink"],"https://s.shopee.com.br/cache")

    def test_real_casa_v23_wrapper_uses_generic_fallback_without_live_api(self):
        """Usa o scanner de Casa REAL, mockando exclusivamente API e R2."""
        script=router.ROOT/"casa_decoracao/src/shopee_oportunidades_casa.py"
        config=router.ROOT/"casa_decoracao/config/shopee_oportunidades.json"
        rules=router.ROOT/"casa_decoracao/config/shopee_intent_rules.json"
        self.assertTrue(script.is_file())
        self.assertTrue(config.is_file())
        self.assertTrue(rules.is_file())
        def fake_r2(site,config_path,rules_path,stage,limit):
            self.assertEqual(site,"wordpress_casa_decoracao")
            return emit_v23_outputs([{
                "itemId":"123","productName":"Luminária Solar para Jardim",
                "offerLink":"https://s.shopee.com.br/real-cached",
                "imageUrl":"https://img.example.invalid/jardim.jpg",
                "priorityTier":"CSV_R2_CACHE",
                "categories":["Area Externa"],
                "keywords":["luminaria solar jardim"],
                "intentMatchedKeywords":["luminaria solar jardim"],
                "sourceModes":["csv_r2_verified_affiliate_cache"],
                "semanticIntentScore":1.0
            }],json.loads(config_path.read_text(encoding="utf-8")),stage)
        with patch.dict(os.environ,{"SHOPEE_APP_ID":"TEST","SHOPEE_SECRET":"TEST"}), \
             patch.object(self.base,"post_graphql",
                          return_value={"errors":[{"extensions":{"code":1000}}]}), \
             patch.object(self.base,"google_suggestions",return_value=[]), \
             patch.object(self.base.time,"sleep",return_value=None), \
             patch.object(router,"run_cloud",side_effect=fake_r2):
            source=router.run_router("wordpress_casa_decoracao",
                    str(script.relative_to(router.ROOT)),str(config),str(rules),
                    str(self.root/"casa_output"),limit=3)
        self.assertEqual(source,"CSV_R2")
        report=json.loads((self.root/"casa_output/intent_report.json").read_text(encoding="utf-8"))
        self.assertEqual(report["ranking"][0]["itemId"],"123")

    def test_other_errors_stop_before_consumer_runs(self):
        with patch.object(self.base,"post_graphql",
                          return_value={"errors":[{"extensions":{"code":10030}}]}), \
             patch.object(router,"run_cloud",side_effect=AssertionError("not permitted")):
            with self.assertRaisesRegex(router.RoutingError,"api_unavailable_without_confirmed_1000"):
                self._run()
        self.assertFalse((self.output/"intent_report.json").exists())


if __name__=="__main__":
    unittest.main()
