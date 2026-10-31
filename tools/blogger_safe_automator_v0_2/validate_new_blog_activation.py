#!/usr/bin/env python3
from __future__ import annotations

import json
import re

import browser_provision as bp
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError, sync_playwright

CDP_URL = bp.DEFAULT_CDP_URL
NEW_BLOG_PATTERN = re.compile(r"^(Novo blog(?:\.\.\.|…)?|New blog(?:\.\.\.|…)?)$", re.I)
TITLE_MARKERS = re.compile(
    r"(escolha.*nome.*blog|nome.*blog|t[ií]tulo|choose.*name.*blog|blog.*title)",
    re.I,
)
NEXT_MARKERS = re.compile(r"^(pr[oó]xima|next|continuar|continue)$", re.I)
MAIN_MENU_PATTERN = re.compile(r"^(Menu principal|Main menu)$", re.I)


def norm(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def compact_error(exc: Exception) -> str:
    return norm(str(exc))[:500]


def first_visible(locator):
    try:
        for i in range(locator.count()):
            item = locator.nth(i)
            try:
                if item.is_visible():
                    return item
            except Exception:
                continue
    except Exception:
        pass
    return None


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


def reset_to_original(page, original_url: str) -> None:
    # Cada tentativa começa de um estado novo. Isso evita locators antigos,
    # drawers fechados e opções destacadas/destacadas pelo teste anterior.
    page.goto(original_url, wait_until="domcontentloaded", timeout=60_000)
    page.wait_for_timeout(1200)


def ensure_blog_switcher(page):
    switcher = first_visible(
        page.locator('[role="listbox"][aria-label="Blog Selection"], '
                     '[role="listbox"][aria-label*="Seleção de blog" i]')
    )
    if switcher is not None:
        return switcher

    # Em algumas renderizações o drawer lateral nasce fechado. Abrimos apenas
    # o menu de navegação, nunca uma ação de criação.
    menu = first_visible(
        page.get_by_role("button", name=MAIN_MENU_PATTERN)
    ) or first_visible(
        page.locator('[role="button"][aria-label="Menu principal"], '
                     '[role="button"][aria-label="Main menu"]')
    )
    if menu is not None:
        try:
            menu.click(timeout=3_000)
        except Exception:
            try:
                menu.evaluate("el => el.click()")
            except Exception:
                pass
        page.wait_for_timeout(500)

    switcher = first_visible(
        page.locator('[role="listbox"][aria-label="Blog Selection"], '
                     '[role="listbox"][aria-label*="Seleção de blog" i]')
    )
    if switcher is None:
        raise bp.SafeAutomationError(
            "Blog Selection não ficou visível após restaurar a página e verificar o drawer."
        )
    return switcher


def reacquire_new_blog(page):
    switcher = ensure_blog_switcher(page)

    # O Blogger materializa/estabiliza as opções após interação com o listbox.
    try:
        switcher.click(timeout=3_000)
    except Exception:
        try:
            switcher.evaluate("el => el.click()")
        except Exception:
            pass
    page.wait_for_timeout(450)

    options = page.get_by_role("option")
    for i in range(options.count()):
        item = options.nth(i)
        try:
            if item.is_visible() and NEW_BLOG_PATTERN.fullmatch(norm(item.inner_text())):
                return item
        except Exception:
            continue

    raise bp.SafeAutomationError('A opção "Novo blog..." não ficou visível após abrir o seletor.')


def activate_once(page, method: str, original_url: str) -> tuple[bool, str | None]:
    try:
        reset_to_original(page, original_url)
        control = reacquire_new_blog(page)

        if method == "click":
            control.click(timeout=3_000)
        elif method == "force-click":
            control.click(timeout=3_000, force=True)
        elif method in {"enter", "space"}:
            try:
                control.focus(timeout=3_000)
            except PlaywrightTimeoutError:
                control.evaluate("el => el.focus()")
            page.wait_for_timeout(100)
            page.keyboard.press("Enter" if method == "enter" else "Space")
        elif method == "dom-click":
            control.evaluate("el => el.click()")
        else:
            raise ValueError(f"Método desconhecido: {method}")
        return True, None
    except Exception as exc:
        return False, compact_error(exc)


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
        final_snapshot = None
        metadata = None

        try:
            reset_to_original(page, original_url)
            first = reacquire_new_blog(page)
            metadata = {
                "text": norm(first.inner_text()),
                "role": first.get_attribute("role") or "",
                "aria": first.get_attribute("aria-label") or "",
                "tabindex": first.get_attribute("tabindex") or "",
                "class": first.get_attribute("class") or "",
                "box": first.bounding_box(),
            }
        except Exception as exc:
            metadata = {"error": compact_error(exc)}

        methods = ("click", "force-click", "enter", "space", "dom-click")
        for method in methods:
            invoked, error = activate_once(page, method, original_url)
            page.wait_for_timeout(900 if invoked else 200)
            snap = visible_snapshot(page)
            attempts.append({
                "method": method,
                "invoked": invoked,
                "error": error,
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

        # Restauração explícita ao final, mesmo quando uma tentativa funcionou.
        try:
            reset_to_original(page, original_url)
        except Exception:
            pass
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
