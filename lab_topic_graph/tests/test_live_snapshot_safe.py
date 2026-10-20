import copy
import unittest

from lab_topic_graph.live_snapshot_safe import build_snapshot_audit, content_hash, extract_links, validate_snapshot
from lab_topic_graph.topic_graph_safe import LabSafetyError


HOST = "achadosparacasa2026.blogspot.com"


def snapshot():
    return {
        "schema_version": "1.0",
        "site_id": "lab-site",
        "site_host": HOST,
        "source": "blogger_api_readonly",
        "complete": True,
        "fetched_at": "2026-10-20T22:00:00Z",
        "posts": [
            {
                "id": "1",
                "url": f"https://{HOST}/2026/10/source.html",
                "title": "Source",
                "status": "live",
                "content": (
                    f'<p><a href="https://{HOST}/2026/10/target.html">Guia do alvo</a></p>'
                    f'<p><a href="https://{HOST}/2026/10/privacy.html">Privacidade</a></p>'
                    f'<p><a href="https://{HOST}/2026/10/missing.html">Link ausente</a></p>'
                ),
            },
            {
                "id": "2",
                "url": f"https://{HOST}/2026/10/target.html",
                "title": "Target",
                "status": "live",
                "content": "<p>target</p>",
            },
            {
                "id": "privacy",
                "url": f"https://{HOST}/2026/10/privacy.html",
                "title": "Política de Privacidade",
                "status": "live",
                "content": "<p>privacy</p>",
            },
        ],
    }


def registry():
    return {
        "schema_version": "1.0",
        "articles": [
            {"article_id": "1", "url": f"https://{HOST}/2026/10/source.html"},
            {"article_id": "2", "url": f"https://{HOST}/2026/10/target.html"},
        ],
    }


class LiveSnapshotSafeTests(unittest.TestCase):
    def test_extract_links_and_anchor(self):
        links = extract_links('<a href="https://example.test/a"><strong>Guia</strong> útil</a>')
        self.assertEqual(links[0]["href"], "https://example.test/a")
        self.assertEqual(links[0]["anchor_text"], "Guia útil")

    def test_snapshot_must_be_complete_and_readonly(self):
        data = snapshot()
        data["complete"] = False
        with self.assertRaises(LabSafetyError):
            validate_snapshot(data)
        data = snapshot()
        data["source"] = "blogger_write"
        with self.assertRaises(LabSafetyError):
            validate_snapshot(data)

    def test_duplicate_post_id_is_blocked(self):
        data = snapshot()
        data["posts"].append(copy.deepcopy(data["posts"][0]))
        with self.assertRaises(LabSafetyError):
            validate_snapshot(data)

    def test_graph_resolves_editorial_non_editorial_and_unknown(self):
        result = build_snapshot_audit(snapshot(), registry())
        resolutions = {edge["resolution"] for edge in result["edges"]}
        self.assertIn("RESOLVED_EDITORIAL_LIVE", resolutions)
        self.assertIn("NON_EDITORIAL_INTERNAL", resolutions)
        self.assertIn("BLOCKED_UNKNOWN_INTERNAL_TARGET", resolutions)
        self.assertEqual(result["metrics"]["blogger_live_matched"], 2)
        self.assertFalse(result["safety"]["plan_ready_allowed"])

    def test_content_hash_is_stable(self):
        self.assertEqual(content_hash("abc"), content_hash("abc"))
        self.assertNotEqual(content_hash("abc"), content_hash("abcd"))


if __name__ == "__main__":
    unittest.main()
