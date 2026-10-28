#!/usr/bin/env python3
from __future__ import annotations

import json
import re

import browser_provision as bp
import browser_provision_v03 as v03
from playwright.sync_api import sync_playwright

CDP_URL = bp.DEFAULT_CDP_URL


def visible_controls(scope):
    items = []
    for role in ("textbox", "button"):
        loc = scope.get_by_role(role)
        for i in range(min(loc.count(), 40)):
            item = loc.nth(i)
            try:
                if not item.is_visible():
                    continue
                text = re.sub(r"\s+", " ", item.inner_text() or "").strip()
                aria = (item.get_attribute("aria-label") or "").strip()
                placeholder = (item.get_attribute("placeholder") or "").strip()
                items.append({
                    "role": role,
                    "text": text[:160],
                    "aria": aria[:160],
                    "placeholder": placeholder[:160],
                })
            except Exception:
                continue
    return items


def main() -> int:
    with sync_playwright() as p:
        browser, context = bp.connect_official_chrome(p, CDP_URL)
        page = bp.select_page(context)
        bp.require_blogger_session(page)
        previous_blog_id = bp.extract_current_blog_id(page)

        v03.open_blog_switcher(page)
        control = v03.find_new_blog(page)
        if control is None:
            print(json.dumps({"ok": False, "error": "Novo blog... não foi localizado."}, ensure_ascii=False, indent=2))
            return 2

        control.click(timeout=10_000)
        page.wait_for_timeout(900)

        dialogs = page.get_by_role("dialog")
        visible_dialog = None
        for i in range(dialogs.count() - 1, -1, -1):
            candidate = dialogs.nth(i)
            try:
                if candidate.is_visible():
                    visible_dialog = candidate
                    break
            except Exception:
                continue

        scope = visible_dialog if visible_dialog is not None else page.locator("body")
        controls = visible_controls(scope)
        has_textbox = any(item["role"] == "textbox" for item in controls)
        next_like = [
            item for item in controls
            if item["role"] == "button"
            and re.search(r"^(pr[oó]xima|next|continuar|continue)$", item["text"] or item["aria"], re.I)
        ]

        try:
            page.keyboard.press("Escape")
            page.wait_for_timeout(500)
        except Exception:
            pass

        current_blog_id = bp.extract_current_blog_id(page)
        print(json.dumps({
            "ok": bool(has_textbox),
            "dialog_detected": visible_dialog is not None,
            "textbox_detected": has_textbox,
            "next_button_matches": next_like,
            "controls": controls,
            "previous_blog_id": previous_blog_id,
            "current_blog_id": current_blog_id,
            "same_blog_after_close": previous_blog_id == current_blog_id,
            "message": "Nenhum campo foi preenchido e nenhum botão de avanço/salvamento foi acionado.",
        }, ensure_ascii=False, indent=2))
        return 0 if has_textbox and previous_blog_id == current_blog_id else 2


if __name__ == "__main__":
    raise SystemExit(main())
