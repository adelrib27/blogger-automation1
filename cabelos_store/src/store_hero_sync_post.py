#!/usr/bin/env python3
from __future__ import annotations
import os
import store_hero_sync as base
from post_target_proxy import BloggerPostTargetProxy
POST_ID=os.getenv('BLOGGER_STORE_POST_ID','2897872370214992246').strip()
if not POST_ID: raise RuntimeError('BLOGGER_STORE_POST_ID ausente.')
_real=base.criar_servico_blogger; base.PAGE_ID=POST_ID; base.criar_servico_blogger=lambda: BloggerPostTargetProxy(_real())
if __name__=='__main__': base.main()
