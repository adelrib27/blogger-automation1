#!/usr/bin/env python3
from __future__ import annotations

import re

import browser_provision as bp

_ORIGINAL_EXTRACT_CURRENT_BLOG_ID = bp.extract_current_blog_id
_THEMES_URL_RE = re.compile(r"/blog/themes/(\d+)(?:[/?#]|$)", re.I)


def extract_current_blog_id_resilient(page):
    """Compatibilidade v0.7 para a rota real /blog/themes/<id> do Blogger.

    O parser histórico reconhece /theme/<id> no singular, enquanto o painel atual
    também usa /themes/<id>. Preserva o comportamento original para todas as demais
    rotas e só aplica o fallback quando ele não encontrou um Blog ID.
    """
    current = _ORIGINAL_EXTRACT_CURRENT_BLOG_ID(page)
    if current:
        return current

    try:
        url = str(page.url or "")
    except Exception:
        return current

    match = _THEMES_URL_RE.search(url)
    if match:
        return match.group(1)
    return current


def install() -> None:
    bp.extract_current_blog_id = extract_current_blog_id_resilient
