#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from playwright.sync_api import sync_playwright

CDP_URL = "http://127.0.0.1:9222"
ACTION_RE = re.compile(r"(novo|nova|new|criar|create|adicionar|add)", re.I)


def visible_items(page, role: str, limit: int = 120) -> list[dict]:
    out: list[dict] = []
    loc = page.get_by_role(role)
    count = min(loc.count(), limit)
    for i in range(count):
        item = loc.nth(i)
        try:
            if not item.is_visible():
                continue
            text = re.sub(r"\s+", " ", item.inner_text() or "").strip()
            aria = (item.get_attribute("aria-label") or "").strip()
            if text or aria:
                out.append({"role": role, "text": text[:180], "aria": aria[:180]})
        except Exception:
            continue
    return out


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

        before_expanded = switcher.first.get_attribute("aria-expanded")
        switcher.first.click(timeout=10_000)
        page.wait_for_timeout(900)
        after_expanded = switcher.first.get_attribute("aria-expanded")

        all_visible: list[dict] = []
        for role in ("option", "menuitem", "button", "link"):
            all_visible.extend(visible_items(page, role))

        action_matches = [
            item for item in all_visible
            if ACTION_RE.search(item.get("text", "")) or ACTION_RE.search(item.get("aria", ""))
        ]

        options = [item for item in all_visible if item["role"] == "option"]

        try:
            page.keyboard.press("Escape")
        except Exception:
            pass

        print(json.dumps({
            "ok": True,
            "switcher": {
                "role": "listbox",
                "aria": "Blog Selection",
                "aria_expanded_before": before_expanded,
                "aria_expanded_after": after_expanded,
            },
            "option_count": len(options),
            "options": options,
            "action_matches": action_matches,
        }, ensure_ascii=False, indent=2))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
