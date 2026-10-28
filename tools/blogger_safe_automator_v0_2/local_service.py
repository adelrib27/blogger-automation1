#!/usr/bin/env python3
from __future__ import annotations

import hmac
import json
import os
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from browser_provision import (
    CREATE_CONFIRMATION,
    DEFAULT_CDP_URL,
    SafeAutomationError,
    execute_audit,
    execute_create,
    execute_preflight,
)

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
MAX_BODY_BYTES = 32 * 1024
TOKEN_ENV = "BLOGGER_RUNNER_TOKEN"
CDP_ENV = "BLOGGER_CDP_URL"
DIAGNOSTICS_ENV = "BLOGGER_DIAGNOSTICS_DIR"

_OPERATION_LOCK = threading.Lock()


def _env_port() -> int:
    raw = os.environ.get("BLOGGER_RUNNER_PORT", str(DEFAULT_PORT)).strip()
    try:
        port = int(raw)
    except ValueError as exc:
        raise RuntimeError("BLOGGER_RUNNER_PORT inválida.") from exc
    if not 1 <= port <= 65535:
        raise RuntimeError("BLOGGER_RUNNER_PORT fora do intervalo 1..65535.")
    return port


def _required_token() -> str:
    token = os.environ.get(TOKEN_ENV, "")
    if len(token) < 32:
        raise RuntimeError(
            f"Defina {TOKEN_ENV} com pelo menos 32 caracteres antes de iniciar o serviço."
        )
    return token


def _cdp_url() -> str:
    return os.environ.get(CDP_ENV, DEFAULT_CDP_URL).strip() or DEFAULT_CDP_URL


def _diagnostics_dir() -> str:
    return os.environ.get(DIAGNOSTICS_ENV, "logs/browser_diagnostics").strip() or "logs/browser_diagnostics"


def _json_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


class Handler(BaseHTTPRequestHandler):
    server_version = "BloggerLocalRunner/0.3"

    def log_message(self, fmt: str, *args: Any) -> None:
        # Avoid logging request bodies or Authorization headers.
        print(f"[runner] {self.address_string()} - {fmt % args}")

    def _send(self, status: int, payload: dict[str, Any]) -> None:
        body = _json_bytes(payload)
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def _authorized(self) -> bool:
        expected = f"Bearer {_required_token()}"
        supplied = self.headers.get("Authorization", "")
        return hmac.compare_digest(supplied, expected)

    def _require_auth(self) -> bool:
        if self._authorized():
            return True
        self._send(HTTPStatus.UNAUTHORIZED, {"ok": False, "error": "unauthorized"})
        return False

    def _read_json(self) -> dict[str, Any]:
        content_type = self.headers.get("Content-Type", "")
        if not content_type.lower().startswith("application/json"):
            raise ValueError("Content-Type deve ser application/json.")
        raw_length = self.headers.get("Content-Length", "0")
        try:
            length = int(raw_length)
        except ValueError as exc:
            raise ValueError("Content-Length inválido.") from exc
        if length < 0 or length > MAX_BODY_BYTES:
            raise ValueError("Corpo da requisição excede o limite permitido.")
        raw = self.rfile.read(length)
        try:
            data = json.loads(raw.decode("utf-8") or "{}")
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("JSON inválido.") from exc
        if not isinstance(data, dict):
            raise ValueError("O corpo JSON deve ser um objeto.")
        return data

    def _run_exclusive(self, fn):
        if not _OPERATION_LOCK.acquire(blocking=False):
            self._send(HTTPStatus.CONFLICT, {"ok": False, "error": "operation_in_progress"})
            return
        try:
            result = fn()
            self._send(HTTPStatus.OK, {"ok": True, "result": result})
        except SafeAutomationError as exc:
            self._send(HTTPStatus.CONFLICT, {"ok": False, "error": "safe_automation_error", "message": str(exc)})
        except Exception:
            # Fail closed; do not leak stack traces or local paths through the API.
            self._send(HTTPStatus.INTERNAL_SERVER_ERROR, {"ok": False, "error": "internal_error"})
        finally:
            _OPERATION_LOCK.release()

    def do_GET(self) -> None:
        if self.path != "/v1/health":
            self._send(HTTPStatus.NOT_FOUND, {"ok": False, "error": "not_found"})
            return
        if not self._require_auth():
            return
        self._send(
            HTTPStatus.OK,
            {
                "ok": True,
                "service": "blogger-local-runner",
                "version": "0.3",
                "bind": "loopback",
            },
        )

    def do_POST(self) -> None:
        if not self._require_auth():
            return
        try:
            payload = self._read_json()
        except ValueError as exc:
            self._send(HTTPStatus.BAD_REQUEST, {"ok": False, "error": "bad_request", "message": str(exc)})
            return

        if self.path == "/v1/audit":
            self._run_exclusive(
                lambda: execute_audit(
                    cdp_url=_cdp_url(),
                    diagnostics_dir=_diagnostics_dir(),
                    allow_remote_cdp=False,
                )
            )
            return

        if self.path == "/v1/preflight":
            title = str(payload.get("title") or "")
            address = str(payload.get("address") or "")
            self._run_exclusive(
                lambda: execute_preflight(
                    title,
                    address,
                    cdp_url=_cdp_url(),
                    diagnostics_dir=_diagnostics_dir(),
                    allow_remote_cdp=False,
                )
            )
            return

        if self.path == "/v1/create-blog":
            title = str(payload.get("title") or "")
            address = str(payload.get("address") or "")
            confirm = str(payload.get("confirm") or "")
            if confirm != CREATE_CONFIRMATION:
                self._send(
                    HTTPStatus.BAD_REQUEST,
                    {
                        "ok": False,
                        "error": "confirmation_required",
                        "message": f'Use confirm="{CREATE_CONFIRMATION}".',
                    },
                )
                return
            self._run_exclusive(
                lambda: execute_create(
                    title,
                    address,
                    confirm=confirm,
                    cdp_url=_cdp_url(),
                    diagnostics_dir=_diagnostics_dir(),
                    allow_remote_cdp=False,
                )
            )
            return

        self._send(HTTPStatus.NOT_FOUND, {"ok": False, "error": "not_found"})


def main() -> int:
    _required_token()
    host = DEFAULT_HOST
    port = _env_port()
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"Blogger local runner ativo em http://{host}:{port}")
    print("Somente loopback. CDP remoto permanece bloqueado.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
