"""C148 — homologação universal SAFE: um piloto primário, todos os sites.

Radar Tech BR é somente a preferência inicial do CLI. Nenhum cadastro, limite,
nicho ou regra de geração no núcleo depende do Radar. A rotina só consulta
CMS (GET autenticado), D1 (SELECT) e snapshot R2 (GET + SQLite read-only).

NÃO gera texto, não chama conversor Shopee, não altera CMS/D1/R2, não publica.
Um resultado de prontidão de leitura NÃO autoriza DRAFT nem LIVE.
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from .campaign_cache_readiness import inspect_campaign_cache
from .catalog import Catalog
from .d1_http_runner import CloudflareD1HTTPRunner
from .editorial_scope_validation import is_route_in_active_scope
from .r2_state import R2State, verify_database
from .reviewed_draft_delivery import read_draft_history
from .routing import sites
from .site_request_queue import MAX_BUDGET, REQUESTS_DIR, VERIFIER_PROFILES, load_requests

DEFAULT_PRIMARY = "wordpress_radartechbr"  # ordem da auditoria, nunca writer
SAFE_STATUSES = frozenset({"READY", "USED"})
SITE_KEY = re.compile(r"[a-z0-9_]{3,50}\Z")


class PilotAuditError(ValueError):
    """Sem strings da rede, URLs assinadas, segredos, SQL ou HTML."""


def _request_modes(directory: Path = REQUESTS_DIR) -> dict[str, str]:
    """Consulta arquivos já validados por load_requests: enabled ou staged."""
    load_requests(directory)  # valida esquema/escopo de todas as demandas
    result = {}
    for path in sorted(directory.glob("*.json")):
        item = json.loads(path.read_text(encoding="utf-8"))
        result[item["site_key"]] = ("ENABLED" if item["enabled"] else "STAGED_DISABLED")
    return result


def plan(*, primary: str = DEFAULT_PRIMARY, routes: dict | None = None,
         request_modes: dict | None = None,
         reviewer_profiles: dict | None = None) -> dict:
    """Monta carteira a partir de rotas verificadas; injeção só para simulações."""
    routes = sites() if routes is None else routes
    request_modes = _request_modes() if request_modes is None else request_modes
    reviewer_profiles = (json.loads(VERIFIER_PROFILES.read_text(encoding="utf-8"))
                         if reviewer_profiles is None else reviewer_profiles)
    if (not isinstance(primary, str) or not SITE_KEY.fullmatch(primary)
            or not isinstance(routes, dict) or not isinstance(request_modes, dict)
            or not isinstance(reviewer_profiles, dict)):
        raise PilotAuditError("pilot_inputs_invalid")
    active = {}
    for key, route in routes.items():
        if (not isinstance(key, str) or not isinstance(route, dict)
                or route.get("site_key") != key):
            raise PilotAuditError("pilot_route_untrusted")
        if not is_route_in_active_scope(route):
            continue
        if (route.get("platform") not in ("blogger", "wordpress")
                or route.get("publish_enabled") is not False
                or not isinstance(route.get("campaign"), str)
                or not isinstance(route.get("allowed_niches"), list)):
            raise PilotAuditError("pilot_active_route_invalid")
        active[key] = route
    if primary not in active:
        raise PilotAuditError("pilot_primary_not_in_active_scope")
    ordered = [primary, *sorted(x for x in active if x != primary)]
    reports = []
    for key in ordered:
        route = active[key]
        mode = request_modes.get(key, "MISSING")
        profile = reviewer_profiles.get(key)
        has_profile = isinstance(profile, dict) and bool(profile.get("offers"))
        identity_match = (has_profile and isinstance(profile.get("home"), str)
                          and (route["platform"] != "wordpress" or
                               profile["home"] == route["identifier"]))
        if mode != "ENABLED":
            blocker = ("PILOT_REQUEST_DISABLED" if mode == "STAGED_DISABLED"
                       else "NO_EDITORIAL_REQUEST")
        elif not has_profile:
            blocker = "VERIFIED_SOURCE_PROFILE_MISSING"
        elif not identity_match:
            blocker = "REVIEW_PROFILE_IDENTITY_MISMATCH"
        else:
            blocker = "E2E_DRAFT_NOT_PROVEN_BY_READONLY"
        reports.append({
            "site_key": key, "platform": route["platform"], "campaign": route["campaign"],
            "is_primary": key == primary,
            "request_state": mode,
            "review_profile_present": bool(has_profile),
            "configured_for_independent_review": blocker == "E2E_DRAFT_NOT_PROVEN_BY_READONLY",
            "blocker": blocker,
            "can_write_draft": False, "can_publish_live": False,
        })
    return {
        "mode": "UNIVERSAL_CONFIG_SCOPE_READ_ONLY",
        "primary": primary, "active_sites": len(reports),
        "platforms": {platform: sum(x["platform"] == platform for x in reports)
                      for platform in ("blogger", "wordpress")},
        "reports": reports, "cms_writes": 0, "d1_writes": 0,
        "r2_writes": 0, "affiliate_mutations": 0, "automatic_live_authorized": False,
    }


def _valid_d1_counts(rows) -> dict:
    if (not isinstance(rows, list) or len(rows) > 5
            or any(not isinstance(x, dict) or x.get("status") not in SAFE_STATUSES
                   or type(x.get("total")) is not int or not 0 <= x["total"] <= 5000
                   for x in rows)):
        raise PilotAuditError("pilot_d1_job_counts_untrusted")
    if len(set(x["status"] for x in rows)) != len(rows):
        raise PilotAuditError("pilot_d1_duplicate_job_status")
    return {x["status"]: x["total"] for x in rows}


def live_readonly(*, primary: str = DEFAULT_PRIMARY, query=None,
                  storage=None, history_reader=None,
                  routes: dict | None = None, request_modes=None,
                  reviewer_profiles=None, all_cms: bool = False) -> dict:
    """Read-only remoto: falha de qualquer fonte não libera artefatos."""
    blueprint = plan(primary=primary, routes=routes, request_modes=request_modes,
                     reviewer_profiles=reviewer_profiles)
    registry = sites() if routes is None else routes
    check = {"cms": "NOT_CHECKED", "d1": "NOT_CHECKED", "r2": "NOT_CHECKED"}
    rows = [dict(item) for item in blueprint["reports"]]
    # Não passar runner D1 com allow_mutations: leitura SELECT é suficiente.
    try:
        sql = (CloudflareD1HTTPRunner.from_environment(allow_mutations=False)
               if query is None else query)
        if not callable(sql):
            raise PilotAuditError("pilot_d1_reader_invalid")
        today = datetime.now(timezone.utc).date().isoformat()
        for entry in rows:
            tenant = (entry["site_key"], entry["campaign"])
            counts = _valid_d1_counts(sql(
                "SELECT status, COUNT(*) AS total FROM v31_ready_jobs "
                "WHERE site_key=? AND campaign=? AND status IN ('READY','USED') "
                "GROUP BY status ORDER BY status", tenant))
            attempts = sql(
                "SELECT COUNT(*) AS total FROM v31_shopee_conversion_attempts "
                "WHERE campaign=? AND day_utc=?", (entry["campaign"], today))
            if (not isinstance(attempts, list) or len(attempts) != 1
                    or type(attempts[0].get("total")) is not int
                    or not 0 <= attempts[0]["total"] <= MAX_BUDGET):
                raise PilotAuditError("pilot_affiliate_attempts_untrusted")
            entry["d1_ready_jobs"] = counts.get("READY", 0)
            entry["d1_used_jobs"] = counts.get("USED", 0)
            entry["affiliate_attempts_today"] = attempts[0]["total"]
        check["d1"] = "READ_ONLY_CONFIRMED"
    except Exception:
        check["d1"] = "BLOCKED_D1_SELECT"
    try:
        store = R2State.from_env() if storage is None else storage
        with tempfile.TemporaryDirectory(prefix="v31-pilot-readonly-") as tmp:
            snapshot = Path(tmp) / "catalog.sqlite3"
            if store.restore_to(snapshot) is not True:
                raise PilotAuditError("pilot_snapshot_missing")
            verify_database(snapshot)
            db = sqlite3.connect("file:" + str(snapshot) + "?mode=ro", uri=True)
            try:
                db.execute("PRAGMA query_only=ON")
                catalog = Catalog.__new__(Catalog)
                catalog.db = db
                for entry in rows:
                    result = inspect_campaign_cache(catalog, registry[entry["site_key"]])
                    entry["catalog_candidates_sample"] = result["catalog_candidates"]
                    entry["cached_links_exact_campaign_sample"] = result["cached_exact_campaign"]
                    entry["affiliate_link_verified_for_draft"] = False
                    if all_cms:
                        exact = inspect_campaign_cache(catalog, registry[entry["site_key"]], cached_only=True)
                        cached_items = exact.get("items", [])
                        if not isinstance(cached_items, list) or len(cached_items) > 4:
                            raise PilotAuditError("pilot_cached_sample_untrusted")
                        entry["exact_cached_candidate_sample"] = []
                        for item in cached_items:
                            sku = item.get("product_key") if isinstance(item, dict) else None
                            title = item.get("title") if isinstance(item, dict) else None
                            if (not isinstance(sku, str) or not re.fullmatch(r"shopee:[0-9]+:[0-9]+", sku)
                                    or not isinstance(title, str) or not 1 <= len(title) <= 145
                                    or item.get("cached_for_exact_campaign") is not True):
                                raise PilotAuditError("pilot_cached_sample_untrusted")
                            title = re.sub(r"[\x00-\x1f\x7f]", " ", title).strip()
                            if not title:
                                raise PilotAuditError("pilot_cached_sample_untrusted")
                            entry["exact_cached_candidate_sample"].append({
                                "product_key": sku, "title": title,
                                "cached_for_exact_campaign": True,
                                "manufacturer_facts_verified": False,
                                "eligible_for_draft_write": False})
                        entry["cached_links_exact_campaign_total"] = db.execute(
                            "SELECT COUNT(*) FROM affiliate_links WHERE campaign=?",
                            (entry["campaign"],)).fetchone()[0]
                    if entry["is_primary"] or all_cms:
                        items = result.get("items", [])
                        if not isinstance(items, list) or len(items) > 4:
                            raise PilotAuditError("pilot_primary_sample_untrusted")
                        sample = []
                        for item in items:
                            sku = item.get("product_key") if isinstance(item, dict) else None
                            title = item.get("title") if isinstance(item, dict) else None
                            cached = item.get("cached_for_exact_campaign") if isinstance(item, dict) else None
                            if (not isinstance(sku, str)
                                    or not re.fullmatch(r"shopee:[0-9]+:[0-9]+", sku)
                                    or not isinstance(title, str)
                                    or not 1 <= len(title) <= 145
                                    or type(cached) is not bool):
                                raise PilotAuditError("pilot_primary_sample_untrusted")
                            safe_title = re.sub(r"\\[nrt]", " ", title)
                            safe_title = re.sub(r"[\x00-\x1f\x7f]", " ", safe_title).strip()
                            if not safe_title:
                                raise PilotAuditError("pilot_primary_sample_untrusted")
                            sample.append({
                                "product_key": sku, "title": safe_title,
                                "cached_for_exact_campaign": cached,
                                "manufacturer_facts_verified": False,
                                "cms_legacy_duplicate_checked": False,
                                "eligible_for_draft_write": False,
                            })
                        entry["primary_candidate_sample" if entry["is_primary"] else "candidate_sample"] = sample
            finally:
                db.close()
        check["r2"] = "READ_ONLY_CONFIRMED"
    except Exception:
        check["r2"] = "BLOCKED_R2_READ"
    # Ações autenticadas feitas por outros conectores não comprovam que os
    # segredos de GitHub Actions estão configurados para o MESMO site.
    # Não mostrar nomes de usuário, tokens, corpos de erro ou URLs privadas.
    targets = rows if all_cms else rows[:1]
    for entry in targets:
        key = entry["site_key"]
        status = "NOT_CHECKED"
        missing_cms_credentials = False
        if history_reader is None and registry[key]["platform"] == "wordpress":
            from .automatic_wordpress_drafts import credentials_for
            try:
                credentials_for(key)
            except Exception:
                missing_cms_credentials = True
                status = "BLOCKED_CMS_SITE_CREDENTIALS_UNAVAILABLE"
        if not missing_cms_credentials:
            try:
                read = read_draft_history if history_reader is None else history_reader
                cms = read(key)
                if (not isinstance(cms, dict) or cms.get("site_key") != key
                        or type(cms.get("count")) is not int or cms["count"] < 0
                        or not all(isinstance(cms.get(field), list)
                                   for field in ("keys", "slugs", "prose"))):
                    raise PilotAuditError("pilot_cms_history_untrusted")
                entry["cms_history_read"] = True
                if registry[key]["platform"] == "wordpress":
                    entry["cms_v31_prefixed_slugs_detected"] = cms["count"]
                else:
                    entry["cms_history_records_scanned"] = cms["count"]
                entry["cms_legacy_duplicate_crosscheck"] = "NOT_PERFORMED"
                status = "AUTHENTICATED_GET_CONFIRMED"
            except Exception:
                status = "BLOCKED_AUTHENTICATED_CMS_GET"
        entry["cms_check"] = status
    check["cms"] = ("AUTHENTICATED_GET_CONFIRMED"
                    if all(x["cms_check"] == "AUTHENTICATED_GET_CONFIRMED" for x in targets)
                    else targets[0]["cms_check"] if not all_cms
                    else "BLOCKED_ONE_OR_MORE_CMS_GET")
    success = all(value in ("READ_ONLY_CONFIRMED", "AUTHENTICATED_GET_CONFIRMED")
                  for value in check.values())
    return {
        **blueprint, "mode": "UNIVERSAL_REAL_READONLY_CHECK",
        "checks": check,
        "status": "READ_ONLY_SOURCES_CONFIRMED_NOT_DRAFT_AUTHORIZED" if success
                  else "READ_ONLY_SOURCE_CHECK_INCOMPLETE",
        "reports": rows,
        "new_drafts_proven": 0,
        "cms_writes": 0, "d1_writes": 0, "r2_writes": 0,
        "affiliate_mutations": 0, "automatic_live_authorized": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Homologação universal SAFE do V31")
    parser.add_argument("--primary-site-key", default=DEFAULT_PRIMARY)
    parser.add_argument("--real-readonly", action="store_true")
    parser.add_argument("--all-cms", action="store_true", help="GET de todas as rotas ativas; cache total por campanha")
    # C151: destino local fixo. Nunca aceitar nome arbitrario nem subir segredos.
    parser.add_argument("--report-json", choices=["v31_pilot_readonly_report.json"],
                        default=None)
    args = parser.parse_args()
    try:
        output = (live_readonly(primary=args.primary_site_key, all_cms=args.all_cms)
                  if args.real_readonly else plan(primary=args.primary_site_key))
    except Exception:
        print("V31_PILOT_READINESS_FAILED_CLOSED")
        return 2
    sanitized = json.dumps(output, ensure_ascii=False, sort_keys=True)
    print("V31_PILOT_READINESS=" + sanitized)
    if args.report_json:
        try:
            Path(args.report_json).write_text(sanitized + "\n", encoding="utf-8")
        except OSError:
            print("V31_PILOT_REPORT_PERSISTENCE_FAILED_CLOSED")
            return 4
    # Em teste real, uma fonte inacessível torna a homologação incompleta.
    # Nunca publicar status SUCCESS de canário se CMS, D1 ou R2 não responder.
    if args.real_readonly and output["status"] != "READ_ONLY_SOURCES_CONFIRMED_NOT_DRAFT_AUTHORIZED":
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
