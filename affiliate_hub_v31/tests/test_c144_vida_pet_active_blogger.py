"""C144: real Vida Pet Prática Blogger blog is distinct from universal C69 methodology.

Offline regression only: no Blogger, Shopee, R2, D1 or live writes.
"""
from __future__ import annotations

import copy
import unittest

from affiliate_hub_v31 import editorial_scope_validation as gate, routing


class VidaPetRealBlogIdentityTests(unittest.TestCase):
    def setUp(self):
        self.policy = gate.load_policy()
        self.deleted = gate.load_tombstones(self.policy)
        self.blog = self.policy["blogger"]["connected_active_blogs_pending_onboarding"][0]

    def test_real_active_blog_is_not_a_deleted_tombstone(self):
        self.assertEqual(self.blog["id"], "8052455848487624244")
        self.assertEqual(self.blog["name"], "Vida Pet Prática")
        self.assertEqual(self.blog["url"], "https://vida-pet-pratica.blogspot.com/")
        self.assertEqual(len(self.deleted["deleted_blogs"]), 24)
        self.assertNotIn(self.blog["id"],
                         {x["blog_id"] for x in self.deleted["deleted_blogs"]})
        self.assertEqual(self.deleted["existing_active_blogger_not_onboarded"]["blog_id"],
                         self.blog["id"])

    def test_connected_blogger_inventory_is_separate_from_v31_registered_targets(self):
        self.assertEqual(len(self.policy["blogger"]["current_targets"]), 4)
        self.assertEqual(self.policy["snapshot_counts"]["blogger_active_connected_non_excluded"], 5)
        self.assertEqual(self.policy["snapshot_counts"]["blogger_active_pending_v31_onboarding"], 1)
        self.assertEqual(self.policy["snapshot_counts"]["blogger_connected_verified_cms_total"], 6)
        self.assertEqual(len(self.policy["wordpress"]["current_targets"]), 3)

    def test_active_blog_without_verified_campaign_remains_fail_closed(self):
        route = {"site_key": self.blog["site_key"], "platform": "blogger",
                 "identifier": self.blog["id"], "campaign": "unverified",
                 "publish_enabled": False}
        self.assertEqual(gate.scope_status(self.policy, route),
                         "CMS_ACTIVE_ONBOARDING_REQUIRED")
        preflight = gate.evaluate_preflight(self.policy, route, {},
                                           site_key=self.blog["site_key"])
        self.assertEqual(preflight["status"], "CMS_ACTIVE_ONBOARDING_REQUIRED")
        self.assertFalse(preflight["allows_cms_write"])
        self.assertFalse(preflight["allows_live"])
        self.assertFalse(preflight["allows_affiliate_mutation"])

    def test_unregistered_blog_is_not_a_special_pet_writer(self):
        self.assertNotIn(self.blog["site_key"], routing.sites())
        self.assertFalse(self.blog["route_registered"])
        self.assertFalse(self.blog["campaign_verified"])
        self.assertEqual(gate.scope_status(self.policy, None, site_key=self.blog["site_key"]),
                         "CMS_ACTIVE_ONBOARDING_REQUIRED")

    def test_spoofed_identity_does_not_acquire_v31_writer_permissions(self):
        real_target = self.policy["blogger"]["current_targets"][0]
        route = {"site_key": real_target["site_key"], "platform": "blogger",
                 "identifier": self.blog["id"], "campaign": "fake",
                 "publish_enabled": False}
        self.assertEqual(gate.scope_status(self.policy, route),
                         "CMS_ACTIVE_ONBOARDING_REQUIRED")
        self.assertFalse(gate.is_route_in_active_scope(route))

    def test_universal_methodology_is_not_a_blog_identity(self):
        method = self.policy["universal_reference_methodology"]
        self.assertIn("Evidence Engine", method["components"])
        self.assertIn("UNIVERSAL", method["architectural_status"])
        self.assertIn("CMS ID 8052455848487624244", method["origin_context"])

    def test_pending_campaign_gate_cannot_be_forged_by_policy_change(self):
        tampered = copy.deepcopy(self.policy)
        tampered["blogger"]["connected_active_blogs_pending_onboarding"][0]["campaign_verified"] = True
        with self.assertRaises(gate.EditorialScopeError):
            gate.validate_policy(tampered)

    def test_50_simulations_include_real_blog_and_all_24_deleted(self):
        cases = gate.simulation_cases(self.policy)
        self.assertEqual(len(cases), 50)
        pending = [x for x in cases if x["site_key"] == self.blog["site_key"]]
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0]["expected"], "CMS_ACTIVE_ONBOARDING_REQUIRED")
        report = gate.run_simulations(policy=self.policy, count=50)
        self.assertEqual(report["passed"], 50)
        self.assertEqual(report["outcomes"]["DELETED_BY_OWNER"], 24)
        self.assertFalse(report["live_authorized"])
        self.assertEqual(report["cms_writes"], 0)


if __name__ == "__main__":
    unittest.main()
