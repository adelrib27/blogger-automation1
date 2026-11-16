"""C11: testar construtores/publicadores ORIGINAIS com e sem reutilização.

Executa somente arquivos temporários e funções sem rede; NUNCA invoca
main() dos publicadores WordPress nem serviços de geração Qwen3.
"""
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]


def load_script(project, name):
    folder=ROOT/project/"src"
    sys.path.insert(0,str(folder))
    try:
        spec=importlib.util.spec_from_file_location(
            f"v31_{project}_{name}_safe",folder/(name+".py"))
        obj=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(obj)
        return obj
    finally:
        sys.path.remove(str(folder))


class ReuseIntegrations(unittest.TestCase):
    def setUp(self):
        handle=tempfile.TemporaryDirectory()
        self.addCleanup(handle.cleanup)
        self.root=Path(handle.name)

    def prepare(self,project):
        casa=project=="casa_decoracao"
        rawcat="Sala" if casa else "Ferramentas"
        keyword="luminaria led" if casa else "furadeira"
        name="Luminária LED de Leitura" if casa else "Furadeira 12V"
        prefix=self.root/project
        prefix.mkdir(parents=True)
        paths={
            k:prefix/(k+".json")
            for k in ("REPORT","RANKING","CONFIG","OUT","HISTORY","ROTATION")
        }
        paths["REPORT"].write_text(json.dumps({"version":"2.3","ranking":[{
            "itemId":"123","productName":name,
            "offerLink":"https://s.shopee.com.br/safe",
            "intentMatchedKeywords":[keyword]
        }]}))
        paths["RANKING"].write_text(json.dumps({"ranking":[{
            "itemId":"123","imageUrl":"https://cf.shopee.com.br/file/product"}
        ]}))
        paths["CONFIG"].write_text(json.dumps({"categories":{rawcat:[keyword]}}))
        old_title=("Como iluminar uma sala pequena com luminárias"
                   if casa else "Como escolher uma furadeira para uso doméstico")
        paths["HISTORY"].write_text(json.dumps({"items":[{
            "shopee_item_id":"123","product":name,
            "editorial_title":old_title,
            "wordpress_url":"https://example.invalid/article1"
        }]}))
        paths["OUT"].write_text(json.dumps({"items":[{
            "id":5,"shopee_item_id":"123","status":"PUBLISHED"
        }]}))
        return paths,old_title

    def test_real_queue_generates_new_id_and_topic_only_with_opt_in(self):
        for project in ("casa_decoracao","oficina_garagem"):
            with self.subTest(project=project):
                paths,old_title=self.prepare(project)
                module=load_script(project,"build_editorial_queue")
                for key,path in paths.items():
                    setattr(module,key,path)
                with patch.object(module,"REUSE_ENABLED",False):
                    with self.assertRaises(SystemExit):
                        module.main()
                self.assertEqual(json.loads(paths["OUT"].read_text())["items"],[])
                # O histórico não é alterado pelo construtor.
                paths["OUT"].write_text(json.dumps({"items":[{
                    "id":5,"shopee_item_id":"123","status":"PUBLISHED"
                }]}))
                with patch.object(module,"REUSE_ENABLED",True):
                    module.main()
                items=json.loads(paths["OUT"].read_text())["items"]
                self.assertEqual(len(items),1)
                self.assertEqual(items[0]["status"],"PENDING")
                self.assertEqual(items[0]["id"],6)
                self.assertTrue(items[0]["reuse_candidate"])
                self.assertEqual(items[0]["prior_publication_count"],1)
                self.assertEqual(items[0]["prior_titles"],[old_title])

    def test_actual_publishers_history_append_allows_different_title_only(self):
        for project in ("casa_decoracao","oficina_garagem"):
            with self.subTest(project=project):
                pub=load_script(project,"publish_generated")
                old="Como iluminar uma sala pequena com luminárias"
                new="Luz indireta para leitura: como evitar reflexos"
                history={"items":[{
                    "shopee_item_id":"123","editorial_title":old,
                    "wordpress_url":"https://example.invalid/old"
                }]}
                item={"shopee_item_id":"123","product":"Luminária LED",
                      "source_keyword":"luminaria led",
                      "reuse_candidate":True,"prior_publication_count":1}
                article={"shopee_item_id":"123","seo_title":new,
                         "editorial_title":new,"topic":new,
                         "focus_keyword":"iluminação para leitura",
                         "reader_need":"Como evitar reflexos em ambientes pequenos",
                         "editorial_html":"<p>Texto útil e diferente.</p>"}
                with patch.object(pub,"REUSE_ENABLED",False):
                    pub.append_history(history,item,article,501,"https://example.invalid/new")
                self.assertEqual(len(history["items"]),1)
                with patch.object(pub,"REUSE_ENABLED",True):
                    pub.append_history(history,item,article,501,"https://example.invalid/new")
                    pub.append_history(history,item,article,501,"https://example.invalid/new")
                self.assertEqual(len(history["items"]),2)
                self.assertEqual(history["items"][-1]["editorial_title"],new)


if __name__ == "__main__":
    unittest.main()
