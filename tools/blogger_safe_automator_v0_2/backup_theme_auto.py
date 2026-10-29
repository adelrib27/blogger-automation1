#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import browser_provision as bp
from auto_blog_route import ensure_theme_page
from playwright.sync_api import sync_playwright


def main() -> int:
    p = argparse.ArgumentParser(description="Abre a rota Tema do Blog ID e executa o backup seguro já validado.")
    p.add_argument("--expected-blog-id", required=True)
    p.add_argument("--output", required=True)
    args = p.parse_args()

    blog_id = str(args.expected_blog_id or "").strip()
    safe_cdp = bp.validate_cdp_url(bp.DEFAULT_CDP_URL, allow_remote=False)

    with sync_playwright() as pw:
        browser, context = bp.connect_official_chrome(pw, safe_cdp)
        page = ensure_theme_page(context, blog_id)
        page.wait_for_timeout(800)
        route = bp.sanitize_url(page.url)
        connected = browser.is_connected()

    script = Path(__file__).with_name("backup_theme_safe.py")
    if not script.exists():
        raise bp.SafeAutomationError(f"backup_theme_safe.py não encontrado: {script}")

    cmd = [
        sys.executable,
        str(script),
        "--expected-blog-id",
        blog_id,
        "--output",
        str(Path(args.output).resolve()),
    ]
    proc = subprocess.run(cmd, text=True, capture_output=True)
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip()
        raise bp.SafeAutomationError(
            "Backup seguro falhou após abrir automaticamente a rota Tema. " + detail
        )

    raw = (proc.stdout or "").strip()
    try:
        result = json.loads(raw)
    except Exception:
        result = {"status":"BACKUP_COMPLETED","raw_output":raw}
    result["auto_route"] = route
    result["browser_connected"] = connected
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
