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


def select_expected_theme_page(context, expected_blog_id: str):
    """Select only the Blogger Theme tab for the expected Blog ID.

    No fallback to settings, another Blogger tab, or another blog is allowed.
    """
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
          const visible = el => {
            const r = el.getBoundingClientRect();
            const s = getComputedStyle(el);
            return r.width > 0 && r.height > 0 && s.display !== 'none' && s.visibility !== 'hidden';
          };
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
            body_text: norm(document.body?.innerText || '').slice(0, 5000)
          };
        }"""
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

        dom = inspect_restore_dom(page)
        dialog_text = " ".join(item.get("text", "") for item in dom["dialogs"]).casefold()
        visible_actions = " ".join(
            (item.get("text") or item.get("aria") or "") for item in dom["buttons"]
        ).casefold()
        if "restaurar" not in dialog_text:
            raise bp.SafeAutomationError(
                "O diálogo Restaurar não está visível. Abra Tema > Restaurar manualmente e tente novamente."
            )
        if "fazer upload" not in visible_actions or "cancelar" not in visible_actions:
            raise bp.SafeAutomationError(
                "As ações CANCELAR e FAZER UPLOAD não foram confirmadas no diálogo Restaurar."
            )
        if any(item.get("files_selected", 0) for item in dom["file_inputs"]):
            raise bp.SafeAutomationError(
                "Já existe arquivo selecionado no diálogo. Inspeção bloqueada para preservar o estado."
            )

        return {
            "status": "THEME_RESTORE_DIALOG_INSPECTED",
            "read_only": True,
            "blog_id": expected_blog_id,
            "url": bp.sanitize_url(page.url),
            "theme": theme,
            "backup": backup,
            "dialog": dom,
            "browser_connected": browser.is_connected(),
            "message": "Somente leitura: nenhum clique, upload, restauração ou salvamento foi executado."
        }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspeciona, sem cliques, o diálogo Restaurar do Tema Blogger."
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
