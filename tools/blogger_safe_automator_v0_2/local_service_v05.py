#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from http import HTTPStatus
from pathlib import Path
from urllib.parse import urlparse

import local_service as base

MODEL_V20_CONFIRMATION = "ADOPT MODEL V20"
RUNTIME_GUARD_STATUS = "BLOGGER_RUNTIME_SYNC_GUARD_PASS"
PALETTES = {"auto", "blue", "emerald", "plum", "terracotta", "teal", "burgundy", "indigo", "amber"}


def _run_runtime_guard() -> dict:
    guard = Path(__file__).with_name("runtime_update_guard_v08.py")
    if not guard.exists():
        raise base.SafeAutomationError("Guardiao de atualizacao V20 nao encontrado no runner local.")
    try:
        proc = subprocess.run(
            [sys.executable, str(guard), "--mode", "v20"],
            text=True,
            capture_output=True,
            timeout=120,
        )
    except subprocess.TimeoutExpired as exc:
        raise base.SafeAutomationError("Guardiao de atualizacao V20 excedeu o tempo maximo de seguranca.") from exc

    stdout = (proc.stdout or "").strip()
    stderr = (proc.stderr or "").strip()
    if proc.returncode != 0:
        detail = (stderr or stdout)[-1600:]
        raise base.SafeAutomationError("Sincronizacao segura V20 falhou antes da adocao: " + detail)

    try:
        result = json.loads(stdout[stdout.find("{"):])
    except (ValueError, json.JSONDecodeError) as exc:
        raise base.SafeAutomationError("Guardiao V20 retornou resposta invalida.") from exc
    if result.get("status") != RUNTIME_GUARD_STATUS:
        raise base.SafeAutomationError("Guardiao V20 nao confirmou sincronizacao segura.")
    return result


def execute_model_v20_adoption(expected_blog_id: str, blog_title: str, blog_url: str, palette: str, *, confirm: str):
    blog_id = str(expected_blog_id or "").strip()
    title = str(blog_title or "").strip()
    url = str(blog_url or "").strip()
    palette = str(palette or "auto").strip().lower()

    if confirm != MODEL_V20_CONFIRMATION:
        raise base.SafeAutomationError(f'Use confirm="{MODEL_V20_CONFIRMATION}".')
    if not blog_id.isdigit():
        raise base.SafeAutomationError("Blog ID inválido.")
    if not title or len(title) > 100:
        raise base.SafeAutomationError("Título do blog inválido.")
    if palette not in PALETTES:
        raise base.SafeAutomationError("Paleta V20 inválida.")

    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or not host.endswith(".blogspot.com"):
        raise base.SafeAutomationError("URL pública do Blogger inválida.")

    runtime_sync = _run_runtime_guard()

    script = Path(__file__).with_name("install_modelo_v20_adoption.py")
    if not script.exists():
        raise base.SafeAutomationError("Instalador V20 não encontrado no runner local.")

    cmd = [
        sys.executable,
        str(script),
        "--expected-blog-id", blog_id,
        "--blog-title", title,
        "--blog-url", url,
        "--palette", palette,
        "--confirm", MODEL_V20_CONFIRMATION,
    ]
    try:
        proc = subprocess.run(cmd, text=True, capture_output=True, timeout=240)
    except subprocess.TimeoutExpired as exc:
        raise base.SafeAutomationError("Instalação V20 excedeu o tempo máximo de segurança.") from exc

    stdout = (proc.stdout or "").strip()
    stderr = (proc.stderr or "").strip()
    if proc.returncode != 0:
        detail = (stderr or stdout)[-1400:]
        raise base.SafeAutomationError("Instalação V20 falhou: " + detail)

    marker = '{\n  "status": "BLOGGER_MODELO_V20_ADOPTED"'
    pos = stdout.rfind(marker)
    if pos < 0:
        raise base.SafeAutomationError("Instalação V20 terminou sem marcador final validável.")
    try:
        result = json.loads(stdout[pos:])
    except json.JSONDecodeError as exc:
        raise base.SafeAutomationError("Resposta final do instalador V20 é inválida.") from exc

    if str(result.get("blog_id")) != blog_id or result.get("status") != "BLOGGER_MODELO_V20_ADOPTED":
        raise base.SafeAutomationError("Instalação V20 não confirmou o Blog ID esperado.")
    result["runtime_sync_guard"] = runtime_sync
    return result


class Handler(base.Handler):
    server_version = "BloggerLocalRunner/0.5"

    def do_GET(self) -> None:
        if self.path != "/v1/health":
            return super().do_GET()
        if not self._require_auth():
            return
        self._send(
            HTTPStatus.OK,
            {
                "ok": True,
                "service": "blogger-local-runner",
                "version": "0.5",
                "bind": "loopback",
            },
        )

    def do_POST(self) -> None:
        if self.path != "/v1/adopt-model-v20":
            return super().do_POST()
        if not self._require_auth():
            return
        try:
            payload = self._read_json()
        except ValueError as exc:
            self._send(HTTPStatus.BAD_REQUEST, {"ok": False, "error": "bad_request", "message": str(exc)})
            return

        confirm = str(payload.get("confirm") or "")
        if confirm != MODEL_V20_CONFIRMATION:
            self._send(
                HTTPStatus.BAD_REQUEST,
                {
                    "ok": False,
                    "error": "confirmation_required",
                    "message": f'Use confirm="{MODEL_V20_CONFIRMATION}".',
                },
            )
            return

        expected_blog_id = str(payload.get("expected_blog_id") or "")
        blog_title = str(payload.get("blog_title") or "")
        blog_url = str(payload.get("blog_url") or "")
        palette = str(payload.get("palette") or "auto")
        self._run_exclusive(
            lambda: execute_model_v20_adoption(
                expected_blog_id,
                blog_title,
                blog_url,
                palette,
                confirm=confirm,
            )
        )


def main() -> int:
    base._required_token()
    host = base.DEFAULT_HOST
    port = base._env_port()
    server = base.ThreadingHTTPServer((host, port), Handler)
    print(f"Blogger local runner V20 ativo em http://{host}:{port}")
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
