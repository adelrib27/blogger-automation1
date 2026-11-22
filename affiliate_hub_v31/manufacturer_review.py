"""C89 — model-based objective evidence from pretrusted manufacturer product pages.

No AI or arbitrary search result can authorize a new domain or invent a SKU.
Discovery is independent of the article generator. Only identity plus objectively
verified material and/or exact features from one official page can pass.
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
    "estofado","estofada","poliester","jogo","peças","pecas","natural",
    "comoda","multiuso","lavanderia","espelho","espelhos","grafite","grafitte",
    "jatoba","atacama","nicho","nichos","ripada","ripadas",
    "amendola","touch","ambiente","sapateira","sapateiro","pes",
    "rodizios","opcional","opcionais","c","s","p","inox"
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
COUNT_PATTERN = re.compile(r"\b(\d{1,2})\s+(?:(?:amplas?|internas?|externas?|ripadas?)\s+)?(portas?|gavetas?)\b")


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
    # Seller titles usually put the actual model before finishing/color terms.
    # Length sorting promoted "lavanderia", "espelho" and "grafitte" as models.
    if not tokens:
        return []
    codes = [w for w in tokens if any(c.isdigit() for c in w)
             and any(c.isalpha() for c in w)]
    chosen = codes[0] if codes else tokens[0]
    raw = unicodedata.normalize("NFKD", title.casefold())
    raw = "".join(c for c in raw if not unicodedata.combining(c))
    variant = re.search(r"\b" + re.escape(chosen) +
                        r"\s+(\d{1,2})[.,](\d{1,2})\b", raw)
    identity = {"brand": brand["brand"], "model": chosen, "kind": kind,
                "hosts": brand["hosts"],
                "product_path_prefix": brand["product_path_prefix"]}
    if variant:
        identity["variant"] = variant.group(1) + "." + variant.group(2)
    return [identity]


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
    if len(model) < 3 or model not in slug:
        return False
    variant = identity.get("variant")
    return not variant or has_phrase(p.path, model + " " + variant)


def _count_map(text):
    found = {}
    for number, label in COUNT_PATTERN.findall(plain(text)):
        kind = "portas" if label.startswith("porta") else "gavetas"
        found.setdefault(kind, set()).add(int(number))
    return found


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
            product_kind(header) != kind or
            identity.get("variant") and not has_phrase(
                header, model + " " + identity["variant"])):
        raise ManufacturerEvidenceError("manufacturer_model_identity_mismatch")
    # First section only: product description, not footer/category suggestions.
    normalized = plain(markdown[:7500])
    model_pos = normalized.find(plain(model))
    if model_pos < 0 or model_pos > 2300:
        raise ManufacturerEvidenceError("manufacturer_product_heading_missing")
    excerpt = normalized[max(0, model_pos - 100):model_pos + 1100]
    if not any(has_phrase(excerpt, alt) for name, alts in KINDS
               if name == kind for alt in alts):
        raise ManufacturerEvidenceError("manufacturer_product_type_missing")
    # Exact seller variant quantities must be demonstrable on the official
    # page. A subcomponent (e.g. two MDF doors of a six-door wardrobe)
    # cannot override the product headline's six doors.
    seller_counts = _count_map(catalog_title)
    source_counts = _count_map(excerpt)
    headline_counts = _count_map(" ".join(markdown.splitlines()[:5]))
    feature_claims = []
    for feature, numbers in seller_counts.items():
        if len(numbers) != 1:
            raise ManufacturerEvidenceError("manufacturer_variant_conflict")
        expected = next(iter(numbers))
        found = source_counts.get(feature, set())
        if expected not in found:
            raise ManufacturerEvidenceError("manufacturer_variant_conflict")
        extra = found - {expected}
        if extra:
            # Other quantities must be explicitly identified as a subset
            # (e.g. two MDF doors OF a six-door wardrobe), never an
            # unexplained conflicting product configuration.
            if (feature != "portas" or
                expected not in headline_counts.get("portas", set())):
                raise ManufacturerEvidenceError("manufacturer_variant_conflict")
            for amount in extra:
                description = re.search(
                    rf"\b0?{amount}\s+portas\s+em\s+(?:mdf|mdp)\b",
                    excerpt)
                if not description:
                    raise ManufacturerEvidenceError("manufacturer_variant_conflict")
        word = ("porta" if expected == 1 else "portas") if feature == "portas" else (
            "gaveta" if expected == 1 else "gavetas")
        feature_claims.append(
            ("features", f"O fabricante informa {expected} {word} no modelo "
             + model.upper() + ".", f"{expected} {word}"))
    material_matches = list(MATERIAL_PATTERN.finditer(excerpt))
    if (not material_matches and re.search(
            r"\b(?:estrutura em|fabricad[oa] em|produzid[oa] em|"
            r"material (?:principal )?(?:de|em))\s+\w+", excerpt)):
        # An explicitly stated but unsupported substance is not silently
        # ignored to make a risky product pass on other measurements.
        raise ManufacturerEvidenceError("manufacturer_material_unverified")
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
    if len(materials) > 1:
        raise ManufacturerEvidenceError("manufacturer_material_ambiguous")
    claims = [
        ("model_identifier", "O fabricante identifica o modelo como " +
         model.upper() + ".", model),
    ]
    if len(materials) == 1 and materials <= MATERIALS:
        material = materials.pop()
        display = material.upper() if material in ("mdp", "mdf") else material
        claims.append(("material", "O fabricante informa material " +
                       display + ".", material))
    claims.extend(feature_claims)
    if len(claims) < 2:
        raise ManufacturerEvidenceError("manufacturer_objective_facts_insufficient")
    return claims
