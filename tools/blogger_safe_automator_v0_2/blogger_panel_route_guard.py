#!/usr/bin/env python3
from __future__ import annotations

import re

BLOG_PANEL_ID_RE = re.compile(
    r"/blog/(?:posts|pages|settings|themes?|layout)/(\d+)(?:[/?#]|$)",
    re.I,
)


def extract_panel_blog_id(url: str) -> str | None:
    match = BLOG_PANEL_ID_RE.search(url or "")
    return match.group(1) if match else None
