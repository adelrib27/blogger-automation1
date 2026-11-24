"""C152 — prevenção universal de colisões em histórico autenticado de CMS.

Este módulo não chama rede nem escreve. O chamador deve validar previamente
identidade/rota do CMS e entregar TODO o histórico publicado + rascunhos.
A ausência de SKU em conteúdo legado não é prova de ineditismo editorial.
"""
from __future__ import annotations

import html
import re
import unicodedata
from difflib import SequenceMatcher
from urllib.parse import parse_qs, urlsplit

SKU = re.compile(r"shopee:([0-9]+):([0-9]+)\Z")
KEYS = re.compile(r"shopee:[0-9]+:[0-9]+", re.I)
URLS = re.compile(r"https?://[^\s\"'<>]+", re.I)
STOP = frozenset({"a", "as", "o", "os", "de", "da", "do", "dos", "em", "um",
                  "uma", "e", "ou", "com", "para", "por", "sobre", "como",
                  "escolher", "guia", "compra", "antes", "verificar", "confira",
                  "produto", "pratico", "pratica"})
VARIANT_LABELS = frozenset({"active", "lite", "pro", "plus", "ultra", "max", "mini", "se"})
STATUSES = {"wordpress": {"publish", "draft", "pending", "future", "private"},
            "blogger": {"live", "draft", "scheduled"}}


class CMSLegacyCollisionError(ValueError):
    """Erro sanitizado, sem conteúdo privado/URL/credenciais."""


def normalized(value: str) -> str:
    if not isinstance(value, str):
        raise CMSLegacyCollisionError("legacy_title_invalid")
    s = unicodedata.normalize("NFKD", html.unescape(value)).casefold()
    s = "".join(c for c in s if not unicodedata.combining(c))
    return " ".join(re.findall(r"[a-z0-9]+", s))


def _text(value) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        v = value.get("raw")
        if isinstance(v, str):
            return v
    raise CMSLegacyCollisionError("cms_legacy_raw_missing_fail_closed")


def _product_keys(body: str) -> set[str]:
    keys = {m.lower() for m in KEYS.findall(html.unescape(body))}
    for match in URLS.finditer(html.unescape(body)):
        raw = match.group(0).rstrip("),.;]")
        try:
            url = urlsplit(raw)
        except ValueError:
            continue
        hostname = (url.hostname or "").lower()
        if not (hostname == "shopee.com.br"
                or hostname.endswith(".shopee.com.br")):
            continue
        path = url.path
        parts = re.search(r"/product/([0-9]+)/([0-9]+)(?:/|$)", path, re.I)
        if not parts:
            parts = re.search(r"-i\.([0-9]+)\.([0-9]+)(?:/|$)", path, re.I)
        if parts:
            keys.add(f"shopee:{parts.group(1)}:{parts.group(2)}")
            continue
        q = parse_qs(url.query)
        shop = (q.get("shopid") or q.get("shop_id") or [""])[0]
        item = (q.get("itemid") or q.get("item_id") or [""])[0]
        if shop.isascii() and item.isascii() and shop.isdecimal() and item.isdecimal():
            keys.add(f"shopee:{shop}:{item}")
    return keys


def _semantic_reason(candidate: str, existing: str) -> str | None:
    a, b = normalized(candidate), normalized(existing)
    if not a or not b:
        raise CMSLegacyCollisionError("cms_legacy_title_empty")
    if a == b:
        return "IDENTICAL_TITLE"
    words_a, words_b = set(a.split()) - STOP, set(b.split()) - STOP
    shared = words_a & words_b
    if len(shared) < 2:
        return None  # só categoria genérica: não confundir com identidade
    # "Watch 5 Active" e "Watch 5 Lite" não são a mesma variante.
    nums_a = {s for s in words_a if s.isdecimal()}
    nums_b = {s for s in words_b if s.isdecimal()}
    if nums_a and nums_b and nums_a != nums_b:
        return None
    # O nome compartilhado não une variantes explicitamente diferentes.
    if ((words_a - words_b) & VARIANT_LABELS
            and (words_b - words_a) & VARIANT_LABELS):
        return None
    union = words_a | words_b
    if (len(shared) >= 3 and len(shared) / max(1, len(union)) >= .70):
        return "HIGH_TOPIC_OVERLAP"
    if SequenceMatcher(None, a, b).ratio() >= .88 and len(shared) >= 3:
        return "NEAR_IDENTICAL_TITLE"
    return None


def audit_candidate_history(*, platform: str, posts: list[dict],
                            product_key: str, article_title: str,
                            slug: str | None = None) -> dict:
    """Analisa o histórico recebido da mesma identidade CMS autenticada.

    Retorna apenas códigos e IDs. Bloqueia tanto duplicata literal quanto
    ambiguidade temática relevante. Não aprova produto, fontes ou DRAFT.
    """
    if (platform not in STATUSES or not isinstance(posts, list)
            or len(posts) > 2000 or not isinstance(product_key, str)
            or not SKU.fullmatch(product_key)
            or not isinstance(article_title, str)
            or not normalized(article_title)
            or (slug is not None and (not isinstance(slug, str) or not slug))):
        raise CMSLegacyCollisionError("legacy_audit_inputs_invalid")
    ids: set[str] = set()
    collisions: list[dict] = []
    for p in posts:
        if not isinstance(p, dict):
            raise CMSLegacyCollisionError("legacy_post_invalid")
        identifier = p.get("id")
        if (not isinstance(identifier, (str, int)) or isinstance(identifier, bool)
                or not str(identifier).isdecimal() or int(identifier) <= 0
                or str(identifier) in ids):
            raise CMSLegacyCollisionError("cms_legacy_id_missing_or_duplicate")
        ids.add(str(identifier))
        status = str(p.get("status", "")).lower()
        if status not in STATUSES[platform]:
            raise CMSLegacyCollisionError("cms_legacy_status_untrusted")
        body = _text(p.get("content"))
        title = _text(p.get("title"))
        old_slug = p.get("slug") if platform == "wordpress" else None
        if platform == "wordpress" and not isinstance(old_slug, str):
            raise CMSLegacyCollisionError("cms_legacy_slug_missing_fail_closed")
        reason = None
        if product_key in _product_keys(body):
            reason = "IDENTICAL_PRODUCT_SKU_OR_URL"
        elif slug is not None and old_slug == slug:
            reason = "IDENTICAL_SLUG"
        else:
            reason = _semantic_reason(article_title, title)
        if reason:
            collisions.append({"cms_id": str(identifier), "status": status,
                               "reason": reason})
    return {"status": "REVIEW_REQUIRED" if collisions else "NO_DETECTED_COLLISION",
            "posts_checked": len(ids), "collisions": collisions,
            "draft_authorized": False, "live_authorized": False}
