"""Política SAFE de reutilização editorial de produtos (C11).

Usar o mesmo produto em dois artigos NÃO significa publicar duas vezes o
mesmo assunto. Reutilização é opt-in, com trava de título/intenção e
histórico transacional de publicações por blog.

Este módulo NÃO chama API, NÃO cria posts, NÃO remove gates antigos.
"""
from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher

MAX_ARTICLES_PER_PRODUCT = 2
MAX_TITLE_JACCARD = 0.56
MAX_TITLE_SEQUENCE = 0.80
STOPWORDS = {
    "a", "ao", "aos", "as", "com", "da", "das", "de", "do",
    "dos", "e", "em", "na", "nas", "no", "nos", "o", "os",
    "para", "por", "um", "uma", "como", "que", "se", "suas",
    "seus", "quando", "onde", "sem", "mais", "antes", "depois",
}


class ReuseDenied(ValueError):
    pass


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKD",str(value or "").lower())
    value = "".join(x for x in value if not unicodedata.combining(x))
    return " ".join(re.findall(r"[a-z0-9]+",value))


def title_tokens(value: str) -> set[str]:
    return {t for t in normalize(value).split()
            if len(t)>=3 and t not in STOPWORDS}


def title_is_distinct(title: str, earlier: str) -> bool:
    title_norm=normalize(title)
    old_norm=normalize(earlier)
    if not title_norm or not old_norm or title_norm == old_norm:
        return False
    first=title_tokens(title)
    second=title_tokens(earlier)
    if not first or not second:
        return False
    similarity=len(first & second)/len(first | second)
    sequence=SequenceMatcher(None,title_norm,old_norm,autojunk=False).ratio()
    return similarity < MAX_TITLE_JACCARD and sequence < MAX_TITLE_SEQUENCE


def published_for_product(history: dict, item_id: str) -> list[dict]:
    if not item_id or not str(item_id).strip():
        raise ReuseDenied("product_id_missing")
    records=history.get("items")
    if not isinstance(records,list):
        raise ReuseDenied("history_invalid")
    return [row for row in records if isinstance(row,dict)
            and str(row.get("shopee_item_id") or "").strip()==str(item_id).strip()]


def can_queue_reuse(history: dict, item_id: str) -> tuple[bool,list[str]]:
    records=published_for_product(history,item_id)
    if not records or len(records)>=MAX_ARTICLES_PER_PRODUCT:
        return False,[]
    titles=[str(row.get("editorial_title") or row.get("title") or "").strip()
            for row in records]
    if any(not title for title in titles):
        return False,[]
    return True,titles


def validate_publication(history: dict, item: dict, article: dict) -> None:
    """Fail closed quando reuso é pedido; valida antes de criar post no WP."""
    if not item.get("reuse_candidate"):
        return
    item_id=str(item.get("shopee_item_id") or "").strip()
    allowed,previous=can_queue_reuse(history,item_id)
    if not allowed:
        raise ReuseDenied("reuse_history_not_eligible")
    if int(item.get("prior_publication_count") or -1)!=len(previous):
        raise ReuseDenied("reuse_history_changed")
    title=str(article.get("seo_title") or "").strip()
    if (not 35<=len(title)<=65 or
        title!=str(article.get("editorial_title") or "").strip() or
        title!=str(article.get("topic") or "").strip() or
        not str(article.get("focus_keyword") or "").strip() or
        not str(article.get("reader_need") or "").strip()):
        raise ReuseDenied("reuse_editorial_fields_incomplete")
    if str(article.get("shopee_item_id") or "")!=item_id:
        raise ReuseDenied("reuse_product_mismatch")
    if not str(article.get("editorial_html") or "").strip():
        raise ReuseDenied("reuse_body_missing")
    all_titles=[]
    for row in history.get("items") or []:
        if isinstance(row,dict):
            prior=str(row.get("editorial_title") or row.get("title") or "").strip()
            if prior:
                all_titles.append(prior)
    if not all(title_is_distinct(title,prior) for prior in all_titles):
        raise ReuseDenied("reuse_title_or_intent_too_similar")
    if not title_tokens(article.get("reader_need") or ""):
        raise ReuseDenied("reuse_reader_need_missing")
    current=str(item.get("source_keyword") or "").strip()
    if not current:
        raise ReuseDenied("reuse_original_keyword_missing")


def history_has_publication(history: dict, item_id: str, title: str) -> bool:
    """Dedup de publicação agora por produto + título (e não só produto)."""
    name=normalize(title)
    return any(
        normalize(row.get("editorial_title") or row.get("title") or "")==name
        for row in published_for_product(history,item_id)
    )
