import copy
import json
import tempfile
import unittest
from pathlib import Path

from lab_topic_graph.topic_graph_safe import (
    LabSafetyError,
    build_content_registry,
    classify_article,
    compare_legacy_vs_topic,
    plan_backfill,
    plan_link_graph,
    run_safe,
    validate_anchor,
    validate_cluster_registry,
    validate_edge,
)


SITE = "achadosparacasa2026.blogspot.com"


def base_registry():
    return {
        "schema_version": "1.0",
        "site_id": "lab-site",
        "site_host": SITE,
        "silos": [
            {
                "silo_id": "silo-quarto",
                "name": "Quarto",
                "clusters": [
                    {
                        "cluster_id": "cama",
                        "name": "Cama",
                        "pillar_article_id": "p1",
                        "source_categories": ["Quarto"],
                        "include_terms": ["cama", "colchao", "lencol"],
                        "forbidden_terms": [],
                        "min_term_hits": 1,
                        "allow_category_drift": False,
                        "link_budget": {"SATELLITE": 3, "PILLAR": 8},
                    },
                    {
                        "cluster_id": "termico",
                        "name": "Termico",
                        "pillar_article_id": None,
                        "source_categories": ["Quarto"],
                        "include_terms": ["temperatura", "calor"],
                        "forbidden_terms": [],
                        "min_term_hits": 1,
                        "allow_category_drift": False,
                        "link_budget": {"SATELLITE": 3, "PILLAR": 8},
                    },
                ],
            },
            {
                "silo_id": "silo-cozinha",
                "name": "Cozinha",
                "clusters": [
                    {
                        "cluster_id": "pia",
                        "name": "Pia",
                        "pillar_article_id": None,
                        "source_categories": ["Cozinha"],
                        "include_terms": ["pia", "escorredor", "torneira"],
                        "forbidden_terms": [],
                        "min_term_hits": 1,
                        "allow_category_drift": False,
                        "link_budget": {"SATELLITE": 3, "PILLAR": 8},
                    }
                ],
            },
        ],
    }


def history():
    return [
        {
            "id": "p1",
            "titulo": "Guia de cama confortável para o quarto",
            "url": f"https://{SITE}/2026/10/guia-cama.html",
            "categoria": "Quarto",
            "palavra_chave": "cama confortável",
            "publicado_em": "2026-10-01T00:00:00Z",
        },
        {
            "id": "s1",
            "titulo": "Como proteger o colchão de manchas",
            "url": f"https://{SITE}/2026/10/colchao.html",
            "categoria": "Quarto",
            "palavra_chave": "proteger colchão",
            "publicado_em": "2026-10-02T00:00:00Z",
        },
        {
            "id": "s2",
            "titulo": "Como escolher lençol para a cama",
            "url": f"https://{SITE}/2026/10/lencol.html",
            "categoria": "Quarto",
            "palavra_chave": "lençol",
            "publicado_em": "2026-10-03T00:00:00Z",
        },
        {
            "id": "c1",
            "titulo": "Torneira para pia de cozinha",
            "url": f"https://{SITE}/2026/10/torneira.html",
            "categoria": "Cozinha",
            "palavra_chave": "torneira pia",
            "publicado_em": "2026-10-04T00:00:00Z",
        },
    ]


class TopicGraphSafeTests(unittest.TestCase):
    def test_registry_rejects_duplicate_cluster(self):
        registry = base_registry()
        registry["silos"][1]["clusters"][0]["cluster_id"] = "cama"
        with self.assertRaises(LabSafetyError):
            validate_cluster_registry(registry)

    def test_classifier_requires_semantic_term_not_category_only(self):
        result = classify_article(
            {"titulo": "Dicas gerais para decorar", "categoria": "Quarto"},
            base_registry(),
        )
        self.assertEqual(result.status, "UNCLASSIFIED_NO_MATCH")

    def test_classifier_blocks_category_conflict(self):
        result = classify_article(
            {"titulo": "Como escolher colchão", "categoria": "Cozinha"},
            base_registry(),
        )
        self.assertEqual(result.status, "BLOCKED_CATEGORY_CONFLICT")

    def test_classifier_blocks_ambiguous_top_score(self):
        registry = base_registry()
        registry["silos"][0]["clusters"][1]["include_terms"] = ["cama"]
        result = classify_article(
            {"titulo": "Cama prática", "categoria": "Quarto"},
            registry,
        )
        self.assertEqual(result.status, "BLOCKED_AMBIGUOUS")

    def test_anchor_policy_blocks_generic(self):
        ok, reasons = validate_anchor("clique aqui")
        self.assertFalse(ok)
        self.assertIn("anchor_generic", reasons)

    def test_cross_silo_edge_is_blocked(self):
        entries = build_content_registry(history(), base_registry())
        source = next(x for x in entries if x["article_id"] == "s1")
        target = next(x for x in entries if x["article_id"] == "c1")
        source = copy.deepcopy(source)
        target = copy.deepcopy(target)
        source["target_health"] = "VERIFIED"
        target["target_health"] = "VERIFIED"
        status, reasons = validate_edge(source, target, "SATELLITE_TO_SATELLITE")
        self.assertEqual(status, "BLOCKED_CROSS_SILO")
        self.assertIn("cross_silo_denied", reasons)

    def test_unverified_target_never_becomes_plan_ready(self):
        entries = build_content_registry(history(), base_registry())
        graph = plan_link_graph(entries, base_registry())
        self.assertTrue(graph["edges"])
        self.assertFalse(any(edge["status"] == "PLAN_READY" for edge in graph["edges"]))
        self.assertTrue(any(edge["status"] == "BLOCKED_TARGET_UNVERIFIED" for edge in graph["edges"]))

    def test_verified_same_cluster_edge_can_be_plan_ready(self):
        entries = build_content_registry(history(), base_registry())
        source = next(x for x in entries if x["article_id"] == "s1")
        target = next(x for x in entries if x["article_id"] == "p1")
        source = copy.deepcopy(source)
        target = copy.deepcopy(target)
        source["target_health"] = "VERIFIED"
        target["target_health"] = "VERIFIED"
        status, reasons = validate_edge(source, target, "SATELLITE_TO_PILLAR")
        self.assertEqual(status, "PLAN_READY")
        self.assertEqual(reasons, [])

    def test_missing_pillar_is_diagnostic_and_closed(self):
        registry = base_registry()
        registry["silos"][0]["clusters"][0]["pillar_article_id"] = "does-not-exist"
        entries = build_content_registry(history(), registry)
        graph = plan_link_graph(entries, registry)
        self.assertTrue(any(d["status"] == "BLOCKED_PILLAR_MISSING" for d in graph["diagnostics"]))

    def test_backfill_blocks_without_content_hash(self):
        entries = build_content_registry(history(), base_registry())
        queue = plan_backfill("s2", entries)
        self.assertTrue(queue["jobs"])
        self.assertTrue(all(job["status"] == "BLOCKED_STALE_SOURCE" for job in queue["jobs"]))
        self.assertTrue(all("source_content_hash_missing" in job["blocking_reasons"] for job in queue["jobs"]))

    def test_ab_comparison_does_not_mutate_or_publish(self):
        entries = build_content_registry(history(), base_registry())
        result = compare_legacy_vs_topic(entries)
        self.assertGreater(result["aggregate"]["sources"], 0)
        self.assertIn("legacy_links_selected", result["aggregate"])
        self.assertIn("topic_structural_candidates", result["aggregate"])

    def test_runner_outputs_safe_manifest(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            history_path = root / "history.json"
            registry_path = root / "registry.json"
            output = root / "out"
            history_path.write_text(json.dumps(history()), encoding="utf-8")
            registry_path.write_text(json.dumps(base_registry()), encoding="utf-8")
            result = run_safe(history_path, registry_path, output)
            self.assertFalse(result["manifest"]["safety"]["cms_write_capability"])
            self.assertFalse(result["manifest"]["safety"]["publishing"])
            graph = json.loads((output / "link_graph.json").read_text(encoding="utf-8"))
            self.assertFalse(any(edge["status"] == "PLAN_READY" for edge in graph["edges"]))


if __name__ == "__main__":
    unittest.main()
