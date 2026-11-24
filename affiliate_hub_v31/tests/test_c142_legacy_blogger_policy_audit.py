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
