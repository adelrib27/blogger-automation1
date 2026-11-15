#!/usr/bin/env python3
"""Publish a validated Shopee catalog in the managed region of an existing Blogger page."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.request
from decimal import Decimal, DecimalException
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

from r57_rotate_store import WriterError, oauth_token
from shopee_r2_safe import GateError, load_commercial_profile, render_cards, trusted

START = "<!-- UNIVERSAL_V31_STORE_AUTO_START -->"
END = "<!-- UNIVERSAL_V31_STORE_AUTO_END -->"
PRELAUNCH = '<section class="v31-store-safe-prelaunch" data-publicacao-comercial="false">'
MAX_CONTENT = 180_000


def store_url(profile):
    return profile["target"]["url"].rstrip("/") + profile["store"]["page_path"]


def split_region(content):
    if content.count(START) != 1 or content.count(END) != 1:
        raise WriterError("STORE_MARKERS_MISSING_OR_AMBIGUOUS")
    before, _, rest = content.partition(START)
    middle, separator, after = rest.partition(END)
    if not separator:
        raise WriterError("STORE_MARKERS_OUT_OF_ORDER")
    return before, middle, after


def compose(content, cards, profile):
    before, middle, after = split_region(content)
    # Older provisioners put the temporary prelaunch text around an empty
    # region. Replace only that exact, explicitly recorded scaffold.
    if content.lstrip().startswith(PRELAUNCH):
        expected = profile["store"].get("empty_page_sha256")
        if middle.strip() or expected != hashlib.sha256(content.encode("utf-8")).hexdigest():
            raise WriterError("PRELAUNCH_CONTENT_CHANGED")
        before, after = "", ""
    updated = before + START + "\n" + cards + "\n" + END + after
    if len(updated.encode("utf-8")) > MAX_CONTENT:
        raise WriterError("STORE_CONTENT_TOO_LARGE")
    return updated


def catalog_products(profile, catalog):
    if (not isinstance(catalog, dict) or catalog.get("blog_id") != profile["target"]["blog_id"]
            or catalog.get("page_id") != profile["store"]["page_id"]
            or catalog.get("store_url") != store_url(profile)):
        raise WriterError("CATALOG_TARGET_MISMATCH")
    products = catalog.get("products")
    if not isinstance(products, list) or not products or catalog.get("count") != len(products):
        raise WriterError("CATALOG_EMPTY_OR_COUNT_MISMATCH")
    categories = {item["name"] for item in profile["store"]["categories"]}
    seen, represented = set(), set()
    normalized = []
    for product in products:
        if not isinstance(product, dict):
            raise WriterError("INVALID_CATALOG_PRODUCT")
        item_id = product.get("item_id")
        title = product.get("title")
        category = product.get("category")
        if (not isinstance(item_id, str) or not re.fullmatch(r"[0-9]{1,30}", item_id)
                or item_id in seen or not isinstance(title, str) or not title.strip()
                or not isinstance(category, str) or category not in categories
                or not isinstance(product.get("offer_link"), str)
                or not isinstance(product.get("image"), str)
                or not trusted(product["offer_link"], affiliate=True)
                or not trusted(product["image"], affiliate=False)):
            raise WriterError("INVALID_CATALOG_PRODUCT")
        try:
            price = Decimal(str(product["price"]))
            if not price.is_finite() or price <= 0:
                raise WriterError("INVALID_CATALOG_PRICE")
        except (KeyError, DecimalException):
            raise WriterError("INVALID_CATALOG_PRICE") from None
        seen.add(item_id)
        represented.add(category)
        normalized.append({"rating": None, **product})
    if represented != categories:
        raise WriterError("CATALOG_MISSING_CATEGORY")
    return normalized


class CardIds(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "article" and "ub-product-card" in (attrs.get("class") or "").split():
            self.ids.append(attrs.get("data-item-id"))


def card_ids(html):
    reader = CardIds()
    reader.feed(html)
    return reader.ids


class BloggerStorePage:
    def __init__(self, profile, token):
        self.blog_id = profile["target"]["blog_id"]
        self.page_id = profile["store"]["page_id"]
        self.url = store_url(profile)
        self.endpoint = f"https://www.googleapis.com/blogger/v3/blogs/{self.blog_id}/pages/{self.page_id}"
        self.token = token

    def request(self, content=None, *, title=None, etag=None):
        headers = {"Authorization": "Bearer " + self.token, "Accept": "application/json"}
        body = None
        if content is not None:
            headers["Content-Type"] = "application/json; charset=utf-8"
            if etag:
                headers["If-Match"] = etag
            body = json.dumps({"title": title, "content": content}, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(self.endpoint, data=body, headers=headers,
                                     method="GET" if body is None else "PUT")
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                page = json.loads(response.read(1_000_000))
                observed_etag = response.headers.get("ETag")
        except urllib.error.HTTPError as error:
            raise WriterError(f"BLOGGER_HTTP_{error.code}") from None
        except (OSError, ValueError):
            raise WriterError("BLOGGER_REQUEST_FAILED") from None
        if (not isinstance(page, dict) or str(page.get("id")) != self.page_id
                or not isinstance(page.get("blog"), dict)
                or str(page["blog"].get("id")) != self.blog_id or page.get("url") != self.url
                or str(page.get("title", "")).strip().casefold() != "loja"
                or str(page.get("status") or "live").casefold() != "live"
                or not page.get("published") or not isinstance(page.get("content"), str)):
            raise WriterError("BLOGGER_TARGET_NOT_VERIFIED")
        if observed_etag:
            page["etag"] = observed_etag
        return page

    def verify_public(self, expected):
        target = urlsplit(self.url)
        for delay in (0, 3, 8):
            if delay:
                time.sleep(delay)
            request = urllib.request.Request(f"{self.url}?v31verify={time.time_ns()}",
                                             headers={"Cache-Control": "no-cache"})
            try:
                with urllib.request.urlopen(request, timeout=15) as response:
                    actual = urlsplit(response.geturl())
                    if response.status != 200 or (actual.scheme, actual.netloc, actual.path) != (
                            target.scheme, target.netloc, target.path):
                        continue
                    content = response.read(2_000_000).decode("utf-8", errors="replace")
                _, region, _ = split_region(content)
                if card_ids(region) == expected:
                    return
            except (OSError, WriterError):
                continue
        raise WriterError("PUBLIC_READBACK_NOT_CONFIRMED")


def publish(profile, catalog, backend, output, *, apply=False):
    products = catalog_products(profile, catalog)
    cards = render_cards(products)
    expected = [p["item_id"] for category in dict.fromkeys(p["category"] for p in products)
                for p in products if p["category"] == category]
    original = backend.request()
    updated = compose(original["content"], cards, profile)
    _, region, _ = split_region(updated)
    if card_ids(region) != expected:
        raise WriterError("CANDIDATE_RENDER_MISMATCH")
    if not apply:
        return {"status": "SAFE_READY", "products": len(expected), "writes": 0}
    if updated == original["content"]:
        backend.verify_public(expected)
        return {"status": "NO_CHANGE", "products": len(expected), "writes": 0}
    latest = backend.request()
    if any(latest.get(k) != original.get(k) for k in ("etag", "updated", "title", "content")):
        raise WriterError("PAGE_CHANGED_BEFORE_WRITE")
    output.mkdir(parents=True, exist_ok=True)
    with (output / "before.json").open("x", encoding="utf-8") as backup:
        json.dump({"blog_id": profile["target"]["blog_id"], "url": store_url(profile),
                   "page": original}, backup, ensure_ascii=False)
    backend.request(updated, title=original["title"], etag=latest.get("etag"))
    after = backend.request()
    before_parts = split_region(updated)
    after_parts = split_region(after["content"])
    if before_parts[0] != after_parts[0] or before_parts[2] != after_parts[2] or card_ids(after_parts[1]) != expected:
        raise WriterError("BLOGGER_READBACK_NOT_CONFIRMED")
    backend.verify_public(expected)
    return {"status": "PUBLIC_PASS", "products": len(expected), "writes": 1}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", required=True, type=Path)
    parser.add_argument("--catalog", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    profile = load_commercial_profile(args.profile)
    scope = f'{profile["target"]["blog_id"]}:{profile["store"]["page_id"]}'
    if args.apply and os.getenv("BLOGGER_STORE_WRITE_TARGET") != scope:
        raise WriterError("BLOGGER_STORE_WRITE_TARGET_MISMATCH")
    catalog = json.loads(args.catalog.read_text(encoding="utf-8"))
    result = publish(profile, catalog, BloggerStorePage(profile, oauth_token()), args.out_dir, apply=args.apply)
    print(json.dumps(result))


if __name__ == "__main__":
    try:
        main()
    except (WriterError, GateError, OSError, ValueError) as error:
        # An ambiguous PUT is verified by readback, never replayed automatically.
        message = str(error) if isinstance(error, WriterError) else type(error).__name__
        print(json.dumps({"status": "STOPPED", "reason": message}))
        raise SystemExit(2) from None
