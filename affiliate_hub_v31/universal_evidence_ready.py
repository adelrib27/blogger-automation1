"""C69 — Evidence/READY universal V31, legado Vida Pet adaptado SEM dados Pet.

Camada SAFE: não faz HTTP, pesquisa, conversão Shopee, IA, D1, R2-write,
POST Blogger ou WordPress. Usa catálogo REAL injetado somente em leitura;
persistência demonstrável em SQLite local isolado. D1 e run REAL requerem
adaptador homologado distinto; nenhum booleano deste módulo autoriza LIVE.
"""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlsplit

from .article_commerce import CommerceArticleError, _single_verified_offer
from .routing import sites


class UniversalReadyError(ValueError):
    pass


IDENTITIES = frozenset(("EXACT_PRODUCT", "MATCHED_MODEL", "SIMILAR_PRODUCT"))
ALLOWED_FACT_TYPES = frozenset((
    "material", "dimensions", "capacity", "features", "care",
    "compatibility", "model_identifier", "included_items",
))
UNSUPPORTED_FACT_TEXT = re.compile(
    r"\b(cura|trata doença|tratamento médico|100\s*%\s*segur[oa]|"
    r"risco zero|garantia de cura|comprovadamente eficaz|preço garantido)\b", re.I,
)
SKU_PATTERN = re.compile(r"shopee:[0-9]+:[0-9]+")
SITE_PATTERN = re.compile(r"[a-z0-9_]{3,50}")


@dataclass(frozen=True)
class UniversalReadyPolicy:
    # Referência R28: defaults operacionais, NÃO limites totais de artigos.
    min_ready: int = 3
    candidate_attempt_limit: int = 20
    candidate_target: int = 5
    product_cooldown_days: int = 30
    max_similarity: float = .72
    evidence_ttl_days: int = 7
    min_external_authorized_sources: int = 1
    min_exact_evidence: int = 2
    max_search_calls: int = 2
    max_http_attempts: int = 3

    def __post_init__(self) -> None:
        ints = (
            self.min_ready, self.candidate_attempt_limit,
            self.candidate_target, self.product_cooldown_days,
            self.evidence_ttl_days, self.min_external_authorized_sources,
            self.min_exact_evidence, self.max_search_calls,
            self.max_http_attempts,
        )
        if (any(type(x) is not int or x < 1 or x > 100 for x in ints)
                or not 0 < self.max_similarity < 1
                or type(self.max_similarity) is not float
                or self.candidate_target > self.candidate_attempt_limit):
            raise UniversalReadyError("universal_policy_invalid")


def _normalize(value: str) -> str:
    if not isinstance(value, str):
        return ""
    chars = unicodedata.normalize("NFKD", value.casefold())
    ascii_text = "".join(x for x in chars if not unicodedata.combining(x))
    return " ".join(re.findall(r"[a-z0-9]+", ascii_text))


def _instant(value: str, *, now: datetime) -> datetime:
    if not isinstance(value, str):
        raise UniversalReadyError("evidence_timestamp_invalid")
    try:
        t = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise UniversalReadyError("evidence_timestamp_invalid") from None
    if t.tzinfo is None or t.utcoffset() != timedelta(0) or t > now:
        raise UniversalReadyError("evidence_timestamp_invalid")
    return t.astimezone(timezone.utc)


def _utc(value: datetime | None) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise UniversalReadyError("timezone_required")
    return value.astimezone(timezone.utc)


def _external_https(url: str) -> bool:
    try:
        p = urlsplit(url)
        host = (p.hostname or "").lower().rstrip(".")
        # Página Shopee do próprio vendedor não é "fonte externa independente".
        is_shopee = any(host == s or host.endswith("." + s)
                        for s in ("shopee.com.br", "shopee.com", "shope.ee"))
        return (p.scheme == "https" and len(url) <= 1500 and
                bool(host) and not is_shopee and
                p.port in (None, 443) and not p.username and not p.password
                and not p.fragment and bool(p.path))
    except (ValueError, TypeError):
        return False


def evidence_whitelist(
    *, package: dict, product_key: str, product_title: str,
    now: datetime | None = None,
    policy: UniversalReadyPolicy = UniversalReadyPolicy(),
) -> dict:
    """Somente claims específicos ao SKU, autorizados e dentro do TTL.

    'AUTHORIZED' é uma decisão rastreada de um verificador EXTERNO, não
    prova criada pelo código. Sem pesquisa real, jamais emitir claims novos.
    """
    clock = _utc(now)
    if not SKU_PATTERN.fullmatch(product_key) or not _normalize(product_title):
        raise UniversalReadyError("evidence_product_identity_invalid")
    if not isinstance(package, dict):
        raise UniversalReadyError("evidence_package_missing")
    if (package.get("product_key") != product_key or
            _normalize(package.get("product_title", "")) != _normalize(product_title) or
            package.get("product_status") != "VERIFIED"):
        raise UniversalReadyError("evidence_exact_product_mismatch")
    checked = _instant(package.get("verified_utc"), now=clock)
    if clock - checked > timedelta(days=policy.evidence_ttl_days):
        raise UniversalReadyError("evidence_cache_expired")
    evidence = package.get("sources")
    if not isinstance(evidence, list) or not evidence or len(evidence) > 100:
        raise UniversalReadyError("evidence_sources_missing")
    valid: list[dict] = []
    external = set()
    identifiers = set()
    for e in evidence:
        if not isinstance(e, dict) or e.get("identity_level") not in IDENTITIES:
            continue
        if e["identity_level"] != "EXACT_PRODUCT":
            # MATCHED_MODEL e SIMILAR_PRODUCT NÃO fornecem especificações.
            continue
        if e.get("product_key") != product_key or e.get("authorized") is not True:
            continue
        # approved_host vem do verificador que revisou a URL, NÃO de
        # heurística em uma URL parecida. Comparar hostname exato.
        try:
            actual_host = urlsplit(e.get("source_url")).hostname
        except (ValueError, TypeError):
            actual_host = None
        if (e.get("source_kind") != "external" or
                e.get("review_status") != "AUTHORIZED" or
                not _external_https(e.get("source_url")) or
                not isinstance(e.get("approved_host"), str) or
                actual_host != e["approved_host"]):
            continue
        try:
            verified = _instant(e.get("checked_utc"), now=clock)
        except UniversalReadyError:
            continue
        if clock - verified > timedelta(days=policy.evidence_ttl_days):
            continue
        eid = e.get("evidence_id")
        claim_type = e.get("claim_type")
        claim_text = e.get("claim_text")
        if (not isinstance(eid, str) or not re.fullmatch(r"[A-Za-z0-9:_-]{5,100}", eid)
                or eid in identifiers or claim_type not in ALLOWED_FACT_TYPES
                or not isinstance(claim_text, str)
                or not 8 <= len(claim_text.strip()) <= 450
                or UNSUPPORTED_FACT_TEXT.search(claim_text)):
            continue
        identifiers.add(eid)
        external.add(e["source_url"])
        valid.append({
            "evidence_id": eid,
            "claim_type": claim_type,
            "claim_text": claim_text.strip(),
            "source_url": e["source_url"],
            "checked_utc": e["checked_utc"],
        })
    if len(external) < policy.min_external_authorized_sources:
        raise UniversalReadyError("evidence_external_source_required")
    if len(valid) < policy.min_exact_evidence:
        raise UniversalReadyError("evidence_exact_claims_insufficient")
    return {
        "product_key": product_key,
        "verified_utc": package["verified_utc"],  # leitura NÃO altera TTL
        "fact_count": len(valid),
        "allowed_facts": valid,
        "external_source_count": len(external),
    }


def _fingerprint(product_key: str, keyword: str, angle: str) -> str:
    return hashlib.sha256((
        product_key + "\n" + _normalize(keyword) + "\n" +
        _normalize(angle)
    ).encode("utf-8")).hexdigest()


def _similarity(a: str, b: str) -> float:
    aa, bb = set(_normalize(a).split()), set(_normalize(b).split())
    return len(aa & bb) / len(aa | bb) if aa and bb else 0.0


class SearchBudget:
    """Budget de tentativas em memória — somente simulador; sem rede.

    A conta GitHub Firecrawl pode ter crédito diferente da conta conectada
    ao chat. 'credits_reported' mede depois do fato, não garante teto em R$.
    Para uso real entre processos, implementar contador atômico durável.
    """
    def __init__(
        self, *, credit_balance_confirmed: bool = False,
        policy: UniversalReadyPolicy = UniversalReadyPolicy()
    ):
        self.policy = policy
        self.confirmed = credit_balance_confirmed is True
        self.search_calls = 0
        self.http_attempts = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.rate_limits_429 = 0
        self.credits_reported = 0.0
        self.circuit_open = False

    def event(self, event: str) -> None:
        if event == "CACHE_HIT":
            self.cache_hits += 1
        elif event == "CACHE_MISS":
            self.cache_misses += 1
        else:
            raise UniversalReadyError("budget_event_invalid")

    def claim(self, kind: str) -> None:
        if self.circuit_open or not self.confirmed:
            raise UniversalReadyError("search_budget_closed_or_unknown")
        if kind == "SEARCH":
            if self.search_calls >= self.policy.max_search_calls:
                raise UniversalReadyError("search_budget_exhausted")
            self.search_calls += 1
        elif kind == "HTTP":
            if self.http_attempts >= self.policy.max_http_attempts:
                raise UniversalReadyError("http_budget_exhausted")
            self.http_attempts += 1
        else:
            raise UniversalReadyError("budget_event_invalid")

    def record_429(self) -> None:
        self.rate_limits_429 += 1
        self.circuit_open = True

    def report_credits(self, value: float) -> None:
        if type(value) not in (int, float) or not 0 <= value <= 1000000:
            raise UniversalReadyError("credits_report_invalid")
        self.credits_reported += float(value)

    def public_report(self) -> dict:
        # Nunca registrar query, SKU, URL, chave de API, nome ou search_id.
        return {
            "search_calls": self.search_calls,
            "http_attempts": self.http_attempts,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "rate_limit_429": self.rate_limits_429,
            "credits_reported_total": self.credits_reported,
            "external_balance_confirmed": self.confirmed,
            "circuit_open": self.circuit_open,
            "network_calls_executed_by_this_module": 0,
        }


class SQLiteReadyLabStore:
    """Demonstração persistente de histórico por site, via SQLite.

    Banco isolado. Não aponta nem modifica R2, D1 Vida Pet ou CMS. O
    adaptador D1 produtivo exigirá atomicidade e lock interprocesso próprios.
    """
    def __init__(self, path: str | Path = ":memory:"):
        self.db = sqlite3.connect(str(path))
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS ready_entries (
                site_key TEXT NOT NULL,
                campaign TEXT NOT NULL,
                product_key TEXT NOT NULL,
                keyword TEXT NOT NULL,
                angle TEXT NOT NULL,
                fingerprint TEXT NOT NULL,
                title TEXT NOT NULL,
                content_sha256 TEXT NOT NULL,
                evidence_verified_utc TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('READY', 'USED')),
                created_utc TEXT NOT NULL,
                used_utc TEXT,
                PRIMARY KEY (site_key, fingerprint)
            )
        """)
        self.db.execute("""
            CREATE INDEX IF NOT EXISTS idx_ready_site
            ON ready_entries(site_key, campaign, status)
        """)
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS verified_evidence_cache (
                site_key TEXT NOT NULL,
                product_key TEXT NOT NULL,
                product_title TEXT NOT NULL,
                package_json TEXT NOT NULL,
                verified_utc TEXT NOT NULL,
                PRIMARY KEY (site_key, product_key)
            )
        """)
        self.db.commit()

    def close(self) -> None:
        self.db.close()

    def cache_verified_evidence(
        self, *, site_key: str, product_key: str, product_title: str,
        package: dict, now: datetime,
        policy: UniversalReadyPolicy = UniversalReadyPolicy()
    ) -> dict:
        """Grava somente pacote já VALIDADO. Nunca renova carimbo do cache."""
        if not isinstance(site_key, str) or not SITE_PATTERN.fullmatch(site_key):
            raise UniversalReadyError("evidence_site_key_invalid")
        audit = evidence_whitelist(
            package=package, product_key=product_key,
            product_title=product_title, now=now, policy=policy)
        raw = json.dumps(package, ensure_ascii=False, sort_keys=True)
        if len(raw) > 100_000:
            raise UniversalReadyError("evidence_cache_payload_too_large")
        with self.db:
            self.db.execute("""
                INSERT INTO verified_evidence_cache (
                    site_key,product_key,product_title,package_json,verified_utc
                ) VALUES (?,?,?,?,?)
                ON CONFLICT(site_key,product_key) DO UPDATE SET
                    product_title=excluded.product_title,
                    package_json=excluded.package_json,
                    verified_utc=excluded.verified_utc
            """, (site_key,product_key,product_title,raw,audit["verified_utc"]))
        return {"cached":True,"fact_count":audit["fact_count"],
                "verified_utc":audit["verified_utc"],
                "network_calls":0,"publication_calls":0}

    def get_verified_evidence(
        self, *, site_key: str, product_key: str, product_title: str,
        now: datetime, policy: UniversalReadyPolicy = UniversalReadyPolicy()
    ) -> dict | None:
        """Reidrata sem alterar TTL; cache expirado ou identidade alterada -> MISS."""
        if (not isinstance(site_key, str) or
                not SITE_PATTERN.fullmatch(site_key) or
                not isinstance(product_key,str) or
                not SKU_PATTERN.fullmatch(product_key)):
            raise UniversalReadyError("evidence_cache_lookup_invalid")
        row = self.db.execute("""
            SELECT package_json,verified_utc FROM verified_evidence_cache
            WHERE site_key=? AND product_key=?
        """, (site_key,product_key)).fetchone()
        if not row:
            return None
        try:
            doc=json.loads(row[0])
            if (not isinstance(doc,dict) or
                    doc.get("verified_utc") != row[1]):
                return None
            evidence_whitelist(package=doc,product_key=product_key,
                               product_title=product_title,now=now,
                               policy=policy)
        except (ValueError,TypeError,UniversalReadyError):
            return None
        return doc

    def ready_count(self, site_key: str, campaign: str) -> int:
        return int(self.db.execute(
            "SELECT COUNT(*) FROM ready_entries WHERE site_key=? AND campaign=? AND status='READY'",
            (site_key, campaign)).fetchone()[0])

    def check(self, *, site_key: str, campaign: str,
              product_key: str, keyword: str, angle: str,
              now: datetime, policy: UniversalReadyPolicy) -> str | None:
        fp = _fingerprint(product_key, keyword, angle)
        history = self.db.execute("""
            SELECT fingerprint,keyword,angle,created_utc,used_utc
              FROM ready_entries WHERE site_key=? AND product_key=?
        """, (site_key, product_key)).fetchall()
        for previous_fp, kw, old_angle, created, used in history:
            if previous_fp == fp:
                return "DUPLICATE_PRODUCT_KEYWORD_ANGLE"
            # Novo ângulo editorial deve ser de fato diferente; sinônimo
            # do mesmo post não pode furar a barreira de anti-duplicidade.
            sim = _similarity(keyword + " " + angle, kw + " " + old_angle)
            if sim >= policy.max_similarity:
                return "EVERGREEN_ANGLE_TOO_SIMILAR"
            ref = _instant(used or created, now=now)
            if now - ref < timedelta(days=policy.product_cooldown_days):
                return "PRODUCT_COOLDOWN_ACTIVE"
        return None

    def add(
        self, *, site_key: str, campaign: str, product_key: str,
        keyword: str, angle: str, title: str, content_html: str,
        evidence_verified_utc: str, now: datetime,
        policy: UniversalReadyPolicy
    ) -> bool:
        # Esta transação não é substituta de lock distribuído entre
        # Actions/D1; usa atomicidade local e fail-closed se falhar.
        fingerprint = _fingerprint(product_key, keyword, angle)
        content_sha256 = hashlib.sha256(
            (title + "\n" + content_html).encode("utf-8")).hexdigest()
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            if self.ready_count(site_key, campaign) >= policy.min_ready:
                return False
            if self.check(site_key=site_key, campaign=campaign,
                          product_key=product_key, keyword=keyword,
                          angle=angle, now=now, policy=policy):
                return False
            self.db.execute("""
                INSERT INTO ready_entries(
                    site_key,campaign,product_key,keyword,angle,fingerprint,
                    title,content_sha256,evidence_verified_utc,status,
                    created_utc,used_utc
                ) VALUES(?,?,?,?,?,?,?,?,?,'READY',?,NULL)
            """, (site_key, campaign, product_key, keyword, angle,
                  fingerprint, title, content_sha256,
                  evidence_verified_utc, now.isoformat()))
            return True

    def consume_one_lab(self, *, site_key: str, campaign: str,
                        fingerprint: str, now: datetime) -> bool:
        """Apenas SIMULA consumo de buffer isolado; NUNCA publica."""
        with self.db:
            cur = self.db.execute("""
                UPDATE ready_entries SET status='USED',used_utc=?
                WHERE site_key=? AND campaign=? AND fingerprint=?
                AND status='READY'
            """, (now.isoformat(), site_key, campaign, fingerprint))
            return cur.rowcount == 1


def _registered_route(site_key: str) -> dict:
    if not isinstance(site_key, str) or not SITE_PATTERN.fullmatch(site_key):
        raise UniversalReadyError("registered_site_required")
    route = sites().get(site_key)
    if (not isinstance(route, dict) or
            route.get("site_key") != site_key or
            route.get("publish_enabled") is not False or
            route.get("platform") not in ("blogger", "wordpress") or
            not isinstance(route.get("campaign"), str)):
        raise UniversalReadyError("registered_draft_only_site_required")
    return route


def safe_refill_preview(
    *, catalog, site_key: str, candidates: list[dict],
    store: SQLiteReadyLabStore,
    policy: UniversalReadyPolicy = UniversalReadyPolicy(),
    now: datetime | None = None,
    budget: SearchBudget | None = None,
) -> dict:
    """V31 real catalog READ + evidence + SEO + READY SQLite LAB.

    No claim de \`READY\` é publicação/consentimento. Input dos candidatos
    deve vir dos adaptadores de pesquisa/IA/verificação FINAL; booleanos
    humanos não são inferidos nem gerados por este módulo.
    """
    clock = _utc(now)
    route = _registered_route(site_key)
    campaign = route["campaign"]
    if (not isinstance(store, SQLiteReadyLabStore) or
            not isinstance(candidates, list) or len(candidates) > 100):
        raise UniversalReadyError("ready_preview_input_invalid")
    ready_before = store.ready_count(site_key, campaign)
    if ready_before >= policy.min_ready:
        return {"status":"BUFFER_HEALTHY_NO_REFILL", "ready_before":ready_before,
                "ready_after":ready_before, "created":0, "attempted":0,
                "rejected_reasons":{}, "publication_calls":0,
                "network_calls":0, "cms_draft_calls":0, "shopee_conversions":0}
    rejects: dict[str,int] = {}
    created = 0
    attempted = 0

    def reject(reason: str) -> None:
        rejects[reason] = rejects.get(reason, 0) + 1

    for item in candidates[:policy.candidate_attempt_limit]:
        if store.ready_count(site_key, campaign) >= policy.min_ready:
            break
        attempted += 1
        if not isinstance(item, dict):
            reject("CANDIDATE_INVALID")
            continue
        key = item.get("product_key")
        if not isinstance(key, str) or not SKU_PATTERN.fullmatch(key):
            reject("PRODUCT_KEY_INVALID")
            continue
        # Fonte autorizada: R2/SQLite V31 real, taxonomia e campanha,
        # NÃO basta o candidato marcar "approved": true.
        try:
            title, image, affiliate = _single_verified_offer(
                catalog, site_key=site_key, product_key=key,
                verified_site_route=route)
        except (CommerceArticleError, KeyError, ValueError):
            reject("CATALOG_OR_CAMPAIGN_NOT_VERIFIED")
            continue
        if not image or not affiliate:
            reject("PRODUCT_IMAGE_OR_AFFILIATE_MISSING")
            continue
        keyword, angle = item.get("keyword"), item.get("angle")
        if (not isinstance(keyword, str) or not 3 <= len(keyword.strip()) <= 160
                or not isinstance(angle, str)
                or not 6 <= len(angle.strip()) <= 200
                or not _normalize(keyword) or not _normalize(angle)):
            reject("EDITORIAL_INTENT_INVALID")
            continue
        seo = item.get("seo_audit")
        if (not isinstance(seo, dict) or
                seo.get("status") != "READY_FOR_EDITORIAL_SAFE_REVIEW" or
                seo.get("keyword_source_verified") is not True or
                seo.get("blockers") != []):
            reject("SEO_SAFE_GATE_REQUIRED")
            continue
        direct_package = item.get("evidence")
        package = direct_package
        cached = False
        if package is None:
            package = store.get_verified_evidence(
                site_key=site_key,product_key=key,product_title=title,
                now=clock,policy=policy)
            cached = package is not None
        try:
            evidence = evidence_whitelist(
                package=package, product_key=key,
                product_title=title, now=clock, policy=policy)
        except UniversalReadyError as exc:
            if budget:
                budget.event("CACHE_MISS")
            reject(str(exc))
            continue
        if direct_package is not None:
            # Escrita APENAS no SQLite do LAB: nunca R2/D1/CMS.
            store.cache_verified_evidence(
                site_key=site_key,product_key=key,product_title=title,
                package=direct_package,now=clock,policy=policy)
        if budget:
            budget.event("CACHE_HIT")
        used = item.get("used_evidence_ids")
        valid_ids = {e["evidence_id"] for e in evidence["allowed_facts"]}
        if (not isinstance(used, list) or
                any(not isinstance(x,str) for x in used) or
                not set(used).issubset(valid_ids)):
            reject("FACTS_WHITELIST_VIOLATION")
            continue
        body = item.get("content_html")
        article_title = item.get("article_title")
        if (not isinstance(body, str) or len(body) < 100 or
                not isinstance(article_title, str) or
                not 20 <= len(article_title.strip()) <= 150 or
                item.get("editorial_quality_verified") is not True):
            reject("EDITORIAL_QUALITY_GATE_REQUIRED")
            continue
        dedup = store.check(site_key=site_key, campaign=campaign,
                            product_key=key, keyword=keyword, angle=angle,
                            now=clock, policy=policy)
        if dedup:
            reject(dedup)
            continue
        if not store.add(
            site_key=site_key, campaign=campaign, product_key=key,
            keyword=keyword, angle=angle, title=article_title,
            content_html=body, evidence_verified_utc=evidence["verified_utc"],
            now=clock, policy=policy
        ):
            reject("BUFFER_OR_DUPLICATE_GATE")
            continue
        created += 1
    after = store.ready_count(site_key, campaign)
    return {
        "status": "BUFFER_HEALTHY" if after >= policy.min_ready
                  else "LOW_READY_FAIL_CLOSED",
        "ready_before": ready_before, "ready_after": after,
        "created": created, "attempted": attempted,
        "rejected_reasons": rejects,
        "publication_calls":0, "network_calls":0,
        "cms_draft_calls":0, "shopee_conversions":0,
    }
