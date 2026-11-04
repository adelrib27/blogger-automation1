#!/usr/bin/env python3
"""Blogger V31 LAB: Cloudflare Browser Rendering public verifier (READ ONLY).

No Blogger credentials, no PUT, no Cloudflare resource creation. This is a
transport adapter to the already versioned exact-catalog HTML verifier.
The operator supplies a scoped Cloudflare API token via environment only.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import sys
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

from v31_public_verify_readonly import (
    LAB_URL, PublicThrottled, VerificationError, digest, reference, require, verify_html,
)

API_HOST = 'https://api.cloudflare.com'
MAX_ENVELOPE_BYTES = 4_000_000
MAX_HTML_BYTES = 3_000_000


class BlockRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Never forward an API bearer token to a different URL or host.
        return None


def no_redirect_open(request, timeout):
    return build_opener(BlockRedirect).open(request, timeout=timeout)


def fetch_via_browser_rendering(account_id: str, api_token: str, *, opener: Callable = no_redirect_open) -> str:
    """Return raw HTML through the documented Cloudflare Browser Rendering API.

    Cloudflare is the transport; the V31 contract checks the actual HTML.
    HTTP 429/503/504 => pending, never pass or retry a write.
    """
    require(isinstance(account_id, str) and re.fullmatch(r'[0-9a-fA-F]{32}', account_id) is not None,
            'Cloudflare account ID inválido')
    require(isinstance(api_token, str) and len(api_token.strip()) >= 20,
            'Credencial Cloudflare ausente ou inválida')
    endpoint = (API_HOST + '/client/v4/accounts/' + account_id +
                '/browser-rendering/content?cacheTTL=0')
    payload = json.dumps({
        'url': LAB_URL,
        'gotoOptions': {'waitUntil': 'domcontentloaded', 'timeout': 30000},
    }, separators=(',', ':')).encode('utf-8')
    req = Request(endpoint, data=payload, method='POST', headers={
        'Authorization': 'Bearer ' + api_token,
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    })
    try:
        with opener(req, timeout=65) as response:
            require(response.status == 200, 'Cloudflare não retornou 200')
            buf = response.read(MAX_ENVELOPE_BYTES + 1)
            require(len(buf) <= MAX_ENVELOPE_BYTES, 'Resposta Cloudflare muito grande')
    except HTTPError as exc:
        if exc.code in (429, 503, 504):
            raise PublicThrottled('Cloudflare temporariamente limitado/indisponível HTTP ' + str(exc.code)) from exc
        # No Authorization or response bodies in errors.
        raise VerificationError('Cloudflare API HTTP ' + str(exc.code)) from exc
    except (URLError, TimeoutError) as exc:
        raise PublicThrottled('Rede Cloudflare temporariamente indisponível') from exc
    try:
        envelope = json.loads(buf)
    except (UnicodeDecodeError, ValueError, TypeError) as exc:
        raise VerificationError('Resposta Cloudflare não é JSON válido') from exc
    require(isinstance(envelope, dict) and envelope.get('success') is True,
            'Cloudflare não confirmou sucesso na obtenção do conteúdo')
    html = envelope.get('result')
    require(isinstance(html, str) and 1000 < len(html.encode('utf-8')) <= MAX_HTML_BYTES,
            'Cloudflare não retornou HTML válido/completo')
    return html


def run(selection_path: Path, profile_path: Path, pin: str,
        account_id: str, api_token: str, *, opener: Callable = no_redirect_open) -> dict:
    raw = selection_path.read_bytes()
    require(digest(raw) == pin, 'SHA-256 da seleção divergiu')
    selection = json.loads(raw)
    profile = json.loads(profile_path.read_text(encoding='utf-8'))
    expected = reference(profile, selection, pin)
    html = fetch_via_browser_rendering(account_id, api_token, opener=opener)
    proof = verify_html(html, expected)
    return {**proof, 'transport': 'CLOUDFLARE_BROWSER_RENDERING',
            'public_verified': True, 'publication_attempted': False}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='V31 LAB verificação pública exata via Cloudflare em READ ONLY')
    parser.add_argument('--selection', type=Path, required=True)
    parser.add_argument('--profile', type=Path, required=True)
    parser.add_argument('--selection-sha256', required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args(argv)
    result: dict = {'status': 'PUBLIC_NOT_RUN', 'public_verified': False,
                    'publication_attempted': False}
    code = 2
    try:
        result = run(args.selection, args.profile, args.selection_sha256,
                     os.environ.get('CLOUDFLARE_ACCOUNT_ID', ''),
                     os.environ.get('CLOUDFLARE_BROWSER_TOKEN', ''))
        code = 0
    except PublicThrottled as exc:
        result = {'status': 'PUBLIC_PENDING_THROTTLED', 'reason': str(exc),
                  'public_verified': False, 'publication_attempted': False}
        code = 75
    except Exception as exc:
        result = {'status': 'PUBLIC_VERIFICATION_FAILED',
                  'error_type': type(exc).__name__, 'reason': str(exc)[:170],
                  'public_verified': False, 'publication_attempted': False}
        code = 2
    result['verified_at_utc'] = datetime.now(timezone.utc).isoformat()
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))
    return code


if __name__ == '__main__':
    sys.exit(main())