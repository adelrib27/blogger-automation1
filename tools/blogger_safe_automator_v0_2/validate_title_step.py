#!/usr/bin/env python3
from __future__ import annotations

import json
import re

import browser_provision as bp
from playwright.sync_api import sync_playwright

CDP_URL = bp.DEFAULT_CDP_URL
TEST_TITLE = "TESTE BLOGGER AUTOMATION"
NEW_BLOG_RE = re.compile(r"^(Novo blog(?:\.\.\.|…)?|New blog(?:\.\.\.|…)?)$", re.I)
ADVANCE_RE = re.compile(r"^(Avan[cç]ar|Advance|Pr[oó]xima|Next|Continuar|Continue)$", re.I)


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

    menu = first_visible(
        page.locator(
            '[role="button"][aria-label="Menu principal"], '
            '[role="button"][aria-label="Main menu"]'
        )
    )
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


def find_advance_targets(page) -> list[dict]:
    # Procura o texto de ação diretamente em TODOS os elementos visíveis.
    # Depois registra também o ancestral clicável mais próximo. Isso evita
    # perder o botão por limite de snapshot ou por falta de role semântico.
    return page.evaluate(
        r"""() => {
          const labels = new Set(['AVANÇAR', 'AVANCAR', 'ADVANCE', 'PRÓXIMA', 'PROXIMA', 'NEXT', 'CONTINUAR', 'CONTINUE']);
          const norm = (s) => (s || '').trim().replace(/\s+/g, ' ');
          const visible = (el) => {
            const r = el.getBoundingClientRect();
            const s = getComputedStyle(el);
            return r.width > 0 && r.height > 0 && s.display !== 'none' && s.visibility !== 'hidden';
          };
          const describe = (el) => ({
            tag: el.tagName,
            role: el.getAttribute('role') || '',
            text: norm(el.innerText || el.textContent || '').slice(0, 180),
            aria: norm(el.getAttribute('aria-label') || '').slice(0, 180),
            tabindex: el.getAttribute('tabindex') || '',
            disabled: el.hasAttribute('disabled') || el.getAttribute('aria-disabled') || '',
            jsaction: (el.getAttribute('jsaction') || '').slice(0, 180)
          });

          const out = [];
          const seen = new Set();
          for (const el of document.querySelectorAll('body *')) {
            if (!visible(el)) continue;
            const text = norm(el.innerText || el.textContent || '').toUpperCase();
            const aria = norm(el.getAttribute('aria-label') || '').toUpperCase();
            if (!labels.has(text) && !labels.has(aria)) continue;

            const clickable = el.closest('button,[role="button"],[jsaction],[tabindex]') || el;
            const key = `${clickable.tagName}|${clickable.getAttribute('role') || ''}|${norm(clickable.innerText || clickable.textContent || '')}|${clickable.getAttribute('jsaction') || ''}`;
            if (seen.has(key)) continue;
            seen.add(key);

            out.push({
              matched_element: describe(el),
              clickable_ancestor: describe(clickable)
            });
          }
          return out;
        }"""
    )


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

            advance_matches = find_advance_targets(page)
            semantic_match = first_visible(
                page.get_by_text(ADVANCE_RE, exact=True)
            )

            result = {
                "ok": bool(advance_matches or semantic_match is not None),
                "title_field_detected": True,
                "temporary_title_filled": TEST_TITLE,
                "advance_matches": advance_matches,
                "semantic_text_match": semantic_match is not None,
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
