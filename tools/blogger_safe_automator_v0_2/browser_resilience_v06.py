#!/usr/bin/env python3
from __future__ import annotations

import browser_provision as bp

# V0.6: corrige carregamento assíncrono do seletor de blogs do Blogger.
# A alteração é deliberadamente restrita a operações NÃO destrutivas:
# abrir o seletor e localizar/clicar em "Novo blog...". As proteções existentes
# para endereço, SALVAR, Blog ID novo e HTTP 200 continuam em browser_provision.py.

_ORIGINAL_OPEN_BLOG_SWITCHER = bp.open_blog_switcher
_ORIGINAL_FIND_NEW_BLOG = bp.find_new_blog
_INSTALLED = False


def _escape(page) -> None:
    try:
        page.keyboard.press("Escape")
    except Exception:
        pass


def ensure_new_blog_available_resilient(page, *, attempts: int = 6) -> bool:
    """Tenta detectar 'Novo blog...' após o carregamento assíncrono do menu.

    Nenhum dado é preenchido e nenhuma criação é iniciada.
    """
    for attempt in range(1, attempts + 1):
        try:
            _ORIGINAL_OPEN_BLOG_SWITCHER(page)
            # O Blogger atual pode materializar as options depois da animação.
            page.wait_for_timeout(500 + attempt * 300)
            control = _ORIGINAL_FIND_NEW_BLOG(page)
            if control is not None:
                return True
        except Exception:
            # O retry continua fail-closed: não executa clique de criação.
            pass
        finally:
            _escape(page)
        page.wait_for_timeout(300 + attempt * 150)
    return False


def click_new_blog_resilient(page, *, attempts: int = 6) -> None:
    """Abre o diálogo de novo blog com retry apenas antes de preencher dados."""
    for attempt in range(1, attempts + 1):
        try:
            _ORIGINAL_OPEN_BLOG_SWITCHER(page)
            page.wait_for_timeout(500 + attempt * 300)
            control = _ORIGINAL_FIND_NEW_BLOG(page)
            if control is None:
                _escape(page)
                page.wait_for_timeout(300 + attempt * 150)
                continue

            # Clicar em "Novo blog..." apenas abre o formulário; não cria blog.
            control.evaluate("el => el.click()")
            page.wait_for_timeout(900 + attempt * 250)

            if bp._visible_field(page, bp.TITLE_FIELD_SELECTORS) is not None:
                return

            # Se a opção foi acionada mas o formulário não apareceu, não seguimos
            # para preenchimento nem SALVAR. Tentamos novamente somente a abertura.
            _escape(page)
            page.wait_for_timeout(350)
        except Exception:
            _escape(page)
            page.wait_for_timeout(300 + attempt * 150)

    raise bp.SafeAutomationError(
        'O comando "Novo blog..." não ficou utilizável após tentativas controladas. '
        "Nenhuma criação foi iniciada."
    )


def install() -> None:
    global _INSTALLED
    if _INSTALLED:
        return
    bp.ensure_new_blog_available = ensure_new_blog_available_resilient
    bp.click_new_blog = click_new_blog_resilient
    _INSTALLED = True
