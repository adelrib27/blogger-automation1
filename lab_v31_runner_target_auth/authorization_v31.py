"""C51 LAB: dynamic, fail-closed authorization for a Blogger theme target.

The V31 Runner currently rejects newly created blogs due to a fixed list
of three IDs. This adapter proposes a SAFE replacement for the allowlist,
but it MUST be wired into the actual Windows service only after reviewing
local_service_v31.py. Merely merging this file does not modify the Runner.

TRUST BOUNDARY: inventory MUST come from the already-authenticated Blogger
account via the Runner's own session/account verification, never from the
request JSON. active_panel_url MUST come from the connected Chrome page,
never from a caller-provided URL.

The function never installs a theme, creates a blog or changes credentials.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Mapping, Sequence
from urllib.parse import urlparse
from unicodedata import normalize

_ID = re.compile(r"^[0-9]{8,22}$")
_PANEL = re.compile(r"^/blog/(?:posts|pages|settings|themes?|layout)/([0-9]+)(?:/)?$", re.I)


class TargetAuthorizationError(ValueError):
    """Error reason deliberately excludes browser state and source data."""


@dataclass(frozen=True)
class AuthorizedTarget:
    blog_id: str
    title: str
    url: str
    source: str = "VERIFIED_AUTHENTICATED_BLOGGER_INVENTORY"


def _title(value: str) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > 100:
        raise TargetAuthorizationError("invalid_blog_title")
    return normalize("NFC", " ".join(value.split()))


def _blog_id(value: str) -> str:
    if not isinstance(value, str) or not _ID.fullmatch(value):
        raise TargetAuthorizationError("invalid_blog_id")
    return value


def _public_blog_url(value: str) -> str:
    if not isinstance(value, str) or len(value) > 300:
        raise TargetAuthorizationError("invalid_blog_url")
    p = urlparse(value)
    if (p.scheme != "https" or not p.hostname or p.username or
        p.password or p.port is not None or p.params or p.query or
        p.fragment or p.path not in ("", "/")):
        raise TargetAuthorizationError("invalid_blog_url")
    host=p.hostname.lower().rstrip(".")
    # Blogs may use a verified custom domain; the account inventory
    # still needs to confirm exactly the same hostname.
    if ("." not in host or host == "localhost" or
        host.endswith(".localhost") or
        any(ord(x)<33 for x in host) or
        re.fullmatch(r"[0-9.]+",host)):
        raise TargetAuthorizationError("invalid_blog_host")
    return "https://" + host + "/"


def _panel_blog_id(value: str) -> str:
    if not isinstance(value,str):
        raise TargetAuthorizationError("invalid_active_blogger_page")
    p=urlparse(value)
    if (p.scheme != "https" or p.hostname not in (
            "draft.blogger.com","www.blogger.com","blogger.com") or
        p.username or p.password or p.port is not None):
        raise TargetAuthorizationError("invalid_active_blogger_page")
    m=_PANEL.fullmatch(p.path)
    if not m:
        raise TargetAuthorizationError("invalid_active_blogger_page")
    return m.group(1)


def authorize_theme_target(*, expected_blog_id: str, expected_title: str,
                           expected_url: str,
                           authenticated_account_inventory: Sequence[Mapping],
                           observed_active_panel_url: str) -> AuthorizedTarget:
    """Authorize *by currently verified ownership*, not a hardcoded blog-ID list.

    Fail closed for unavailable/untrusted inventory, mismatched blog ID/title
    or URL, duplicate/conflicting inventory entries, and wrong active tab.
    The handler must construct inventory from the authenticated Blogger session
    and active_panel_url from CDP AFTER verifying the current profile.
    """
    bid=_blog_id(expected_blog_id)
    title=_title(expected_title)
    url=_public_blog_url(expected_url)
    if _panel_blog_id(observed_active_panel_url) != bid:
        raise TargetAuthorizationError("active_panel_blog_mismatch")
    if (not isinstance(authenticated_account_inventory,(list,tuple)) or
        len(authenticated_account_inventory)>1000):
        raise TargetAuthorizationError("authenticated_inventory_unavailable")
    matched=[]
    for row in authenticated_account_inventory:
        if not isinstance(row,Mapping):
            raise TargetAuthorizationError("authenticated_inventory_invalid")
        if row.get("id")==bid:
            matched.append(row)
    if len(matched)!=1:
        raise TargetAuthorizationError("blog_not_uniquely_owned")
    row=matched[0]
    try:
        recorded_id=_blog_id(row.get("id"))
        recorded_title=_title(row.get("name") or row.get("title"))
        recorded_url=_public_blog_url(row.get("url"))
    except (TargetAuthorizationError,ValueError,TypeError):
        raise TargetAuthorizationError("authenticated_blog_identity_invalid") from None
    if recorded_id!=bid or recorded_title!=title or recorded_url!=url:
        raise TargetAuthorizationError("owned_blog_identity_mismatch")
    return AuthorizedTarget(blog_id=bid,title=title,url=url)
