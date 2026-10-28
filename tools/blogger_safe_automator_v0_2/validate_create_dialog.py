#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from urllib.parse import urlparse

import browser_provision as bp
import browser_provision_v03 as v03
from playwright.sync_api import sync_playwright

CDP_URL = bp.DEFAULT_CDP_URL


def compact(value: str, limit: int = 220) -> str:
    return re.sub(r"\s+", " ", value or "").strip()[:limit]


def visible_native_fields(page):
    items = []
    loc = page.locator('input, textarea, [contenteditable="true"]')
    for i in range(min(loc.count(), 80)):
        item = loc.nth(i)
        try:
            if not item.is_visible():
                continue
            items.append({
                "tag": item.evaluate("el => el.tagName"),
                "type": item.get_attribute("type") or "",
                "name": item.get_attribute("name") or "",
                "aria": compact(item.get_attribute("aria-label") or ""),
                "placeholder": compact(item.get_attribute("placeholder") or ""),
                "role": item.get_attribute("role") or "",
                "contenteditable": item.get_attribute("contenteditable") or "",
            })
        except Exception:
            continue
    return items


def visible_buttons(page):
    items = []
    loc = page.locator('button, [role="button"]')
    for i in range(min(loc.count(), 120)):
        item = loc.nth(i)
        try:
            if not item.is_visible():
                continue
            items.append({
                "tag": item.evaluate("el => el.tagName"),
                "text": compact(item.inner_text() or ""),
                "aria": compact(item.get_attribute("aria-label") or ""),
            })
        except Exception:
            continue
    return items


def visible_dialogs(page):
    items = []
    loc = page.locator('[role="dialog"]')
    for i in range(min(loc.count(), 30)):
        item = loc.nth(i)
        try:
            if not item.is_visible():
                continue
            items.append({
                "index": i,
                "aria": compact(item.get_attribute("aria-label") or ""),
                "aria_modal": item.get_attribute("aria-modal") or "",
                "text": compact(item.inner_text() or "", 500),
            })
        except Exception:
            continue
    return items


def same_blogger_blog(url_a: str, url_b: str) -> bool:
    return bp.extract_blog_id_from_url(url_a) == bp.extract_blog_id_from_url(url_b)


def main() -> int:
    with sync_playwright() as p:
        browser, context = bp.connect_official_chrome(p, CDP_URL)
        page = bp.select_page(context)
        bp.require_blogger_session(page)

        original_url = page.url
        previous_blog_id = bp.extract_current_blog_id(page)

        v03.open_blog_switcher(page)
        control = v03.find_new_blog(page)
        if control is None:
            print(json.dumps({"ok": False, "error": "Novo blog... não foi localizado."}, ensure_ascii=False, indent=2))
            return 2

        control.click(timeout=10_000)
        page.wait_for_timeout(1400)

        url_after_click = page.url
        fields = visible_native_fields(page)
        buttons = visible_buttons(page)
        dialogs = visible_dialogs(page)

        title_like_fields = [
            item for item in fields
            if re.search(r"(t[ií]tulo|title|nome.*blog|blog.*name)",
                         " ".join([item["name"], item["aria"], item["placeholder"]]), re.I)
        ]
        next_like_buttons = [
            item for item in buttons
            if re.search(r"^(pr[oó]xima|next|continuar|continue)$",
                         compact(item["text"] or item["aria"]), re.I)
        ]

        # Cleanup seguro: primeiro tenta fechar modal; se a ação tiver navegado,
        # restaura exatamente a URL original do painel do Blogger.
        try:
            page.keyboard.press("Escape")
            page.wait_for_timeout(500)
        except Exception:
            pass

        host = (urlparse(page.url).hostname or "").lower()
        if page.url != original_url and (host == "blogger.com" or host.endswith(".blogger.com")):
            try:
                page.goto(original_url, wait_until="domcontentloaded", timeout=60_000)
                page.wait_for_timeout(900)
            except Exception:
                pass

        current_blog_id = bp.extract_current_blog_id(page)
        restored = page.url == original_url or same_blogger_blog(original_url, page.url)

        payload = {
            "ok": bool(fields or title_like_fields) and restored,
            "original_url": bp.sanitize_url(original_url),
            "url_after_click": bp.sanitize_url(url_after_click),
            "url_changed_after_click": url_after_click != original_url,
            "visible_dialogs": dialogs,
            "visible_fields": fields,
            "title_like_fields": title_like_fields,
            "next_button_matches": next_like_buttons,
            "visible_buttons": buttons[:40],
            "previous_blog_id": previous_blog_id,
            "current_blog_id": current_blog_id,
            "restored_original_blog": restored,
            "message": "Nenhum campo foi preenchido e nenhum botão de avanço/salvamento foi acionado.",
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0 if payload["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
