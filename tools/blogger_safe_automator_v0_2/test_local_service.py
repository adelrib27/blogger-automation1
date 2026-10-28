from __future__ import annotations

import json
import os
import threading
import unittest
from contextlib import contextmanager
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import local_service


@contextmanager
def running_server(token: str):
    with patch.dict(os.environ, {local_service.TOKEN_ENV: token}, clear=False):
        server = local_service.ThreadingHTTPServer(("127.0.0.1", 0), local_service.Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            host, port = server.server_address
            yield f"http://{host}:{port}"
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


class LocalServiceTests(unittest.TestCase):
    TOKEN = "x" * 48

    def request(self, url: str, *, method: str = "GET", token: str | None = None, body=None):
        data = None
        headers = {}
        if token is not None:
            headers["Authorization"] = f"Bearer {token}"
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        req = Request(url, data=data, headers=headers, method=method)
        try:
            with urlopen(req, timeout=3) as response:
                return response.status, json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            try:
                return exc.code, json.loads(exc.read().decode("utf-8"))
            finally:
                exc.close()

    def test_health_rejects_missing_token(self):
        with running_server(self.TOKEN) as base:
            status, payload = self.request(base + "/v1/health")
        self.assertEqual(status, 401)
        self.assertFalse(payload["ok"])

    def test_health_accepts_valid_token(self):
        with running_server(self.TOKEN) as base:
            status, payload = self.request(base + "/v1/health", token=self.TOKEN)
        self.assertEqual(status, 200)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["bind"], "loopback")

    def test_audit_endpoint_calls_safe_automation(self):
        fake = {"status": "AUDIT_OK", "new_blog_available": True}
        with patch.object(local_service, "execute_audit", return_value=fake) as audit:
            with running_server(self.TOKEN) as base:
                status, payload = self.request(
                    base + "/v1/audit",
                    method="POST",
                    token=self.TOKEN,
                    body={},
                )
        self.assertEqual(status, 200)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["result"], fake)
        audit.assert_called_once()
        self.assertFalse(audit.call_args.kwargs["allow_remote_cdp"])

    def test_settings_preflight_endpoint_calls_read_only_runner(self):
        fake = {"status": "SETTINGS_PREFLIGHT_OK", "read_only": True}
        body = {
            "expected_blog_id": "123456789",
            "description": "Descrição de teste",
            "search_description": "Descrição de pesquisa de teste",
        }
        with patch.object(local_service, "execute_settings_preflight", return_value=fake) as runner:
            with running_server(self.TOKEN) as base:
                status, payload = self.request(
                    base + "/v1/preflight/settings-profile",
                    method="POST",
                    token=self.TOKEN,
                    body=body,
                )
        self.assertEqual(status, 200)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["result"], fake)
        runner.assert_called_once()
        self.assertEqual(runner.call_args.args[0], "123456789")
        self.assertFalse(runner.call_args.kwargs["allow_remote_cdp"])

    def test_configure_settings_requires_explicit_confirmation(self):
        body = {
            "expected_blog_id": "123456789",
            "description": "Descrição de teste",
            "search_description": "Descrição de pesquisa de teste",
        }
        with patch.object(local_service, "execute_configure_settings") as runner:
            with running_server(self.TOKEN) as base:
                status, payload = self.request(
                    base + "/v1/configure-settings",
                    method="POST",
                    token=self.TOKEN,
                    body=body,
                )
        self.assertEqual(status, 400)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["error"], "confirmation_required")
        runner.assert_not_called()

    def test_configure_settings_calls_runner_with_confirmation(self):
        fake = {"status": "SETTINGS_PROFILE_VALIDATED", "robots_untouched": True}
        body = {
            "expected_blog_id": "123456789",
            "description": "Descrição de teste",
            "search_description": "Descrição de pesquisa de teste",
            "confirm": local_service.SETTINGS_CONFIRMATION,
        }
        with patch.object(local_service, "execute_configure_settings", return_value=fake) as runner:
            with running_server(self.TOKEN) as base:
                status, payload = self.request(
                    base + "/v1/configure-settings",
                    method="POST",
                    token=self.TOKEN,
                    body=body,
                )
        self.assertEqual(status, 200)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["result"], fake)
        runner.assert_called_once()
        self.assertEqual(runner.call_args.kwargs["confirm"], local_service.SETTINGS_CONFIRMATION)
        self.assertFalse(runner.call_args.kwargs["allow_remote_cdp"])


if __name__ == "__main__":
    unittest.main()
