#!/usr/bin/env python3
from __future__ import annotations

import json
import re

import browser_provision as bp
import browser_provision_v03 as v03
from playwright.sync_api import sync_playwright

CDP_URL = bp.DEFAULT_CDP_URL
TITLE_MARKERS = re.compile(
    r"(escolha.*nome.*blog|nome.*blog|t[ií]tulo|choose.*name.*blog|blog.*title)",
    re.I,
)
NEXT_MARKERS = re.compile(r"^(pr[oó]xima|next|continuar|continue)$", re.I)


def norm(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def visible_snapshot(page) -> dict:
    fields = []
    loc = page.locator('input, textarea, [contenteditable="true"]')
    for i in range(min(loc.count(), 60)):
        item = loc.nth(i)
        try:
            if not item.is_visible():
                continue
            fields.append({
                "tag": item.evaluate("el => el.tagName"),
                "type": item.get_attribute("type") or "",
                "role": item.get_attribute("role") or "",
                "aria": item.get_attribute("aria-label") or "",
                "placeholder": item.get_attribute("placeholder") or "",
            })
        except Exception:
            continue

    buttons = []
    btn = page.locator('button, [role="button"]')
    for i in range(min(btn.count(), 80)):
        item = btn.nth(i)
        try:
            if not item.is_visible():
                continue
            buttons.append({
                "text": norm(item.inner_text())[:160],
                "aria": norm(item.get_attribute("aria-label"))[:160],
            })
        except Exception:
            continue

    body_text = ""
    try:
        body_text = norm(page.locator("body").inner_text())
    except Exception:
        pass

    non_search_fields = [
        f for f in fields
        if not re.search(r"pesquisa|search", f.get("aria", ""), re.I)
        and f.get("role", "").lower() != "combobox"
    ]
    next_buttons = [
        b for b in buttons
        if NEXT_MARKERS.fullmatch(norm(b.get("text") or b.get("aria")))
    ]
    title_marker = bool(TITLE_MARKERS.search(body_text))

    return {
        "creation_ui_detected": bool(non_search_fields and (next_buttons or title_marker)),
        "visible_fields": fields,
        "non_search_fields": non_search_fields,
        "next_buttons": next_buttons,
        "title_marker_in_body": title_marker,
    }


def reacquire_new_blog(page):
    v03.open_blog_switcher(page)
    page.wait_for_timeout(350)
    control = v03.find_new_blog(page)
    if control is None:
        raise bp.SafeAutomationError('A opção "Novo blog..." não foi localizada.')
    return control


def restore(page, original_url: str) -> None:
    try:
        page.keyboard.press("Escape")
        page.wait_for_timeout(350)
    except Exception:
        pass
    if bp.sanitize_url(page.url) != bp.sanitize_url(original_url):
        page.goto(original_url, wait_until="domcontentloaded", timeout=60_000)
        page.wait_for_timeout(700)


def main() -> int:
    with sync_playwright() as p:
        _, context = bp.connect_official_chrome(p, CDP_URL)
        page = bp.select_page(context)
        bp.require_blogger_session(page)

        original_url = page.url
        original_blog_id = bp.extract_current_blog_id(page)
        attempts = []
        activated = False
        activation_method = None

        control = reacquire_new_blog(page)
        metadata = {
            "text": norm(control.inner_text()),
            "role": control.get_attribute("role") or "",
            "aria": control.get_attribute("aria-label") or "",
            "tabindex": control.get_attribute("tabindex") or "",
            "class": control.get_attribute("class") or "",
            "box": control.bounding_box(),
        }

        methods = ("click", "enter", "space")
        final_snapshot = None

        for method in methods:
            control = reacquire_new_blog(page)
            if method == "click":
                control.click(timeout=10_000)
            else:
                control.focus()
                page.wait_for_timeout(150)
                page.keyboard.press("Enter" if method == "enter" else "Space")

            page.wait_for_timeout(900)
            snap = visible_snapshot(page)
            attempts.append({
                "method": method,
                "url": bp.sanitize_url(page.url),
                "creation_ui_detected": snap["creation_ui_detected"],
                "non_search_field_count": len(snap["non_search_fields"]),
                "next_button_count": len(snap["next_buttons"]),
                "title_marker_in_body": snap["title_marker_in_body"],
            })
            if snap["creation_ui_detected"]:
                activated = True
                activation_method = method
                final_snapshot = snap
                break

            try:
                page.keyboard.press("Escape")
                page.wait_for_timeout(250)
            except Exception:
                pass

        restore(page, original_url)
        current_blog_id = bp.extract_current_blog_id(page)

        result = {
            "ok": activated and current_blog_id == original_blog_id,
            "new_blog_option": metadata,
            "activation_method": activation_method,
            "attempts": attempts,
            "final_snapshot": final_snapshot,
            "original_blog_id": original_blog_id,
            "current_blog_id": current_blog_id,
            "restored_original_blog": current_blog_id == original_blog_id,
            "message": "Nenhum campo foi preenchido e nenhum botão Próxima/Salvar foi acionado.",
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
