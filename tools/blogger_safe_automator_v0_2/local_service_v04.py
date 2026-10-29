#!/usr/bin/env python3
from __future__ import annotations

import browser_provision as bp
from active_blogger_page import select_active_blogger_page


_original_select_page = bp.select_page


def _select_page(context):
    return select_active_blogger_page(context, _original_select_page)


bp.select_page = _select_page

import local_service  # noqa: E402  (must import after patching browser_provision)


if __name__ == "__main__":
    raise SystemExit(local_service.main())
