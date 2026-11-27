import unittest
from http import HTTPStatus
from unittest.mock import patch
import runner_source_http_v31 as http


class HandlerStub:
    def __init__(self, path, authorized=True, payload=None):
        self.path, self.authorized = path, authorized
        self.payload = payload or {}
        self.calls = []

    def _require_auth(self):
        self.calls.append("auth")
        return self.authorized

    def _read_json(self):
        self.calls.append("json")
        return self.payload

    def _send(self, status, body):
        self.calls.append(("send", status, body))


class HttpTests(unittest.TestCase):
    def test_unrelated_path_is_untouched(self):
        h = HandlerStub("/v1/health")
        self.assertFalse(http.handle_get(h))
        self.assertFalse(http.handle_post(h))
        self.assertEqual(h.calls, [])

    def test_manifest_requires_auth(self):
        h = HandlerStub(http.GET_PATH, authorized=False)
        self.assertTrue(http.handle_get(h))
        self.assertEqual(h.calls, ["auth"])

    def test_source_requires_auth(self):
        h = HandlerStub(http.POST_PATH, authorized=False)
        self.assertTrue(http.handle_post(h))
        self.assertEqual(h.calls, ["auth"])

    def test_gate_disabled_by_default(self):
        h = HandlerStub(http.GET_PATH)
        with patch.dict(http.os.environ, {http.ENABLED_ENV: "false"}):
            self.assertTrue(http.handle_get(h))
        self.assertEqual(h.calls[-1][1], HTTPStatus.FORBIDDEN)
        self.assertEqual(h.calls[-1][2]["error"], "inspection_not_enabled")

    def test_manifest_ok(self):
        h = HandlerStub(http.GET_PATH)
        with patch.object(http, "manifest", return_value={"mode": "READ_ONLY"}), patch.object(http, "_enabled", return_value=True):
            self.assertTrue(http.handle_get(h))
        self.assertEqual(h.calls[-1][1], HTTPStatus.OK)
        self.assertEqual(h.calls[-1][2]["result"]["mode"], "READ_ONLY")

    def test_read_denied_no_secret_in_response(self):
        h = HandlerStub(http.POST_PATH, payload={
            "name": "../private.env", "expected_sha256": "0" * 64,
            "confirm": "READ V31 SOURCE"
        })
        with patch.object(http, "_enabled", return_value=True):
            self.assertTrue(http.handle_post(h))
        self.assertEqual(h.calls[-1][1], HTTPStatus.CONFLICT)
        self.assertEqual(h.calls[-1][2]["error"], "SOURCE_NOT_ALLOWLISTED")


if __name__ == "__main__":
    unittest.main()
