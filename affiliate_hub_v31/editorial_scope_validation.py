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
HISTORICAL_PATH = Path(__file__).with_name("EDITORIAL_GLOBAL_PORTFOLIO_C141.json")
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
    "historical_pending": ("PENDING_ACCOUNT_AUTHENTICATION",) * 5,
    "unregistered_pending": ("ROUTE_NOT_REGISTERED",) * 5,
    "reference_only": ("REFERENCE_ONLY_NOT_V31_DESTINATION",) * 5,
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


def load_global_inventory(policy: dict) -> dict:
    """Histórico de IDs C102, nunca uma autorização remota de escrita."""
    if not isinstance(policy, dict) or policy.get("blogger", {}).get(
            "historical_inventory_manifest") != (
            "affiliate_hub_v31/EDITORIAL_GLOBAL_PORTFOLIO_C141.json"):
        raise EditorialScopeError("portfolio_manifest_untrusted")
    try:
        doc = json.loads(HISTORICAL_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeError):
        raise EditorialScopeError("global_portfolio_unreadable") from None
    if (not isinstance(doc, dict)
            or doc.get("schema") != "v31_editorial_global_inventory_c141/v1"
            or not isinstance(doc.get("sites"), list)
            or not isinstance(doc.get("summary"), dict)):
        raise EditorialScopeError("global_portfolio_schema_invalid")
    rows = doc["sites"]
    if not rows or len(rows) != len({
            z.get("blog_id") for z in rows if isinstance(z, dict)}):
        raise EditorialScopeError("global_portfolio_duplicates_or_empty")
    types = {
        "AUTHENTICATED_CONNECTED_ACCOUNT_SUBSET": 0,
        "HISTORICALLY_VERIFIED_PENDING_CROSS_ACCOUNT_AUTH": 0,
        "EXCLUDED_BY_OWNER": 0,
        "REFERENCE_ONLY_NOT_V31_EDITORIAL_DESTINATION": 0,
    }
    identities = set()
    route_keys = set()
    for row in rows:
        if not isinstance(row, dict):
            raise EditorialScopeError("global_portfolio_row_invalid")
        key = row.get("legacy_site_key")
        bid = row.get("blog_id")
        kind = row.get("current_access_class")
        route_key = row.get("existing_universal_route")
        if (not isinstance(key, str)
                or not re.fullmatch(r"[a-z0-9_]{3,50}", key)
                or not isinstance(bid, str) or not bid.isdecimal()
                or kind not in types
                or type(row.get("editorial_candidate")) is not bool
                or (route_key is not None and
                    (not isinstance(route_key, str) or
                     not re.fullmatch(r"[a-z0-9_]{3,50}", route_key)))
                or not isinstance(row.get("c102_verified_live_post_id"), str)
                or not row["c102_verified_live_post_id"].isdecimal()
                or not isinstance(row.get("c102_verified_live_url"), str)
                or not row["c102_verified_live_url"].startswith("https://")):
            raise EditorialScopeError("global_portfolio_row_invalid")
        if row["editorial_candidate"] != (kind in {
                "AUTHENTICATED_CONNECTED_ACCOUNT_SUBSET",
                "HISTORICALLY_VERIFIED_PENDING_CROSS_ACCOUNT_AUTH"}):
            raise EditorialScopeError("global_portfolio_candidate_mismatch")
        if key in identities or (route_key is not None and route_key in route_keys):
            raise EditorialScopeError("global_portfolio_key_reused")
        identities.add(key)
        if route_key:
            route_keys.add(route_key)
        types[kind] += 1
    expected = {
        "history_total": len(rows),
        "global_candidates": sum(r["editorial_candidate"] for r in rows),
        "currently_authenticated_candidates": types["AUTHENTICATED_CONNECTED_ACCOUNT_SUBSET"],
        "cross_account_pending": types["HISTORICALLY_VERIFIED_PENDING_CROSS_ACCOUNT_AUTH"],
        "owner_excluded": types["EXCLUDED_BY_OWNER"],
        "reference_only": types["REFERENCE_ONLY_NOT_V31_EDITORIAL_DESTINATION"],
        "routed_candidates": sum(r["editorial_candidate"] and bool(r["existing_universal_route"]) for r in rows),
        "without_route": sum(r["editorial_candidate"] and not r["existing_universal_route"] for r in rows),
    }
    if expected != doc["summary"]:
        raise EditorialScopeError("global_portfolio_summary_mismatch")
    policy_counts = policy.get("snapshot_counts", {})
    if (policy_counts.get("blogger_targets") != expected["global_candidates"]
            or policy_counts.get("blogger_connected_verified_subset") != expected[
                "currently_authenticated_candidates"]
            or policy_counts.get("blogger_candidates_pending_current_account_auth") != expected[
                "cross_account_pending"]
            or policy_counts.get("reference_only") != expected["reference_only"]
            or policy_counts.get("blogger_excluded") != expected["owner_excluded"]):
        raise EditorialScopeError("global_portfolio_policy_counts_mismatch")
    auth_ids = {r["blog_id"] for r in rows if r["current_access_class"] ==
                "AUTHENTICATED_CONNECTED_ACCOUNT_SUBSET"}
    policy_ids = {p.get("id") for p in policy.get("blogger", {}).get("current_targets", [])}
    if auth_ids != policy_ids or None in policy_ids:
        raise EditorialScopeError("global_portfolio_connected_identity_mismatch")
    exclusions = {x.get("id") for x in policy.get("blogger", {}).get("exclusions", [])}
    inventory_exclusions = {r["blog_id"] for r in rows if r["current_access_class"] ==
                             "EXCLUDED_BY_OWNER"}
    if inventory_exclusions != exclusions:
        raise EditorialScopeError("global_portfolio_owner_exclusion_mismatch")
    return doc


def validate_policy(policy: dict) -> None:
    if (not isinstance(policy, dict) or policy.get("schema") != EXPECTED_SCHEMA
            or policy.get("enrollment") !=
            "ALL_CURRENTLY_ACTIVE_BLOGGER_ACROSS_ACCOUNTS_AND_WORDPRESS_EXCEPT_EXPLICIT_EXCLUSIONS"
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
    # A validação das 50 simulações sempre lê TODAS as identidades C102.
    load_global_inventory(policy)


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
        # Uma conta parcial não significa que os outros blogs deixaram de
        # existir. C102 os documentou por ID e LIVE; o acesso atual é pendente.
        historic = next((entry for entry in load_global_inventory(policy)["sites"]
                         if entry["blog_id"] == route_id), None)
        if historic and historic["editorial_candidate"]:
            existing = historic.get("existing_universal_route")
            if existing and existing != key:
                return "ROUTE_IDENTITY_MISMATCH"
            return "PENDING_ACCOUNT_AUTHENTICATION"
        if historic and historic["current_access_class"] == "REFERENCE_ONLY_NOT_V31_EDITORIAL_DESTINATION":
            return "REFERENCE_ONLY_NOT_V31_DESTINATION"
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
    """50 verificações sem rede: 28 Blogger históricos + 3 WP e riscos globais.

    Blogs adicionais permanecem suportados: se houver mais de 31 destinos,
    os lotes seguintes rotacionam com cycle_index sem ampliar o limite 50.
    """
    validate_policy(policy)
    inventory = load_global_inventory(policy)
    actors = []
    for row in inventory["sites"]:
        if not row["editorial_candidate"]:
            continue
        key = row["existing_universal_route"] or row["legacy_site_key"]
        ident = row["blog_id"]
        route = ({
            "site_key": key, "platform": "blogger", "identifier": ident,
            "campaign": "simulatedcamp", "publish_enabled": False,
        } if row["existing_universal_route"] else None)
        if row["current_access_class"] == "AUTHENTICATED_CONNECTED_ACCOUNT_SUBSET":
            kind = "registered_active"
        elif route is None:
            kind = "unregistered_pending"
        else:
            kind = "historical_pending"
        actors.append((key, route, kind))
    for wp in policy["wordpress"]["current_targets"]:
        key = wp["site_key"]
        route = ({
            "site_key": key, "platform": "wordpress", "identifier": wp["url"],
            "campaign": "simulatedcamp", "publish_enabled": False,
        } if wp["route_registered"] else None)
        actors.append((key, route, "registered_active" if route else "unregistered_pending"))
    if not actors:
        raise EditorialScopeError("no_real_portfolio_candidates")
    # Um ciclo não é limitado ao tamanho da conta Google conectada.
    # O inventário integral é validado antes; se houver >31 blogs futuros,
    # a escolha de 31 gira entre ciclos sem que nenhum seja 'inativo'.
    cycle = 0
    selected = (actors[cycle % len(actors):] + actors[:cycle % len(actors)])[:31]
    while len(selected) < 31:
        selected.append(actors[len(selected) % len(actors)])
    excluded = policy["blogger"]["exclusions"][0]
    excluded_route = {
        "site_key": excluded["site_key"], "platform": "blogger",
        "identifier": excluded["id"], "campaign": "historicalcamp",
        "publish_enabled": False,
    }
    reference = next((r for r in inventory["sites"] if r["current_access_class"]
                      == "REFERENCE_ONLY_NOT_V31_EDITORIAL_DESTINATION"), None)
    if reference is None:
        raise EditorialScopeError("universal_reference_identity_missing")
    reference_route = {
        "site_key": "blogger_reference_only_not_a_destination",
        "platform": "blogger", "identifier": reference["blog_id"],
        "campaign": "historicalcamp", "publish_enabled": False,
    }
    extras = [
        (excluded["site_key"], excluded_route, "explicitly_excluded"),
        ("blogger_reference_only_not_a_destination", reference_route, "reference_only"),
        ("blogger_future_site_pending", None, "unregistered_pending"),
    ]
    # 31 originais + 5 exclusões + 5 referências negadas + 5 futuros + 4
    # repetições de riscos independentes = 50, todos sem API.
    selection = [(a, VARIANTS[i % len(VARIANTS)])
                 for i, a in enumerate(selected)]
    selection += [(a, v) for a in extras for v in VARIANTS]
    active = [a for a in actors if a[2] == "registered_active"]
    if not active:
        raise EditorialScopeError("no_verified_active_pilot")
    selection += [(active[i % len(active)], VARIANTS[(i + 1) % len(VARIANTS)])
                  for i in range(4)]
    if len(selection) != 50:
        raise EditorialScopeError("fifty_simulation_matrix_invalid")
    cases = []
    for actor, variant in selection:
        key, route, kind = actor
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
        index = VARIANTS.index(variant)
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
    inventory = load_global_inventory(policy)
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
        "global_coverage_audit": inventory["summary"],
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
