"""C70: agendamentos de handoff aceitam pedidos contínuos sem publicar."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from affiliate_hub_v31.handoff_dispatch import DispatchError,dispatch
from affiliate_hub_v31.universal_editorial_handoff import MAX_ARTICLES_PER_BATCH


class CatalogContext:
    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False


class FakeR2:
    def __init__(self):
        self.restores = 0

    def restore_to(self, path):
        self.restores += 1
        Path(path).write_bytes(b"fixture-verified-by-mock")
        return True


def request(key, count):
    return {"site_key": key, "platform": "blogger",
            "topic": "móveis reais", "articles": count, "enabled": True}


def safe_plan(*_, **kwargs):
    if type(kwargs["articles"]) is not int or not 1 <= kwargs["articles"] <= 24:
        raise ValueError("invalid_article_count")
    return {"site_registered": True, "can_publish": False,
            "ready_review_jobs": [{"status": "REVIEW_REQUIRED"}],
            "conversion_required_keys": []}


class ContinuousHandoffScheduleTests(unittest.TestCase):
    def setUp(self):
        self.r2 = FakeR2()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)
        patches = (
            patch("affiliate_hub_v31.handoff_dispatch.verify_database"),
            patch("affiliate_hub_v31.handoff_dispatch.Catalog",
                  return_value=CatalogContext()),
            patch("affiliate_hub_v31.handoff_dispatch.plan_editorial_handoff",
                  side_effect=safe_plan),
        )
        self.patches = [p.start() for p in patches]
        for p in patches:
            self.addCleanup(p.stop)

    def test_two_continuous_sites_are_each_planned_as_one_bounded_batch(self):
        with patch("affiliate_hub_v31.handoff_dispatch.load_requests",
                   return_value=[request("site_a", None),
                                 request("site_b", None)]):
            result = dispatch(self.r2, directory=self.dir)
        self.assertEqual(result["mode"], "DRY_RUN")
        self.assertEqual(result["requests_evaluated"], 2)
        self.assertEqual(result["ready_review_jobs"], 2)
        self.assertEqual(result["private_envelopes_saved"], 0)
        self.assertEqual(result["publication_calls"], 0)
        self.assertEqual(result["catalog_r2_writes"], 0)
        plans = self.patches[2].call_args_list
        self.assertEqual(len(plans), 2)
        self.assertTrue(all(c.kwargs["articles"] == MAX_ARTICLES_PER_BATCH
                            for c in plans))
        self.assertEqual(self.r2.restores, 1)

    def test_finite_request_retains_exact_requested_count(self):
        with patch("affiliate_hub_v31.handoff_dispatch.load_requests",
                   return_value=[request("site_a", 3)]):
            dispatch(self.r2, directory=self.dir)
        self.assertEqual(self.patches[2].call_args.kwargs["articles"], 3)

    def test_execute_saves_private_review_only_and_is_fail_closed(self):
        with patch("affiliate_hub_v31.handoff_dispatch.load_requests",
                   return_value=[request("site_a", None)]), \
             patch("affiliate_hub_v31.handoff_dispatch.persist_private_handoff",
                   return_value={"saved_and_verified": True}) as persist:
            report = dispatch(self.r2, directory=self.dir, execute=True)
            self.assertEqual(persist.call_count, 1)
        self.assertEqual(report["private_envelopes_saved"], 1)
        self.assertEqual(report["publication_calls"], 0)
        self.assertEqual(report["catalog_r2_writes"], 0)
        with patch("affiliate_hub_v31.handoff_dispatch.load_requests",
                   return_value=[request("site_a", None)]), \
             patch("affiliate_hub_v31.handoff_dispatch.persist_private_handoff",
                   return_value={"saved_and_verified": False}):
            with self.assertRaisesRegex(DispatchError, "handoff_not_persisted"):
                dispatch(self.r2, directory=self.dir, execute=True)

    def test_empty_queue_never_reads_or_writes_r2(self):
        with patch("affiliate_hub_v31.handoff_dispatch.load_requests",
                   return_value=[]):
            report = dispatch(self.r2, directory=self.dir, execute=True)
        self.assertEqual(report["requests_evaluated"], 0)
        self.assertEqual(report["private_envelopes_saved"], 0)
        self.assertEqual(self.r2.restores, 0)


if __name__ == "__main__":
    unittest.main()
