#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib
import sys
import time

import browser_provision as bp


def connect_official_chrome_resilient(playwright, cdp_url: str):
    safe_cdp = bp.validate_cdp_url(cdp_url, allow_remote=False)
    last_exc: Exception | None = None
    for attempt in range(1, 4):
        try:
            bp.probe_cdp(safe_cdp, timeout_seconds=5.0)
            browser = playwright.chromium.connect_over_cdp(safe_cdp, timeout=30_000)
            if not browser.contexts:
                raise bp.SafeAutomationError("Chrome conectado via CDP, mas nenhum contexto foi encontrado.")
            return browser, browser.contexts[0]
        except Exception as exc:
            last_exc = exc
            if attempt < 3:
                time.sleep(1.5 * attempt)
    raise bp.SafeAutomationError(
        "Chrome/CDP respondeu, mas o Playwright nao conseguiu concluir a conexao apos 3 tentativas seguras."
    ) from last_exc


def main() -> int:
    parser = argparse.ArgumentParser(description="Executa etapa V20 com conexao CDP resiliente e restrita a loopback.")
    parser.add_argument("target", choices=("backup", "apply"))
    args, remaining = parser.parse_known_args()

    bp.connect_official_chrome = connect_official_chrome_resilient

    module_name = "backup_theme_auto" if args.target == "backup" else "apply_theme_auto"
    module = importlib.import_module(module_name)
    if not hasattr(module, "main"):
        raise bp.SafeAutomationError(f"Modulo alvo sem main(): {module_name}")

    sys.argv = [module_name + ".py", *remaining]
    return int(module.main())


if __name__ == "__main__":
    raise SystemExit(main())
