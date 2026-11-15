"""Testes do contrato de credenciais: sem vazamento de valores e sem API."""
import json
import tempfile
import unittest
from pathlib import Path

from affiliate_hub_v31.credentials import check_presence, load_registry


class CredentialContractTests(unittest.TestCase):
    def test_manifest_has_unique_names_and_no_secret_values(self):
        registry = load_registry()
        self.assertEqual(len(registry["credentials"]), 8)
        names = [item["name"] for item in registry["credentials"]]
        self.assertEqual(len(set(names)), len(names))
        self.assertTrue(all(name.startswith("V31_EDITORIAL_") for name in names))
        self.assertTrue(all(set(item) == {"name", "type", "profile", "purpose"} for item in registry["credentials"]))

    def test_profiles_validate_without_credentials(self):
        self.assertEqual(check_presence("manifest", {}), [])
        self.assertEqual(len(check_presence("shopee", {})), 2)
        self.assertEqual(len(check_presence("feeds", {})), 2)
        self.assertEqual(len(check_presence("storage", {})), 4)
        self.assertTrue(all(not present for _, _, present in check_presence("all", {})))

    def test_does_not_return_secret_values(self):
        sentinel = "private-credential-must-never-appear"
        statuses = check_presence("shopee", {
            "V31_EDITORIAL_SHOPEE_APP_ID": sentinel,
            "V31_EDITORIAL_SHOPEE_APP_SECRET": sentinel
        })
        self.assertTrue(all(present for _, _, present in statuses))
        self.assertNotIn(sentinel, str(statuses))

    def test_reject_embedded_values_or_unknown_fields(self):
        registry = load_registry()
        registry["credentials"][0]["value"] = "must-not-be-here"
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "credentials_registry.json"
            path.write_text(json.dumps(registry, ensure_ascii=False), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_registry(path)


if __name__ == "__main__":
    unittest.main()
