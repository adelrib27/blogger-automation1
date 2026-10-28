#!/usr/bin/env python3
from __future__ import annotations

import json
import re

import browser_provision as bp
from playwright.sync_api import sync_playwright

CDP_URL = bp.DEFAULT_CDP_URL
TEST_TITLE = "TESTE BLOGGER AUTOMATION"
NEW_BLOG_RE = re.compile(r"^(Novo blog(?:\.\.\.|…)?|New blog(?:\.\.\.|…)?)$", re.I)
NEXT_RE = re.compile(r"^(Avan[cç]ar|Advance|Pr[oó]xima|Next|Continuar|Continue)$", re.I)


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

    menu = first_visible(page.locator('[role="button"][aria-label="Menu principal"], [role="button"][aria-label="Main menu"]'))
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


def snapshot_clickables(page) -> list[dict]:
    data = page.evaluate(
        r"""() => {
          const out = [];
          const nodes = [...document.querySelectorAll('button,[role="button"],[role="option"],[jsaction],[tabindex]')];
          for (const el of nodes) {
            const r = el.getBoundingClientRect();
            const s = getComputedStyle(el);
            if (r.width <= 0 || r.height <= 0 || s.display === 'none' || s.visibility === 'hidden') continue;
            const text = (el.innerText || el.textContent || '').trim().replace(/\s+/g, ' ');
            const aria = (el.getAttribute('aria-label') || '').trim();
            if (!text && !aria) continue;
            out.push({
              tag: el.tagName,
              role: el.getAttribute('role') || '',
              text: text.slice(0, 180),
              aria: aria.slice(0, 180),
              tabindex: el.getAttribute('tabindex') || '',
              disabled: el.hasAttribute('disabled') || el.getAttribute('aria-disabled') || '',
              jsaction: (el.getAttribute('jsaction') || '').slice(0, 180)
            });
            if (out.length >= 120) break;
          }
          return out;
        }"""
    )
    return data


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
                raise bp.SafeAutomationError('Campo de título não foi localizado com segurança.')

            title.fill(TEST_TITLE)
            page.wait_for_timeout(500)

            clickables = snapshot_clickables(page)
            next_matches = [
                x for x in clickables
                if NEXT_RE.fullmatch(norm(x.get("text") or x.get("aria")))
            ]

            result = {
                "ok": bool(next_matches),
                "title_field_detected": True,
                "temporary_title_filled": TEST_TITLE,
                "advance_matches": next_matches,
                "clickables": clickables,
                "message": "O título foi preenchido apenas temporariamente. Nenhum botão Avançar/Salvar foi acionado.",
            }
        except Exception as exc:
            result = {
                "ok": False,
                "error": norm(str(exc))[:700],
                "message": "Nenhum botão Avançar/Salvar foi acionado.",
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
