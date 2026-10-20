import copy
import json
import unittest
from pathlib import Path

from lab_topic_graph.observed_live_graph import ObservedGraphError, validate_observed_graph

ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT = ROOT / 'lab_topic_graph' / 'reviews' / 'live_link_graph_observed.v1.json'


class ObservedLiveGraphTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snapshot = json.loads(SNAPSHOT.read_text(encoding='utf-8'))

    def test_real_observation_metrics(self):
        metrics = validate_observed_graph(copy.deepcopy(self.snapshot))
        self.assertEqual(metrics['editorial_articles_total'], 35)
        self.assertEqual(metrics['editorial_edges_total'], 70)
        self.assertEqual(metrics['cross_silo_edges'], 16)
        self.assertEqual(metrics['orphan_articles_inbound_zero'], 13)
        self.assertEqual(metrics['unknown_internal_targets'], 0)

    def test_fail_closed_if_write_capability_appears(self):
        sample = copy.deepcopy(self.snapshot)
        sample['safety']['cms_write'] = True
        with self.assertRaises(ObservedGraphError):
            validate_observed_graph(sample)

    def test_fail_closed_if_plan_ready_enabled(self):
        sample = copy.deepcopy(self.snapshot)
        sample['safety']['plan_ready'] = True
        with self.assertRaises(ObservedGraphError):
            validate_observed_graph(sample)

    def test_fail_closed_on_duplicate_edge(self):
        sample = copy.deepcopy(self.snapshot)
        sample['edges'].append(copy.deepcopy(sample['edges'][0]))
        with self.assertRaises(ObservedGraphError):
            validate_observed_graph(sample)

    def test_fail_closed_on_unknown_target(self):
        sample = copy.deepcopy(self.snapshot)
        sample['edges'][0][1] = 'unknown'
        with self.assertRaises(ObservedGraphError):
            validate_observed_graph(sample)

    def test_fail_closed_on_relationship_tampering(self):
        sample = copy.deepcopy(self.snapshot)
        current = sample['edges'][0][2]
        sample['edges'][0][2] = 'CROSS_SILO' if current != 'CROSS_SILO' else 'SAME_CLUSTER'
        with self.assertRaises(ObservedGraphError):
            validate_observed_graph(sample)

    def test_fail_closed_if_full_content_hash_claimed(self):
        sample = copy.deepcopy(self.snapshot)
        sample['safety']['full_content_hash'] = True
        with self.assertRaises(ObservedGraphError):
            validate_observed_graph(sample)


if __name__ == '__main__':
    unittest.main()
