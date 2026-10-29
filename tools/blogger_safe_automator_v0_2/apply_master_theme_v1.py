#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
import urllib.request
from pathlib import Path

import browser_provision as bp
from blogger_panel_route_guard import extract_panel_blog_id
from inspect_theme_restore_dialog import (
    THEMES_ROUTE_RE,
    _exactly_one_visible,
    _restore_card_is_open,
    inspect_restore_dom,
    open_restore_dialog,
    select_expected_theme_page,
    validate_blog_id,
    validate_restore_evidence,
    validate_xml_file,
)
from playwright.sync_api import sync_playwright

LAB_BLOG_ID = "99449222854490000"
CONFIRM_PHRASE = "APPLY MASTER THEME"
UPLOAD_LABEL = "FAZER UPLOAD"
PUBLIC_MARKERS = (
    "Conteúdo editorial independente com foco em informação útil e decisões de compra.",
    "tm-topbar",
    "tm-brand",
)


def validate_confirmation(value: str) -> None:
    if (value or "").strip() != CONFIRM_PHRASE:
        raise bp.SafeAutomationError(
            f"Confirmação inválida. Use exatamente: {CONFIRM_PHRASE}"
        )


def validate_lab_target(blog_id: str) -> None:
    if blog_id != LAB_BLOG_ID:
        raise bp.SafeAutomationError(
            f"Tema Mestre v1.0 permanece LAB_ONLY. Blog permitido: {LAB_BLOG_ID}."
        )


def _enabled_file_inputs(page):
    locator = page.locator('input[type="file"]')
    items = []
    for index in range(locator.count()):
        item = locator.nth(index)
        try:
            if not item.is_disabled():
                items.append(item)
        except Exception:
            continue
    return items


def _select_theme_file(page, theme_path: str) -> str:
    inputs = _enabled_file_inputs(page)
    if len(inputs) == 1:
        inputs[0].set_input_files(theme_path)
        return "direct_file_input"
    if len(inputs) > 1:
        raise bp.SafeAutomationError(
            f"Upload bloqueado: encontrados {len(inputs)} inputs de arquivo habilitados."
        )

    upload = _exactly_one_visible(
        page.get_by_role("button", name=UPLOAD_LABEL, exact=True),
        "Botão FAZER UPLOAD",
    )
    try:
        with page.expect_file_chooser(timeout=5_000) as chooser_info:
            upload.click(timeout=5_000)
        chooser_info.value.set_files(theme_path)
        return "file_chooser"
    except Exception as exc:
        raise bp.SafeAutomationError(
            f"Não foi possível selecionar o arquivo do Tema Mestre com segurança: {exc}"
        ) from exc


def _wait_restore_dialog_close(page, timeout_ms: int = 20_000) -> None:
    deadline = time.monotonic() + timeout_ms / 1000
    while time.monotonic() < deadline:
        if not _restore_card_is_open(page):
            return
        page.wait_for_timeout(250)
    evidence = (inspect_restore_dom(page).get("restore_evidence") or {})
    raise bp.SafeAutomationError(
        "O upload foi iniciado, mas o cartão Restaurar não fechou no prazo esperado. "
        f"Evidências finais: {evidence}."
    )


def _fetch_public_html(public_url: str, timeout: float = 15.0) -> str:
    request = urllib.request.Request(
        public_url,
        headers={"User-Agent": "Mozilla/5.0 BloggerMasterThemeValidator/1.0"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        if int(getattr(response, "status", 200)) != 200:
            raise bp.SafeAutomationError(
                f"URL pública retornou HTTP {getattr(response, 'status', 'desconhecido')}."
            )
        return response.read().decode("utf-8", errors="replace")


def _wait_public_markers(public_url: str, timeout_seconds: int = 45) -> dict:
    deadline = time.monotonic() + timeout_seconds
    last_error = ""
    while time.monotonic() < deadline:
        try:
            html = _fetch_public_html(public_url)
            found = {marker: (marker in html) for marker in PUBLIC_MARKERS}
            if all(found.values()):
                return {
                    "public_url": public_url,
                    "http_ok": True,
                    "markers": found,
                    "validated": True,
                }
            last_error = f"marcadores={found}"
        except Exception as exc:
            last_error = str(exc)
        time.sleep(1.5)
    raise bp.SafeAutomationError(
        "Tema não pôde ser validado no HTML público dentro do prazo. "
        f"Última observação: {last_error}"
    )


def execute_apply(
    expected_blog_id: str,
    theme_path: str,
    backup_path: str,
    public_url: str,
    confirm: str,
) -> dict:
    expected_blog_id = validate_blog_id(expected_blog_id)
    validate_lab_target(expected_blog_id)
    validate_confirmation(confirm)

    theme = validate_xml_file(theme_path, label="Tema Mestre")
    backup = validate_xml_file(backup_path, label="Backup do tema atual")
    theme_file = Path(theme["path"])
    if theme_file.name.lower() != "theme.xml":
        raise bp.SafeAutomationError("Arquivo esperado do Tema Mestre deve se chamar theme.xml.")

    safe_cdp = bp.validate_cdp_url(bp.DEFAULT_CDP_URL, allow_remote=False)

    with sync_playwright() as p:
        browser, context = bp.connect_official_chrome(p, safe_cdp)
        page = select_expected_theme_page(context, expected_blog_id)
        current_blog_id = extract_panel_blog_id(page.url)
        if current_blog_id != expected_blog_id:
            raise bp.SafeAutomationError(
                f"Blog errado bloqueado: atual={current_blog_id!r}, esperado={expected_blog_id!r}."
            )
        match = THEMES_ROUTE_RE.search(page.url or "")
        if not match or match.group(1) != expected_blog_id:
            raise bp.SafeAutomationError("A aba ativa precisa ser Tema do blog-laboratório.")

        navigation = open_restore_dialog(page)
        dom = inspect_restore_dom(page)
        validate_restore_evidence(dom)
        if any(item.get("files_selected", 0) for item in dom.get("file_inputs", [])):
            raise bp.SafeAutomationError("Já existe arquivo selecionado; aplicação bloqueada.")

        selection_method = _select_theme_file(page, theme["path"])
        _wait_restore_dialog_close(page)

        # Revalidate the target after the write-triggering file selection.
        if extract_panel_blog_id(page.url) != expected_blog_id:
            raise bp.SafeAutomationError("Blog ID mudou após o upload; validação bloqueada.")

        public_validation = _wait_public_markers(public_url)

        return {
            "status": "MASTER_THEME_V1_APPLIED_AND_PUBLICLY_VALIDATED",
            "blog_id": expected_blog_id,
            "theme": theme,
            "backup": backup,
            "navigation": navigation,
            "selection_method": selection_method,
            "public_validation": public_validation,
            "browser_connected": browser.is_connected(),
            "message": "Tema Mestre v1.0 aplicado no blog-laboratório e validado no HTML público.",
        }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Aplica o Tema Mestre Blogger v1.0 no blog-laboratório.")
    parser.add_argument("--expected-blog-id", required=True)
    parser.add_argument("--theme-path", required=True)
    parser.add_argument("--backup-path", required=True)
    parser.add_argument("--public-url", required=True)
    parser.add_argument("--confirm", required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = execute_apply(
        args.expected_blog_id,
        args.theme_path,
        args.backup_path,
        args.public_url,
        args.confirm,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
