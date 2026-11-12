#!/usr/bin/env python3
"""V31 LAB: resume an interrupted new-blog provision exactly once.

NO generic authorization, NO Blogger API calls, NO blog creation.
The active V31 Runner must supply bound SEO/theme/public-readback helpers.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from urllib.parse import urlsplit

CONFIRM = "RESUME BLOG V31"
PARTIAL = "PROVISION_V31_PARTIAL_STOP"
AWAIT_THEME = "SETTINGS_VALIDATED_AWAIT_THEME"


class HandoffBlocked(RuntimeError):
    pass


def check(ok: bool, reason: str) -> None:
    if not ok:
        raise HandoffBlocked(reason)


def strict_target(blog_id: str, title: str, url: str) -> str:
    check(isinstance(blog_id, str) and bool(re.fullmatch(r"[0-9]{6,24}", blog_id)),
          "BLOG_ID_INVALID")
    check(isinstance(title, str) and title.strip() == title and 1 <= len(title) <= 100,
          "BLOG_TITLE_INVALID")
    check(isinstance(url, str) and 12 <= len(url) <= 300, "BLOG_URL_INVALID")
    parsed = urlsplit(url)
    check(parsed.scheme == "https" and parsed.port in (None, 443)
          and not parsed.username and not parsed.password and not parsed.query
          and not parsed.fragment and parsed.path in ("", "/"), "BLOG_URL_NOT_CANONICAL")
    host = parsed.hostname or ""
    check(bool(re.fullmatch(
          r"[a-z0-9](?:[a-z0-9-]{1,61}[a-z0-9])?\.blogspot\.com", host)),
          "BLOG_HOST_INVALID")
    return host.removesuffix(".blogspot.com")


def pinned_checkpoint(value: object, *, blog_id: str, title: str, url: str) -> dict:
    address = strict_target(blog_id, title, url)
    check(isinstance(value, dict), "CHECKPOINT_INVALID")
    cp = value
    check(cp.get("schema") == "v31-new-blog-checkpoint/v1", "CHECKPOINT_SCHEMA_INVALID")
    check(cp.get("created") is True and cp.get("blog_id") == blog_id
          and cp.get("title") == title and cp.get("blog_url") == url
          and cp.get("address") == address, "CHECKPOINT_TARGET_MISMATCH")
    check(isinstance(cp.get("steps"), list)
          and "CREATE_BLOG_VALIDATED" in cp["steps"], "CHECKPOINT_CREATE_NOT_PROVEN")
    check(cp.get("status") == PARTIAL, "CHECKPOINT_NOT_RESUMABLE")
    check(cp.get("theme_install_started") is False
          and cp.get("theme_validated") is not True, "THEME_ATTEMPTED_NO_RETRY")
    check(cp.get("resume_attempted") is not True, "RESUME_ALREADY_ATTEMPTED")
    return cp


def public_title_check(body: str, title: str) -> None:
    check(isinstance(body, str) and len(body) > 600, "PUBLIC_READBACK_MISSING")
    check(title.casefold() in unescape(body).casefold(), "PUBLIC_TITLE_MISMATCH")


def resume_exact(*, blog_id: str, title: str, url: str,
                 description: str, search_description: str,
                 timezone_text: str, confirm: str,
                 root: Path, save, settings_apply, theme_adopt, theme_paths,
                 public_readback, settings_confirmation: str,
                 theme_confirmation: str) -> dict:
    """Single resume bound to durable checkpoint. No implicit installation.

    The theme installer must independently re-check authorization and latch.
    When in doubt, preserve the partial state; never retry automatically.
    """
    check(confirm == CONFIRM, "RESUME_CONFIRMATION_REQUIRED")
    address = strict_target(blog_id, title, url)
    root = Path(root).resolve()
    cp_path = root / "logs" / "provisioning" / "v31" / (address + ".json")
    check(cp_path.parent.resolve().is_relative_to(root), "CHECKPOINT_PATH_INVALID")
    check(cp_path.is_file() and not cp_path.is_symlink(), "CHECKPOINT_NOT_FOUND")
    cp = pinned_checkpoint(json.loads(cp_path.read_text(encoding="utf8")),
                           blog_id=blog_id, title=title, url=url)
    paths = theme_paths(blog_id)
    check(isinstance(paths, dict) and all(k in paths for k in
          ("latch", "result", "preflight")), "THEME_PATHS_INVALID")
    check(not any(paths[k].exists() for k in ("latch", "result")),
          "THEME_LATCH_OR_RESULT_EXISTS")
    check(not paths["preflight"].exists(), "THEME_PREFLIGHT_EXISTS")
    status, body = public_readback(url)
    check(status == 200, "PUBLIC_HTTP_NOT_200")
    public_title_check(body, title)
    check("V31_R52" not in body and "V31_R56_STORE_AUTO_START" not in body,
          "THEME_ALREADY_PRESENT_REVIEW_REQUIRED")

    cp = dict(cp)
    cp.update(status="RESUME_SETTINGS_IN_PROGRESS", resume_attempted=True,
              resume_started_at=datetime.now(timezone.utc).isoformat())
    save(cp_path, cp)
    try:
        result = settings_apply(blog_id, description, search_description,
                                confirm=settings_confirmation, timezone=timezone_text)
        check(isinstance(result, dict)
              and result.get("status") == "SETTINGS_PROFILE_VALIDATED"
              and str(result.get("blog_id")) == blog_id,
              "RESUME_SETTINGS_NOT_VALIDATED")
        cp.update(status=AWAIT_THEME, settings_validated=True,
                  theme_authorization={
                      "scope": "V31_R52_THEME_ONESHOT",
                      "blog_id": blog_id,
                      "blog_title": title,
                      "blog_url": url,
                      "origin": "RECOVERED_EXACT_CREATION_CHECKPOINT",
                      "approved_at": datetime.now(timezone.utc).isoformat(),
                  })
        if "SETTINGS_PROFILE_VALIDATED" not in cp["steps"]:
            cp["steps"].append("SETTINGS_PROFILE_VALIDATED")
        save(cp_path, cp)
        adopted = theme_adopt(blog_id, title, url, confirm=theme_confirmation)
        check(isinstance(adopted, dict)
              and adopted.get("status") == "V31_R52_APPLIED_AND_PUBLICLY_VALIDATED"
              and str(adopted.get("blog_id")) == blog_id,
              "RESUME_THEME_NOT_VALIDATED")
        cp.update(status="V31_THEME_VALIDATED_AWAIT_PAGES",
                  theme_install_started=True, theme_validated=True,
                  theme=adopted)
        if "V31_R52_APPLIED_AND_PUBLICLY_VALIDATED" not in cp["steps"]:
            cp["steps"].append("V31_R52_APPLIED_AND_PUBLICLY_VALIDATED")
        save(cp_path, cp)
        return {"status": "BLOGGER_NEW_BLOG_V31_CORE_RESUMED",
                "blog_id": blog_id, "blog_title": title, "blog_url": url,
                "settings_validated": True, "theme_validated": True,
                "publication_status": "NOT_PUBLISHED",
                "store_population_required": True, "checkpoint": str(cp_path)}
    except Exception:
        cp.update(status=PARTIAL, error_type="ResumeInterrupted")
        save(cp_path, cp)
        raise HandoffBlocked("RESUME_STOPPED_REVIEW_CHECKPOINT_AND_PUBLIC_SITE") from None
