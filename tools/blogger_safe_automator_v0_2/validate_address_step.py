#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from datetime import datetime

import browser_provision as bp
from playwright.sync_api import sync_playwright

CDP_URL = bp.DEFAULT_CDP_URL
TEST_TITLE = "TESTE BLOGGER AUTOMATION"
TEST_ADDRESS = f"teste-blogger-automation-{datetime.now().strftime('%Y%m%d%H%M%S')}"
NEW_BLOG_RE = re.compile(r"^(Novo blog(?:\.\.\.|…)?|New blog(?:\.\.\.|…)?)$", re.I)
ADVANCE_RE = re.compile(r"^(Avan[cç]ar|Advance|Pr[oó]xima|Next|Continuar|Continue)$", re.I)
ADDRESS_RE = re.compile(r"(endere[cç]o|address|url)", re.I)
FINAL_RE = re.compile(r"^(Salvar|Save|Criar blog|Create blog|Concluir|Finish)$", re.I)


def norm(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


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


def reset(page, url: str) -> None:
    page.goto(url, wait_until="domcontentloaded", timeout=60_000)
    page.wait_for_timeout(1200)


def ensure_switcher(page):
    switcher = first_visible(page.locator('[role="listbox"][aria-label="Blog Selection"]'))
    if switcher is not None:
        return switcher

    menu = first_visible(page.locator(
        '[role="button"][aria-label="Menu principal"], '
        '[role="button"][aria-label="Main menu"]'
    ))
    if menu is not None:
        try:
            menu.click(timeout=3_000)
        except Exception:
            menu.evaluate("el => el.click()")
        page.wait_for_timeout(500)

    switcher = first_visible(page.locator('[role="listbox"][aria-label="Blog Selection"]'))
    if switcher is None:
        raise bp.SafeAutomationError("Blog Selection não ficou visível.")
    return switcher


def open_create_ui(page) -> None:
    switcher = ensure_switcher(page)
    try:
        switcher.click(timeout=3_000)
    except Exception:
        switcher.evaluate("el => el.click()")
    page.wait_for_timeout(500)

    options = page.get_by_role("option")
    target = None
    for i in range(options.count()):
        item = options.nth(i)
        try:
            if item.is_visible() and NEW_BLOG_RE.fullmatch(norm(item.inner_text())):
                target = item
                break
        except Exception:
            continue
    if target is None:
        raise bp.SafeAutomationError('A opção "Novo blog..." não foi localizada.')

    # Método confirmado empiricamente no Blogger atual.
    target.evaluate("el => el.click()")
    page.wait_for_timeout(900)


def exact_visible_text_match(page, pattern: re.Pattern):
    handles = page.locator("body *")
    matches = []
    for i in range(handles.count()):
        item = handles.nth(i)
        try:
            if not item.is_visible():
                continue
            text = norm(item.inner_text())
            aria = norm(item.get_attribute("aria-label"))
            value = text or aria
            if not pattern.fullmatch(value):
                continue
            matches.append(item)
        except Exception:
            continue
    return matches


def element_meta(item) -> dict:
    return {
        "tag": item.evaluate("el => el.tagName"),
        "role": item.get_attribute("role") or "",
        "text": norm(item.inner_text())[:160],
        "aria": norm(item.get_attribute("aria-label"))[:160],
        "placeholder": norm(item.get_attribute("placeholder"))[:160],
        "type": item.get_attribute("type") or "",
        "tabindex": item.get_attribute("tabindex") or "",
        "disabled": item.get_attribute("disabled") or item.get_attribute("aria-disabled") or "",
    }


def visible_fields(page) -> list[dict]:
    result = []
    loc = page.locator('input, textarea, [contenteditable="true"]')
    for i in range(min(loc.count(), 80)):
        item = loc.nth(i)
        try:
            if item.is_visible():
                result.append(element_meta(item))
        except Exception:
            continue
    return result


def find_address_field(page):
    loc = page.locator('input, textarea, [contenteditable="true"]')
    candidates = []
    for i in range(loc.count()):
        item = loc.nth(i)
        try:
            if not item.is_visible():
                continue
            aria = norm(item.get_attribute("aria-label"))
            placeholder = norm(item.get_attribute("placeholder"))
            name = norm(item.get_attribute("name"))
            marker = " ".join([aria, placeholder, name])
            if ADDRESS_RE.search(marker):
                return item
            role = (item.get_attribute("role") or "").lower()
            if role != "combobox" and not re.search(r"pesquisa|search", aria, re.I):
                candidates.append(item)
        except Exception:
            continue

    # Na segunda etapa do modal deve haver um único campo não-pesquisa.
    if len(candidates) == 1:
        return candidates[0]
    return None


def main() -> int:
    with sync_playwright() as p:
        _, context = bp.connect_official_chrome(p, CDP_URL)
        page = bp.select_page(context)
        bp.require_blogger_session(page)

        original_url = page.url
        original_blog_id = bp.extract_current_blog_id(page)
        result = {}

        try:
            reset(page, original_url)
            open_create_ui(page)

            title = first_visible(page.locator('input[aria-label="Título"], input[aria-label="Title"]'))
            if title is None:
                raise bp.SafeAutomationError("Campo de título não foi localizado com segurança.")
            title.fill(TEST_TITLE)
            page.wait_for_timeout(350)

            advance_matches = exact_visible_text_match(page, ADVANCE_RE)
            if not advance_matches:
                raise bp.SafeAutomationError("Botão AVANÇAR não foi localizado com segurança.")

            # Usa o menor elemento clicável que contém exatamente AVANÇAR.
            advance = None
            for item in reversed(advance_matches):
                try:
                    role = (item.get_attribute("role") or "").lower()
                    if item.evaluate("el => el.tagName") == "BUTTON" or role == "button" or item.get_attribute("tabindex") == "0":
                        advance = item
                        break
                except Exception:
                    continue
            advance = advance or advance_matches[-1]
            try:
                advance.click(timeout=3_000)
            except Exception:
                advance.evaluate("el => el.click()")
            page.wait_for_timeout(1000)

            before_fields = visible_fields(page)
            address = find_address_field(page)
            if address is None:
                raise bp.SafeAutomationError("Campo de endereço não foi localizado com segurança após AVANÇAR.")

            address_meta = element_meta(address)
            address.fill(TEST_ADDRESS)
            page.wait_for_timeout(1400)

            body_text = norm(page.locator("body").inner_text())
            unavailable = bool(re.search(
                r"(endere[cç]o.*n[aã]o.*dispon[ií]vel|address.*not.*available)",
                body_text,
                re.I,
            ))
            available_marker = bool(re.search(
                r"(endere[cç]o.*dispon[ií]vel|address.*available)",
                body_text,
                re.I,
            )) and not unavailable

            final_matches = exact_visible_text_match(page, FINAL_RE)
            final_meta = [element_meta(item) for item in final_matches[:12]]

            result = {
                "ok": bool(address_meta) and bool(final_matches),
                "title_step_advanced": True,
                "address_field_detected": True,
                "temporary_address_filled": TEST_ADDRESS,
                "address_field": address_meta,
                "visible_fields_after_advance": before_fields,
                "address_unavailable": unavailable,
                "address_available_marker": available_marker,
                "final_action_matches": final_meta,
                "message": "Título e endereço foram preenchidos apenas temporariamente. Nenhum botão final Salvar/Criar foi acionado.",
            }
        except Exception as exc:
            result = {
                "ok": False,
                "error": norm(str(exc))[:900],
                "message": "Nenhum botão final Salvar/Criar foi acionado.",
            }
        finally:
            try:
                page.keyboard.press("Escape")
                page.wait_for_timeout(300)
            except Exception:
                pass
            try:
                reset(page, original_url)
            except Exception:
                pass

        current_blog_id = bp.extract_current_blog_id(page)
        result["original_blog_id"] = original_blog_id
        result["current_blog_id"] = current_blog_id
        result["restored_original_blog"] = current_blog_id == original_blog_id
        result["ok"] = bool(result.get("ok")) and result["restored_original_blog"]
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
