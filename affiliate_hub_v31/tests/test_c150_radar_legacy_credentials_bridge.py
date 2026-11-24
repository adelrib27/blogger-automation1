"""C150: bridge explícita de credenciais legadas, exclusivamente Radar Tech.

Todos os testes são locais; não acessam WordPress nem segredos reais.
"""
import json
import os
import unittest
from pathlib import Path
from unittest.mock import patch
from affiliate_hub_v31 import automatic_wordpress_drafts as wp
from affiliate_hub_v31.routing import sites

ROOT=Path(__file__).resolve().parents[2]
RADAR="wordpress_radartechbr"
USER="fake-radar-user"
PASS="fake-radar-password"

class RadarScopedCredentialsTests(unittest.TestCase):
    def setUp(self):
        env=patch.dict(os.environ,{
            "V31_RADAR_LEGACY_CMS_BRIDGE_ENABLED":"true",
            "V31_RADAR_LEGACY_WORDPRESS_USERNAME":USER,
            "V31_RADAR_LEGACY_WORDPRESS_APP_PASSWORD":PASS,
            "V31_WORDPRESS_SITE_CREDENTIALS_JSON":""
        })
        env.start()
        self.addCleanup(env.stop)

    def test_reuses_old_radar_secrets_when_json_missing(self):
        self.assertEqual(wp.credentials_for(RADAR),(USER,PASS))

    def test_only_radar_exact_key_is_allowed(self):
        for key in ("wordpress_casa_decoracao","wordpress_oficina_garagem",
                    "wordpress_fake","blogger_moveis_para_cada_canto"):
            with self.subTest(key=key),self.assertRaises(wp.WordPressAutoDraftError):
                wp.credentials_for(key)

    def test_opt_in_required(self):
        os.environ["V31_RADAR_LEGACY_CMS_BRIDGE_ENABLED"]="false"
        with self.assertRaisesRegex(wp.WordPressAutoDraftError,"wordpress_credentials_not_configured"):
            wp.credentials_for(RADAR)

    def test_explicit_raw_empty_cannot_use_legacy(self):
        with self.assertRaisesRegex(wp.WordPressAutoDraftError,"wordpress_credentials_not_configured"):
            wp.credentials_for(RADAR,raw="")

    def test_canonical_json_prioritized(self):
        os.environ["V31_WORDPRESS_SITE_CREDENTIALS_JSON"]=json.dumps({
            RADAR:{"username":"new-user","application_password":"new-password"}})
        self.assertEqual(wp.credentials_for(RADAR),("new-user","new-password"))

    def test_other_site_json_preserved_while_radar_legacy_used(self):
        os.environ["V31_WORDPRESS_SITE_CREDENTIALS_JSON"]=json.dumps({
            "wordpress_casa_decoracao":{"username":"casa-user","application_password":"casa-pass"}})
        self.assertEqual(wp.credentials_for(RADAR),(USER,PASS))
        self.assertEqual(wp.credentials_for("wordpress_casa_decoracao"),("casa-user","casa-pass"))

    def test_explicit_other_site_json_does_not_fallback(self):
        raw=json.dumps({"wordpress_casa_decoracao":{"username":"a","application_password":"b"}})
        with self.assertRaisesRegex(wp.WordPressAutoDraftError,"wordpress_site_credentials_missing"):
            wp.credentials_for(RADAR,raw=raw)

    def test_malformed_radar_json_blocks_legacy(self):
        os.environ["V31_WORDPRESS_SITE_CREDENTIALS_JSON"]=json.dumps({
            RADAR:{"username":USER,"application_password":""}})
        with self.assertRaisesRegex(wp.WordPressAutoDraftError,"wordpress_site_credentials_missing"):
            wp.credentials_for(RADAR)

    def test_invalid_json_blocks_legacy(self):
        os.environ["V31_WORDPRESS_SITE_CREDENTIALS_JSON"]="{bad"
        with self.assertRaisesRegex(wp.WordPressAutoDraftError,"wordpress_credentials_schema_invalid"):
            wp.credentials_for(RADAR)

    def test_partial_old_credentials_block(self):
        os.environ["V31_RADAR_LEGACY_WORDPRESS_APP_PASSWORD"]=""
        with self.assertRaises(wp.WordPressAutoDraftError):
            wp.credentials_for(RADAR)

    def test_wrong_opt_in_value_blocks(self):
        os.environ["V31_RADAR_LEGACY_CMS_BRIDGE_ENABLED"]="1"
        with self.assertRaises(wp.WordPressAutoDraftError):
            wp.credentials_for(RADAR)

    def test_original_route_still_draft_only(self):
        route=sites()[RADAR]
        self.assertEqual(route["identifier"],"https://radartechbr.com.br/")
        self.assertEqual(route["campaign"],"radarwp")
        self.assertIs(route["publish_enabled"],False)

    def test_read_draft_history_checks_authenticated_domain(self):
        body=(ROOT/"affiliate_hub_v31/reviewed_draft_delivery.py").read_text()
        self.assertIn("wordpress._verify_blog_url(client.site_settings().get",body)
        self.assertIn("wordpress.credentials_for(site_key)",body)

    def test_universal_workflows_bind_legacy_secrets_not_values(self):
        for filename in ("v31_c148_universal_pilot_readonly.yml",
                         "v31_universal_wordpress_autodraft_daily.yml",
                         "v31_independent_review_draft.yml",
                         "v31_autonomous_draft_scheduler.yml"):
            with self.subTest(filename=filename):
                text=(ROOT/".github/workflows"/filename).read_text()
                self.assertIn("V31_RADAR_LEGACY_CMS_BRIDGE_ENABLED: 'true'",text)
                self.assertIn("V31_RADAR_LEGACY_WORDPRESS_USERNAME:",text)
                self.assertIn("secrets.WORDPRESS_USERNAME",text)
                self.assertIn("secrets.WORDPRESS_APP_PASSWORD",text)
                self.assertNotIn(PASS,text)

    def test_live_job_never_receives_legacy_secrets(self):
        text=(ROOT/".github/workflows/v31_autonomous_draft_scheduler.yml").read_text()
        self.assertEqual(text.count("V31_RADAR_LEGACY_CMS_BRIDGE_ENABLED: 'true'"),1)
        self.assertIn("environment: v31-autonomous-live",text)
        self.assertNotIn("V31_RADAR_LEGACY_CMS_BRIDGE_ENABLED",
                         text.split("environment: v31-autonomous-live",1)[1])

    def test_legacy_executors_stay_retired(self):
        doc=json.loads((ROOT/"affiliate_hub_v31/EDITORIAL_LEGACY_RADAR_RETIREMENT_C149.json").read_text())
        self.assertTrue(all(not (ROOT/x["path"]).exists() for x in doc["retired_workflows"]))

    def test_request_remains_disabled_and_live_requires_approval(self):
        req=json.loads((ROOT/"affiliate_hub_v31/site_requests.d/wordpress_radartechbr.json").read_text())
        self.assertIs(req["enabled"],False)
        policy=json.loads((ROOT/"affiliate_hub_v31/autonomous_live_policy.json").read_text())
        self.assertEqual(policy["activation"],"pending_policy_approval")

if __name__=="__main__":
    unittest.main()
