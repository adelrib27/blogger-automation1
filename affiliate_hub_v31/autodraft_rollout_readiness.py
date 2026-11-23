"""V31 C133: prontidão declarativa para homologação DRAFT por site.

Somente leitura de arquivos locais, SEM credenciais, rede, conversão ou CMS.
Não declara nenhum site homologado nem autoriza LIVE.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .routing import sites
from .site_request_queue import VERIFIER_PROFILES, load_requests

PORTFOLIO = Path(__file__).with_name("BLOGGER_PORTFOLIO_FIVE_2026-11-23.json")


def build_readiness(portfolio: dict, routes: dict, active_requests: set[str],
                    reviewer_profiles: set[str]) -> dict:
    """Separar rota técnica, pedido real e perfil de verificação autônoma.

    A lista de cinco Blogger é somente PRIORIDADE; não limita a capacidade
    universal de cadastrar novos blogs pela pasta sites.d.
    """
    if not isinstance(portfolio, dict) or not isinstance(portfolio.get("kept"), list):
        raise ValueError("portfolio_invalid")
    if not isinstance(routes, dict):
        raise ValueError("routes_invalid")
    by_blog_id: dict[str, list[tuple[str, dict]]] = {}
    wp_sites = []
    for key, route in routes.items():
        if not isinstance(route, dict) or route.get("site_key") != key:
            raise ValueError("route_invalid")
        if route.get("platform") == "blogger":
            by_blog_id.setdefault(str(route.get("identifier")), []).append((key, route))
        elif route.get("platform") == "wordpress":
            wp_sites.append((key, route))
    entries = []
    seen = set()
    for blog in portfolio["kept"]:
        if not isinstance(blog, dict):
            raise ValueError("portfolio_entry_invalid")
        ident = str(blog.get("id", ""))
        if not ident.isdigit() or ident in seen:
            raise ValueError("portfolio_blog_id_invalid")
        seen.add(ident)
        matched = by_blog_id.get(ident, [])
        entries.append(_result("blogger", ident, blog.get("name", ""),
                               matched, active_requests, reviewer_profiles))
    for key, route in sorted(wp_sites):
        entries.append(_result("wordpress", str(route.get("identifier")), key,
                               [(key, route)], active_requests, reviewer_profiles))
    complete = sum(x["configured_for_draft_preflight"] for x in entries)
    by_status: dict[str, int] = {}
    for entry in entries:
        by_status[entry["status"]] = by_status.get(entry["status"], 0) + 1
    return {
        "schema": "v31-autodraft-rollout-readiness/v1",
        "mode": "OFFLINE_READ_ONLY",
        "scope": "five prioritized Blogger plus all registered WordPress",
        "universal_registered_routes": len(routes),
        "priority_sites": len(entries),
        "configured_for_draft_preflight": complete,
        "not_configured_for_draft_preflight": len(entries) - complete,
        "all_configured_for_draft_preflight": complete == len(entries) and bool(entries),
        "status_counts": by_status,
        "sites": entries,
        "cautions": [
            "Profile + request + route are prerequisites, NOT proof of CMS DRAFT canary",
            "No remote credentials, stock, quotas, signatures or LIVE flags checked",
            "Never enable all-sites rollout automatically",
            "Future Blogger/WordPress registrations remain declarative and unbounded"
        ]
    }


def _result(platform: str, identifier: str, label: str,
            matched: list[tuple[str, dict]], active_requests: set[str],
            reviewer_profiles: set[str]) -> dict:
    unique = len(matched) == 1
    key, route = matched[0] if unique else (None, {})
    route_safe = unique and route.get("platform") == platform and (
        route.get("publish_enabled") is False) and bool(route.get("campaign"))
    request = bool(key and key in active_requests)
    profile = bool(key and key in reviewer_profiles)
    configured = bool(route_safe and request and profile)
    if not unique:
        status = "ROUTE_MISSING" if not matched else "AMBIGUOUS_ROUTE"
    elif not route_safe:
        status = "ROUTE_UNSAFE"
    elif not profile and not request:
        status = "PROFILE_AND_REQUEST_MISSING"
    elif not profile:
        status = "REVIEW_PROFILE_MISSING"
    elif not request:
        status = "ENABLED_REQUEST_MISSING"
    else:
        status = "CONFIGURED_NOT_REMOTE_HOMOLOGATED"
    return {
        "platform": platform,
        "name": str(label),
        "identifier": identifier,
        "site_key": key,
        "route_registered_and_safe": bool(route_safe),
        "campaign_from_registry": route.get("campaign") if route_safe else None,
        "review_profile_present": profile,
        "enabled_request_present": request,
        "configured_for_draft_preflight": configured,
        "status": status,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="")
    parser.add_argument("--require-complete", action="store_true")
    args = parser.parse_args()
    portfolio = json.loads(PORTFOLIO.read_text(encoding="utf-8"))
    profiles = json.loads(VERIFIER_PROFILES.read_text(encoding="utf-8"))
    if not isinstance(profiles, dict):
        raise SystemExit("review_profile_schema_invalid")
    requests = {entry["site_key"] for entry in load_requests()}
    report = build_readiness(portfolio, sites(), requests, set(profiles))
    encoded = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        target = Path(args.output)
        if target.is_symlink():
            raise SystemExit("unsafe_report_destination")
        target.write_text(encoded, encoding="utf-8")
    print("V31_C133_READINESS=" + json.dumps({
        "priority_sites": report["priority_sites"],
        "configured": report["configured_for_draft_preflight"],
        "status_counts": report["status_counts"],
        "all_configured": report["all_configured_for_draft_preflight"],
        "mode": report["mode"]
    }, ensure_ascii=False))
    if args.require_complete and not report["all_configured_for_draft_preflight"]:
        raise SystemExit("readiness_incomplete_fail_closed")


if __name__ == "__main__":
    main()
