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
LAB_PUBLIC_URL = "https://teste-tema-editorial-blogger.blogspot.com/"
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


def validate_lab_target(blog_id: str, public_url: str) -> None:
    if blog_id != LAB_BLOG_ID:
        raise bp.SafeAutomationError(
            f"Tema Mestre v1.0 permanece LAB_ONLY. Blog permitido: {LAB_BLOG_ID}."
        )
    if (public_url or "").strip() != LAB_PUBLIC_URL:
        raise bp.SafeAutomationError(
            f"URL pública bloqueada. Para o laboratório use exatamente: {LAB_PUBLIC_URL}"
        )


def _normalize_action_text(value: str | None) -> str:
    return " ".join((value or "").split()).casefold()


def _exact_visible_action_by_text(page, expected_text: str):
    """Find one visible button/role=button by its rendered text or aria-label.

    Blogger's Restore dialog exposes FAZER UPLOAD in the visible DOM, but the
    Playwright accessibility-role lookup does not currently surface it. The
    same DOM contract is already used by inspect_restore_dom().
    """
    target = _normalize_action_text(expected_text)
    locator = page.locator('button,[role="button"]')
    matches = []
    observed = []

    for index in range(locator.count()):
        item = locator.nth(index)
        try:
            if not item.is_visible():
                continue
            text = _normalize_action_text(item.inner_text())
            aria = _normalize_action_text(item.get_attribute("aria-label"))
            if text or aria:
                observed.append({"text": text, "aria": aria})
            if text == target or aria == target:
                matches.append(item)
        except Exception:
            continue

    if len(matches) != 1:
        raise bp.SafeAutomationError(
            f"Ação {expected_text!r} ambígua ou ausente: esperado 1 elemento visível, "
            f"encontrado(s) {len(matches)}. Ações visíveis observadas: {observed}."
        )
    return matches[0]


def _clear_stale_file_inputs(page) -> int:
    """Clear only browser-local stale file selections from earlier failed attempts."""
    locator = page.locator('input[type="file"]')
    cleared = 0
    for index in range(locator.count()):
        item = locator.nth(index)
        try:
            selected = item.evaluate("el => el.files ? el.files.length : 0")
        except Exception:
            continue
        if selected:
            try:
                item.set_input_files([])
                cleared += 1
            except Exception as exc:
                raise bp.SafeAutomationError(
                    f"Não foi possível limpar seleção local antiga do input de arquivo: {exc}"
                ) from exc
    return cleared


def _select_theme_file_via_native_chooser(page, theme_path: str) -> str:
    """Follow the exact Blogger UI contract: FAZER UPLOAD -> native chooser -> XML."""
    upload = _exact_visible_action_by_text(page, UPLOAD_LABEL)
    try:
        with page.expect_file_chooser(timeout=5_000) as chooser_info:
            upload.click(timeout=5_000)
        chooser = chooser_info.value
        chooser.set_files(theme_path)
        return "native_file_chooser"
    except Exception as exc:
        raise bp.SafeAutomationError(
            f"Não foi possível selecionar o Tema Mestre pelo fluxo nativo FAZER UPLOAD: {exc}"
        ) from exc


def _wait_restore_dialog_close(page, timeout_ms: int = 30_000) -> None:
    deadline = time.monotonic() + timeout_ms / 1000
    while time.monotonic() < deadline:
        if not _restore_card_is_open(page):
            return
        page.wait_for_timeout(250)
    evidence = (inspect_restore_dom(page).get("restore_evidence") or {})
    raise bp.SafeAutomationError(
        "O arquivo foi escolhido pelo seletor nativo, mas o cartão Restaurar não fechou no prazo esperado. "
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


def _wait_public_markers(public_url: str, timeout_seconds: int = 60) -> dict:
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


def _prepare_restore_dialog(page) -> tuple[dict, dict, int]:
    """Open Restore, validate it, and clear browser-local stale file state without cancelling."""
    navigation = open_restore_dialog(page)
    dom = inspect_restore_dom(page)
    validate_restore_evidence(dom)

    cleared = _clear_stale_file_inputs(page)
    dom = inspect_restore_dom(page)
    validate_restore_evidence(dom)

    if any(item.get("files_selected", 0) for item in dom.get("file_inputs", [])):
        raise bp.SafeAutomationError(
            "Persistiu seleção local de arquivo mesmo após limpeza; upload bloqueado."
        )

    return navigation, dom, cleared


def execute_apply(
    expected_blog_id: str,
    theme_path: str,
    backup_path: str,
    public_url: str,
    confirm: str,
) -> dict:
    expected_blog_id = validate_blog_id(expected_blog_id)
    validate_lab_target(expected_blog_id, public_url)
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

        navigation, _, stale_inputs_cleared = _prepare_restore_dialog(page)

        selection_method = _select_theme_file_via_native_chooser(page, theme["path"])
        _wait_restore_dialog_close(page)

        if extract_panel_blog_id(page.url) != expected_blog_id:
            raise bp.SafeAutomationError("Blog ID mudou após o upload; validação bloqueada.")

        public_validation = _wait_public_markers(public_url)

        return {
            "status": "MASTER_THEME_V1_APPLIED_AND_PUBLICLY_VALIDATED",
            "blog_id": expected_blog_id,
            "theme": theme,
            "backup": backup,
            "navigation": navigation,
            "stale_inputs_cleared": stale_inputs_cleared,
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
