#!/usr/bin/env python3
from __future__ import annotations

import re

import browser_provision as bp
from blogger_panel_route_guard import extract_panel_blog_id
from blogger_session_guard import is_blogger_url

BLOG_ID_RE = re.compile(r"^[0-9]+$")


def _validate_blog_id(value: str) -> str:
    blog_id = str(value or "").strip()
    if not BLOG_ID_RE.fullmatch(blog_id):
        raise bp.SafeAutomationError("Blog ID esperado inválido.")
    return blog_id


def _route_url(route: str, blog_id: str) -> str:
    route = str(route or "").strip().strip("/")
    if route not in {"themes", "settings", "posts", "pages", "layout"}:
        raise bp.SafeAutomationError(f"Rota Blogger não permitida: {route!r}.")
    return f"https://draft.blogger.com/blog/{route}/{blog_id}"


def _matches(page, route: str, blog_id: str) -> bool:
    try:
        if not is_blogger_url(page.url):
            return False
        if extract_panel_blog_id(page.url) != blog_id:
            return False
        return f"/blog/{route}/{blog_id}" in (page.url or "")
    except Exception:
        return False


def ensure_expected_route(context, expected_blog_id: str, route: str):
    """Return the exact Blogger panel route for a Blog ID, opening it when needed.

    Existing tabs are reused only when both route and Blog ID match exactly.
    Otherwise a new tab is opened directly on the requested official Blogger URL.
    The final URL is validated again before the caller may continue.
    """
    blog_id = _validate_blog_id(expected_blog_id)
    target_url = _route_url(route, blog_id)

    candidates = [page for page in context.pages if _matches(page, route, blog_id)]
    if candidates:
        page = candidates[-1]
    else:
        try:
            page = context.new_page()
        except Exception as exc:
            raise bp.SafeAutomationError(
                "Não foi possível abrir uma nova aba no Chrome conectado."
            ) from exc
        try:
            page.goto(target_url, wait_until="domcontentloaded", timeout=20_000)
        except Exception as exc:
            raise bp.SafeAutomationError(
                f"Não foi possível abrir a rota Blogger esperada: /blog/{route}/{blog_id}."
            ) from exc

    # Blogger can update the SPA route shortly after DOMContentLoaded.
    for _ in range(40):
        if _matches(page, route, blog_id):
            try:
                page.bring_to_front()
            except Exception:
                pass
            return page
        page.wait_for_timeout(250)

    final_url = getattr(page, "url", "") or ""
    final_id = extract_panel_blog_id(final_url)
    if not is_blogger_url(final_url):
        raise bp.SafeAutomationError(
            "A sessão do Blogger não ficou disponível no Chrome conectado. "
            "Abra/login no Blogger uma vez nesse perfil e tente novamente."
        )
    raise bp.SafeAutomationError(
        "Blogger abriu uma rota diferente da solicitada; operação bloqueada. "
        f"atual_id={final_id!r}, esperado_id={blog_id!r}, rota={route!r}."
    )


def ensure_theme_page(context, expected_blog_id: str):
    return ensure_expected_route(context, expected_blog_id, "themes")


def ensure_settings_page(context, expected_blog_id: str):
    return ensure_expected_route(context, expected_blog_id, "settings")
