#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re

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


def _page_visibility(page) -> bool:
    try:
        return page.evaluate("() => document.visibilityState") == "visible"
    except Exception:
        return False


def select_expected_theme_page(context, expected_blog_id: str):
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


def _visible_restore_count(page) -> int:
    return page.evaluate(
        r"""() => {
          const norm = v => String(v || '').trim().replace(/\s+/g, ' ');
          const visible = el => {
            const r = el.getBoundingClientRect();
            const s = getComputedStyle(el);
            return r.width > 0 && r.height > 0 && s.display !== 'none' && s.visibility !== 'hidden';
          };
          return [...document.querySelectorAll('*')]
            .filter(el => visible(el) && norm(el.textContent) === 'Restaurar').length;
        }"""
    )


def ensure_actions_menu_open(page) -> bool:
    if _visible_restore_count(page) > 0:
        return False
    more = page.locator('[role="button"][aria-label="Mais ações"]')
    visible = []
    for i in range(more.count()):
        item = more.nth(i)
        try:
            if item.is_visible():
                visible.append(item)
        except Exception:
            pass
    if len(visible) != 1:
        raise bp.SafeAutomationError(
            f"Controle 'Mais ações' ambíguo ou ausente: encontrado(s) {len(visible)} visível(is)."
        )
    visible[0].click(timeout=5_000)
    page.wait_for_timeout(300)
    if _visible_restore_count(page) == 0:
        raise bp.SafeAutomationError("Menu abriu, mas a opção Restaurar não ficou visível.")
    return True


def inspect_restore_item(page) -> dict:
    return page.evaluate(
        r"""() => {
          const norm = v => String(v || '').trim().replace(/\s+/g, ' ');
          const visible = el => {
            const r = el.getBoundingClientRect();
            const s = getComputedStyle(el);
            return r.width > 0 && r.height > 0 && s.display !== 'none' && s.visibility !== 'hidden';
          };
          const describe = el => {
            if (!el) return null;
            const r = el.getBoundingClientRect();
            const s = getComputedStyle(el);
            return {
              tag: el.tagName,
              text: norm(el.innerText || el.textContent),
              role: el.getAttribute('role') || '',
              aria: el.getAttribute('aria-label') || '',
              tabindex: el.getAttribute('tabindex') || '',
              class_name: typeof el.className === 'string' ? el.className : '',
              visible: visible(el),
              pointer_events: s.pointerEvents,
              cursor: s.cursor,
              x: Math.round(r.x), y: Math.round(r.y),
              width: Math.round(r.width), height: Math.round(r.height)
            };
          };
          const all = [...document.querySelectorAll('*')]
            .filter(el => visible(el) && norm(el.textContent) === 'Restaurar');
          return all.map(el => {
            const chain = [];
            let cur = el;
            for (let i = 0; i < 6 && cur; i++, cur = cur.parentElement) chain.push(describe(cur));
            return { self: describe(el), ancestor_chain: chain };
          });
        }"""
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspeciona, sem clicar em Restaurar, o item do menu Tema.")
    parser.add_argument("--expected-blog-id", required=True)
    args = parser.parse_args()
    expected = validate_blog_id(args.expected_blog_id)
    safe_cdp = bp.validate_cdp_url(bp.DEFAULT_CDP_URL, allow_remote=False)

    with sync_playwright() as p:
        browser, context = bp.connect_official_chrome(p, safe_cdp)
        page = select_expected_theme_page(context, expected)
        if extract_panel_blog_id(page.url) != expected:
            raise bp.SafeAutomationError("Blog ID divergente; inspeção bloqueada.")
        menu_opened = ensure_actions_menu_open(page)
        result = {
            "status": "THEME_RESTORE_MENU_ITEM_INSPECTED",
            "read_only": True,
            "blog_id": expected,
            "url": bp.sanitize_url(page.url),
            "menu_opened_by_script": menu_opened,
            "matches": inspect_restore_item(page),
            "browser_connected": browser.is_connected(),
            "message": "Nenhum clique em Restaurar, upload, restauração ou salvamento foi executado.",
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
