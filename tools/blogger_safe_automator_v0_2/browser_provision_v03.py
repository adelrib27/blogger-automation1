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
    # O Blogger atual expõe "Novo blog..." como role=option sem aria-label.
    # Percorremos as opções visíveis e comparamos o texto real.
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
    # Estrutura confirmada no Blogger atual: um listbox visível chamado
    # "Blog Selection". Mesmo quando aria-expanded="true", o clique é
    # necessário para materializar/atualizar as options para o Playwright.
    listbox = page.get_by_role("listbox", name=BLOG_SELECTION_PATTERN)
    try:
        if listbox.count() == 1 and listbox.first.is_visible():
            listbox.first.click(timeout=10_000)
            page.wait_for_timeout(900)
            return
    except Exception:
        pass

    switcher = bp.visible_first(
        [
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

    switcher.click(timeout=10_000)
    page.wait_for_timeout(900)


# Injeta a correção no módulo original para que audit/preflight/create usem
# a estrutura real observada no Blogger atual.
bp.find_new_blog = find_new_blog
bp.open_blog_switcher = open_blog_switcher


if __name__ == "__main__":
    raise SystemExit(bp.main())
