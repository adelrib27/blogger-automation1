"""Planejamento por site Blogger/WordPress (somente leitura, sem publicações)."""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

from .catalog import Catalog
from .taxonomy import rules

ROUTES_PATH = Path(__file__).with_name("site_routes.json")


@lru_cache(maxsize=1)
def sites() -> dict:
    doc = json.loads(ROUTES_PATH.read_text(encoding="utf-8"))
    if doc.get("version") != "v31-editorial-site-routes-1" or doc.get("state") is None:
        raise ValueError("Contrato de rotas incompatível")
    known = {f"{cat}/{niche}" for cat, niche, *_ in rules()[1]}
    mappings = {}
    campaigns = set()
    identities = set()
    for route in doc.get("sites", []):
        if set(route) != {"site_key","platform","identifier","campaign","allowed_niches","publish_enabled"}:
            raise ValueError("Chaves inesperadas em rota")
        key, campaign = route["site_key"], route["campaign"]
        if (not re.fullmatch(r"[a-z0-9_]{3,50}", key)
                or not re.fullmatch(r"[a-z0-9_]{1,32}", campaign)):
            raise ValueError("Identificador inválido")
        if key in mappings or campaign in campaigns:
            raise ValueError("Rota ou campanha repetida")
        if route["platform"] not in {"blogger", "wordpress"}:
            raise ValueError("Plataforma inválida")
        identity = str(route["identifier"])
        if route["platform"] == "blogger" and not re.fullmatch(r"\d{10,24}", identity):
            raise ValueError("ID Blogger inválido")
        if route["platform"] == "wordpress" and not (
            identity.startswith("https://") and identity.endswith("/") and
            identity.count("/") == 3
        ):
            raise ValueError("Identidade WordPress inválida")
        if (route["platform"], identity) in identities:
            raise ValueError("Blog duplicado")
        if route["publish_enabled"] is not False:
            raise ValueError("Publicação não permitida no C2 SAFE")
        niches = route["allowed_niches"]
        if (not isinstance(niches, list) or not niches or len(niches) != len(set(niches))
                or not set(niches).issubset(known)):
            raise ValueError("Nicho ausente/duplicado/inválido")
        mappings[key] = route
        campaigns.add(campaign)
        identities.add((route["platform"], identity))
    if len(mappings) < 1:
        raise ValueError("Nenhuma rota")
    return mappings


def plan_site(catalog: Catalog, site_key: str, limit: int = 20) -> dict:
    if not 1 <= limit <= 100:
        raise ValueError("Limite inválido")
    route = sites().get(site_key)
    if route is None:
        raise ValueError("Site não cadastrado para o hub")
    selected = []
    seen = set()
    for pair in route["allowed_niches"]:
        category, niche = pair.split("/",1)
        for product in catalog.candidates(route["campaign"],limit,category=category,niche=niche):
            if product[0] not in seen:
                selected.append(product[0])
                seen.add(product[0])
            if len(selected) >= limit:
                break
        if len(selected) >= limit:
            break
    return {"mode":"SAFE_NO_PUBLICATION", "site_key":site_key,
            "platform":route["platform"], "campaign":route["campaign"],
            "eligible_selected":len(selected), "product_keys":selected}
