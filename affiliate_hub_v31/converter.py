"""Conversor Shopee por demanda, isolado dos publicadores (nenhuma execução por import).

Pré-condições: produto e nicho aprovados, link original HTTPS Shopee,
campanha identificada, credenciais lidas apenas em runtime. O cache persiste
no Catalog fornecido; sem storage remoto configurado, não executar em Actions.
"""
from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.request

from .catalog import Catalog, host_allowed
from .shopee_probe import ENDPOINT, authorization

MAX_RESPONSE_BYTES = 65536


class ConversionError(RuntimeError):
    """Erro sanitizado. Nunca incluir URL, segredo, header ou corpo remoto."""


def valid_campaign(campaign: str) -> str:
    if not isinstance(campaign, str) or not re.fullmatch(r"[a-z0-9_-]{1,32}", campaign):
        raise ValueError("Campanha inválida")
    # Sem espaços, caracteres de URL ou conteúdo derivado de campos externos.
    sub_id = re.sub(r"[^A-Z0-9]", "", campaign.upper())
    if not sub_id or len(sub_id) > 32:
        raise ValueError("Sub ID inválido")
    return sub_id


def make_payload(origin_url: str, campaign: str) -> str:
    if not host_allowed(origin_url):
        raise ValueError("Origem Shopee HTTPS inválida")
    sub_id = valid_campaign(campaign)
    # Strings são codificadas como JSON e não interpoladas sem escape em GraphQL.
    graphql = (
        "mutation V31EditorialGenerateLink { "
        "generateShortLink(input: { originUrl: "
        + json.dumps(origin_url, ensure_ascii=False)
        + ", subIds: ["
        + json.dumps(sub_id)
        + "] }) { shortLink } }"
    )
    return json.dumps(
        {"query": graphql, "operationName": "V31EditorialGenerateLink"},
        ensure_ascii=False,
        separators=(",", ":"),
    )


def generate_shortlink(origin_url: str, campaign: str, app_id: str, secret: str) -> str:
    """Única tentativa de mutation; falhas/retries ficam para a fila persistente."""
    body = make_payload(origin_url, campaign)
    try:
        auth = authorization(app_id, secret, body, int(time.time()))
    except ValueError as exc:
        raise ConversionError("credentials_missing") from None
    request = urllib.request.Request(
        ENDPOINT,
        data=body.encode("utf-8"),
        method="POST",
        headers={
            "Authorization": auth,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "V31EditorialConverter/0.2",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            if response.status != 200:
                raise ConversionError("http_unexpected_status")
            raw = response.read(MAX_RESPONSE_BYTES + 1)
    except urllib.error.HTTPError as exc:
        # Não expor mensagens remotas ou Authorization no traceback.
        raise ConversionError("http_error_" + str(exc.code)) from None
    except (urllib.error.URLError, TimeoutError):
        raise ConversionError("network_error") from None
    if len(raw) > MAX_RESPONSE_BYTES:
        raise ConversionError("response_too_large")
    try:
        parsed = json.loads(raw)
    except (ValueError, UnicodeDecodeError):
        raise ConversionError("invalid_response") from None
    if not isinstance(parsed, dict) or parsed.get("errors"):
        raise ConversionError("graphql_error")
    result = (parsed.get("data") or {}).get("generateShortLink")
    url = result.get("shortLink") if isinstance(result, dict) else None
    if not isinstance(url, str) or not host_allowed(url, allow_short=True):
        raise ConversionError("untrusted_or_missing_affiliate_link")
    return url


def convert_one(catalog: Catalog, product_key: str, campaign: str,
                app_id: str, secret: str) -> tuple[str, bool]:
    """Retorna (link, criado_agora). Nunca converte item sem nicho aprovado."""
    valid_campaign(campaign)
    item = catalog.for_conversion(product_key)
    if item is None:
        raise ConversionError("not_eligible_for_conversion")
    existing = catalog.cached_link(product_key, campaign)
    if existing:
        if not host_allowed(existing, allow_short=True):
            raise ConversionError("cached_link_untrusted")
        return existing, False
    origin_url, _category, _niche = item
    link = generate_shortlink(origin_url, campaign, app_id, secret)
    # Recheca permissões após a chamada e guarda idempotentemente, sem sobrescrever.
    if catalog.for_conversion(product_key) is None:
        raise ConversionError("product_became_ineligible")
    catalog.cache_link(product_key, campaign, link, origin="shopee_api")
    saved = catalog.cached_link(product_key, campaign)
    if not saved:
        raise ConversionError("cache_not_persisted")
    return saved, saved == link


def planned_candidates(catalog: Catalog, campaign: str, category: str | None = None,
                       niche: str | None = None, limit: int = 20) -> dict:
    """Planejamento só contagem/IDs internos; nenhum acesso à Shopee."""
    candidates = catalog.candidates(campaign, limit, category=category, niche=niche)
    return {
        "mode": "SAFE_NO_API",
        "campaign": campaign,
        "category": category,
        "niche": niche,
        "count": len(candidates),
        "keys": [row[0] for row in candidates],
    }
