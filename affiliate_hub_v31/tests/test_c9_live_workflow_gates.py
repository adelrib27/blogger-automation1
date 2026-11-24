"""C9 — contratos de integração reversível, sem modificar LIVE na main.

Os arquivos de workflows são lidos como texto para o teste independer de
parsers YAML externos no GitHub Actions. O PR guarda as alterações e suas
variáveis de ativação seguem ausentes/desligadas em produção.
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from affiliate_hub_v31 import opportunity_router as router
from affiliate_hub_v31.fallback_v23 import emit_v23_outputs

ROOT=Path(__file__).resolve().parents[2]


class WorkflowGatesTests(unittest.TestCase):
    def test_reusable_workflow_uses_isolated_environment_not_wp_secrets(self):
        contents=(ROOT/".github/workflows/v31_c9_discovery_reusable.yml").read_text()
        self.assertIn("workflow_call:",contents)
        self.assertIn("environment: v31-editorial-safe",contents)
        self.assertIn("github.ref == 'refs/heads/main'",contents)
        self.assertIn("V31_EDITORIAL_R2_ACCESS_KEY_ID",contents)
        self.assertIn("--min-fallback",contents)
        self.assertIn("actions/upload-artifact@v4",contents)
        self.assertNotIn("WORDPRESS_APP_PASSWORD",contents)
        self.assertNotIn("publish_generated.py",contents)

    def test_original_casa_oficina_and_radar_jobs_are_fail_closed(self):
        for workflow,flag,job,source,minimum in [
            ("casa_editorial_generate_schedule.yml",
             "V31_CASA_R2_FALLBACK_ENABLED","v31_casa_discovery",
             "casa_decoracao/src/shopee_oportunidades_casa.py",3),
            ("oficina_editorial_autonomous.yml",
             "V31_OFICINA_R2_FALLBACK_ENABLED","v31_oficina_discovery",
             "oficina_garagem/src/shopee_oportunidades_oficina.py",2),
        ]:
            with self.subTest(workflow=workflow):
                text=(ROOT/".github/workflows"/workflow).read_text()
                self.assertIn("uses: ./.github/workflows/v31_c9_discovery_reusable.yml",text)
                self.assertIn("needs: ["+job+"]",text)
                self.assertIn("needs."+job+".result == 'skipped'",text)
                self.assertIn("needs."+job+".result == 'success'",text)
                self.assertIn("vars."+flag+" == 'true'",text)
                self.assertIn("vars."+flag+" != 'true'",text)
                self.assertIn("vars.V31_EDITORIAL_C9_RELEASE_ENABLED == 'true'",text)
                self.assertIn("vars.V31_EDITORIAL_C9_RELEASE_ENABLED != 'true'",text)
                self.assertIn("actions/download-artifact@v4",text)
                self.assertIn("min_fallback: "+str(minimum),text)
                self.assertIn(source,text)
        casa=(ROOT/".github/workflows/casa_editorial_generate_schedule.yml").read_text()
        self.assertIn("src/editorial_cross_blog_guard.py --project casa_decoracao",casa)
        self.assertIn("V31_EDITORIAL_C9_RELEASE_ENABLED == 'true'",casa)
        # C149: Radar's standalone Fase3 queue is retired, not silently
        # carried over as a separate writer; the universal V31 engine owns it.
        radar=ROOT/".github/workflows/radar_fase3_fila_diaria.yml"
        self.assertFalse(radar.exists())
        archive=json.loads((ROOT/
            "affiliate_hub_v31/EDITORIAL_LEGACY_RADAR_RETIREMENT_C149.json"
        ).read_text(encoding="utf-8"))
        self.assertIn(".github/workflows/"+radar.name,
                      {row["path"] for row in archive["retired_workflows"]})

    def test_reuse_requires_three_independent_flags(self):
        for path,blog_flag in (
            ("casa_editorial_generate_schedule.yml", "V31_CASA_R2_FALLBACK_ENABLED"),
            ("oficina_editorial_autonomous.yml","V31_OFICINA_R2_FALLBACK_ENABLED"),
        ):
            with self.subTest(path=path):
                content=(ROOT/".github/workflows"/path).read_text()
                self.assertIn("V31_EDITORIAL_PRODUCT_REUSE_ENABLED:",content)
                self.assertIn("vars.V31_EDITORIAL_C9_RELEASE_ENABLED == 'true' &&",content)
                self.assertIn("vars."+blog_flag+" == 'true' &&",content)
                self.assertIn("vars.V31_EDITORIAL_PRODUCT_REUSE_ENABLED == 'true'",content)
                self.assertIn("&& 'true' || 'false'",content)

    def test_no_fallback_flags_pre_enabled_in_any_workflow(self):
        for path in (ROOT/".github/workflows").glob("v31_c9_*.yml"):
            contents=path.read_text()
            self.assertNotIn("LIVE_PUBLISH_ENABLED: 'true'",contents)
            self.assertNotIn("publish_generated.py",contents)


class MinimumFallbackTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.out=self.root/"final"
        self.scanner=self.root/"scanner.py"
        self.scanner.write_text("""
import json, os
from pathlib import Path
import shopee_oportunidades as base
out=base.post_graphql('unused','unused','query')
if not out.get('errors'):
    root=Path(os.environ['SHOPEE_OUTPUT_DIR'])
    root.mkdir(parents=True,exist_ok=True)
    product={
      "itemId":"12","productName":"Luminária de Mesa",
      "offerLink":"https://s.shopee.com.br/valid","imageUrl":"https://img.example.invalid/p"}
    (root/'ranking.json').write_text(json.dumps({"ranking":[product]}))
    (root/'intent_report.json').write_text(json.dumps({"ranking":[product]}))
    (root/'ranking.csv').write_text('itemId\\n12')
    (root/'search_signals.json').write_text('{}')
""",encoding="utf-8")
        self.config=self.root/"config.json"
        self.rules=self.root/"rules.json"
        self.config.write_text(json.dumps({"categories":{"Decoracao":["luminaria"]}}))
        self.rules.write_text('{"rules":{}}')
        sys.path.insert(0,str(router.ROOT/"src"))
        import shopee_oportunidades as base
        self.base=base
        self.addCleanup(sys.path.remove,str(router.ROOT/"src"))

    def test_underfilled_r2_blocks_without_clobbering_previous_ranking(self):
        self.out.mkdir(parents=True)
        marker='{"ranking":[{"original":true}]}'
        (self.out/"ranking.json").write_text(marker)
        def one_cached(site,config,rules,stage,limit):
            return emit_v23_outputs([{
                "itemId":"99","productName":"Luminária de Mesa",
                "imageUrl":"https://img.example.invalid/1.png",
                "offerLink":"https://s.shopee.com.br/cache-c9",
                "categories":["Decoracao"],
                "keywords":["luminaria"],
                "intentMatchedKeywords":["luminaria"],
                "sourceModes":["csv_r2_verified_affiliate_cache"],
                "priorityTier":"CSV_R2_CACHE",
            }],{"categories":{"Decoracao":["luminaria"]}},stage)
        with patch.object(router,"validate_scanner",return_value=self.scanner), \
             patch.object(self.base,"post_graphql",return_value={
                 "errors":[{"extensions":{"code":1000}}]}), \
             patch.object(router,"run_cloud",side_effect=one_cached):
            with self.assertRaisesRegex(router.RoutingError,
                                        "insufficient_verified_cached_offers"):
                router.run_router("wordpress_casa_decoracao","fake.py",
                    str(self.config),str(self.rules),str(self.out),limit=6,min_fallback=3)
        self.assertEqual((self.out/"ranking.json").read_text(),marker)

    def test_api_success_ignores_fallback_minimum(self):
        with patch.object(router,"validate_scanner",return_value=self.scanner), \
             patch.object(self.base,"post_graphql",return_value={"data":{}}), \
             patch.object(router,"run_cloud",side_effect=AssertionError("must not use R2")):
            self.assertEqual(router.run_router("wordpress_casa_decoracao","fake.py",
                str(self.config),str(self.rules),str(self.out),
                limit=5,min_fallback=5),"API")
        self.assertEqual(len(json.loads((self.out/"ranking.json").read_text())["ranking"]),1)


if __name__=="__main__":
    unittest.main()
