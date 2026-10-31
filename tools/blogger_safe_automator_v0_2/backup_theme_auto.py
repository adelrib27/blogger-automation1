#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import browser_provision as bp
from auto_blog_route import ensure_theme_page
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError, sync_playwright

BACKUP_LABEL_RE = re.compile(r"^(Fazer backup|Backup|Back up)$", re.I)
DOWNLOAD_LABEL_RE = re.compile(r"^(Fazer download|Download|Baixar|Download theme|Baixar tema)$", re.I)


def _first_visible(locator):
    try:
        count = min(locator.count(), 30)
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


def _open_actions(page) -> None:
    # Se o item de backup já estiver visível, o menu já está aberto.
    if _first_visible(page.get_by_role("menuitem", name=BACKUP_LABEL_RE)) is not None:
        return
    if _first_visible(page.get_by_text(BACKUP_LABEL_RE, exact=True)) is not None:
        return

    more = _first_visible(page.locator('[role="button"][aria-label="Mais ações"]'))
    if more is None:
        more = _first_visible(page.locator('[role="button"][aria-label="More actions"]'))
    if more is None:
        raise bp.SafeAutomationError("Controle 'Mais ações' do tema não foi localizado com segurança.")
    try:
        more.click(timeout=5_000)
    except Exception:
        more.evaluate("el => el.click()")
    page.wait_for_timeout(350)


def _backup_item(page):
    item = _first_visible(page.get_by_role("menuitem", name=BACKUP_LABEL_RE))
    if item is not None:
        return item
    item = _first_visible(page.get_by_text(BACKUP_LABEL_RE, exact=True))
    if item is not None:
        return item
    raise bp.SafeAutomationError("Opção 'Fazer backup' não foi localizada no menu Tema.")


def _download_button(page):
    for locator in (
        page.get_by_role("button", name=DOWNLOAD_LABEL_RE),
        page.get_by_text(DOWNLOAD_LABEL_RE, exact=True),
    ):
        item = _first_visible(locator)
        if item is not None:
            return item
    return None


def _save_download(download, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    tmp = output.with_suffix(output.suffix + ".downloading")
    download.save_as(str(tmp))
    if not tmp.exists() or tmp.stat().st_size < 128:
        raise bp.SafeAutomationError("Backup do tema foi baixado vazio ou incompleto.")
    try:
        ET.parse(tmp)
    except Exception as exc:
        try:
            tmp.unlink(missing_ok=True)
        except Exception:
            pass
        raise bp.SafeAutomationError("Backup baixado não é um XML válido do tema Blogger.") from exc
    tmp.replace(output)


def execute_backup(expected_blog_id: str, output: str) -> dict:
    blog_id = str(expected_blog_id or "").strip()
    if not blog_id.isdigit():
        raise bp.SafeAutomationError("Blog ID esperado inválido.")
    out = Path(output).resolve()
    safe_cdp = bp.validate_cdp_url(bp.DEFAULT_CDP_URL, allow_remote=False)

    with sync_playwright() as pw:
        browser, context = bp.connect_official_chrome(pw, safe_cdp)
        page = ensure_theme_page(context, blog_id)
        page.wait_for_timeout(900)
        route = bp.sanitize_url(page.url)
        if bp.extract_current_blog_id(page) != blog_id:
            raise bp.SafeAutomationError("Blog ID divergente antes do backup do tema.")

        _open_actions(page)
        item = _backup_item(page)
        download = None
        try:
            with page.expect_download(timeout=5_000) as info:
                try:
                    item.click(timeout=5_000)
                except Exception:
                    item.evaluate("el => el.click()")
            download = info.value
        except PlaywrightTimeoutError:
            # Algumas versões do Blogger abrem um diálogo intermediário.
            page.wait_for_timeout(500)
            button = _download_button(page)
            if button is None:
                raise bp.SafeAutomationError(
                    "A opção Fazer backup foi acionada, mas nenhum download ou botão de download apareceu."
                )
            with page.expect_download(timeout=15_000) as info:
                try:
                    button.click(timeout=5_000)
                except Exception:
                    button.evaluate("el => el.click()")
            download = info.value

        _save_download(download, out)
        connected = browser.is_connected()

    return {
        "status": "BLOGGER_THEME_BACKUP_VALIDATED",
        "blog_id": blog_id,
        "output": str(out),
        "bytes": out.stat().st_size,
        "xml_valid": True,
        "auto_route": route,
        "browser_connected": connected,
    }


def main() -> int:
    p = argparse.ArgumentParser(description="Abre a rota Tema do Blog ID e cria backup XML validado pelo Chrome oficial.")
    p.add_argument("--expected-blog-id", required=True)
    p.add_argument("--output", required=True)
    args = p.parse_args()
    result = execute_backup(args.expected_blog_id, args.output)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
