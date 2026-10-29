#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import browser_provision as bp
from blogger_panel_route_guard import extract_panel_blog_id
from blogger_session_guard import is_blogger_url
from playwright.sync_api import sync_playwright

BLOG_ID_RE = re.compile(r"^[0-9]+$")
THEMES_ROUTE_RE = re.compile(r"/blog/themes/(\d+)(?:[/?#]|$)", re.I)
MORE_ACTIONS_RE = re.compile(r"^\s*Mais ações\s*$", re.I)
RESTORE_MENUITEM_RE = re.compile(r"^\s*Restaurar um tema antigo\s*$", re.I)
CANCEL_RE = re.compile(r"^\s*CANCELAR\s*$", re.I)


def validate_blog_id(value: str) -> str:
    value = (value or "").strip()
    if not BLOG_ID_RE.fullmatch(value):
        raise bp.SafeAutomationError("Blog ID esperado inválido.")
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def validate_xml_file(raw_path: str, *, label: str) -> dict:
    path = Path(raw_path).expanduser().resolve()
    if not path.is_file():
        raise bp.SafeAutomationError(f"{label} não encontrado: {path}")
    try:
        ET.parse(path)
    except ET.ParseError as exc:
        raise bp.SafeAutomationError(f"{label} não é XML válido: {exc}") from exc
    size = path.stat().st_size
    if size <= 0:
        raise bp.SafeAutomationError(f"{label} está vazio.")
    return {
        "path": str(path),
        "size_bytes": size,
        "sha256": sha256_file(path),
        "xml_valid": True,
    }


def _page_visibility(page) -> bool:
    try:
        return page.evaluate("() => document.visibilityState") == "visible"
    except Exception:
        return False


def _visible_items(locator):
    items = []
    try:
        count = locator.count()
    except Exception:
        return items
    for index in range(count):
        item = locator.nth(index)
        try:
            if item.is_visible():
                items.append(item)
        except Exception:
            continue
    return items


def _exactly_one_visible(locator, label: str):
    items = _visible_items(locator)
    if len(items) != 1:
        raise bp.SafeAutomationError(
            f"{label} ambíguo ou ausente: esperado 1 elemento visível, encontrado(s) {len(items)}."
        )
    return items[0]


def select_expected_theme_page(context, expected_blog_id: str):
    """Select only the Blogger Theme tab for the expected Blog ID."""
    candidates = []
    for page in context.pages:
        try:
            if not is_blogger_url(page.url):
                continue
            if extract_panel_blog_id(page.url) != expected_blog_id:
                continue
            match = THEMES_ROUTE_RE.search(page.url or "")
            if not match or match.group(1) != expected_blog_id:
                continue
            candidates.append(page)
        except Exception:
            continue

    if not candidates:
        raise bp.SafeAutomationError(
            f"Nenhuma aba Tema (/blog/themes/) do Blog ID esperado {expected_blog_id} foi encontrada."
        )

    visible = [page for page in candidates if _page_visibility(page)]
    return visible[-1] if visible else candidates[-1]


def inspect_restore_dom(page) -> dict:
    return page.evaluate(
        r"""() => {
          const norm = v => String(v || '').trim().replace(/\s+/g, ' ');
          const fold = v => norm(v).toLocaleLowerCase('pt-BR');
          const visible = el => {
            const r = el.getBoundingClientRect();
            const s = getComputedStyle(el);
            return r.width > 0 && r.height > 0 && s.display !== 'none' && s.visibility !== 'hidden';
          };

          const bodyTextFull = norm(document.body?.innerText || '');
          const bodyFold = fold(bodyTextFull);

          const dialogs = [...document.querySelectorAll('[role="dialog"]')]
            .filter(visible)
            .map(el => ({
              text: norm(el.innerText || el.textContent).slice(0, 1200),
              aria: norm(el.getAttribute('aria-label')).slice(0, 200)
            }));

          const buttons = [...document.querySelectorAll('button,[role="button"]')]
            .filter(visible)
            .map(el => ({
              text: norm(el.innerText || el.textContent).slice(0, 200),
              aria: norm(el.getAttribute('aria-label')).slice(0, 200),
              disabled: el.matches(':disabled') || el.getAttribute('aria-disabled') === 'true'
            }))
            .filter(x => x.text || x.aria);

          const actionNames = buttons.map(x => fold(x.text || x.aria || ''));

          const fileInputs = [...document.querySelectorAll('input[type="file"]')]
            .map(el => ({
              visible: visible(el),
              accept: el.getAttribute('accept') || '',
              multiple: !!el.multiple,
              disabled: !!el.disabled,
              name: el.getAttribute('name') || '',
              id: el.id || '',
              files_selected: el.files ? el.files.length : 0
            }));

          return {
            dialogs,
            buttons,
            file_inputs: fileInputs,
            restore_evidence: {
              title_visible: bodyFold.includes('restaurar'),
              explanation_visible:
                bodyFold.includes('você pode fazer o upload de um tema a partir de um arquivo no seu computador') ||
                bodyFold.includes('voce pode fazer o upload de um tema a partir de um arquivo no seu computador'),
              cancel_action_visible: actionNames.includes('cancelar'),
              upload_action_visible: actionNames.includes('fazer upload')
            },
            body_text: bodyTextFull.slice(0, 5000)
          };
        }"""
    )


def validate_restore_evidence(dom: dict) -> dict:
    evidence = dict(dom.get("restore_evidence") or {})
    required = {
        "title_visible": bool(evidence.get("title_visible")),
        "explanation_visible": bool(evidence.get("explanation_visible")),
        "cancel_action_visible": bool(evidence.get("cancel_action_visible")),
        "upload_action_visible": bool(evidence.get("upload_action_visible")),
    }
    if not all(required.values()):
        missing = [name for name, ok in required.items() if not ok]
        raise bp.SafeAutomationError(
            "O cartão Restaurar não foi confirmado por texto e ações visíveis. "
            f"Evidências ausentes: {', '.join(missing)}."
        )
    return required


def _restore_card_is_open(page) -> bool:
    try:
        validate_restore_evidence(inspect_restore_dom(page))
        return True
    except bp.SafeAutomationError:
        return False


def _restore_menuitem_visible(page):
    items = _visible_items(page.get_by_role("menuitem", name=RESTORE_MENUITEM_RE))
    if len(items) > 1:
        raise bp.SafeAutomationError(
            f"Menuitem Restaurar ambíguo: encontrado(s) {len(items)} elementos visíveis."
        )
    return items[0] if items else None


def _open_theme_actions_menu(page) -> None:
    more_actions = _exactly_one_visible(
        page.get_by_role("button", name=MORE_ACTIONS_RE),
        "Botão Mais ações do tema",
    )
    more_actions.click(timeout=5_000)
    page.wait_for_timeout(350)


def _wait_restore_card_open(page, *, attempts: int = 20, delay_ms: int = 250) -> bool:
    for _ in range(attempts):
        if _restore_card_is_open(page):
            return True
        page.wait_for_timeout(delay_ms)
    return _restore_card_is_open(page)


def open_restore_dialog(page) -> dict:
    if _restore_card_is_open(page):
        return {"menu_opened": False, "restore_clicked": False, "already_open": True}

    restore = _restore_menuitem_visible(page)
    menu_opened = False
    if restore is None:
        _open_theme_actions_menu(page)
        menu_opened = True
        restore = _restore_menuitem_visible(page)

    if restore is None:
        raise bp.SafeAutomationError(
            "Menuitem Restaurar um tema antigo não foi localizado após abrir Mais ações."
        )

    # The current Blogger menuitem is a SPAN role="menuitem" with accessible
    # name "Restaurar um tema antigo". A synthesized pointer click was observed
    # to leave the row only focused/highlighted in this UI. Invoke the element's
    # native DOM click directly, then wait for positive dialog evidence.
    restore.evaluate("el => el.click()")

    if not _wait_restore_card_open(page):
        # Cleanup only: if the menu stayed open, close it without selecting any
        # other action. No upload or theme write is attempted.
        try:
            if _restore_menuitem_visible(page) is not None:
                page.keyboard.press("Escape")
                page.wait_for_timeout(250)
        except Exception:
            pass
        evidence = (inspect_restore_dom(page).get("restore_evidence") or {})
        raise bp.SafeAutomationError(
            "O menuitem Restaurar foi acionado, mas o cartão Restaurar não abriu em até 5 segundos. "
            f"Evidências finais: {evidence}."
        )

    dom = inspect_restore_dom(page)
    validate_restore_evidence(dom)
    return {
        "menu_opened": menu_opened,
        "restore_clicked": True,
        "activation": "dom_click",
        "already_open": False,
    }


def close_restore_dialog(page) -> bool:
    if not _restore_card_is_open(page):
        return False
    cancel = _exactly_one_visible(
        page.get_by_role("button", name=CANCEL_RE),
        "Botão CANCELAR do cartão Restaurar",
    )
    cancel.click(timeout=5_000)

    # Blogger closes this Material dialog with an animation. Do not assume a
    # fixed 250 ms transition: poll the visible dialog evidence for up to 5 s.
    for _ in range(20):
        page.wait_for_timeout(250)
        if not _restore_card_is_open(page):
            return True

    evidence = (inspect_restore_dom(page).get("restore_evidence") or {})
    raise bp.SafeAutomationError(
        "O cartão Restaurar permaneceu visível após CANCELAR por mais de 5 segundos. "
        f"Evidências finais: {evidence}."
    )


def execute_inspection(expected_blog_id: str, theme_path: str, backup_path: str) -> dict:
    expected_blog_id = validate_blog_id(expected_blog_id)
    theme = validate_xml_file(theme_path, label="Tema Mestre")
    backup = validate_xml_file(backup_path, label="Backup do tema atual")
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
            raise bp.SafeAutomationError(
                "A aba correta deve estar na tela Tema (/blog/themes/<BlogID>) antes da inspeção."
            )

        navigation = open_restore_dialog(page)
        try:
            dom = inspect_restore_dom(page)
            confirmed_evidence = validate_restore_evidence(dom)

            if any(item.get("files_selected", 0) for item in dom["file_inputs"]):
                raise bp.SafeAutomationError(
                    "Já existe arquivo selecionado no diálogo. Inspeção bloqueada para preservar o estado."
                )

            result = {
                "status": "THEME_RESTORE_PREFLIGHT_OK",
                "read_only": True,
                "blog_id": expected_blog_id,
                "url": bp.sanitize_url(page.url),
                "theme": theme,
                "backup": backup,
                "navigation": navigation,
                "restore_evidence": confirmed_evidence,
                "dialog": dom,
                "browser_connected": browser.is_connected(),
                "message": (
                    "Preflight sem gravação: abriu Tema > opções > Restaurar, não selecionou arquivo, "
                    "não clicou FAZER UPLOAD e fechou com CANCELAR."
                ),
            }
        finally:
            close_restore_dialog(page)

        return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Preflight sem gravação do fluxo Tema > Restaurar do Blogger."
    )
    parser.add_argument("--expected-blog-id", required=True)
    parser.add_argument("--theme-path", required=True)
    parser.add_argument("--backup-path", required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = execute_inspection(args.expected_blog_id, args.theme_path, args.backup_path)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
