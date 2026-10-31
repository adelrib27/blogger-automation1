#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib
import json
import re
import sys
import time
from pathlib import Path

import browser_provision as bp

EDIT_HTML_RE = re.compile(r"^(Editar HTML|Edit HTML)$", re.I)
CANCEL_RE = re.compile(r"^(Cancelar|Cancel)$", re.I)


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


def _first_visible(locator):
    try:
        count = min(locator.count(), 40)
    except Exception:
        return None
    for i in range(count):
        item = locator.nth(i)
        try:
            if item.is_visible():
                return item
        except Exception:
            continue
    return None


def _dismiss_dialog(page) -> None:
    button = _first_visible(page.get_by_role("button", name=CANCEL_RE))
    if button is None:
        button = _first_visible(page.get_by_text(CANCEL_RE, exact=True))
    if button is not None:
        try:
            button.click(timeout=4_000)
        except Exception:
            _physical_click(page, button)
        page.wait_for_timeout(500)


def _editor_menu_item(module, page):
    module._open_actions(page)
    item = _first_visible(page.get_by_role("menuitem", name=EDIT_HTML_RE))
    if item is None:
        item = _first_visible(page.get_by_text(EDIT_HTML_RE, exact=True))
    if item is None:
        raise bp.SafeAutomationError("Opção 'Editar HTML' não foi localizada no menu Tema.")
    return item


def _theme_candidates_from_frame(frame) -> list[str]:
    try:
        values = frame.evaluate(
            r"""() => {
              const out = [];
              const add = v => {
                if (typeof v !== 'string' || v.length < 1000) return;
                if (!v.includes('<html') || !(/<b:(skin|section|widget|template-skin)/.test(v))) return;
                out.push(v);
              };
              for (const el of document.querySelectorAll('textarea')) add(el.value || el.textContent || '');
              for (const el of document.querySelectorAll('.CodeMirror')) {
                try { if (el.CodeMirror) add(el.CodeMirror.getValue()); } catch (_) {}
              }
              try {
                if (window.monaco && window.monaco.editor) {
                  for (const model of window.monaco.editor.getModels()) add(model.getValue());
                }
              } catch (_) {}
              try {
                if (window.ace) {
                  for (const el of document.querySelectorAll('.ace_editor')) add(window.ace.edit(el).getValue());
                }
              } catch (_) {}
              for (const el of document.querySelectorAll('pre,code')) add(el.textContent || '');
              return out.sort((a,b) => b.length - a.length).slice(0, 8);
            }"""
        )
        return [str(v) for v in (values or [])]
    except Exception:
        return []


def _walk_json_strings(value, out: list[str]) -> None:
    if isinstance(value, str):
        if len(value) >= 1000 and "<html" in value and re.search(r"<b:(skin|section|widget|template-skin)", value):
            out.append(value)
        return
    if isinstance(value, dict):
        for v in value.values():
            _walk_json_strings(v, out)
    elif isinstance(value, list):
        for v in value:
            _walk_json_strings(v, out)


def _theme_candidates_from_responses(responses: list) -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    for response in reversed(responses[-160:]):
        try:
            if int(response.status) < 200 or int(response.status) >= 400:
                continue
            url = str(response.url or "")
            if "blogger" not in url.lower() and "google" not in url.lower():
                continue
            body = response.body()
            if not body or len(body) > 10_000_000:
                continue
            text = body.decode("utf-8", errors="replace")
            if "<html" in text and re.search(r"<b:(skin|section|widget|template-skin)", text):
                found.append((text, url))
                continue
            try:
                data = json.loads(text)
            except Exception:
                continue
            strings: list[str] = []
            _walk_json_strings(data, strings)
            for candidate in strings:
                found.append((candidate, url))
        except Exception:
            continue
    found.sort(key=lambda item: len(item[0]), reverse=True)
    return found[:12]


def _backup_from_html_editor(module, expected_blog_id: str, output: str) -> dict:
    blog_id = str(expected_blog_id or "").strip()
    if not blog_id.isdigit():
        raise bp.SafeAutomationError("Blog ID esperado inválido no fallback do editor HTML.")
    out = Path(output).resolve()
    safe_cdp = bp.validate_cdp_url(bp.DEFAULT_CDP_URL, allow_remote=False)

    with bp.sync_playwright() as pw:
        browser, context = bp.connect_official_chrome(pw, safe_cdp)
        page = module.ensure_theme_page(context, blog_id)
        page.wait_for_timeout(900)
        actual_id = module.extract_panel_blog_id(page.url)
        if actual_id != blog_id:
            raise bp.SafeAutomationError(
                f"Blog ID divergente no fallback do editor HTML: atual={actual_id!r}, esperado={blog_id!r}."
            )

        _dismiss_dialog(page)
        responses: list = []
        page.on("response", lambda response: responses.append(response))
        item = _editor_menu_item(module, page)
        try:
            item.click(timeout=5_000)
        except Exception:
            _physical_click(page, item)
        page.wait_for_timeout(4_000)

        for frame in page.frames:
            for text in _theme_candidates_from_frame(frame):
                try:
                    validation = module._write_validated_bytes(
                        text.encode("utf-8"), out, "blogger-html-editor-dom",
                        editor_url=bp.sanitize_url(page.url),
                    )
                    return {
                        "status": "BLOGGER_THEME_BACKUP_VALIDATED",
                        "blog_id": blog_id,
                        "output": str(out),
                        "bytes": out.stat().st_size,
                        "auto_route": bp.sanitize_url(page.url),
                        "browser_connected": browser.is_connected(),
                        **validation,
                    }
                except bp.SafeAutomationError:
                    continue

        for text, source_url in _theme_candidates_from_responses(responses):
            try:
                validation = module._write_validated_bytes(
                    text.encode("utf-8"), out, "blogger-html-editor-network",
                    editor_url=bp.sanitize_url(page.url), response_url=source_url[:500],
                )
                return {
                    "status": "BLOGGER_THEME_BACKUP_VALIDATED",
                    "blog_id": blog_id,
                    "output": str(out),
                    "bytes": out.stat().st_size,
                    "auto_route": bp.sanitize_url(page.url),
                    "browser_connected": browser.is_connected(),
                    **validation,
                }
            except bp.SafeAutomationError:
                continue

        raise bp.SafeAutomationError(
            "O editor HTML abriu, mas nenhum conteúdo completo de tema Blogger passou na validação estrutural."
        )


def _is_capture_failure(message: str) -> bool:
    low = message.lower()
    return (
        "nenhum download novo e válido" in low
        or "nenhum xml válido" in low
        or "fallback físico do backup" in low
    )


def _install_backup_resilience(module) -> None:
    original = module.execute_backup

    def wrapped(expected_blog_id: str, output: str):
        try:
            return original(expected_blog_id, output)
        except bp.SafeAutomationError as first:
            if not _is_capture_failure(str(first)):
                raise
            try:
                return _backup_with_physical_click(module, expected_blog_id, output)
            except bp.SafeAutomationError as second:
                if not _is_capture_failure(str(second)):
                    raise
                return _backup_from_html_editor(module, expected_blog_id, output)

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
