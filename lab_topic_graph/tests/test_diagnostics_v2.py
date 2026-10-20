import unittest

from lab_topic_graph.diagnostics_v2 import (
    build_anchor_registry,
    build_enhanced_ab,
    build_link_health,
)


class DiagnosticsV2Tests(unittest.TestCase):
    def test_ab_separates_cross_cluster_from_cross_silo(self):
        content = {"articles": [
            {"article_id": "s", "silo_id": "A", "cluster_id": "1", "classification": {"status": "APPROVED"}},
            {"article_id": "same", "silo_id": "A", "cluster_id": "1", "classification": {"status": "APPROVED"}},
            {"article_id": "cluster", "silo_id": "A", "cluster_id": "2", "classification": {"status": "APPROVED"}},
            {"article_id": "silo", "silo_id": "B", "cluster_id": "3", "classification": {"status": "APPROVED"}},
        ]}
        comparison = {"rows": [{"source_article_id": "s", "legacy_selected": [
            {"target_article_id": "same"},
            {"target_article_id": "cluster"},
            {"target_article_id": "silo"},
        ]}]}
        result = build_enhanced_ab(content, comparison)["aggregate"]
        self.assertEqual(result["legacy_same_cluster"], 1)
        self.assertEqual(result["legacy_cross_cluster_same_silo"], 1)
        self.assertEqual(result["legacy_cross_silo"], 1)

    def test_link_health_is_registered_only_until_verified(self):
        result = build_link_health({"articles": [{
            "article_id": "1",
            "url": "https://example.test/a",
            "canonical_url": "https://example.test/a",
            "status": "LIVE",
            "target_health": "REGISTERED_ONLY",
            "last_verified_at": None,
        }]})
        self.assertEqual(result["verification_mode"], "OFFLINE_REGISTERED_ONLY")
        self.assertEqual(result["status_counts"], {"REGISTERED_ONLY": 1})

    def test_anchor_registry_counts_reuse(self):
        graph = {"edges": [
            {"anchor_text": "Guia de colchão", "anchor_type": "TITLE_VARIANT", "target_article_id": "1", "status": "BLOCKED_TARGET_UNVERIFIED"},
            {"anchor_text": "Guia de colchão", "anchor_type": "TITLE_VARIANT", "target_article_id": "1", "status": "BLOCKED_TARGET_UNVERIFIED"},
        ]}
        rows = build_anchor_registry(graph)["rows"]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["uses"], 2)


if __name__ == "__main__":
    unittest.main()
