"""C75: HTTP D1 runner contract tests — mocked transport, NO network/CMS."""
import json
import os
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from affiliate_hub_v31.d1_http_runner import (
    CloudflareD1HTTPRunner, D1HTTPError, D1_ENDPOINT,
    OFFICIAL_ACCOUNT_ID, OFFICIAL_DATABASE_ID, WRITE_CONFIRMATION,
)
from affiliate_hub_v31.d1_universal_ready import UniversalD1ReadyState
from affiliate_hub_v31.tests.test_c71_d1_universal_ready import B, C, ROUTES


TOKEN = "v31_mock_token_" + ("x" * 40)


def envelope(rows=None, *, top_ok=True, statement_ok=True):
    return json.dumps({
        "success": top_ok,
        "errors": [],
        "result": [{"success": statement_ok, "results": rows if rows is not None else []}],
    }).encode("utf-8")


class Reply:
    status = 200

    def __init__(self, data):
        self.data = data

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def read(self, limit):
        return self.data[:limit]


class Opener:
    def __init__(self, response=None, error=None):
        self.response = response or Reply(envelope([{"n": 2}]))
        self.error = error
        self.request = None
        self.timeout = None

    def open(self, request, timeout):
        self.request, self.timeout = request, timeout
        if self.error is not None:
            raise self.error
        return self.response


class CloudflareD1HTTPTests(unittest.TestCase):
    def setUp(self):
        self.runner = CloudflareD1HTTPRunner(
            token=TOKEN, account_id=OFFICIAL_ACCOUNT_ID,
            database_id=OFFICIAL_DATABASE_ID,
        )

    def query(self, sql="SELECT COUNT(*) n FROM v31_ready_jobs", params=()):
        opener = Opener()
        with patch("affiliate_hub_v31.d1_http_runner._no_redirect_opener",
                   return_value=opener) as new_opener:
            rows = self.runner(sql, params)
        self.assertEqual(new_opener.call_count, 1)
        self.assertEqual(opener.request.full_url, D1_ENDPOINT)
        self.assertEqual(opener.request.get_method(), "POST")
        self.assertEqual(opener.timeout, 15)
        return rows, opener.request

    def test_single_select_prepared_params_and_pinned_https_url(self):
        rows, request = self.query(
            " SELECT COUNT(*) n FROM v31_ready_jobs WHERE site_key=?",
            ("blogger_site",),
        )
        self.assertEqual(rows, [{"n": 2}])
        self.assertEqual(
            json.loads(request.data),
            {"sql": "SELECT COUNT(*) n FROM v31_ready_jobs WHERE site_key=?",
             "params": ["blogger_site"]},
        )
        self.assertEqual(request.get_header("Authorization"), "Bearer " + TOKEN)
        self.assertTrue(D1_ENDPOINT.startswith("https://api.cloudflare.com/client/v4/"))

    def test_readonly_default_blocks_writes_before_network(self):
        with patch("affiliate_hub_v31.d1_http_runner._no_redirect_opener") as transport:
            for sql in (
                "INSERT INTO v31_ready_jobs VALUES (?)",
                "UPDATE v31_ready_jobs SET status='USED'",
                "DELETE FROM v31_ready_jobs",
            ):
                with self.subTest(sql=sql), self.assertRaisesRegex(
                    D1HTTPError, "metadata_write_disabled"
                ):
                    self.runner(sql, ())
            transport.assert_not_called()

    def test_write_requires_two_independent_opt_ins(self):
        writer = CloudflareD1HTTPRunner(
            token=TOKEN, account_id=OFFICIAL_ACCOUNT_ID,
            database_id=OFFICIAL_DATABASE_ID, allow_mutations=True,
        )
        with patch.dict(os.environ, {"V31_D1_SAFE_WRITES_ENABLED": ""}):
            with self.assertRaisesRegex(D1HTTPError, "metadata_write_disabled"):
                writer("UPDATE v31_ready_jobs SET status='USED'", ())
        with patch.dict(os.environ, {
            "V31_D1_SAFE_WRITES_ENABLED": WRITE_CONFIRMATION
        }):
            opener = Opener(Reply(envelope([{"fingerprint": "f" * 64}])))
            with patch("affiliate_hub_v31.d1_http_runner._no_redirect_opener",
                       return_value=opener):
                rows = writer("UPDATE v31_ready_jobs SET status=? RETURNING fingerprint",
                              ("USED",))
            self.assertEqual(rows, [{"fingerprint": "f" * 64}])

    def test_official_account_and_db_cannot_be_redirected_to_other_projects(self):
        for account_id, database_id in (
            ("b1515400afe32581994c4d3f038f835f", OFFICIAL_DATABASE_ID),
            (OFFICIAL_ACCOUNT_ID, "e16554d8-27e8-40ca-9b6e-5f6d7b54d076"),
            ("", ""),
        ):
            with self.subTest(account_id=account_id), self.assertRaisesRegex(
                D1HTTPError, "official_resource_mismatch"
            ):
                CloudflareD1HTTPRunner(
                    token=TOKEN, account_id=account_id, database_id=database_id)

    def test_no_token_or_resource_guessing_from_environment(self):
        with patch.dict(os.environ, {
            "V31_D1_API_TOKEN": TOKEN,
            "V31_D1_ACCOUNT_ID": "b1515400afe32581994c4d3f038f835f",
            "V31_D1_DATABASE_ID": OFFICIAL_DATABASE_ID,
        }):
            with self.assertRaisesRegex(D1HTTPError, "official_resource_mismatch"):
                CloudflareD1HTTPRunner.from_environment()
        with patch.dict(os.environ, {
            "V31_D1_API_TOKEN": TOKEN,
            "V31_D1_ACCOUNT_ID": OFFICIAL_ACCOUNT_ID,
            "V31_D1_DATABASE_ID": OFFICIAL_DATABASE_ID,
        }):
            self.assertIsInstance(CloudflareD1HTTPRunner.from_environment(),
                                  CloudflareD1HTTPRunner)
        with self.assertRaisesRegex(D1HTTPError, "token_missing"):
            CloudflareD1HTTPRunner(
                token="", account_id=OFFICIAL_ACCOUNT_ID,
                database_id=OFFICIAL_DATABASE_ID)

    def test_reject_sql_batches_ddl_comments_and_untrusted_params(self):
        rejected = [
            ("SELECT 1; DELETE FROM v31_ready_jobs", ()),
            ("SELECT 1 -- comment", ()),
            ("SELECT /*hack*/ 1", ()),
            ("DROP TABLE v31_ready_jobs", ()),
            ("PRAGMA writable_schema=ON", ()),
            ("WITH hacked AS (DELETE FROM v31_ready_jobs) SELECT 1", ()),
            ("SELECT ?", ([1, 2],)),
            ("SELECT ?", (True,)),
            ("SELECT ?", (float("nan"),)),
            ("SELECT 1", []),
        ]
        with patch("affiliate_hub_v31.d1_http_runner._no_redirect_opener") as net:
            for sql, params in rejected:
                with self.subTest(sql=sql, params=params), self.assertRaises(D1HTTPError):
                    self.runner(sql, params)
            net.assert_not_called()

    def test_no_sensitive_sql_token_or_results_in_network_failure(self):
        opener = Opener(error=HTTPError(D1_ENDPOINT, 401, "Unauthorized", None, None))
        with patch("affiliate_hub_v31.d1_http_runner._no_redirect_opener",
                   return_value=opener):
            with self.assertRaises(D1HTTPError) as ctx:
                self.runner("SELECT ? AS private", ("private_shopee_url",))
        self.assertEqual(str(ctx.exception), "d1_http_request_failed_closed")
        self.assertNotIn(TOKEN, str(ctx.exception))
        self.assertNotIn("private_shopee_url", str(ctx.exception))

    def test_timeout_and_redirect_fail_closed(self):
        for error in (TimeoutError("timeout"), URLError("network"),
                      D1HTTPError("d1_redirect_denied")):
            with self.subTest(error=type(error).__name__):
                with patch("affiliate_hub_v31.d1_http_runner._no_redirect_opener",
                           return_value=Opener(error=error)):
                    with self.assertRaises(D1HTTPError):
                        self.runner("SELECT 1", ())

    def test_cloudflare_top_failure_statement_failure_and_malformed_json(self):
        for response in (
            envelope([], top_ok=False),
            envelope([], statement_ok=False),
            b'{"success":true,"result":[]}',
            b"not-json",
            envelope([{"n": 1}] * 10001),
            b"x" * 1_048_577,
        ):
            with self.subTest(response_size=len(response)):
                with patch("affiliate_hub_v31.d1_http_runner._no_redirect_opener",
                           return_value=Opener(Reply(response))):
                    with self.assertRaises(D1HTTPError):
                        self.runner("SELECT COUNT(*) n FROM v31_ready_jobs", ())

    def test_sql_store_interface_count_ready_with_mocked_cloudflare(self):
        with patch("affiliate_hub_v31.d1_universal_ready.sites",
                   return_value=ROUTES):
            opener = Opener(Reply(envelope([{"n": 3}])))
            with patch("affiliate_hub_v31.d1_http_runner._no_redirect_opener",
                       return_value=opener):
                store = UniversalD1ReadyState(self.runner)
                self.assertEqual(store.count_ready(site_key=B, campaign=C), 3)
                self.assertIn("site_key=?", json.loads(opener.request.data)["sql"])
                self.assertEqual(
                    json.loads(opener.request.data)["params"], [B, C])

    def test_no_cms_or_publishing_methods(self):
        for name in ("create_post", "publish", "write_wordpress", "write_blogger",
                     "convert_shopee_link"):
            self.assertFalse(hasattr(self.runner, name))


if __name__ == "__main__":
    unittest.main()
