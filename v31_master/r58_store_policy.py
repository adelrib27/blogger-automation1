#!/usr/bin/env python3
"""Isolated R57 store policy. Read-only with respect to local R49 files.

The legacy R49 boot pins policy/acceptance/registry SHA256. NEVER update those
files. This policy is used only by an independent, single-target store workflow.
"""
from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlsplit
from html import unescape

BLOG_ID = "5999019959932264006"
PAGE_ID = "7680030566642713590"
STORE_URL = "https://lab-v31-r58-shopee-e2e-20261106.blogspot.com/p/loja.html"
START = "<!-- V31_R58_STORE_AUTO_START -->"
END = "<!-- V31_R58_STORE_AUTO_END -->"
AFF = 'rel="nofollow sponsored noopener"'
SCHEMA = "blogger-v31-r58-store-state/v1"
EXPECTED_CATS = ["Casa e Organização", "Cozinha", "Tecnologia", "Utilidades"]

class GuardError(RuntimeError):
    pass

def fail(reason: str) -> None:
    raise GuardError(reason)

def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def ids(html: str) -> list[str]:
    return re.findall(r'\bdata-item-id="([0-9]{6,18})"', html)

def validate_store_html(content: str) -> dict:
    if not isinstance(content, str) or len(content) > 180_000:
        fail("STORE_SIZE_INVALID")
    if content.count(START) != 1 or content.count(END) != 1 or content.index(START) > content.index(END):
        fail("STORE_MARKER_INVALID")
    region = content[content.index(START):content.index(END) + len(END)]
    if re.search(r'<(?:script|iframe|object|embed|form)\b', region, re.I):
        fail("STORE_ACTIVE_TAG_FORBIDDEN")
    item_ids = ids(region)
    if len(item_ids) != 16 or len(set(item_ids)) != 16:
        fail("STORE_PRODUCTS_NOT_16_UNIQUE")
    if region.count('class="ub-product-card"') != 16:
        fail("STORE_CARDS_NOT_16")
    if region.count(AFF) != 32:
        fail("STORE_AFFILIATES_NOT_32")
    if len(re.findall(r'<img\b', region, re.I)) != 16:
        fail("STORE_IMAGES_NOT_16")
    if region.count('class="ub-store-category"') != 4:
        fail("STORE_CATEGORIES_NOT_4")
    for cat in EXPECTED_CATS:
        if f"<h3>{cat}</h3>" not in unescape(region):
            fail("STORE_CATEGORY_MISMATCH")
    for url in re.findall(r'<a\b[^>]*\bhref="([^"]+)"', region, re.I):
        p = urlsplit(unescape(url))
        if p.scheme != "https" or not p.hostname or not (
                p.hostname == "s.shopee.com.br" or p.hostname.endswith(".shopee.com.br")
                or p.hostname == "shope.ee"):
            fail("AFFILIATE_URL_NOT_WHITELISTED")
    return {"items":item_ids, "sha256": sha256(region), "cards":16, "affiliate_links":32}

def validate_state(s: dict) -> dict:
    if s.get("schema") != SCHEMA or s.get("blog_id") != BLOG_ID or s.get("page_id") != PAGE_ID or s.get("url") != STORE_URL:
        fail("STATE_TARGET_INVALID")
    if s.get("card_count") != 16 or s.get("affiliate_link_count") != 32:
        fail("STATE_COUNTS_INVALID")
    if len(s.get("item_ids") or []) != 16 or len(set(s["item_ids"])) != 16 or not all(x.isdigit() for x in s["item_ids"]):
        fail("STATE_IDS_INVALID")
    if not re.fullmatch(r"[0-9a-f]{64}", str(s.get("html_sha256",""))):
        fail("STATE_HASH_INVALID")
    guards = s.get("guards") or {}
    if not all(guards.get(k) is True for k in (
        "blogger_page_exact", "no_runner_files_write", "no_theme_install",
        "no_new_post_or_page", "public_pass_before_state_update")):
        fail("STATE_GUARDS_INVALID")
    return s

def decision(current: str, candidate: str, state: dict, *, allow_write: bool = False) -> dict:
    validate_state(state)
    old = validate_store_html(current)
    new = validate_store_html(candidate)
    if old["sha256"] != state["html_sha256"] or old["items"] != state["item_ids"]:
        fail("LIVE_PAGE_DIFFERS_FROM_PERSISTED_STATE")
    if current.count(START) != 1 or current.count(END) != 1:
        fail("CURRENT_PAGE_STRUCTURE_INVALID")
    if old["sha256"] == new["sha256"]:
        return {"status":"R58_NO_CHANGE", "writes":False, "new_item_count":0}
    new_count = len(set(new["items"]) - set(old["items"]))
    if new_count < 1:
        # Changes in price/links can be useful but do not count as rotation.
        # Rather than write silently, require an explicit review.
        fail("NO_NEW_ITEMS_REQUIRE_REVIEW")
    if not allow_write or s_bool(state.get("allow_auto_write")) is not True:
        return {"status":"R58_CANDIDATE_SAFE_NOT_AUTHORIZED", "writes":False, "new_item_count":new_count}
    return {"status":"R58_CANDIDATE_READY_ONE_WRITE", "writes":False, "new_item_count":new_count}

def s_bool(value: object) -> bool:
    return value is True

def replace_managed_region(current: str, candidate: str) -> str:
    validate_store_html(current)
    validate_store_html(candidate)
    a=current.index(START)
    b=current.index(END)+len(END)
    if candidate.startswith(START) and candidate.endswith(END):
        replacement=candidate
    else:
        replacement=candidate[candidate.index(START):candidate.index(END)+len(END)]
    return current[:a]+replacement+current[b:]

def make_state(previous: dict, content: str) -> dict:
    v=validate_store_html(content)
    new=dict(validate_state(previous))
    new.update(item_ids=v["items"],html_sha256=v["sha256"],card_count=16,affiliate_link_count=32)
    return new

def main() -> int:
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--state", type=Path, required=True)
    p.add_argument("--current", type=Path, required=True)
    p.add_argument("--candidate", type=Path, required=True)
    x=p.parse_args()
    try:
        out=decision(x.current.read_text(encoding="utf-8"),
                     x.candidate.read_text(encoding="utf-8"),
                     json.loads(x.state.read_text(encoding="utf-8")))
        print(json.dumps(out, ensure_ascii=False))
        return 0
    except (GuardError, OSError, ValueError) as e:
        print(json.dumps({"status":"R58_FAIL_CLOSED","reason":str(e),"writes":False},ensure_ascii=False))
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
