from __future__ import annotations

from urllib.parse import urlparse


def _is_blogger_page(page) -> bool:
    try:
        host = (urlparse(page.url).hostname or "").lower()
        return host == "blogger.com" or host.endswith(".blogger.com")
    except Exception:
        return False


def select_active_blogger_page(context, fallback):
    """Prefer the foreground Blogger tab; otherwise use the most recently created Blogger tab.

    This avoids selecting the first stale Blogger tab when several Blogger tabs are open.
    The fallback is only used when no Blogger tab can be identified safely.
    """
    blogger_pages = [page for page in context.pages if _is_blogger_page(page)]

    visible_pages = []
    for page in blogger_pages:
        try:
            if page.evaluate("() => document.visibilityState") == "visible":
                visible_pages.append(page)
        except Exception:
            continue

    if visible_pages:
        return visible_pages[-1]
    if blogger_pages:
        return blogger_pages[-1]
    return fallback(context)
