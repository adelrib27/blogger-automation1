#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

import browser_provision as bp
from inspect_theme_restore_dialog import select_expected_theme_page, validate_blog_id
from playwright.sync_api import sync_playwright


def inspect_controls(page) -> dict:
    return page.evaluate(
        r"""() => {
          const norm = v => String(v || '').trim().replace(/\s+/g, ' ');
          const visible = el => {
            const r = el.getBoundingClientRect();
            const s = getComputedStyle(el);
            return r.width > 0 && r.height > 0 && s.display !== 'none' && s.visibility !== 'hidden';
          };
          const meta = el => {
            if (!el) return null;
            const r = el.getBoundingClientRect();
            return {
              tag: el.tagName,
              text: norm(el.innerText || el.textContent),
              role: el.getAttribute('role') || '',
              aria: norm(el.getAttribute('aria-label')),
              title: norm(el.getAttribute('title')),
              tabindex: el.getAttribute('tabindex') || '',
              class_name: String(el.className || '').slice(0, 500),
              visible: visible(el),
              x: Math.round(r.x), y: Math.round(r.y), width: Math.round(r.width), height: Math.round(r.height)
            };
          };

          const matches = [];
          for (const el of document.querySelectorAll('body *')) {
            if (!visible(el)) continue;
            const text = norm(el.innerText || el.textContent);
            const aria = norm(el.getAttribute('aria-label'));
            if (text === 'PERSONALIZAR' || aria === 'PERSONALIZAR') {
              const parent = el.parentElement;
              const grand = parent?.parentElement || null;
              matches.push({
                self: meta(el),
                parent: meta(parent),
                grandparent: meta(grand),
                parent_children: parent ? [...parent.children].map(meta) : [],
                grandparent_children: grand ? [...grand.children].map(meta) : []
              });
            }
          }

          const nearbyButtons = [...document.querySelectorAll('button,[role="button"],[tabindex="0"]')]
            .filter(visible)
            .map(meta)
            .filter(x => x && x.y >= 250 && x.y <= 500 && x.x >= 850 && x.x <= 1350);

          return {
            title: document.title,
            url: location.href,
            visibility_state: document.visibilityState,
            personalizar_matches: matches,
            nearby_controls: nearbyButtons
          };
        }"""
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspeção somente leitura dos controles da tela Tema do Blogger.")
    parser.add_argument("--expected-blog-id", required=True)
    args = parser.parse_args()
    expected_blog_id = validate_blog_id(args.expected_blog_id)
    safe_cdp = bp.validate_cdp_url(bp.DEFAULT_CDP_URL, allow_remote=False)

    with sync_playwright() as p:
        browser, context = bp.connect_official_chrome(p, safe_cdp)
        page = select_expected_theme_page(context, expected_blog_id)
        result = inspect_controls(page)
        result.update({
            "status": "THEME_CONTROLS_INSPECTED",
            "read_only": True,
            "expected_blog_id": expected_blog_id,
            "browser_connected": browser.is_connected(),
            "message": "Somente leitura: nenhum clique, upload, restauração ou salvamento foi executado."
        })
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
