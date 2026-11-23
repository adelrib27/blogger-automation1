#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

import browser_provision as bp
from inspect_theme_restore_dialog import (
    _open_theme_actions_menu,
    _restore_menuitem_visible,
    select_expected_theme_page,
    validate_blog_id,
)
from playwright.sync_api import sync_playwright


def inspect_menu_contract(page) -> dict:
    return page.evaluate(
        r"""() => {
          const visible = el => {
            const r = el.getBoundingClientRect();
            const s = getComputedStyle(el);
            return r.width > 0 && r.height > 0 && s.display !== 'none' && s.visibility !== 'hidden';
          };
          const attrs = el => Object.fromEntries([...el.attributes].map(a => [a.name, a.value]));
          const summarize = el => ({
            tag: el.tagName,
            text: String(el.innerText || el.textContent || '').trim().replace(/\s+/g, ' '),
            attrs: attrs(el),
            onclick_type: typeof el.onclick,
            outer_html: el.outerHTML.slice(0, 5000),
            children: [...el.children].map(child => ({
              tag: child.tagName,
              text: String(child.innerText || child.textContent || '').trim().replace(/\s+/g, ' '),
              attrs: attrs(child),
              outer_html: child.outerHTML.slice(0, 2500)
            }))
          });
          const menuitems = [...document.querySelectorAll('[role="menuitem"]')]
            .filter(visible)
            .map(summarize);
          return {
            menuitems,
            active_element: document.activeElement ? summarize(document.activeElement) : null
          };
        }"""
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspeciona o contrato DOM/eventos dos menuitems de Tema sem acioná-los.")
    parser.add_argument("--expected-blog-id", required=True)
    args = parser.parse_args()
    expected = validate_blog_id(args.expected_blog_id)
    safe_cdp = bp.validate_cdp_url(bp.DEFAULT_CDP_URL, allow_remote=False)

    with sync_playwright() as p:
        browser, context = bp.connect_official_chrome(p, safe_cdp)
        page = select_expected_theme_page(context, expected)
        opened = False
        if _restore_menuitem_visible(page) is None:
            _open_theme_actions_menu(page)
            opened = True
        result = {
            "status": "THEME_MENU_EVENT_CONTRACT_INSPECTED",
            "read_only": True,
            "blog_id": expected,
            "url": bp.sanitize_url(page.url),
            "menu_opened_by_script": opened,
            "contract": inspect_menu_contract(page),
            "browser_connected": browser.is_connected(),
            "message": "Nenhum menuitem foi acionado; nenhum upload, restauração ou salvamento foi executado."
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
