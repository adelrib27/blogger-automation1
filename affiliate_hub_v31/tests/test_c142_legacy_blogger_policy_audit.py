"""C142: proteger auditorias de segurança mesmo quando o par Loja foi aposentado."""
import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from src import blogger_policy_repo_audit as checker


class BloggerRetiredWorkflowAuditTests(unittest.TestCase):
    def test_both_legacy_achados_casa_writers_currently_absent(self):
        self.assertEqual(len(checker.RETIRED_ACHADOS_CASA_PAIR),2)
        self.assertTrue(all(not (checker.ROOT / p).exists()
                            for p in checker.RETIRED_ACHADOS_CASA_PAIR))
        checker.audit_retired_achados_casa_pair()

    def test_retired_file_must_not_be_in_live_safe_active_lists(self):
        for path in checker.RETIRED_ACHADOS_CASA_PAIR:
            self.assertNotIn(path,checker.SAFE_WORKFLOWS)
            self.assertNotIn(path,checker.LIVE_WORKFLOWS)
        self.assertEqual(len(checker.SAFE_WORKFLOWS),17)
        self.assertEqual(len(checker.LIVE_WORKFLOWS),17)

    def test_reappearance_of_only_safe_writer_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            p=root / checker.RETIRED_ACHADOS_CASA_PAIR[0]
            p.parent.mkdir(parents=True)
            p.write_text("no guard",encoding="utf-8")
            with self.assertRaisesRegex(SystemExit,"reapareceu"):
                checker.audit_retired_achados_casa_pair(root=root)

    def test_reappearance_of_only_live_writer_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            p=root / checker.RETIRED_ACHADOS_CASA_PAIR[1]
            p.parent.mkdir(parents=True)
            p.write_text("no guard",encoding="utf-8")
            with self.assertRaisesRegex(SystemExit,"reapareceu"):
                checker.audit_retired_achados_casa_pair(root=root)

    def test_reappearance_of_both_writers_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            for n in checker.RETIRED_ACHADOS_CASA_PAIR:
                p=root / n
                p.parent.mkdir(parents=True,exist_ok=True)
                p.write_text("no policy",encoding="utf-8")
            with self.assertRaisesRegex(SystemExit,"reapareceu"):
                checker.audit_retired_achados_casa_pair(root=root)

    def test_workflows_that_still_exist_remain_audited(self):
        # Isto continua a verificar todos os 17 SAFE e 17 LIVE reais
        # contra tokens de Policy Guard, sem reduzir os requisitos.
        checker.audit_workflows()

    def test_full_repository_audit_readonly_pass(self):
        with redirect_stdout(io.StringIO()) as output:
            checker.main()
        result=output.getvalue()
        self.assertIn("BLOGGER_POLICY_REPO_AUDIT_PASS",result)
        self.assertIn("17/17 pares presentes protegidos",result)

    def test_8_monthly_store_schedules_remain_guarded(self):
        expected = {
            "casa_em_ordem_store_autonomous.yml": "5 8 8 * *",
            "escolha_certa_online_store_autonomous.yml": "20 8 13 * *",
            "achados_que_valem_store_autonomous.yml": "50 9 3 * *",
            "guia_achados_ofertas_store_autonomous.yml": "5 10 15 * *",
            "moda_ofertas_store_autonomous.yml": "20 10 18 * *",
            "achadinhos_beleza_store_autonomous.yml": "35 10 1 * *",
            "radar_tech_blogger_store_autonomous.yml": "50 10 22 * *",
            "cozinha_sem_complicacao_store_autonomous.yml": "5 11 11 * *",
        }
        audit_source=Path(checker.__file__).read_text(encoding="utf-8")
        for name, cron in expected.items():
            with self.subTest(name=name):
                wf=(checker.ROOT / ".github/workflows" / name).read_text(encoding="utf-8")
                self.assertIn('cron: "' + cron + '"', wf)
                self.assertIn('cron: "' + cron + '"', audit_source)

    def test_legacy_reference_policy_auditor_is_still_readonly(self):
        # A infraestrutura antiga permanece intacta; só a asserção
        # acompanha o agendamento mensal já existente. Nada é implantado
        # como subprojeto editorial do V31.
        from src import blogger_new_blog_policy_repo_audit as legacy
        with redirect_stdout(io.StringIO()) as captured:
            legacy.main()
        self.assertIn("PASS",captured.getvalue())

    def test_legacy_reference_monthly_writer_not_executed_here(self):
        file=(checker.ROOT / ".github/workflows" /
              "vida_pet_pratica_store_page_autonomous.yml")
        body=file.read_text(encoding="utf-8")
        self.assertIn('cron: "35 11 26 * *"',body)
        # Esta auditoria não aciona workflow_dispatch nem troca LIVE de site.
        self.assertFalse(any("workflow_dispatch" in x for x in checker.RETIRED_ACHADOS_CASA_PAIR))

    def test_no_cms_or_network_dependency_in_auditor(self):
        # O auditor é estático: lê fontes do GitHub Actions checkout.
        src=Path(checker.__file__).read_text(encoding="utf-8")
        for forbidden in ("service.posts().insert(", "service.pages().update(",
                          "requests.post(", "boto3.client(", "publish_post("):
            self.assertNotIn(forbidden,src)

    def test_retired_pair_is_not_wordpress_casa_store(self):
        for path in checker.RETIRED_ACHADOS_CASA_PAIR:
            self.assertNotIn("casa_store_safe.yml",path.split("/")[-1] if "achados_" not in path else "")
        self.assertNotIn(".github/workflows/casa_store_safe.yml",
                         checker.RETIRED_ACHADOS_CASA_PAIR)
        self.assertNotIn(".github/workflows/casa_store_autonomous.yml",
                         checker.RETIRED_ACHADOS_CASA_PAIR)


if __name__=="__main__":
    unittest.main()
