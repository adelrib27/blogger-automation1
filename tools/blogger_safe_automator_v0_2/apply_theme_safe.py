#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

import browser_provision as bp
from blogger_panel_route_guard import extract_panel_blog_id
from inspect_theme_restore_dialog import (
    THEMES_ROUTE_RE,
    _restore_card_is_open,
    inspect_restore_dom,
    open_restore_dialog,
    select_expected_theme_page,
    validate_blog_id,
    validate_restore_evidence,
    validate_xml_file,
)
from playwright.sync_api import sync_playwright

CONFIRM_PHRASE = "APPLY THEME"
UPLOAD_LABELS = ("FAZER UPLOAD", "UPLOAD")
EXPECTED_UPLOAD_MIME = "text/xml"


def _norm(value: str | None) -> str:
    return " ".join((value or "").split()).casefold()


def _validate_confirmation(value: str) -> None:
    if (value or "").strip() != CONFIRM_PHRASE:
        raise bp.SafeAutomationError(f'Confirmação inválida. Use exatamente: {CONFIRM_PHRASE}')


def _validate_public_url(value: str) -> str:
    raw = (value or "").strip()
    parsed = urlparse(raw)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or not host.endswith(".blogspot.com"):
        raise bp.SafeAutomationError("URL pública precisa ser HTTPS em domínio blogspot.com.")
    return raw.rstrip("/") + "/"


def _visible_action(page, labels: tuple[str, ...]):
    targets = {_norm(x) for x in labels}
    matches = []
    controls = page.locator('button,[role="button"]')
    for index in range(min(controls.count(), 120)):
        item = controls.nth(index)
        try:
            if not item.is_visible():
                continue
            text = _norm(item.inner_text(timeout=500))
            aria = _norm(item.get_attribute("aria-label"))
            if text in targets or aria in targets:
                matches.append(item)
        except Exception:
            continue
    if len(matches) != 1:
        raise bp.SafeAutomationError(
            f"Ação de upload ambígua/ausente: esperado 1 controle visível, encontrado(s) {len(matches)}."
        )
    return matches[0]


def _clear_stale_file_inputs(page) -> int:
    locator = page.locator('input[type="file"]')
    cleared = 0
    for index in range(locator.count()):
        item = locator.nth(index)
        try:
            selected = int(item.evaluate("el => el.files ? el.files.length : 0"))
        except Exception:
            continue
        if selected:
            item.set_input_files([])
            cleared += 1
    return cleared


def _prepare_restore_dialog(page) -> tuple[dict, int]:
    navigation = open_restore_dialog(page)
    dom = inspect_restore_dom(page)
    validate_restore_evidence(dom)
    cleared = _clear_stale_file_inputs(page)
    dom = inspect_restore_dom(page)
    validate_restore_evidence(dom)
    if any(item.get("files_selected", 0) for item in dom.get("file_inputs", [])):
        raise bp.SafeAutomationError("Persistiu seleção antiga de arquivo no diálogo Restaurar.")
    return navigation, cleared


def _select_theme(page, theme_path: Path) -> dict:
    payload = {
        "name": theme_path.name,
        "mimeType": EXPECTED_UPLOAD_MIME,
        "buffer": theme_path.read_bytes(),
    }
    upload = _visible_action(page, UPLOAD_LABELS)
    try:
        with page.expect_file_chooser(timeout=8_000) as chooser_info:
            upload.click(timeout=5_000)
        chooser = chooser_info.value
        chooser.set_files(payload)
        evidence = chooser.element.evaluate(
            """el => ({
              count: el.files ? el.files.length : 0,
              name: el.files && el.files[0] ? el.files[0].name : '',
              size: el.files && el.files[0] ? el.files[0].size : -1,
              type: el.files && el.files[0] ? el.files[0].type : ''
            })"""
        )
    except Exception as exc:
        raise bp.SafeAutomationError(f"Falha ao selecionar theme.xml no file chooser: {exc}") from exc

    expected_size = theme_path.stat().st_size
    if evidence.get("count") != 1:
        raise bp.SafeAutomationError(f"Seleção do tema não confirmada: {evidence}")
    if evidence.get("name") != theme_path.name:
        raise bp.SafeAutomationError(f"Arquivo selecionado diverge de {theme_path.name!r}: {evidence}")
    if int(evidence.get("size", -1)) != expected_size:
        raise bp.SafeAutomationError(f"Tamanho do arquivo selecionado diverge: {evidence}")
    if evidence.get("type") not in {EXPECTED_UPLOAD_MIME, "application/xml", "text/plain", ""}:
        raise bp.SafeAutomationError(f"MIME inesperado para theme.xml: {evidence}")
    return {"selection_verified": True, **evidence}


def _wait_restore_close(page, timeout_ms: int = 30_000) -> None:
    deadline = time.monotonic() + timeout_ms / 1000
    while time.monotonic() < deadline:
        if not _restore_card_is_open(page):
            return
        page.wait_for_timeout(250)
    raise bp.SafeAutomationError("O diálogo Restaurar não fechou após o upload do tema.")


def _public_probe(public_url: str, marker: str, timeout_seconds: int = 75) -> dict:
    marker = (marker or "").strip()
    if not marker:
        raise bp.SafeAutomationError("Marcador público obrigatório ficou vazio.")
    deadline = time.monotonic() + timeout_seconds
    last = ""
    while time.monotonic() < deadline:
        try:
            target = public_url + ("&" if "?" in public_url else "?") + f"theme_probe={int(time.time())}"
            req = urllib.request.Request(
                target,
                headers={"User-Agent": "Mozilla/5.0 BloggerThemeSafeValidator/2.0", "Cache-Control": "no-cache"},
            )
            with urllib.request.urlopen(req, timeout=20) as response:
                status = int(getattr(response, "status", 200))
                body = response.read().decode("utf-8", errors="replace")
            if status == 200 and marker in body:
                return {"validated": True, "http_status": status, "public_marker": marker}
            last = f"status={status}; marker_present={marker in body}"
        except Exception as exc:
            last = str(exc)[:500]
        time.sleep(2)
    raise bp.SafeAutomationError(
        "Tema foi enviado, mas o marcador público não apareceu dentro do prazo. Última observação: " + last
    )


def execute_apply(
    expected_blog_id: str,
    theme_path: str,
    backup_path: str,
    public_url: str,
    public_marker: str,
    *,
    confirm: str,
) -> dict:
    blog_id = validate_blog_id(expected_blog_id)
    _validate_confirmation(confirm)
    public_url = _validate_public_url(public_url)
    theme = validate_xml_file(theme_path, label="Tema")
    backup = validate_xml_file(backup_path, label="Backup do tema atual")
    theme_file = Path(theme["path"]).resolve()
    if theme_file.name.lower() != "theme.xml":
        raise bp.SafeAutomationError("Arquivo de tema precisa se chamar literalmente theme.xml.")

    safe_cdp = bp.validate_cdp_url(bp.DEFAULT_CDP_URL, allow_remote=False)
    with sync_playwright() as pw:
        browser, context = bp.connect_official_chrome(pw, safe_cdp)
        page = select_expected_theme_page(context, blog_id)
        actual = extract_panel_blog_id(page.url)
        match = THEMES_ROUTE_RE.search(page.url or "")
        if actual != blog_id or not match or match.group(1) != blog_id:
            raise bp.SafeAutomationError(
                f"Blog errado/rota Tema inválida bloqueada: atual={actual!r}, esperado={blog_id!r}."
            )
        navigation, cleared = _prepare_restore_dialog(page)
        selection = _select_theme(page, theme_file)
        _wait_restore_close(page)
        page.wait_for_timeout(900)
        if extract_panel_blog_id(page.url) != blog_id:
            raise bp.SafeAutomationError("Blog ID mudou após o upload; operação bloqueada.")
        connected = browser.is_connected()

    public_validation = _public_probe(public_url, public_marker)
    return {
        "status": "BLOGGER_THEME_APPLIED_AND_PUBLICLY_VALIDATED",
        "blog_id": blog_id,
        "theme": theme,
        "backup": backup,
        "navigation": navigation,
        "stale_inputs_cleared": cleared,
        "selection": selection,
        "public_validation": public_validation,
        "browser_connected": connected,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Aplica theme.xml com guardas de Blog ID, backup prévio e validação pública.")
    parser.add_argument("--expected-blog-id", required=True)
    parser.add_argument("--theme-path", required=True)
    parser.add_argument("--backup-path", required=True)
    parser.add_argument("--public-url", required=True)
    parser.add_argument("--public-marker", required=True)
    parser.add_argument("--confirm", required=True)
    args = parser.parse_args()
    result = execute_apply(
        args.expected_blog_id,
        args.theme_path,
        args.backup_path,
        args.public_url,
        args.public_marker,
        confirm=args.confirm,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
