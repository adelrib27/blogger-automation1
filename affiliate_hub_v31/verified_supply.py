"""C89 — shared supply selectors for trusted factual drafts and conversion queue.

Only registered, moderation-approved, source-uncontested catalogue products.
This selector does not approve facts; verification still requires a live external
manufacturer/structured source before any READY/DRAFT.
"""
from __future__ import annotations

import json
from pathlib import Path

from .catalog import Catalog
from .manufacturer_review import models_for_catalog_title
from .source_policy_gate import source_safe_for_use
from .structured_review_source import catalog_gtin

PROFILE = Path(__file__).with_name("autonomous_review_sources.json")
GENERIC_ADVICE = [
    ["Meça o espaço disponível",
     "Confira o espaço para circulação e para abrir portas ou gavetas. Meça o local em mais de um ponto, considerando tomadas, rodapés e outros móveis antes de comparar as opções."],
    ["Compare as características informadas",
     "Verifique no anúncio a configuração exata da oferta, as fotos e as variações de acabamento. Não presuma que acessórios ou recursos exibidos em outras lojas façam parte deste anúncio."],
    ["Planeje o recebimento e a montagem",
     "Confira dimensões de passagem, transporte e instruções de montagem quando aplicáveis. Antes da compra, confirme diretamente com o vendedor quais peças e serviços acompanham a oferta."],
]


def route_allows_sku(catalog: Catalog, route: dict, key: str) -> bool:
    if (not isinstance(route, dict) or route.get("publish_enabled") is not False
            or not isinstance(key, str) or not key.startswith("shopee:")):
        return False
    row = catalog.db.execute("""
        SELECT p.moderation,t.status,t.category,t.niche
        FROM products p JOIN product_taxonomy t ON t.product_key=p.product_key
        WHERE p.product_key=?
    """, (key,)).fetchone()
    if not row or row[0] != "eligible" or row[1] != "matched":
        return False
    if not source_safe_for_use(catalog, key) or catalog.for_conversion(key) is None:
        return False
    if (row[2] + "/" + row[3]) in route.get("allowed_niches", []):
        return True
    paths = route.get("allowed_source_paths", [])
    if not paths:
        return False
    for path in paths:
        l1, l2 = path.split("/", 1)
        found = catalog.db.execute("""
            SELECT 1 FROM product_source_categories
            WHERE product_key=? AND status='matched' AND level1=? AND level2=?
        """, (key, l1, l2)).fetchone()
        if found:
            return True
    return False


def route_supply_keys(catalog: Catalog, route: dict, *, limit_per_path=100):
    if type(limit_per_path) is not int or not 1 <= limit_per_path <= 100:
        raise ValueError("verified_supply_limit_invalid")
    campaign = route["campaign"]
    seen = set()
    for pair in route.get("allowed_niches", []):
        category, niche = pair.split("/", 1)
        for row in catalog.select_products(campaign, limit=limit_per_path,
                                           category=category, niche=niche):
            key = row[0]
            if key not in seen and route_allows_sku(catalog, route, key):
                seen.add(key)
                yield key
    for pair in route.get("allowed_source_paths", []):
        a, b = pair.split("/", 1)
        for row in catalog.select_by_source_path(campaign, a, b,
                                                 limit=limit_per_path):
            key = row[0]
            if key not in seen and route_allows_sku(catalog, route, key):
                seen.add(key)
                yield key


def _safe_display_title(value):
    text = " ".join(str(value).split())
    if not text:
        raise ValueError("empty_catalog_product_title")
    if len(text) <= 75:
        return text
    return text[:75].rsplit(" ", 1)[0].rstrip(" -:,") or text[:64]


def dynamic_profile(catalog: Catalog, route: dict, policy: dict, sku: str):
    if not route_allows_sku(catalog, route, sku):
        return None
    row = catalog.db.execute(
        "SELECT title,description FROM products WHERE product_key=?", (sku,)
    ).fetchone()
    if not row:
        return None
    title, description = str(row[0]), str(row[1] or "")
    template = dict(policy.get("structured_template") or {})
    if not template.get("advice") or not template.get("cluster"):
        return None
    try:
        gtin = catalog_gtin(description)
    except ValueError:
        gtin = None
    name = _safe_display_title(title)
    if gtin and policy.get("trusted_structured_hosts"):
        return {**template, "name": name, "gtin": gtin, "query": gtin}
    manufacturer = models_for_catalog_title(title, site_key=route["site_key"])
    if not manufacturer:
        return None
    identity = manufacturer[0]
    kind = identity["kind"]
    profile = {**template, "name": name,
               "query": " ".join((identity["brand"], identity["model"], kind)),
               "catalog_identity": [identity["model"]],
               "manufacturer_identity": identity,
               "cluster": kind.replace(" ", "-").casefold()}
    # A manufacturer-confirmed desk should not link to a wardrobe article
    # merely because the first pilot was a wardrobe.
    if (template.get("cluster") != profile["cluster"] and
            template.get("cluster") not in (kind, kind.replace(" ", "-"))):
        profile.pop("related", None)
        profile.pop("related_wordpress_id", None)
        profile["advice"] = GENERIC_ADVICE
    return profile


def supply_profiles(catalog: Catalog, route: dict, policy: dict, *,
                    only_key: str | None = None):
    """Registered manual profiles first, then automatic catalog/model profiles.

    It is safe to return a missing-affiliate SKU here for the *conversion
    selector*. The independent verifier must still require campaign link.
    """
    static = policy.get("offers", {})
    keys = ([only_key] if only_key is not None else
            [*static, *route_supply_keys(catalog, route)])
    seen = set()
    for key in keys:
        if not isinstance(key, str) or key in seen:
            continue
        seen.add(key)
        if not route_allows_sku(catalog, route, key):
            continue
        if key in static:
            yield key, static[key]
        else:
            profile = dynamic_profile(catalog, route, policy, key)
            if profile:
                yield key, profile


def conversion_priority_keys(catalog: Catalog, route: dict, policy: dict):
    """Only IDs, never raw affiliate links or an unreviewed promotion flag."""
    campaign = route["campaign"]
    for key, profile in supply_profiles(catalog, route, policy):
        if not catalog.cached_link(key, campaign):
            yield key
