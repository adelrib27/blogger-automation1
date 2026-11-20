"""C71 — adaptador de metadados READY em SQL compatível com Cloudflare D1.

Nenhum banco é provisionado, nenhuma conexão HTTP ocorre neste módulo.
A função query é INJETADA pelo ambiente explicitamente aprovado. Cada
ação concorrente é UMA instrução SQL atômica com RETURNING, não depende
de meta.changes (que pode refletir alterações cumulativas).
Não gera posts nem concede publicação LIVE. Não usa dados do Vida Pet.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timedelta, timezone
from typing import Callable

from .routing import sites
from .universal_evidence_ready import (
    UniversalReadyPolicy, UniversalReadyError, evidence_whitelist,
)


class D1SafeError(ValueError):
    pass


SITE_RE = re.compile(r"[a-z0-9_]{3,50}")
HEX_RE = re.compile(r"[a-f0-9]{64}")
NONCE_RE = re.compile(r"[A-Za-z0-9_-]{16,96}")
SKU_RE = re.compile(r"shopee:[0-9]+:[0-9]+")


def _params_site(site_key: str, campaign: str) -> None:
    if (not isinstance(site_key, str) or not SITE_RE.fullmatch(site_key)
            or not isinstance(campaign, str)
            or not re.fullmatch(r"[a-z0-9_-]{3,80}", campaign)):
        raise D1SafeError("tenant_identifier_invalid")
    route = sites().get(site_key)
    if (not isinstance(route, dict) or route.get("site_key") != site_key
            or route.get("campaign") != campaign
            or route.get("publish_enabled") is not False
            or route.get("platform") not in ("blogger", "wordpress")):
        raise D1SafeError("tenant_registry_campaign_mismatch")


def _clock(now_epoch: int) -> int:
    if type(now_epoch) is not int or not 1_700_000_000 <= now_epoch <= 4_000_000_000:
        raise D1SafeError("clock_invalid")
    return now_epoch


def _nonce(value: str) -> str:
    if not isinstance(value, str) or not NONCE_RE.fullmatch(value):
        raise D1SafeError("lease_owner_nonce_invalid")
    return value


class UniversalD1ReadyState:
    """A query runner executa prepared SQL + tupla de parâmetros e retorna
    list[dict] (resultado RETURNING/SELECT). Qualquer erro fecha a operação.
    Prod não deve aceitar runner vindo do candidato/IA.
    """

    def __init__(self, query: Callable[[str, tuple], list[dict]]):
        if not callable(query):
            raise D1SafeError("d1_query_runner_required")
        self._query = query

    def _call(self, sql: str, params: tuple) -> list[dict]:
        try:
            rows = self._query(sql, params)
        except Exception as exc:
            raise D1SafeError("d1_query_failed_closed") from exc
        if not isinstance(rows, list) or not all(
                isinstance(r, dict) for r in rows):
            raise D1SafeError("d1_query_result_untrusted")
        return rows

    def acquire_lease(
        self, *, site_key: str, campaign: str, lease_name: str,
        owner_nonce: str, now_epoch: int, ttl_seconds: int = 300
    ) -> bool:
        _params_site(site_key, campaign)
        _nonce(owner_nonce)
        t = _clock(now_epoch)
        if (lease_name not in ("refill", "writer", "firecrawl")
                or type(ttl_seconds) is not int
                or not 5 <= ttl_seconds <= 900):
            raise D1SafeError("lease_policy_invalid")
        rows = self._call("""
          INSERT INTO v31_ready_leases
            (site_key,campaign,lease_name,owner_nonce,acquired_epoch,expires_epoch)
          VALUES (?,?,?,?,?,?)
          ON CONFLICT(site_key,campaign,lease_name) DO UPDATE SET
            owner_nonce=excluded.owner_nonce,
            acquired_epoch=excluded.acquired_epoch,
            expires_epoch=excluded.expires_epoch
          WHERE v31_ready_leases.expires_epoch <= excluded.acquired_epoch
          RETURNING owner_nonce
        """, (site_key,campaign,lease_name,owner_nonce,t,t+ttl_seconds))
        return len(rows) == 1 and rows[0].get("owner_nonce") == owner_nonce

    def release_lease(
        self, *, site_key: str, campaign: str,
        lease_name: str, owner_nonce: str
    ) -> bool:
        _params_site(site_key, campaign)
        _nonce(owner_nonce)
        if lease_name not in ("refill", "writer", "firecrawl"):
            raise D1SafeError("lease_policy_invalid")
        rows = self._call("""
          DELETE FROM v31_ready_leases
          WHERE site_key=? AND campaign=? AND lease_name=? AND owner_nonce=?
          RETURNING owner_nonce
        """, (site_key,campaign,lease_name,owner_nonce))
        return len(rows) == 1 and rows[0].get("owner_nonce") == owner_nonce

    def reserve_ready(
        self, *, site_key: str, campaign: str,
        owner_nonce: str, fingerprint: str, product_key: str,
        html_sha256: str, evidence_sha256: str,
        now_epoch: int, min_ready: int = 3, cooldown_days: int = 30
    ) -> bool:
        """O lease de refill e limite do buffer são conferidos no MESMO INSERT.
        min_ready limita somente o buffer SIMULTÂNEO, nunca total histórico.
        """
        _params_site(site_key, campaign)
        _nonce(owner_nonce)
        t = _clock(now_epoch)
        if (any(not isinstance(x, str) or not HEX_RE.fullmatch(x)
                for x in (fingerprint,html_sha256,evidence_sha256))
                or not isinstance(product_key, str)
                or not SKU_RE.fullmatch(product_key)
                or type(min_ready) is not int or not 1 <= min_ready <= 100
                or type(cooldown_days) is not int
                or not 1 <= cooldown_days <= 365):
            raise D1SafeError("ready_job_input_invalid")
        rows = self._call("""
          INSERT INTO v31_ready_jobs
          (site_key,campaign,fingerprint,product_key,html_sha256,
           evidence_sha256,status,created_epoch,used_epoch)
          SELECT ?,?,?,?,?,?,'READY',?,NULL
          WHERE EXISTS (
            SELECT 1 FROM v31_ready_leases
            WHERE site_key=? AND campaign=? AND lease_name='refill'
              AND owner_nonce=? AND expires_epoch>?
          )
          AND (SELECT COUNT(*) FROM v31_ready_jobs
               WHERE site_key=? AND campaign=? AND status='READY') < ?
          AND NOT EXISTS (
            SELECT 1 FROM v31_ready_jobs
            WHERE site_key=? AND campaign=? AND product_key=?
              AND (status='READY' OR COALESCE(used_epoch,created_epoch)>?)
          )
          ON CONFLICT(site_key,campaign,fingerprint) DO NOTHING
          RETURNING fingerprint
        """, (site_key,campaign,fingerprint,product_key,html_sha256,
              evidence_sha256,t,site_key,campaign,owner_nonce,t,
              site_key,campaign,min_ready,site_key,campaign,product_key,
              t-cooldown_days*86400))
        return len(rows) == 1 and rows[0].get("fingerprint") == fingerprint

    def consume_one(
        self, *, site_key: str, campaign: str, owner_nonce: str,
        fingerprint: str, now_epoch: int
    ) -> bool:
        """Apenas reserva USED; jamais publica. Writer must do separate CMS gate."""
        _params_site(site_key, campaign)
        _nonce(owner_nonce)
        t = _clock(now_epoch)
        if not isinstance(fingerprint, str) or not HEX_RE.fullmatch(fingerprint):
            raise D1SafeError("ready_fingerprint_invalid")
        rows = self._call("""
          UPDATE v31_ready_jobs SET status='USED',used_epoch=?
          WHERE site_key=? AND campaign=? AND fingerprint=? AND status='READY'
          AND EXISTS (
            SELECT 1 FROM v31_ready_leases
            WHERE site_key=? AND campaign=? AND lease_name='writer'
              AND owner_nonce=? AND expires_epoch>?
          )
          RETURNING fingerprint
        """, (t,site_key,campaign,fingerprint,
              site_key,campaign,owner_nonce,t))
        return len(rows) == 1 and rows[0].get("fingerprint") == fingerprint

    def count_ready(self, *, site_key: str, campaign: str) -> int:
        _params_site(site_key, campaign)
        rows = self._call("""
          SELECT COUNT(*) AS n FROM v31_ready_jobs
          WHERE site_key=? AND campaign=? AND status='READY'
        """, (site_key,campaign))
        if (len(rows) != 1 or type(rows[0].get("n")) is not int
                or rows[0]["n"] < 0):
            raise D1SafeError("d1_count_untrusted")
        return rows[0]["n"]

    def cache_verified_evidence(
        self, *, site_key: str, campaign: str, owner_nonce: str,
        product_key: str, product_title: str, package: dict,
        now_epoch: int, policy: UniversalReadyPolicy = UniversalReadyPolicy()
    ) -> bool:
        """Certifica pacote usando whitelist C69 e guarda carimbo original.
        Acesso exige lease refill: nenhuma fonte inventada pelo crawler/IA.
        """
        _params_site(site_key, campaign)
        _nonce(owner_nonce)
        t = _clock(now_epoch)
        try:
            audit = evidence_whitelist(
                package=package, product_key=product_key,
                product_title=product_title,
                policy=policy, now=datetime.fromtimestamp(t, timezone.utc))
        except UniversalReadyError as exc:
            raise D1SafeError("evidence_not_verified") from exc
        raw = json.dumps(package, sort_keys=True, ensure_ascii=False)
        if len(raw.encode("utf-8")) > 100_000:
            raise D1SafeError("evidence_payload_too_large")
        verified = int(datetime.fromisoformat(
            audit["verified_utc"].replace("Z","+00:00")
        ).timestamp())
        expires = verified + policy.evidence_ttl_days * 86400
        sha = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        rows = self._call("""
          INSERT INTO v31_verified_evidence
           (site_key,campaign,product_key,product_title,verified_epoch,
            expires_epoch,evidence_sha256,payload_json)
          SELECT ?,?,?,?,?,?,?,?
          WHERE EXISTS (
            SELECT 1 FROM v31_ready_leases
            WHERE site_key=? AND campaign=? AND lease_name='refill'
              AND owner_nonce=? AND expires_epoch>?
          )
          ON CONFLICT(site_key,campaign,product_key) DO UPDATE SET
            product_title=excluded.product_title,
            verified_epoch=excluded.verified_epoch,
            expires_epoch=excluded.expires_epoch,
            evidence_sha256=excluded.evidence_sha256,
            payload_json=excluded.payload_json
          WHERE excluded.verified_epoch > v31_verified_evidence.verified_epoch
          RETURNING evidence_sha256
        """, (site_key,campaign,product_key,product_title,verified,
              expires,sha,raw,site_key,campaign,owner_nonce,t))
        return len(rows) == 1 and rows[0].get("evidence_sha256") == sha

    def get_verified_evidence(
        self, *, site_key: str, campaign: str,
        product_key: str, product_title: str, now_epoch: int,
        policy: UniversalReadyPolicy = UniversalReadyPolicy()
    ) -> dict | None:
        _params_site(site_key,campaign)
        t = _clock(now_epoch)
        if not isinstance(product_key,str) or not SKU_RE.fullmatch(product_key):
            raise D1SafeError("product_key_invalid")
        rows = self._call("""
          SELECT product_title, verified_epoch, expires_epoch,
                 evidence_sha256,payload_json
          FROM v31_verified_evidence
          WHERE site_key=? AND campaign=? AND product_key=?
            AND expires_epoch>?
        """, (site_key,campaign,product_key,t))
        if not rows:
            return None
        if len(rows) != 1 or rows[0].get("product_title") != product_title:
            return None
        try:
            raw = rows[0]["payload_json"]
            if (hashlib.sha256(raw.encode("utf-8")).hexdigest()
                    != rows[0]["evidence_sha256"]):
                return None
            package = json.loads(raw)
            evidence_whitelist(
                package=package,product_key=product_key,
                product_title=product_title,policy=policy,
                now=datetime.fromtimestamp(t,timezone.utc))
            return package
        except (ValueError,TypeError,KeyError,UniversalReadyError):
            return None

    def claim_search_budget(
        self, *, site_key: str, campaign: str, owner_nonce: str,
        now_epoch: int, kind: str, daily_cap: int
    ) -> bool:
        """Uma reserva de tentativa atômica POR SITE/DIA, antes de HTTP pago.
        Não é cotação do fornecedor nem garantia de custo monetário.
        """
        _params_site(site_key,campaign)
        _nonce(owner_nonce)
        t=_clock(now_epoch)
        if kind not in ("SEARCH", "HTTP") or type(daily_cap) is not int or not 1 <= daily_cap <= 100:
            raise D1SafeError("search_budget_policy_invalid")
        day=datetime.fromtimestamp(t,timezone.utc).date().isoformat()
        rows=self._call("""
          INSERT INTO v31_search_budget
            (site_key,campaign,day_utc,kind,used,max_allowed,blocked_until_epoch)
          SELECT ?,?,?,?,1,?,0
          WHERE EXISTS (
            SELECT 1 FROM v31_ready_leases
            WHERE site_key=? AND campaign=? AND lease_name='firecrawl'
              AND owner_nonce=? AND expires_epoch>?
          )
          ON CONFLICT(site_key,campaign,day_utc,kind) DO UPDATE SET
            used=v31_search_budget.used+1
          WHERE v31_search_budget.used < v31_search_budget.max_allowed
            AND v31_search_budget.blocked_until_epoch <= ?
            AND v31_search_budget.max_allowed=excluded.max_allowed
          RETURNING used
        """, (site_key,campaign,day,kind,daily_cap,
              site_key,campaign,owner_nonce,t,t))
        return len(rows) == 1 and isinstance(rows[0].get("used"), int)

    def block_search_on_429(
        self, *, site_key: str, campaign: str, owner_nonce: str,
        now_epoch: int, block_seconds: int = 3600
    ) -> int:
        """Circuit breaker persistente para cada classe de pesquisa do dia."""
        _params_site(site_key,campaign)
        _nonce(owner_nonce)
        t=_clock(now_epoch)
        if type(block_seconds) is not int or not 60 <= block_seconds <= 86400:
            raise D1SafeError("block_duration_invalid")
        day=datetime.fromtimestamp(t,timezone.utc).date().isoformat()
        rows=self._call("""
          UPDATE v31_search_budget
          SET blocked_until_epoch=?
          WHERE site_key=? AND campaign=? AND day_utc=?
          AND EXISTS (
            SELECT 1 FROM v31_ready_leases
            WHERE site_key=? AND campaign=? AND lease_name='firecrawl'
              AND owner_nonce=? AND expires_epoch>?
          )
          RETURNING kind
        """, (t+block_seconds,site_key,campaign,day,
              site_key,campaign,owner_nonce,t))
        return len(rows)
