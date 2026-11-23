"""C140/C141 — 50 cenários individuais, portfólio global e guardas.

Casos synthetic-only; nenhum login CMS, nenhuma chamada Shopee/D1/R2, nem
mutação de arquivos de produção. A métrica é testes executados, não DRAFTs.
"""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from affiliate_hub_v31 import editorial_scope_validation as gate


POLICY = gate.load_policy()
CASES = gate.simulation_cases(POLICY)
assert len(CASES) == 50, "exactly_fifty_scenarios_required"


class FiftyUniversalScopeSimulations(unittest.TestCase):
    """Um teste unittest para CADA cenário, garantindo contagem rastreável."""


def _create_case_test(case):
    def test(self):
        actual = gate.evaluate_preflight(POLICY, case["route"], case["quality"],
                                         site_key=case["site_key"])
        self.assertEqual(actual["status"], case["expected"])
        self.assertFalse(actual["allows_cms_write"])
        self.assertFalse(actual["allows_live"])
        self.assertFalse(actual["allows_affiliate_mutation"])
        self.assertEqual(actual["network_calls"], 0)
        self.assertEqual(actual["passes_simulated_preflight"],
                         case["expected"] == "PREFLIGHT_ONLY_NOT_AUTHORIZED")
    return test


for _case in CASES:
    setattr(FiftyUniversalScopeSimulations,
            f"test_{_case['id']}_{_case['variant']}", _create_case_test(_case))


class ScopeGuardContractTests(unittest.TestCase):
    def test_explicit_excluded_id_cannot_spoof_site_key(self):
        excluded = POLICY["blogger"]["exclusions"][0]
        target = POLICY["blogger"]["current_targets"][0]
        spoof = {"site_key": target["site_key"], "platform": "blogger",
                 "identifier": excluded["id"], "publish_enabled": False,
                 "campaign": "fake_campaign"}
        self.assertEqual(gate.scope_status(POLICY, spoof), "EXCLUDED_BY_OWNER")

    def test_missing_or_wrong_site_identity_fails_closed(self):
        active = next(e for e in POLICY["blogger"]["current_targets"]
                      if e["route_registered"])
        mock = {"site_key": active["site_key"], "platform": "blogger",
                "identifier": "9999999999999999999", "publish_enabled": False,
                "campaign": "fakecampaign"}
        self.assertEqual(gate.scope_status(POLICY, mock), "ROUTE_IDENTITY_MISMATCH")
        self.assertEqual(gate.scope_status(POLICY, None, site_key=active["site_key"]),
                         "ROUTE_NOT_REGISTERED")

    def test_live_not_granted_even_all_simulated_quality_flags_true(self):
        result = gate.run_simulations(count=50)
        self.assertEqual(result["executed"], 50)
        self.assertEqual(result["failed"], 0)
        self.assertEqual(result["cms_writes"], 0)
        self.assertEqual(result["affiliate_mutations"], 0)
        self.assertFalse(result["live_authorized"])
        self.assertGreaterEqual(result["outcomes"]["PREFLIGHT_ONLY_NOT_AUTHORIZED"], 1)
        self.assertEqual(result["global_coverage_audit"]["global_candidates"], 28)
        self.assertEqual(result["global_coverage_audit"]["cross_account_pending"], 24)

    def test_ten_to_fifty_enforced(self):
        self.assertEqual(gate.run_simulations(count=10)["passed"], 10)
        for count in (0, 9, 51, True, "50"):
            with self.subTest(count=count), self.assertRaises(gate.EditorialScopeError):
                gate.run_simulations(count=count)

    def test_reference_method_is_universal_not_separate_pipeline(self):
        method = POLICY["universal_reference_methodology"]
        self.assertIn("UNIVERSAL_BLOGGER_WORDPRESS", method["architectural_status"])
        self.assertIn("every active", method["allowed_for"])
        self.assertFalse(any(k.startswith("vida_pet_") for k in POLICY["rollout"]))
        self.assertEqual(POLICY["simulation_gate"]["target_cases_per_validation_cycle"], 50)
        # A metodologia inspiradora NÃO é blog, projeto nem destino editorial do V31.
        self.assertNotIn("8052455848487624244",
                         [x["id"] for x in POLICY["blogger"]["current_targets"]])
        self.assertEqual(len(POLICY["blogger"]["current_targets"]), 4)
        self.assertEqual(POLICY["snapshot_counts"]["total_current_targets"], 31)
        self.assertEqual(POLICY["snapshot_counts"]["blogger_connected_verified_subset"], 4)

    def test_policy_tampering_fails_closed(self):
        tampered = copy.deepcopy(POLICY)
        tampered["rollout"]["global_third_party_writes_now_authorized"] = True
        with self.assertRaises(gate.EditorialScopeError):
            gate.validate_policy(tampered)
        tampered = copy.deepcopy(POLICY)
        tampered["simulation_gate"]["target_cases_per_validation_cycle"] = 0
        with self.assertRaises(gate.EditorialScopeError):
            gate.validate_policy(tampered)
        tampered = copy.deepcopy(POLICY)
        tampered["blogger"]["exclusions"][0]["exclude_from_new_v31_editorial_article_automation"] = False
        with self.assertRaises(gate.EditorialScopeError):
            gate.validate_policy(tampered)

    def test_active_sites_have_same_rule_without_niche_exemptions(self):
        for candidate in POLICY["blogger"]["current_targets"]:
            self.assertIn("route_registered",candidate)
        for candidate in POLICY["wordpress"]["current_targets"]:
            self.assertIn("route_registered",candidate)
        self.assertFalse(any("pet_only" in str(c).lower()
                             for c in POLICY["universal_reference_methodology"]["components"]))

    def test_50_simulations_no_credentials_and_no_mutations(self):
        with patch("affiliate_hub_v31.editorial_scope_validation.load_policy",
                   return_value=POLICY):
            self.assertEqual(gate.run_simulations()["passed"], 50)

    @staticmethod
    def request_doc(site, enabled=True):
        return {"site_key":site["site_key"], "topic":"pauta real somente no gate",
                "platform":site["platform"], "articles":None, "enabled":enabled}

    def test_live_queue_rejects_owner_excluded_blogger_even_with_valid_route(self):
        from affiliate_hub_v31.site_request_queue import load_requests, RequestQueueError
        from affiliate_hub_v31.routing import sites
        blocked = sites()["blogger_ar_condicionado_sem_duvidas"]
        with tempfile.TemporaryDirectory() as d:
            Path(d, blocked["site_key"] + ".json").write_text(
                json.dumps(self.request_doc(blocked)), encoding="utf-8")
            with self.assertRaisesRegex(RequestQueueError,"site_outside_verified_active_scope"):
                load_requests(Path(d))

    def test_live_queue_rejects_old_blogger_outside_active_inventory(self):
        from affiliate_hub_v31.site_request_queue import load_requests, RequestQueueError
        from affiliate_hub_v31.routing import sites
        old_route=sites()["blogger_ventiladores"]
        with tempfile.TemporaryDirectory() as d:
            Path(d, old_route["site_key"] + ".json").write_text(
                json.dumps(self.request_doc(old_route)),encoding="utf-8")
            with self.assertRaisesRegex(RequestQueueError,"site_outside_verified_active_scope"):
                load_requests(Path(d))

    def test_live_queue_accepts_registered_active_pilot_without_publication(self):
        from affiliate_hub_v31.site_request_queue import load_requests
        from affiliate_hub_v31.routing import sites
        pilot=sites()["blogger_moveis_para_cada_canto"]
        with tempfile.TemporaryDirectory() as d:
            Path(d, pilot["site_key"] + ".json").write_text(
                json.dumps(self.request_doc(pilot)),encoding="utf-8")
            self.assertEqual([x["site_key"] for x in load_requests(Path(d))],
                             [pilot["site_key"]])

    def test_disabled_old_route_does_not_enter_queue_or_fail(self):
        from affiliate_hub_v31.site_request_queue import load_requests
        from affiliate_hub_v31.routing import sites
        old_route=sites()["blogger_ar_condicionado_sem_duvidas"]
        with tempfile.TemporaryDirectory() as d:
            Path(d,old_route["site_key"]+".json").write_text(
                json.dumps(self.request_doc(old_route,enabled=False)),encoding="utf-8")
            self.assertEqual(load_requests(Path(d)),[])


if __name__ == "__main__":
    unittest.main()
