"""C71: contrato SAFE de fatos EXATOS no HTML final, separado do gerador.

Nunca interpreta afirmações da IA como prova. Cada fato aprovado precisa
aparecer literalmente em span data-v31-fact-id com o mesmo SKU/fonte/TTL.
Texto editorial restante só passa com hashes previamente aprovados por
revisor INDEPENDENTE (NUNCA enviados pelo próprio modelo).
Mesmo após PASS, continua REVISÃO OBRIGATÓRIA antes de LIVE.
Nenhuma API, R2, D1 ou CMS é chamada por este módulo.
"""
from __future__ import annotations

import hashlib
import re
from html.parser import HTMLParser
from typing import Iterable
from urllib.parse import urlsplit

from .universal_evidence_ready import (
    UniversalReadyError, UniversalReadyPolicy, evidence_whitelist,
)


class FinalFactGateError(ValueError):
    pass


PROSE = frozenset({"p", "li", "h2", "h3", "figcaption", "blockquote"})
VOID = frozenset({"img", "br", "hr"})
ALLOWED = frozenset({
    "article", "section", "aside", "div", "figure", "figcaption",
    "h2", "h3", "p", "ul", "ol", "li", "blockquote", "a", "img",
    "span", "strong", "em", "b", "i", "small", "br", "hr",
})
ID_RE = re.compile(r"[A-Za-z0-9:_-]{5,100}")
SHA_RE = re.compile(r"[a-f0-9]{64}")


def reviewed_text_digest(text: str) -> str:
    """SHA256 da string renderizada com espaços normalizados."""
    if not isinstance(text, str) or not text.strip():
        raise FinalFactGateError("reviewed_text_invalid")
    normalized = " ".join(text.split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


class _FinalHTMLScanner(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tags: list[str] = []
        self.article_count = 0
        self.current_block: dict | None = None
        self.fact_span: dict | None = None
        self.facts: dict[str, str] = {}
        self.unbound: list[str] = []
        self.prose_count = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag not in ALLOWED or not self.article_count and tag != "article":
            raise FinalFactGateError("html_tag_outside_safe_contract")
        keys = [name for name, _ in attrs]
        if len(keys) != len(set(keys)) or any(
            name.startswith("on") or name in ("srcdoc", "formaction", "style", "srcset")
            for name in keys
        ):
            raise FinalFactGateError("html_untrusted_attribute")
        attr = dict(attrs)
        if "data-v31-fact-id" in attr and tag != "span":
            raise FinalFactGateError("fact_marker_wrong_element")
        if tag in ("a", "img"):
            u = attr.get("href") if tag == "a" else attr.get("src")
            if not isinstance(u, str):
                raise FinalFactGateError("html_link_required")
            try:
                p = urlsplit(u)
                if (p.scheme != "https" or not p.hostname or p.username
                        or p.password or p.port not in (None, 443)):
                    raise FinalFactGateError("html_unsafe_url")
            except (TypeError, ValueError):
                raise FinalFactGateError("html_unsafe_url") from None
        if tag == "article":
            self.article_count += 1
            if self.article_count != 1 or self.tags:
                raise FinalFactGateError("html_article_root_invalid")
        if tag in PROSE:
            if self.current_block is not None or self.fact_span is not None:
                raise FinalFactGateError("nested_prose_not_supported")
            self.current_block = {"tag": tag, "unbound": []}
            self.prose_count += 1
        if tag == "span" and "data-v31-fact-id" in attr:
            eid = attr["data-v31-fact-id"]
            if (self.current_block is None or self.fact_span is not None
                    or not isinstance(eid, str) or not ID_RE.fullmatch(eid)
                    or eid in self.facts):
                raise FinalFactGateError("fact_span_invalid_or_duplicate")
            self.fact_span = {"id": eid, "text": []}
        elif self.fact_span is not None and tag not in ("strong", "em", "b", "i"):
            raise FinalFactGateError("fact_span_nested_markup_unsafe")
        if tag not in VOID:
            self.tags.append(tag)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag not in VOID:
            raise FinalFactGateError("html_self_closing_invalid")
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag: str) -> None:
        if not self.tags or self.tags[-1] != tag:
            raise FinalFactGateError("html_unbalanced")
        if tag == "span" and self.fact_span is not None:
            eid = self.fact_span["id"]
            self.facts[eid] = " ".join("".join(self.fact_span["text"]).split())
            self.fact_span = None
        if tag in PROSE:
            if self.current_block is None or self.current_block["tag"] != tag:
                raise FinalFactGateError("html_prose_unbalanced")
            free = " ".join("".join(self.current_block["unbound"]).split())
            if free:
                self.unbound.append(free)
            self.current_block = None
        self.tags.pop()

    def handle_data(self, data: str) -> None:
        if not data.strip():
            return
        if self.fact_span is not None:
            self.fact_span["text"].append(data)
        elif self.current_block is not None:
            self.current_block["unbound"].append(data)
        else:
            raise FinalFactGateError("unreviewed_text_outside_prose")

    def handle_comment(self, data: str) -> None:
        raise FinalFactGateError("html_comments_disallowed")

    def unknown_decl(self, data: str) -> None:
        raise FinalFactGateError("html_declaration_disallowed")


def verify_final_html_facts(
    *, html_content: str, evidence_package: dict,
    product_key: str, product_title: str,
    used_evidence_ids: list[str],
    trusted_reviewed_text_hashes: Iterable[str] = (),
    now=None, policy: UniversalReadyPolicy = UniversalReadyPolicy()
) -> dict:
    """Gate estrutural: evidência literal + revisão independente do resto.

    O chamador deve obter trusted_reviewed_text_hashes de uma fonte
    independente, nunca de parâmetros fornecidos por IA/candidato.
    PASS nunca significa autorização LIVE.
    """
    if not isinstance(html_content, str) or not 100 <= len(html_content) <= 120_000:
        raise FinalFactGateError("html_size_invalid")
    if (not isinstance(used_evidence_ids, list) or
            not used_evidence_ids or len(used_evidence_ids) > 100 or
            not all(isinstance(x, str) and ID_RE.fullmatch(x)
                    for x in used_evidence_ids) or
            len(used_evidence_ids) != len(set(used_evidence_ids))):
        raise FinalFactGateError("used_evidence_ids_invalid")
    hashes = set(trusted_reviewed_text_hashes)
    if len(hashes) > 300 or not all(
        isinstance(x, str) and SHA_RE.fullmatch(x) for x in hashes
    ):
        raise FinalFactGateError("trusted_review_hashes_invalid")
    try:
        audit = evidence_whitelist(
            package=evidence_package, product_key=product_key,
            product_title=product_title, policy=policy, now=now)
    except UniversalReadyError as exc:
        raise FinalFactGateError("package_not_verified_exact_fresh") from exc
    verified = {e["evidence_id"]: " ".join(e["claim_text"].split())
                for e in audit["allowed_facts"]}
    scanner = _FinalHTMLScanner()
    try:
        scanner.feed(html_content)
        scanner.close()
    except FinalFactGateError:
        raise
    except Exception as exc:
        raise FinalFactGateError("html_parser_rejected") from exc
    if (scanner.article_count != 1 or scanner.tags or scanner.fact_span
            or scanner.current_block or scanner.prose_count == 0):
        raise FinalFactGateError("html_structure_invalid")
    if set(scanner.facts) != set(used_evidence_ids):
        raise FinalFactGateError("fact_ids_not_exactly_bound")
    for eid, observed in scanner.facts.items():
        if observed != verified.get(eid):
            raise FinalFactGateError("html_fact_changed_or_unsupported")
    unreviewed = [
        text for text in scanner.unbound
        if reviewed_text_digest(text) not in hashes
    ]
    if unreviewed:
        # Nenhuma frase de IA não revisada chega à READY.
        raise FinalFactGateError("unreviewed_editorial_text")
    return {
        "status": "EXACT_FACT_BINDINGS_VERIFIED_REVIEW_STILL_REQUIRED",
        "verified_facts": len(scanner.facts),
        "editorial_blocks_independently_reviewed": len(scanner.unbound),
        "source_external_count": audit["external_source_count"],
        "evidence_verified_utc": audit["verified_utc"],
        "requires_human_live_approval": True,
        "ready_publication_authorized": False,
        "network_calls": 0,
        "cms_draft_calls": 0,
        "publication_calls": 0,
    }
