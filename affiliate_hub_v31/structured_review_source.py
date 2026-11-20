"""Discover objective facts using a catalog GTIN and trusted Product JSON-LD."""

import json
import re
from html.parser import HTMLParser

from .independent_review import IndependentReviewError

_CODES = ("gtin", "gtin8", "gtin12", "gtin13", "gtin14")
_MATERIALS = {"vidro", "polietileno", "aço inoxidável", "madeira", "alumínio", "cerâmica"}


def catalog_gtin(description):
    ns = set(re.findall(r"\b(?:ean|gtin)(?:-?(?:8|12|13|14))?\s*[:#]\s*(\d{8,14})\b",
                        description, flags=re.I))
    if len(ns) != 1:
        raise IndependentReviewError("trusted_catalog_gtin_missing_or_ambiguous")
    code = ns.pop()
    if len(code) not in (8, 12, 13, 14) or sum(
        int(value) * (1 if index % 2 == 0 else 3)
        for index, value in enumerate(reversed(code))
    ) % 10:
        raise IndependentReviewError("catalog_gtin_invalid")
    return code


class ProductMetadata(HTMLParser):
    def __init__(self):
        super().__init__()
        self.active = False
        self.parts = []
        self.documents = []

    def handle_starttag(self, tag, attrs):
        if tag == "script":
            self.active = dict(attrs).get("type") == "application/ld+json"
            self.parts = []

    def handle_data(self, value):
        if self.active:
            self.parts.append(value)

    def handle_endtag(self, tag):
        if tag == "script" and self.active:
            self.active = False
            try:
                self.documents.append(json.loads("".join(self.parts)))
            except (ValueError, RecursionError):
                pass


def _entities(value):
    pending = [value]
    for _ in range(200):
        if not pending:
            return
        item = pending.pop()
        if isinstance(item, list):
            pending.extend(item)
        elif isinstance(item, dict):
            if item.get("@type") in ("Product", "https://schema.org/Product"):
                yield item
            if "@graph" in item:
                pending.append(item["@graph"])
    raise IndependentReviewError("source_metadata_document_too_complex")


def gtin_facts(raw, gtin):
    scanner = ProductMetadata()
    scanner.feed(raw.decode("utf-8", errors="replace"))
    scanner.close()
    matches = []
    for document in scanner.documents:
        for product in _entities(document):
            values = {str(product[key]).strip() for key in _CODES if key in product}
            if values == {gtin}:
                matches.append(product)
    if not matches:
        raise IndependentReviewError("trusted_source_gtin_mismatch")
    material = {str(product.get("material", "")).casefold().strip() for product in matches}
    if len(material) != 1 or not material <= _MATERIALS:
        raise IndependentReviewError("structured_facts_insufficient_or_conflicting")
    value = material.pop()
    return [
        ("model_identifier", f"A ficha técnica identifica o produto pelo GTIN {gtin}.", gtin),
        ("material", f"O material informado na ficha técnica é {value}.", value),
    ]
