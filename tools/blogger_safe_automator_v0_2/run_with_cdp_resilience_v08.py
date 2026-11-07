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
THEME_RE = re.compile(r"<b:(skin|section|widget|template-skin)")


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


def _first_visible(locator):
    try:
        count = min(locator.count(), 50)
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


def _physical_click(page, locator) -> None:
    try:
        locator.scroll_into_view_if_needed(timeout=3_000)
    except Exception:
        pass
    box = locator.bounding_box()
    if not box:
        raise bp.SafeAutomationError("Controle do Blogger ficou visível, mas sem caixa física clicável.")
    page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)


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
    if item is not None:
        return item
    text_item = _first_visible(page.get_by_text(EDIT_HTML_RE, exact=True))
    if text_item is None:
        raise bp.SafeAutomationError("Opção 'Editar HTML' não foi localizada no menu Tema.")
    try:
        ancestor = text_item.locator("xpath=ancestor::*[@role='menuitem' or @role='button' or self::button][1]")
        clickable = _first_visible(ancestor)
        if clickable is not None:
            return clickable
    except Exception:
        pass
    return text_item


def _looks_like_theme(text: str) -> bool:
    return len(text) >= 1000 and "<html" in text and bool(THEME_RE.search(text))


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
                try { if (el.CodeMirror && typeof el.CodeMirror.getValue === 'function') add(el.CodeMirror.getValue()); } catch (_) {}
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
              for (const el of document.querySelectorAll('.cm-content,[contenteditable="true"],.CodeMirror-code,pre,code')) {
                add(el.innerText || el.textContent || '');
              }
              const lines = [...document.querySelectorAll('.cm-line')].map(el => el.textContent || '').join('\n');
              add(lines);
              return [...new Set(out)].sort((a,b) => b.length - a.length).slice(0, 12);
            }"""
        )
        return [str(v) for v in (values or []) if _looks_like_theme(str(v))]
    except Exception:
        return []


def _walk_strings(value, out: list[str]) -> None:
    if isinstance(value, str):
        if _looks_like_theme(value):
            out.append(value)
        return
    if isinstance(value, dict):
        for v in value.values():
            _walk_strings(v, out)
    elif isinstance(value, list):
        for v in value:
            _walk_strings(v, out)


def _json_payloads(text: str) -> list[object]:
    payloads: list[object] = []
    candidates = [text]
    stripped = text.lstrip()
    if stripped.startswith(")]}'"):
        parts = stripped.split("\n", 1)
        if len(parts) == 2:
            candidates.append(parts[1])
    for candidate in candidates:
        try:
            payloads.append(json.loads(candidate))
        except Exception:
            pass
    return payloads


def _decode_embedded_strings(text: str) -> list[str]:
    found: list[str] = []
    if _looks_like_theme(text):
        found.append(text)
    for payload in _json_payloads(text):
        _walk_strings(payload, found)
    if "\\u003c" in text or "\\x3c" in text or "\\n" in text:
        try:
            decoded = bytes(text, "utf-8").decode("unicode_escape")
            if _looks_like_theme(decoded):
                found.append(decoded)
        except Exception:
            pass
    return found


def _theme_candidates_from_responses(responses: list) -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    for response in reversed(responses[-240:]):
        try:
            status = int(response.status)
            if status < 200 or status >= 400:
                continue
            url = str(response.url or "")
            low_url = url.lower()
            if "blogger" not in low_url and "google" not in low_url:
                continue
            body = response.body()
            if not body or len(body) > 12_000_000:
                continue
            text = body.decode("utf-8", errors="replace")
            for candidate in _decode_embedded_strings(text):
                found.append((candidate, url))
        except Exception:
            continue
    dedup: dict[str, tuple[str, str]] = {}
    for text, url in found:
        dedup[text[:5000]] = (text, url)
    result = list(dedup.values())
    result.sort(key=lambda item: len(item[0]), reverse=True)
    return result[:16]


def _editor_diagnostics(page) -> str:
    try:
        return str(page.evaluate(
            r"""() => JSON.stringify({
              url: location.href,
              textareas: document.querySelectorAll('textarea').length,
              codeMirror: document.querySelectorAll('.CodeMirror').length,
              cmEditor: document.querySelectorAll('.cm-editor').length,
              cmContent: document.querySelectorAll('.cm-content').length,
              contenteditable: document.querySelectorAll('[contenteditable="true"]').length,
              ace: document.querySelectorAll('.ace_editor').length,
              pre: document.querySelectorAll('pre').length,
              bodyText: (document.body?.innerText || '').slice(0, 500)
            })"""
        ))[:1400]
    except Exception:
        return "diagnóstico indisponível"


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
        _physical_click(page, item)

        deadline = time.time() + 12
        editor_open = False
        while time.time() < deadline:
            page.wait_for_timeout(500)
            try:
                editor_open = bool(page.evaluate(
                    r"""() => !!(
                      document.querySelector('textarea,.CodeMirror,.cm-editor,.cm-content,[contenteditable="true"],.ace_editor')
                      || /Editar HTML|Edit HTML/i.test(document.title)
                      || /html/i.test(location.pathname.split('/').pop() || '')
                    )"""
                ))
            except Exception:
                editor_open = False
            if editor_open:
                break
        page.wait_for_timeout(2_000)

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
            "Editar HTML foi acionado, mas o tema completo não ficou acessível para backup validado. "
            + f"editor_open={editor_open}; " + _editor_diagnostics(page)
        )


def _is_capture_failure(message: str) -> bool:
    low = message.lower()
    return (
        "nenhum download novo e válido" in low
        or "nenhum xml válido" in low
        or "fallback físico do backup" in low
        or "nenhum conteúdo completo de tema blogger" in low
        or "tema completo não ficou acessível" in low
    )


def _install_backup_resilience(module) -> None:
    original = module.execute_backup

    def wrapped(expected_blog_id: str, output: str):
        try:
            return original(expected_blog_id, output)
        except bp.SafeAutomationError as exc:
            if not _is_capture_failure(str(exc)):
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
