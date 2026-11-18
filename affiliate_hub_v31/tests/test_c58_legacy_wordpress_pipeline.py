"""C58 — contrato de importação e links internos dos 3 WordPress legados.

Sem API externa, sem publicação, sem alterar arquivos de fila.
"""
import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT=Path(__file__).resolve().parents[2]
FOLDERS=("casa_decoracao","oficina_garagem","radar_tech_br")


class WordPressPipelineIntegrationTests(unittest.TestCase):
    def test_all_legacy_scripts_import_without_repo_in_pythonpath(self):
        # Reproduz a causa real dos runs Casa/Oficina: execução como arquivo,
        # onde sys.path contém somente o diretório src e não a raiz do repo.
        loader=r"""
import importlib.util
import sys
from pathlib import Path
p=Path(sys.argv[1]).resolve()
sys.path.insert(0,str(p.parent))
spec=importlib.util.spec_from_file_location("standalone_wp",p)
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
print("V31_LEGACY_WP_IMPORT_PASS")
"""
        for folder in FOLDERS:
            for name in (
                ("build_editorial_queue.py",) if folder!="radar_tech_br"
                else ()
            ) + ("generate_articles.py","publish_generated.py"):
                file=ROOT/folder/"src"/name
                result=subprocess.run(
                    [sys.executable,"-I","-c",loader,str(file)],
                    cwd=str(ROOT),capture_output=True,text=True,timeout=20)
                with self.subTest(path=str(file)):
                    self.assertEqual(result.returncode,0,
                                     result.stderr[-1500:])
                    self.assertIn("V31_LEGACY_WP_IMPORT_PASS",result.stdout)

    def test_safe_publishers_noop_without_external_writes(self):
        env={"PATH": __import__("os").environ.get("PATH","")}
        for folder in FOLDERS:
            script=ROOT/folder/"src"/"publish_generated.py"
            result=subprocess.run(
                [sys.executable,str(script)],cwd=str(ROOT),
                env=env,capture_output=True,text=True,timeout=20)
            with self.subTest(site=folder):
                self.assertEqual(result.returncode,0,result.stderr[-1800:])
                self.assertIn("desativada",result.stdout.lower())

    def test_each_legacy_article_gets_real_internal_post_links(self):
        # A origem é o histórico de URLs devolvidas pelo WordPress após
        # publicar posts. Cada blog usa o MESMO renderizador universal.
        editorial=(
            "<h2>Como escolher</h2><p>Orientações de compra.</p>"
            "<h2>O que medir</h2><p>Confira o espaço.</p>"
            "<h2>Cuidados</h2><p>Compare os anúncios.</p>"
            "<h2>Conclusão</h2><p>Resumo.</p>"
        )
        hosts={
            "casa_decoracao":"https://casaedecoracao.radartechbr.com.br",
            "oficina_garagem":"https://oficina.radartechbr.com.br",
            "radar_tech_br":"https://radartechbr.com.br",
        }
        for folder in FOLDERS:
            path=ROOT/folder/"src"/"generate_articles.py"
            # Importar pelo arquivo sem executar CLI e com diretório src local.
            old=sys.path[:]
            try:
                sys.path.insert(0,str(path.parent))
                spec=importlib.util.spec_from_file_location(
                    "wp_c58_"+folder,path)
                module=importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
            finally:
                sys.path[:]=old
            # CTA é mockado: não precisa criar link/insumo comercial.
            with patch.object(module,"SITE_URL",hosts[folder]), \
                 patch.object(module,"cta_block",return_value="<p>CTA seguro</p>"):
                html=module.insert_contextual_blocks(
                    editorial,{"category":"Sala","editorial_title":
                    "Título novo, único, ainda não publicado"},
                    "mensagem mockada")
            with self.subTest(site=folder):
                self.assertIn('data-v31-related="1"',html)
                self.assertIn("Leia também neste blog",html)
                self.assertGreaterEqual(html.count("<li>"),1)
                self.assertIn("CTA seguro",html)
                self.assertNotIn('href="https://evil.example',html)


if __name__=="__main__":
    unittest.main()
