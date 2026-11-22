"""C89 — model-based objective evidence from pretrusted manufacturer product pages.

No AI or arbitrary search result can authorize a new domain or invent a SKU.
Discovery is independent of the article generator. Without identity + material
from one exact product page, this module fails closed.
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from urllib.parse import urlsplit

REGISTRY = Path(__file__).with_name("trusted_manufacturer_sources.json")

STOP = frozenset((
    "guarda","roupa","roupeiro","armario","casal","solteiro","cama","mesa",
    "escritorio","escrivaninha","gaveta","gavetas","porta","portas","movel",
    "moveis","decorativo","decorativa","decoracao","vaso","produto","kit",
    "pintura","estilo","moderno","premium","original","promo","oferta","frete",
    "branco","branca","preto","preta","marrom","bege","off","white","cinza",
    "altura","largura","profundidade","com","sem","para","dos","das","de",
    "do","da","em","cor","cores","casa","sala","quarto","canto","modelo",
    "cm","mdp","mdf","metal","ate","corredica","corredicas","puxador","puxadores",
    "estofado","estofada","poliester","jogo","peças","pecas","natural"
))

KINDS = (
    ("guarda-roupa", ("guarda roupa", "roupeiro")),
    ("cômoda", ("comoda",)),
    ("mesa", ("mesa", "escrivaninha")),
    ("sofá", ("sofa",)),
    ("vaso", ("vaso",)),
    ("armário", ("armario",)),
    ("cadeira", ("cadeira",)),
    ("estante", ("estante",)),
    ("rack", ("rack",)),
)
MATERIALS = {"mdp", "mdf", "madeira", "madeira macica",
             "polietileno", "polipropileno", "vidro", "ceramica",
             "aluminio", "aco inoxidavel", "aco", "ferro", "plastico"}
MATERIAL_PATTERN = re.compile(
    r"(?:estrutura em|fabricad[oa] em|produzid[oa] em|confeccionad[oa] em|"
    r"material(?: principal)?(?: informado)?(?: e| em| de)?|"
    r"compost[oa] por)\s+"
    r"(madeira macica|aco inoxidavel|mdp|mdf|madeira|polietileno|"
    r"polipropileno|vidro|ceramica|aluminio|aco|ferro|plastico)\b",
    re.I,
)
COUNT_PATTERN = re.compile(r"\b(\d{1,2})\s+(portas|gavetas)\b")


class ManufacturerEvidenceError(ValueError):
    pass


def plain(value):
    if not isinstance(value, str):
        return ""
    text = unicodedata.normalize("NFKD", value.casefold())
    text = "".join(c for c in text if not unicodedata.combining(c))
    return " ".join(re.findall(r"[a-z0-9]+", text))


def has_phrase(whole, phrase):
    return bool(phrase and (" " + plain(phrase) + " ") in (" " + plain(whole) + " "))


def product_kind(title):
    for name, alternatives in KINDS:
        if any(has_phrase(title, alt) for alt in alternatives):
            return name
    return None


def trusted_brands(site_key, *, registry_path=REGISTRY):
    payload = json.loads(Path(registry_path).read_text(encoding="utf-8"))
    if payload.get("schema") != "v31-trusted-manufacturer-registry-1":
        raise ManufacturerEvidenceError("manufacturer_registry_untrusted")
    data = payload.get("sites", {}).get(site_key, [])
    if not isinstance(data, list) or len(data) > 50:
        raise ManufacturerEvidenceError("manufacturer_sites_invalid")
    for item in data:
        if not isinstance(item, dict) or set(item) != {
            "brand", "aliases", "hosts", "product_path_prefix"
        }:
            raise ManufacturerEvidenceError("manufacturer_schema_invalid")
        hosts = item["hosts"]
        if (not isinstance(hosts, list) or not 1 <= len(hosts) <= 5
            or not all(isinstance(h, str) and
                       re.fullmatch(r"[a-z0-9][a-z0-9.-]{3,100}", h) and
                       ".." not in h for h in hosts)
            or not isinstance(item["aliases"], list)
            or not 1 <= len(item["aliases"]) <= 5
            or not all(isinstance(a, str) and len(plain(a)) >= 3
                       for a in item["aliases"])
            or not isinstance(item["brand"], str) or
            not isinstance(item["product_path_prefix"], str) or
            not item["product_path_prefix"].startswith("/") or
            "//" in item["product_path_prefix"]):
            raise ManufacturerEvidenceError("manufacturer_trust_invalid")
    return data


def models_for_catalog_title(title, *, site_key, registry_path=REGISTRY):
    """An unambiguous brand + model + category, never a guessed variant."""
    kind = product_kind(title)
    if not kind:
        return []
    items = [m for m in trusted_brands(site_key, registry_path=registry_path)
             if any(has_phrase(title, alias) for alias in m["aliases"])]
    if len(items) != 1:
        return []
    brand = items[0]
    brand_tokens = set(" ".join(plain(a) for a in brand["aliases"]).split())
    tokens = [w for w in plain(title).split()
              if w not in STOP and w not in brand_tokens and
              ((len(w) >= 5 and not w.isdecimal()) or
               (len(w) >= 3 and any(c.isdigit() for c in w)
                and any(c.isalpha() for c in w)))]
    tokens = list(dict.fromkeys(tokens))
    # A model token with letters+digits is less ambiguous than generic prose.
    tokens.sort(key=lambda w: (-(any(c.isdigit() for c in w) and
                                 any(c.isalpha() for c in w)), -len(w), w))
    return [{"brand": brand["brand"], "model": model, "kind": kind,
             "hosts": brand["hosts"],
             "product_path_prefix": brand["product_path_prefix"]}
            for model in tokens[:2]]


def source_page_allowed(url, identity):
    if not isinstance(url, str):
        return False
    try:
        p = urlsplit(url)
        if (p.scheme != "https" or p.hostname not in identity["hosts"] or
            p.username or p.password or p.port not in (None, 443) or
            p.query or p.fragment or not p.path.startswith(
                identity["product_path_prefix"])):
            return False
    except (ValueError, KeyError, TypeError):
        return False
    # A product page must identify the actual model, not a category/search page.
    model = plain(identity["model"]).replace(" ", "")
    slug = plain(p.path).replace(" ", "")
    return len(model) >= 3 and model in slug


def _count_map(text):
    return {kind: int(n) for n, kind in COUNT_PATTERN.findall(plain(text))}


def verify_manufacturer_markdown(*, identity, catalog_title, source_url,
                                 source_metadata, markdown):
    if not source_page_allowed(source_url, identity):
        raise ManufacturerEvidenceError("manufacturer_url_untrusted")
    if not isinstance(source_metadata, dict) or not isinstance(markdown, str):
        raise ManufacturerEvidenceError("manufacturer_source_missing")
    resolved = source_metadata.get("url") or source_metadata.get("sourceURL")
    if (not isinstance(resolved, str) or
            urlsplit(resolved).scheme != "https" or
            urlsplit(resolved).netloc != urlsplit(source_url).netloc or
            urlsplit(resolved).path != urlsplit(source_url).path or
            urlsplit(resolved).query or urlsplit(resolved).fragment):
        raise ManufacturerEvidenceError("manufacturer_source_redirected")
    header = source_metadata.get("title", "")
    model = identity["model"]
    kind = identity["kind"]
    if (not has_phrase(catalog_title, identity["brand"]) or
            not has_phrase(catalog_title, model) or
            product_kind(catalog_title) != kind or
            not has_phrase(header, model) or
            not has_phrase(header, identity["brand"]) or
            product_kind(header) != kind):
        raise ManufacturerEvidenceError("manufacturer_model_identity_mismatch")
    # First section only: product description, not footer/category suggestions.
    normalized = plain(markdown[:7500])
    model_pos = normalized.find(plain(model))
    if model_pos < 0 or model_pos > 2300:
        raise ManufacturerEvidenceError("manufacturer_product_heading_missing")
    excerpt = normalized[model_pos:model_pos + 1100]
    if not any(has_phrase(excerpt, alt) for name, alts in KINDS
               if name == kind for alt in alts):
        raise ManufacturerEvidenceError("manufacturer_product_type_missing")
    # Never approve a seller variant explicitly contradicted by manufacturer.
    seller_counts = _count_map(catalog_title)
    source_counts = _count_map(excerpt)
    if any(k in source_counts and source_counts[k] != v
           for k, v in seller_counts.items()):
        raise ManufacturerEvidenceError("manufacturer_variant_conflict")
    material_matches = list(MATERIAL_PATTERN.finditer(excerpt))
    materials = {m.group(1) for m in material_matches}
    # Não transformar "estrutura em MDF e MDP" em alegação exclusiva MDF.
    for match in material_matches:
        suffix = excerpt[match.end():match.end()+30]
        another = re.match(
            r"\s+(?:e|/|mais)\s+(madeira macica|aco inoxidavel|"
            r"mdp|mdf|madeira|polietileno|polipropileno|vidro|"
            r"ceramica|aluminio|aco|ferro|plastico)\b", suffix)
        if another:
            materials.add(another.group(1))
    if len(materials) != 1 or not materials <= MATERIALS:
        raise ManufacturerEvidenceError("manufacturer_material_unverified")
    material = materials.pop()
    display = material.upper() if material in ("mdp", "mdf") else material
    return [
        ("model_identifier", "O fabricante identifica o modelo como " +
         model.upper() + ".", model),
        ("material", "O fabricante informa material " + display + ".",
         material),
    ]
