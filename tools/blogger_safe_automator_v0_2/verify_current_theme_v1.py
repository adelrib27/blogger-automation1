#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import browser_provision as bp
from inspect_theme_restore_dialog import (
    _active_aria_label,
    _exactly_one_visible,
    _open_theme_actions_menu,
    _restore_card_is_open,
    close_restore_dialog,
    select_expected_theme_page,
    validate_blog_id,
    validate_xml_file,
)
from playwright.sync_api import sync_playwright

LAB_BLOG_ID = "99449222854490000"
BACKUP_LABEL = "Fazer backup do tema atual"
DOWNLOAD_LABEL = "FAZER DOWNLOAD"
MASTER_MARKERS = (
    "Tema Mestre Blogger v1.0",
    "tm-topbar",
    "tm-brand",
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def _visible_exact_text_controls(page, text: str):
    locator = page.locator('button,[role="button"]')
    matches = []
    wanted = text.strip()
    for index in range(locator.count()):
        item = locator.nth(index)
        try:
            if not item.is_visible():
                continue
            actual = (item.inner_text() or "").strip()
            if actual == wanted:
                matches.append(item)
        except Exception:
            continue
    return matches


def _download_current_theme(page) -> bytes:
    if _restore_card_is_open(page):
        close_restore_dialog(page)

    _open_theme_actions_menu(page)
    page.wait_for_timeout(250)

    active = _active_aria_label(page)
    if active != BACKUP_LABEL:
        backup = _exactly_one_visible(
            page.get_by_role("menuitem", name=BACKUP_LABEL, exact=True),
            "Menuitem Backup do tema atual",
        )
        backup.focus()
        active = _active_aria_label(page)

    if active != BACKUP_LABEL:
        raise bp.SafeAutomationError(
            f"Backup não recebeu foco com segurança. Foco atual: {active!r}."
        )

    # Enter opens the Backup dialog; it does not start the download.
    page.keyboard.press("Enter")
    page.wait_for_timeout(400)

    download_controls = _visible_exact_text_controls(page, DOWNLOAD_LABEL)
    if len(download_controls) != 1:
        raise bp.SafeAutomationError(
            f"Botão {DOWNLOAD_LABEL} ambíguo ou ausente: esperado 1 visível, encontrado(s) {len(download_controls)}."
        )

    try:
        with page.expect_download(timeout=15_000) as info:
            download_controls[0].click(timeout=5_000)
        download = info.value
        path = download.path()
        if not path:
            raise bp.SafeAutomationError("O Blogger iniciou o backup, mas não forneceu arquivo temporário.")
        data = Path(path).read_bytes()
    except Exception as exc:
        raise bp.SafeAutomationError(f"Falha ao baixar o tema atual para verificação: {exc}") from exc

    if not data:
        raise bp.SafeAutomationError("Backup atual do tema veio vazio.")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description="Verifica em modo leitura se o Tema Mestre v1 está aplicado.")
    parser.add_argument("--expected-blog-id", required=True)
    parser.add_argument("--master-theme-path", required=True)
    parser.add_argument("--old-backup-path", required=True)
    args = parser.parse_args()

    blog_id = validate_blog_id(args.expected_blog_id)
    if blog_id != LAB_BLOG_ID:
        raise bp.SafeAutomationError(f"Verificação LAB_ONLY. Blog permitido: {LAB_BLOG_ID}.")

    master = validate_xml_file(args.master_theme_path, label="Tema Mestre")
    old_backup = validate_xml_file(args.old_backup_path, label="Backup anterior")
    safe_cdp = bp.validate_cdp_url(bp.DEFAULT_CDP_URL, allow_remote=False)

    with sync_playwright() as p:
        browser, context = bp.connect_official_chrome(p, safe_cdp)
        page = select_expected_theme_page(context, blog_id)
        current_bytes = _download_current_theme(page)
        connected = browser.is_connected()

    current_text = current_bytes.decode("utf-8", errors="replace")
    current_sha = sha256_bytes(current_bytes)
    markers = {marker: (marker in current_text) for marker in MASTER_MARKERS}

    if all(markers.values()):
        state = "MASTER_THEME_V1_PRESENT_IN_CURRENT_BACKUP"
    elif current_sha == old_backup["sha256"]:
        state = "OLD_THEME_STILL_ACTIVE_EXACT_HASH"
    elif current_sha == master["sha256"]:
        state = "MASTER_THEME_V1_EXACT_HASH"
    else:
        state = "CURRENT_THEME_DIFFERS_FROM_BOTH"

    result = {
        "status": "CURRENT_THEME_VERIFIED_READ_ONLY",
        "read_only": True,
        "blog_id": blog_id,
        "state": state,
        "current_theme": {
            "size_bytes": len(current_bytes),
            "sha256": current_sha,
            "master_markers": markers,
        },
        "master_theme": master,
        "old_backup": old_backup,
        "browser_connected": connected,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
