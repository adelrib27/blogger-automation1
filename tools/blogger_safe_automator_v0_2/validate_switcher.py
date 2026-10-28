#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from playwright.sync_api import sync_playwright

CDP_URL = "http://127.0.0.1:9222"


def main() -> int:
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(CDP_URL, timeout=10_000)
        pages = [pg for ctx in browser.contexts for pg in ctx.pages]
        page = next((pg for pg in pages if "blogger.com" in pg.url), None)
        if page is None:
            print(json.dumps({"ok": False, "error": "Nenhuma aba do Blogger encontrada."}, ensure_ascii=False, indent=2))
            return 2

        switcher = page.get_by_role(
            "listbox",
            name=re.compile(r"^(Blog Selection|Sele[cç][aã]o de blog)$", re.I),
        )
        if switcher.count() != 1 or not switcher.first.is_visible():
            print(json.dumps({"ok": False, "error": "Blog Selection não foi identificado de forma única e visível."}, ensure_ascii=False, indent=2))
            return 2

        switcher.first.click(timeout=10_000)
        page.wait_for_timeout(700)

        candidates = []
        for role in ("option", "menuitem", "button"):
            loc = page.get_by_role(role, name=re.compile(r"^(Novo blog|New blog)$", re.I))
            for i in range(loc.count()):
                item = loc.nth(i)
                if item.is_visible():
                    candidates.append({"role": role, "text": item.inner_text().strip()})

        if not candidates:
            text = page.get_by_text(re.compile(r"^(Novo blog|New blog)$", re.I), exact=True)
            for i in range(text.count()):
                item = text.nth(i)
                if item.is_visible():
                    candidates.append({"role": "text", "text": item.inner_text().strip()})

        try:
            page.keyboard.press("Escape")
        except Exception:
            pass

        print(json.dumps({
            "ok": True,
            "switcher": {"role": "listbox", "aria": "Blog Selection"},
            "new_blog_visible": bool(candidates),
            "matches": candidates,
        }, ensure_ascii=False, indent=2))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
