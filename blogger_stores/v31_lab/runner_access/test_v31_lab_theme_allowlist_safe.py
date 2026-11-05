#!/usr/bin/env python3
"""R23 SAFE: política de IDs do LAB, sem browser, tokens, temas ou PUT."""
import unittest

from blogger_stores.v31_lab.runner_access.v31_lab_theme_allowlist_safe import (
    ACTION, EXACT_LABS, OLD_LAB_ID, NEW_REPLICATION_LAB_ID,
    V31LabAuthorizationError, authorize_v31_lab_theme,
)


class LabThemeAllowlistTests(unittest.TestCase):
    def good(self, blog_id):
        target = EXACT_LABS[blog_id]
        return {
            "blog_id": blog_id, "blog_url": target.url,
            "loja_page_id": target.loja_page_id, "operation": ACTION,
            "confirm": f"ADOPT UNIVERSAL V31 BLOG {blog_id}",
        }

    def test_legacy_lab_remains_authorized(self):
        self.assertEqual(authorize_v31_lab_theme(**self.good(OLD_LAB_ID)).blog_id, OLD_LAB_ID)

    def test_new_lab_is_authorized(self):
        self.assertEqual(authorize_v31_lab_theme(**self.good(NEW_REPLICATION_LAB_ID)).blog_id,
                         NEW_REPLICATION_LAB_ID)

    def test_only_two_labs(self):
        self.assertEqual(set(EXACT_LABS), {OLD_LAB_ID, NEW_REPLICATION_LAB_ID})

    def test_other_existing_blogger_blog_denied(self):
        data = self.good(NEW_REPLICATION_LAB_ID)
        data["blog_id"] = "8052455848487624244"  # Vida Pet: nunca autorizado
        with self.assertRaises(V31LabAuthorizationError):
            authorize_v31_lab_theme(**data)

    def test_random_blog_denied(self):
        data = self.good(NEW_REPLICATION_LAB_ID)
        data["blog_id"] = "9999999999999999999"
        with self.assertRaises(V31LabAuthorizationError):
            authorize_v31_lab_theme(**data)

    def test_url_alias_denied(self):
        data = self.good(NEW_REPLICATION_LAB_ID)
        data["blog_url"] = data["blog_url"].replace("https://", "http://")
        with self.assertRaises(V31LabAuthorizationError):
            authorize_v31_lab_theme(**data)

    def test_port_url_denied(self):
        data = self.good(NEW_REPLICATION_LAB_ID)
        data["blog_url"] = data["blog_url"].replace(".com/", ".com:443/")
        with self.assertRaises(V31LabAuthorizationError):
            authorize_v31_lab_theme(**data)

    def test_query_url_denied(self):
        data = self.good(NEW_REPLICATION_LAB_ID)
        data["blog_url"] += "?x=1"
        with self.assertRaises(V31LabAuthorizationError):
            authorize_v31_lab_theme(**data)

    def test_loja_id_mismatch_denied(self):
        data = self.good(NEW_REPLICATION_LAB_ID)
        data["loja_page_id"] = EXACT_LABS[OLD_LAB_ID].loja_page_id
        with self.assertRaises(V31LabAuthorizationError):
            authorize_v31_lab_theme(**data)

    def test_wrong_confirmation_denied(self):
        data = self.good(NEW_REPLICATION_LAB_ID)
        data["confirm"] = "ADOPT MODEL V20"
        with self.assertRaises(V31LabAuthorizationError):
            authorize_v31_lab_theme(**data)

    def test_cross_blog_confirmation_denied(self):
        data = self.good(NEW_REPLICATION_LAB_ID)
        data["confirm"] = f"ADOPT UNIVERSAL V31 BLOG {OLD_LAB_ID}"
        with self.assertRaises(V31LabAuthorizationError):
            authorize_v31_lab_theme(**data)

    def test_unrelated_operation_denied(self):
        data = self.good(NEW_REPLICATION_LAB_ID)
        data["operation"] = "PROVISION BLOG V20"
        with self.assertRaises(V31LabAuthorizationError):
            authorize_v31_lab_theme(**data)

    def test_whitespace_denied(self):
        data = self.good(NEW_REPLICATION_LAB_ID)
        data["blog_id"] += " "
        with self.assertRaises(V31LabAuthorizationError):
            authorize_v31_lab_theme(**data)

    def test_none_denied(self):
        data = self.good(NEW_REPLICATION_LAB_ID)
        data["blog_id"] = None
        with self.assertRaises(V31LabAuthorizationError):
            authorize_v31_lab_theme(**data)


if __name__ == "__main__":
    unittest.main()
