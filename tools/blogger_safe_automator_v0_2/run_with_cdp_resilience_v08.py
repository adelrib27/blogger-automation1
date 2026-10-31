#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib
import sys
import time
from pathlib import Path

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


def _physical_click(page, locator) -> None:
    try:
        locator.scroll_into_view_if_needed(timeout=3_000)
    except Exception:
        pass
    box = locator.bounding_box()
    if not box:
        raise bp.SafeAutomationError("Controle do Blogger ficou visível, mas sem caixa física clicável.")
    page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)


def _wait_enabled(page, locator, timeout_ms: int = 30_000) -> None:
    deadline = time.time() + max(1, timeout_ms) / 1000.0
    last_state = "unknown"
    while time.time() < deadline:
        try:
            disabled_attr = locator.get_attribute("disabled")
            aria_disabled = (locator.get_attribute("aria-disabled") or "").strip().lower()
            enabled = locator.is_enabled()
            last_state = f"enabled={enabled} disabled={disabled_attr!r} aria-disabled={aria_disabled!r}"
            if enabled and disabled_attr is None and aria_disabled not in {"true", "1"}:
                return
        except Exception as exc:
            last_state = type(exc).__name__
        page.wait_for_timeout(500)
    raise bp.SafeAutomationError("Botão de download não ficou habilitado no tempo seguro: " + last_state)


def _configure_download_path(context, page) -> str:
    download_root = Path(r"C:\Blogger-Automator\downloads")
    download_root.mkdir(parents=True, exist_ok=True)
    params = {
        "behavior": "allow",
        "downloadPath": str(download_root),
        "eventsEnabled": True,
    }
    session = context.new_cdp_session(page)
    configured = False
    for method in ("Browser.setDownloadBehavior", "Page.setDownloadBehavior"):
        try:
            session.send(method, params)
            configured = True
            break
        except Exception:
            continue
    if not configured:
        raise bp.SafeAutomationError("Não foi possível configurar uma pasta de download explícita via CDP.")
    return str(download_root)


def _backup_with_physical_click(module, expected_blog_id: str, output: str) -> dict:
    blog_id = str(expected_blog_id or "").strip()
    if not blog_id.isdigit():
        raise bp.SafeAutomationError("Blog ID esperado inválido no fallback físico.")
    out = Path(output).resolve()
    safe_cdp = bp.validate_cdp_url(bp.DEFAULT_CDP_URL, allow_remote=False)

    with bp.sync_playwright() as pw:
        browser, context = bp.connect_official_chrome(pw, safe_cdp)
        page = module.ensure_theme_page(context, blog_id)
        page.wait_for_timeout(900)
        route = bp.sanitize_url(page.url)
        actual_id = module.extract_panel_blog_id(page.url)
        if actual_id != blog_id:
            raise bp.SafeAutomationError(
                f"Blog ID divergente no fallback físico do backup: atual={actual_id!r}, esperado={blog_id!r}."
            )

        download_path = _configure_download_path(context, page)
        before = module._snapshot_downloads()
        started = time.time()
        module._open_actions(page)
        item = module._backup_item(page)
        validation = None

        try:
            with page.expect_download(timeout=8_000) as info:
                _physical_click(page, item)
            validation = module._save_download(info.value, out)
            validation["interaction_mode"] = "physical-mouse-menu-item"
        except module.PlaywrightTimeoutError:
            page.wait_for_timeout(700)
            validation = module._capture_new_download(before, out, started)
            if validation is None:
                button = module._wait_download_button(page, timeout_ms=12_000)
                if button is not None:
                    _wait_enabled(page, button, timeout_ms=30_000)
                    try:
                        with page.expect_download(timeout=25_000) as info:
                            _physical_click(page, button)
                        validation = module._save_download(info.value, out)
                        validation["interaction_mode"] = "physical-mouse-enabled-dialog-button"
                    except module.PlaywrightTimeoutError:
                        deadline = time.time() + 20
                        while validation is None and time.time() < deadline:
                            page.wait_for_timeout(1_000)
                            validation = module._capture_new_download(before, out, started)

        if validation is None:
            detail = module._visible_backup_diagnostics(page)
            raise bp.SafeAutomationError(
                "Fallback físico do backup também não detectou download válido. "
                + (f"Diagnóstico: {detail}" if detail else "Sem controles adicionais visíveis.")
            )
        connected = browser.is_connected()

    return {
        "status": "BLOGGER_THEME_BACKUP_VALIDATED",
        "blog_id": blog_id,
        "output": str(out),
        "bytes": out.stat().st_size,
        "auto_route": route,
        "browser_connected": connected,
        "download_path": download_path,
        **(validation or {}),
    }


def _install_backup_resilience(module) -> None:
    original = module.execute_backup

    def wrapped(expected_blog_id: str, output: str):
        try:
            return original(expected_blog_id, output)
        except bp.SafeAutomationError as exc:
            message = str(exc)
            if "nenhum download novo e válido foi detectado" not in message:
                raise
            return _backup_with_physical_click(module, expected_blog_id, output)

    module.execute_backup = wrapped


def main() -> int:
    parser = argparse.ArgumentParser(description="Executa etapa V20 com conexao CDP resiliente e restrita a loopback.")
    parser.add_argument("target", choices=("backup", "apply"))
    args, remaining = parser.parse_known_args()

    bp.connect_official_chrome = connect_official_chrome_resilient

    module_name = "backup_theme_auto" if args.target == "backup" else "apply_theme_auto"
    module = importlib.import_module(module_name)
    if args.target == "backup":
        _install_backup_resilience(module)
    if not hasattr(module, "main"):
        raise bp.SafeAutomationError(f"Modulo alvo sem main(): {module_name}")

    sys.argv = [module_name + ".py", *remaining]
    return int(module.main())


if __name__ == "__main__":
    raise SystemExit(main())
