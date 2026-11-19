"""C59 — planos JSON fora do limite são repetidos, nunca aprovados à força."""
import importlib.util
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
PROJECTS=("casa_decoracao","oficina_garagem","radar_tech_br")
VALID={
 "title":"Como escolher um modelo para organizar a casa",
 "keyword":"organizar a casa",
 "reader_need":"Entender espaço, limpeza e funcionalidade.",
 "product_connection":"O produto selecionado ajuda a comparar alternativas."
}
BAD={**VALID,"title":"Título curto"}


class PlanRetrySafetyTests(unittest.TestCase):
    def _load(self,folder):
        file=ROOT/folder/"src"/"generate_articles.py"
        sys.path.insert(0,str(file.parent))
        try:
            spec=importlib.util.spec_from_file_location(
                "wp_plan_retry_"+folder,file)
            module=importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
        finally:
            sys.path.remove(str(file.parent))

    def _record(self):
        return {"product":"Produto de exemplo genérico",
                "category":"Organização",
                "source_keyword":"organizar a casa"}

    def test_three_projects_retry_rejected_short_title(self):
        for folder in PROJECTS:
            module=self._load(folder)
            with self.subTest(folder=folder):
                replies=[json.dumps(BAD),json.dumps(VALID)]
                prompts=[]
                def simulated_ai(prompt,kind="html"):
                    self.assertEqual(kind,"plan")
                    prompts.append(prompt)
                    return replies.pop(0)
                with patch.object(module,"ai",side_effect=simulated_ai):
                    result=module.make_plan(self._record())
                self.assertEqual(result["title"],VALID["title"])
                self.assertEqual(len(prompts),2)
                self.assertIn("35 a 60" if folder=="radar_tech_br" else "35 a 65",prompts[1])

    def test_three_invalid_responses_block_without_publishing(self):
        for folder in PROJECTS:
            module=self._load(folder)
            with self.subTest(folder=folder):
                with patch.object(module,"ai",
                                  return_value=json.dumps(BAD)) as model:
                    with self.assertRaisesRegex(
                        RuntimeError,"planejamento bloqueado após 3 tentativas"):
                        module.make_plan(self._record())
                self.assertEqual(model.call_count,3)

    def test_explicit_raw_invalid_plan_does_not_trigger_ai(self):
        for folder in PROJECTS:
            module=self._load(folder)
            with self.subTest(folder=folder):
                with patch.object(module,"ai") as model:
                    with self.assertRaisesRegex(
                        RuntimeError,"título editorial fora da faixa"):
                        module.make_plan(self._record(),raw=json.dumps(BAD))
                model.assert_not_called()


if __name__=="__main__":
    unittest.main()
