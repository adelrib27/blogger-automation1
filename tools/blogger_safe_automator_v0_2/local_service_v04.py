#!/usr/bin/env python3
from __future__ import annotations

import browser_provision as bp
from active_blogger_page import select_active_blogger_page
from blogger_session_guard import is_blogger_url


_original_select_page = bp.select_page
_original_require_blogger_session = bp.require_blogger_session


def _select_page(context):
    return select_active_blogger_page(context, _original_select_page)


def _require_blogger_session(page):
    # If the user already opened a Blogger panel, preserve that exact blog.
    # Navigating to Blogger home can silently switch to the account's default blog.
    if is_blogger_url(page.url):
        return None
    return _original_require_blogger_session(page)


bp.select_page = _select_page
bp.require_blogger_session = _require_blogger_session

# Patch only the dialog-targeting layer used by settings_profile. This keeps the
# validated settings logic intact while preventing Blogger's navigation drawer
# from being mistaken for the active edit dialog.
import configure_core_settings as cfg  # noqa: E402
import settings_dialog_guard as sdg  # noqa: E402

cfg.set_dialog_text = sdg.set_dialog_text
cfg.set_timezone = sdg.set_timezone

import local_service  # noqa: E402  (must import after patching browser_provision/settings)


if __name__ == "__main__":
    raise SystemExit(local_service.main())
