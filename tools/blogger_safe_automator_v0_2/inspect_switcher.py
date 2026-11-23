#!/usr/bin/env python3
from __future__ import annotations

import json
from playwright.sync_api import sync_playwright

CDP_URL = "http://127.0.0.1:9222"

JS = r"""
() => {
  const out = [];
  const nodes = [...document.querySelectorAll('*')];
  for (const el of nodes) {
    const text = (el.innerText || el.textContent || '').trim().replace(/\s+/g, ' ');
    if (!text) continue;
    if (text === 'Achados para Casa' || /Achados para Casa/i.test(text)) {
      const r = el.getBoundingClientRect();
      const s = getComputedStyle(el);
      if (r.width <= 0 || r.height <= 0 || s.display === 'none' || s.visibility === 'hidden') continue;
      out.push({
        tag: el.tagName,
        text: text.slice(0, 200),
        id: el.id || '',
        class: typeof el.className === 'string' ? el.className : '',
        role: el.getAttribute('role') || '',
        aria: el.getAttribute('aria-label') || '',
        ariaExpanded: el.getAttribute('aria-expanded') || '',
        ariaHaspopup: el.getAttribute('aria-haspopup') || '',
        tabindex: el.getAttribute('tabindex') || '',
        parentTag: el.parentElement?.tagName || '',
        parentRole: el.parentElement?.getAttribute('role') || '',
        parentAria: el.parentElement?.getAttribute('aria-label') || '',
        parentClass: typeof el.parentElement?.className === 'string' ? el.parentElement.className : ''
      });
      if (out.length >= 20) break;
    }
  }
  return out;
}
"""


def main() -> int:
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(CDP_URL, timeout=10_000)
        pages = [pg for ctx in browser.contexts for pg in ctx.pages]
        page = next((pg for pg in pages if 'blogger.com' in pg.url), None)
        if page is None:
            print(json.dumps({"ok": False, "error": "Nenhuma aba do Blogger encontrada."}, ensure_ascii=False, indent=2))
            return 2
        result = page.evaluate(JS)
        print(json.dumps({"ok": True, "url": page.url.split('?')[0], "matches": result}, ensure_ascii=False, indent=2))
        return 0


if __name__ == '__main__':
    raise SystemExit(main())
