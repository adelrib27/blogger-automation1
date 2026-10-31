from __future__ import annotations

from urllib.parse import urlparse


def is_blogger_url(value: str) -> bool:
    """Return True only for Blogger dashboard origins.

    Keeps an already-open Blogger panel intact instead of navigating to Blogger home,
    which can switch the current blog to the account's default blog.
    """
    try:
        host = (urlparse(value or "").hostname or "").lower()
    except Exception:
        return False
    return host == "blogger.com" or host.endswith(".blogger.com")
