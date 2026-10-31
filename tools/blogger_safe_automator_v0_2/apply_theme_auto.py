#!/usr/bin/env python3
from __future__ import annotations

import apply_theme_safe as impl
from auto_blog_route import ensure_theme_page

# apply_theme_safe imports select_expected_theme_page into its own module namespace.
# Replace only that selector; all validated upload/backup/public-validation logic stays intact.
impl.select_expected_theme_page = ensure_theme_page


if __name__ == "__main__":
    raise SystemExit(impl.main())
