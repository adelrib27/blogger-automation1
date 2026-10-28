#!/usr/bin/env python3
from __future__ import annotations

import re

import browser_provision as bp

NEW_BLOG_PATTERN = re.compile(r"^(Novo blog(?:\.\.\.|…)?|New blog(?:\.\.\.|…)?)$", re.I)
BLOG_SELECTION_PATTERN = re.compile(r"^(Blog Selection|Sele[cç][aã]o de blog)$", re.I)


def _normalized_text(locator) -> str:
    try:
        return re.sub(r"\s+", " ", locator.inner_text() or "").strip()
    except Exception:
        return ""


def find_new_blog(page):
    # No Blogger atual, "Novo blog..." aparece como role=option com texto
    # visível, mas sem aria-label. Por isso percorremos as opções visíveis
    # e comparamos o texto real antes de usar os fallbacks semânticos.
    options = page.get_by_role("option")
    for i in range(options.count()):
        item = options.nth(i)
        try:
            if item.is_visible() and NEW_BLOG_PATTERN.fullmatch(_normalized_text(item)):
                return item
        except Exception:
            continue

    return bp.visible_first(
        [
            page.get_by_role("button", name=NEW_BLOG_PATTERN),
            page.get_by_role("menuitem", name=NEW_BLOG_PATTERN),
            page.get_by_text(NEW_BLOG_PATTERN, exact=True),
        ]
    )


def open_blog_switcher(page) -> None:
    switcher = bp.visible_first(
        [
            page.get_by_role("listbox", name=BLOG_SELECTION_PATTERN),
            page.get_by_role(
                "button",
                name=re.compile(
                    r"(Selecionar blog|Lista de blogs|Trocar blog|Choose a blog|Blog list|Switch blog)",
                    re.I,
                ),
            ),
            page.locator('button[aria-label*="blog" i], [role="button"][aria-label*="blog" i]'),
        ]
    )
    if switcher is None:
        raise bp.SafeAutomationError(
            "Não foi possível identificar com segurança o seletor de blogs. "
            "Nenhum clique de criação foi executado."
        )

    expanded = (switcher.get_attribute("aria-expanded") or "").strip().lower()
    if expanded != "true":
        switcher.click(timeout=10_000)
        page.wait_for_timeout(700)


# Injeta a correção no módulo original para que audit/preflight/create usem
# a estrutura real observada no Blogger atual.
bp.find_new_blog = find_new_blog
bp.open_blog_switcher = open_blog_switcher


if __name__ == "__main__":
    raise SystemExit(bp.main())
