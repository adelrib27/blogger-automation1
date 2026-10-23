#!/usr/bin/env python3
from __future__ import annotations

import os

import store_auto as base
from post_target_proxy import BloggerPostTargetProxy

POST_ID = os.getenv("BLOGGER_STORE_POST_ID", "8867555367475283866").strip()
if not POST_ID:
    raise RuntimeError("BLOGGER_STORE_POST_ID ausente.")

_real_factory = base.criar_servico_blogger
base.PAGE_ID = POST_ID
base.criar_servico_blogger = lambda: BloggerPostTargetProxy(_real_factory())

if __name__ == "__main__":
    base.main()
