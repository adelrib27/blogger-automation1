"""C140 — guard universal de escopo e 50 simulações OFFLINE de preflight.

Nenhuma leitura externa, criação de post ou mutação de campanha. A elegibilidade
para preflight NUNCA é autorização de DRAFT ou LIVE.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

POLICY_PATH = Path(__file__).with_name("EDITORIAL_ACTIVE_SCOPE_POLICY.json")
EXPECTED_SCHEMA = "v31_editorial_active_scope_policy/v1"
REQUIRED_FLAGS = (
    "affiliate_campaign_verified",
    "independent_facts_verified",
    "real_product_image_verified",
    "original_seo_verified",
    "cms_no_duplicate_or_conflict",
)
VARIANTS = (
    "complete_simulated_preflight",
    "affiliate_unverified",
    "factual_source_missing",
    "cms_duplicate",
    "live_requested",
)
OLD_SOURCE_ROUTE = {
    "site_key": "blogger_ventiladores",
    "platform": "blogger",
    "identifier": "4473989735719981382",
    "campaign": "ventiladores",
    "publish_enabled": False,
}
EXPECTED_BY_CLASS = {
    "registered_active": (
        "PREFLIGHT_ONLY_NOT_AUTHORIZED",
        "AFFILIATE_CAMPAIGN_UNVERIFIED",
        "INDEPENDENT_FACTS_MISSING",
        "CMS_DUPLICATE_OR_CONFLICT",
        "LIVE_NOT_AUTHORIZED",
    ),
    "unregistered_active": ("ROUTE_NOT_REGISTERED",) * 5,
    "explicitly_excluded": ("EXCLUDED_BY_OWNER",) * 5,
    "historical_not_active": ("NOT_IN_VERIFIED_ACTIVE_INVENTORY",) * 5,
}


class EditorialScopeError(ValueError):
    pass


def load_policy(path: Path = POLICY_PATH) -> dict:
    try:
        policy = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeError):
        raise EditorialScopeError("scope_policy_unreadable") from None
    validate_policy(policy)
    return policy


def validate_policy(policy: dict) -> None:
    if (not isinstance(policy, dict) or policy.get("schema") != EXPECTED_SCHEMA
            or policy.get("enrollment") !=
            "ALL_EXISTING_ACTIVE_CONNECTED_BLOGGER_AND_WORDPRESS_EXCEPT_EXPLICIT_EXCLUSIONS"
            or policy.get("rollout", {}).get("global_third_party_writes_now_authorized") is not False
            or policy.get("rollout", {}).get("do_not_activate_live_during_onboarding") is not True):
        raise EditorialScopeError("scope_contract_invalid")
    sim = policy.get("simulation_gate", {})
    if (sim.get("minimum_cases_per_validation_cycle") != 10
            or sim.get("target_cases_per_validation_cycle") != 50
            or sim.get("maximum_cases_per_validation_cycle") != 50
            or sim.get("mode") != "OFFLINE_ONLY_NO_NETWORK_NO_MUTATIONS"):
        raise EditorialScopeError("simulation_policy_invalid")
    method = policy.get("universal_reference_methodology", {})
    if (method.get("architectural_status") !=
            "FUSED_INTO_ONE_UNIVERSAL_BLOGGER_WORDPRESS_V31_ENGINE_NOT_SEPARATE_SUBPROJECT"
            or not isinstance(method.get("components"), list)):
        raise EditorialScopeError("reference_must_be_universal")
    targets = [
        *(dict(x, platform="blogger") for x in policy.get("blogger", {}).get("current_targets", [])),
        *(dict(x, platform="wordpress") for x in policy.get("wordpress", {}).get("current_targets", [])),
    ]
    excluded = policy.get("blogger", {}).get("exclusions", [])
    if not targets or not excluded:
        raise EditorialScopeError("active_targets_or_exclusions_missing")
    all_keys, all_ids = [], []
    for entry in targets + excluded:
        key = entry.get("site_key")
        identifier = entry.get("id") if "id" in entry else entry.get("url")
        if (not isinstance(key, str) or not re.fullmatch(r"[a-z0-9_]{3,50}", key)
                or not isinstance(identifier, str) or not identifier
                or (entry in targets and type(entry.get("route_registered")) is not bool)):
            raise EditorialScopeError("scope_identity_invalid")
        all_keys.append(key)
        all_ids.append(identifier)
    if len(set(all_keys)) != len(all_keys) or len(set(all_ids)) != len(all_ids):
        raise EditorialScopeError("scope_duplicate_identity")
    if any(e.get("exclude_from_new_v31_editorial_article_automation") is not True
           for e in excluded):
        raise EditorialScopeError("scope_exclusion_not_enforced")


def scope_status(policy: dict, route: dict | None,
                 *, site_key: str | None = None) -> str:
    """Escopo para QUALQUER site pelo mesmo contrato, sem exceção por nicho."""
    validate_policy(policy)
    if route is not None and not isinstance(route, dict):
        return "ROUTE_UNTRUSTED"
    key = site_key if site_key is not None else (
        route.get("site_key") if route else None)
    if not isinstance(key, str) or not re.fullmatch(r"[a-z0-9_]{3,50}", key):
        return "SITE_ID_INVALID"
    route_id = route.get("identifier") if route else None
    excluded = policy["blogger"]["exclusions"]
    if any(key == e["site_key"] or (route_id is not None and route_id == e["id"])
           for e in excluded):
        return "EXCLUDED_BY_OWNER"
    if route is None:
        return "ROUTE_NOT_REGISTERED"
    if route.get("site_key") != key:
        return "ROUTE_IDENTITY_MISMATCH"
    if (route.get("platform") not in ("blogger", "wordpress")
            or route.get("publish_enabled") is not False
            or not isinstance(route.get("campaign"), str)
            or not re.fullmatch(r"[a-z0-9_-]{1,32}", route["campaign"])):
        return "ROUTE_UNSAFE"
    possible = [
        *(dict(x, platform="blogger") for x in policy["blogger"]["current_targets"]),
        *(dict(x, platform="wordpress") for x in policy["wordpress"]["current_targets"]),
    ]
    match = next((x for x in possible if x["site_key"] == key), None)
    if match is None:
        return "NOT_IN_VERIFIED_ACTIVE_INVENTORY"
    expected_id = match.get("id", match.get("url"))
    if match["platform"] != route["platform"] or expected_id != route_id:
        return "ROUTE_IDENTITY_MISMATCH"
    if match["route_registered"] is not True:
        return "ROUTE_NOT_VERIFIED"
    return "IN_SCOPE"


def is_route_in_active_scope(route: dict) -> bool:
    """Usado nos pontos de entrada universais de requests; não autoriza LIVE."""
    return scope_status(load_policy(), route) == "IN_SCOPE"


def evaluate_preflight(policy: dict, route: dict | None,
                       quality: dict, *, site_key: str) -> dict:
    status = scope_status(policy, route, site_key=site_key)
    if status == "IN_SCOPE":
        if not isinstance(quality, dict) or any(
                type(quality.get(flag)) is not bool for flag in REQUIRED_FLAGS):
            status = "QUALITY_INPUT_UNTRUSTED"
        elif quality.get("manual_live_requested") is not False:
            status = "LIVE_NOT_AUTHORIZED"
        elif not quality["affiliate_campaign_verified"]:
            status = "AFFILIATE_CAMPAIGN_UNVERIFIED"
        elif not quality["independent_facts_verified"]:
            status = "INDEPENDENT_FACTS_MISSING"
        elif not quality["real_product_image_verified"]:
            status = "REAL_PRODUCT_IMAGE_MISSING"
        elif not quality["original_seo_verified"]:
            status = "SEO_ORIGINALITY_MISSING"
        elif not quality["cms_no_duplicate_or_conflict"]:
            status = "CMS_DUPLICATE_OR_CONFLICT"
        else:
            status = "PREFLIGHT_ONLY_NOT_AUTHORIZED"
    return {
        "status": status,
        "passes_simulated_preflight": status == "PREFLIGHT_ONLY_NOT_AUTHORIZED",
        "allows_cms_write": False,
        "allows_live": False,
        "allows_affiliate_mutation": False,
        "network_calls": 0,
    }


def simulation_cases(policy: dict) -> list[dict]:
    """Dez identidades de naturezas distintas × cinco falhas/condições = 50."""
    validate_policy(policy)
    actors = []
    for platform in ("blogger", "wordpress"):
        for target in policy[platform]["current_targets"]:
            key = target["site_key"]
            route = None
            kind = "unregistered_active"
            if target["route_registered"]:
                route = {
                    "site_key": key, "platform": platform,
                    "identifier": target.get("id", target.get("url")),
                    "campaign": "verifiedfixture", "publish_enabled": False,
                }
                kind = "registered_active"
            actors.append((key, route, kind))
    for excluded in policy["blogger"]["exclusions"]:
        actors.append((excluded["site_key"], {
            "site_key": excluded["site_key"], "platform": "blogger",
            "identifier": excluded["id"], "campaign": "legacyfixture",
            "publish_enabled": False,
        }, "explicitly_excluded"))
    # Um futuro site ainda NÃO registrado é simulado genericamente, sem
    # associar a referência metodológica Vida Pet a qualquer blog-alvo.
    actors.append(("blogger_future_site_pending", None, "unregistered_active"))
    actors.append((OLD_SOURCE_ROUTE["site_key"], OLD_SOURCE_ROUTE,
                   "historical_not_active"))
    if len(actors) != 10:
        raise EditorialScopeError("snapshot_ten_actors_required")
    cases = []
    for key, route, kind in actors:
        for index, variant in enumerate(VARIANTS):
            quality = {flag: True for flag in REQUIRED_FLAGS}
            quality["manual_live_requested"] = False
            if variant == "affiliate_unverified":
                quality["affiliate_campaign_verified"] = False
            elif variant == "factual_source_missing":
                quality["independent_facts_verified"] = False
            elif variant == "cms_duplicate":
                quality["cms_no_duplicate_or_conflict"] = False
            elif variant == "live_requested":
                quality["manual_live_requested"] = True
            cases.append({
                "id": f"simulation_{len(cases)+1:02d}",
                "site_key": key, "route": route, "quality": quality,
                "variant": variant,
                "expected": EXPECTED_BY_CLASS[kind][index],
            })
    return cases


def run_simulations(*, count: int = 50, policy: dict | None = None) -> dict:
    if type(count) is not int or not 10 <= count <= 50:
        raise EditorialScopeError("simulation_count_must_be_10_to_50")
    policy = load_policy() if policy is None else policy
    cases = simulation_cases(policy)[:count]
    counts = {}
    for case in cases:
        actual = evaluate_preflight(policy, case["route"], case["quality"],
                                    site_key=case["site_key"])
        if (actual["status"] != case["expected"]
                or any((actual["allows_cms_write"], actual["allows_live"],
                        actual["allows_affiliate_mutation"], actual["network_calls"]))):
            raise EditorialScopeError("simulation_failed_closed_" + case["id"])
        counts[actual["status"]] = counts.get(actual["status"], 0) + 1
    return {
        "phase": "C140",
        "mode": "OFFLINE_SIMULATIONS_NO_REMOTE_WRITES",
        "executed": len(cases),
        "passed": len(cases),
        "failed": 0,
        "outcomes": counts,
        "cms_writes": 0,
        "r2_writes": 0,
        "d1_writes": 0,
        "affiliate_mutations": 0,
        "live_authorized": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="V31 10 a 50 simulações universais offline")
    parser.add_argument("--cases", type=int, default=50)
    args = parser.parse_args()
    try:
        result = run_simulations(count=args.cases)
    except Exception:
        print("V31_SCOPE_SIMULATIONS_FAILED_CLOSED")
        return 1
    print("V31_SCOPE_SIMULATIONS=" + json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
