"""V31 C143: current authenticated Blogger/WordPress scope; deleted Blogger denylist.

The C102/C141 historical site manifest is RETIRED. Never use it for planning.
50 deterministic offline simulations per critical workflow, no network or writes.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

POLICY_PATH = Path(__file__).with_name("EDITORIAL_ACTIVE_SCOPE_POLICY.json")
TOMBSTONES_PATH = Path(__file__).with_name("EDITORIAL_DELETED_BLOGGER_TOMBSTONES_C143.json")
EXPECTED_SCHEMA = "v31_editorial_active_scope_policy/v1"
TOMBSTONE_SCHEMA = "v31_deleted_blogger_tombstones_c143/v1"
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
EXPECTED_BY_CLASS = {
    "registered_active": (
        "PREFLIGHT_ONLY_NOT_AUTHORIZED",
        "AFFILIATE_CAMPAIGN_UNVERIFIED",
        "INDEPENDENT_FACTS_MISSING",
        "CMS_DUPLICATE_OR_CONFLICT",
        "LIVE_NOT_AUTHORIZED",
    ),
    "deleted_by_owner": ("DELETED_BY_OWNER",) * 5,
    "explicitly_excluded": ("EXCLUDED_BY_OWNER",) * 5,
    "active_unonboarded": ("CMS_ACTIVE_ONBOARDING_REQUIRED",) * 5,
    "unregistered": ("ROUTE_NOT_REGISTERED",) * 5,
}


class EditorialScopeError(ValueError):
    pass


def load_tombstones(policy: dict) -> dict:
    """Minimal denylist; no post/affiliate history and never a source of offers."""
    path = policy.get("blogger", {}).get("deleted_tombstones_manifest")
    if path != "affiliate_hub_v31/EDITORIAL_DELETED_BLOGGER_TOMBSTONES_C143.json":
        raise EditorialScopeError("deleted_tombstones_path_untrusted")
    try:
        doc = json.loads(TOMBSTONES_PATH.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        raise EditorialScopeError("deleted_tombstones_unreadable") from None
    if (not isinstance(doc, dict) or doc.get("schema") != TOMBSTONE_SCHEMA
            or doc.get("state") != "DELETED_BY_OWNER_DO_NOT_RECREATE_OR_REAUTHENTICATE"
            or not isinstance(doc.get("deleted_blogs"), list)):
        raise EditorialScopeError("deleted_tombstones_schema_invalid")
    rows = doc["deleted_blogs"]
    ids, keys, routekeys = set(), set(), set()
    for row in rows:
        if not isinstance(row, dict):
            raise EditorialScopeError("deleted_tombstone_row_invalid")
        bid, key, oldroute = row.get("blog_id"), row.get("legacy_site_key"), row.get("old_route_key")
        if (not isinstance(bid, str) or not re.fullmatch(r"\d{10,24}", bid)
                or not isinstance(key, str) or not re.fullmatch(r"[a-z0-9_]{3,50}", key)
                or oldroute is not None and (
                    not isinstance(oldroute, str) or not re.fullmatch(r"[a-z0-9_]{3,50}", oldroute))
                or row.get("deleted_by_owner") is not True
                or row.get("eligible_for_editorial") is not False
                or row.get("allow_reenroll") is not False
                or bid in ids or key in keys or oldroute is not None and oldroute in routekeys):
            raise EditorialScopeError("deleted_tombstone_identity_or_guard_invalid")
        ids.add(bid)
        keys.add(key)
        if oldroute:
            routekeys.add(oldroute)
    if len(rows) != doc.get("deleted_count") or len(rows) != policy.get("blogger", {}).get("deleted_by_owner_count"):
        raise EditorialScopeError("deleted_tombstone_count_mismatch")
    active = policy.get("blogger", {}).get("current_targets", [])
    exclusions = policy.get("blogger", {}).get("exclusions", [])
    all_current_ids = {x.get("id") for x in active + exclusions}
    pending = policy.get("blogger", {}).get("connected_active_blogs_pending_onboarding", [])
    existing = doc.get("existing_active_blogger_not_onboarded", {})
    if (not isinstance(pending, list) or not pending
            or not isinstance(existing, dict)
            or not isinstance(existing.get("blog_id"), str)
            or existing.get("state") != "EXISTING_ACTIVE_BLOGGER_CMS_VERIFIED_V31_ROUTE_CAMPAIGN_PENDING"):
        raise EditorialScopeError("existing_blogger_identity_contract_invalid")
    pending_ids = {x.get("id") for x in pending if isinstance(x, dict)}
    pending_keys = {x.get("site_key") for x in pending if isinstance(x, dict)}
    if (existing["blog_id"] in ids or existing["blog_id"] in all_current_ids
            or ids & pending_ids or keys & pending_keys or routekeys & pending_keys
            or pending_ids & all_current_ids
            or len(pending_ids) != len(pending) or len(pending_keys) != len(pending)
            or sum(x.get("id") == existing["blog_id"] and
                   x.get("site_key") == existing.get("site_key")
                   for x in pending if isinstance(x, dict)) != 1
            or ids & all_current_ids
            or keys & {x.get("site_key") for x in active + exclusions}
            or routekeys & {x.get("site_key") for x in active + exclusions}):
        raise EditorialScopeError("deleted_identity_overlaps_current")
    scope_ids = {x.get("blog_id") for x in doc.get("current_blogger_targets", [])}
    if scope_ids != {x.get("id") for x in active}:
        raise EditorialScopeError("deleted_manifest_current_identity_mismatch")
    owner_exclusion = doc.get("excluded_existing", {})
    if {owner_exclusion.get("blog_id")} != {e.get("id") for e in exclusions}:
        raise EditorialScopeError("deleted_manifest_exclusion_mismatch")
    return doc


def load_policy(path: Path = POLICY_PATH) -> dict:
    try:
        policy = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        raise EditorialScopeError("scope_policy_unreadable") from None
    validate_policy(policy)
    return policy


def validate_policy(policy: dict) -> None:
    if (not isinstance(policy, dict) or policy.get("schema") != EXPECTED_SCHEMA
            or policy.get("enrollment") !=
                "CURRENTLY_AUTHENTICATED_ACTIVE_BLOGGER_AND_WORDPRESS_EXCEPT_DELETED_OR_EXCLUDED"
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
    exclusions = policy.get("blogger", {}).get("exclusions", [])
    if not targets or not exclusions:
        raise EditorialScopeError("active_targets_or_exclusions_missing")
    allkeys, allids = [], []
    for entry in targets + exclusions:
        key = entry.get("site_key")
        identifier = entry.get("id", entry.get("url"))
        if (not isinstance(key, str) or not re.fullmatch(r"[a-z0-9_]{3,50}", key)
                or not isinstance(identifier, str) or not identifier
                or entry in targets and type(entry.get("route_registered")) is not bool):
            raise EditorialScopeError("scope_identity_invalid")
        allkeys.append(key)
        allids.append(identifier)
    if len(set(allkeys)) != len(allkeys) or len(set(allids)) != len(allids):
        raise EditorialScopeError("scope_duplicate_identity")
    if any(e.get("exclude_from_new_v31_editorial_article_automation") is not True
           for e in exclusions):
        raise EditorialScopeError("scope_exclusion_not_enforced")
    pending = policy.get("blogger", {}).get("connected_active_blogs_pending_onboarding", [])
    if not isinstance(pending, list) or not pending:
        raise EditorialScopeError("active_blogger_pending_inventory_missing")
    for entry in pending:
        if (not isinstance(entry, dict) or
                not isinstance(entry.get("site_key"), str) or
                not re.fullmatch(r"[a-z0-9_]{3,50}", entry["site_key"]) or
                not isinstance(entry.get("id"), str) or
                not re.fullmatch(r"\d{10,24}", entry["id"]) or
                entry.get("cms_verified") is not True or
                entry.get("route_registered") is not False or
                entry.get("campaign_verified") is not False or
                entry.get("editorial_status") != "CMS_ACTIVE_ONBOARDING_REQUIRED_NO_CMS_WRITES"):
            raise EditorialScopeError("pending_blogger_untrusted")
    if (set(allkeys) & {x["site_key"] for x in pending}
            or set(allids) & {x["id"] for x in pending}):
        raise EditorialScopeError("pending_blogger_identity_collision")
    counts = policy.get("snapshot_counts", {})
    if (counts.get("blogger_targets") != len(policy["blogger"]["current_targets"])
            or counts.get("wordpress_targets") != len(policy["wordpress"]["current_targets"])
            or counts.get("total_current_targets") != len(targets)
            or counts.get("blogger_active_pending_v31_onboarding") != len(pending)
            or counts.get("blogger_active_connected_non_excluded") != len(policy["blogger"]["current_targets"]) + len(pending)
            or counts.get("blogger_deleted_by_owner") != policy["blogger"].get("deleted_by_owner_count")
            or counts.get("deleted_blogger_pending_authentication") != 0):
        raise EditorialScopeError("active_snapshot_counts_invalid")
    load_tombstones(policy)


def scope_status(policy: dict, route: dict | None, *, site_key: str | None = None) -> str:
    """Fail closed for deleted IDs even if a caller spoofs the site key."""
    validate_policy(policy)
    if route is not None and not isinstance(route, dict):
        return "ROUTE_UNTRUSTED"
    key = site_key if site_key is not None else route.get("site_key") if route else None
    rid = route.get("identifier") if route else None
    tombstones = load_tombstones(policy)
    if any((rid is not None and rid == x["blog_id"])
           or key in (x["legacy_site_key"], x["old_route_key"])
           for x in tombstones["deleted_blogs"]):
        return "DELETED_BY_OWNER"
    excluded = policy["blogger"]["exclusions"]
    if any(key == x["site_key"] or rid is not None and rid == x["id"] for x in excluded):
        return "EXCLUDED_BY_OWNER"
    pending = policy["blogger"]["connected_active_blogs_pending_onboarding"]
    if any((rid is not None and rid == x["id"]) or key == x["site_key"] for x in pending):
        return "CMS_ACTIVE_ONBOARDING_REQUIRED"
    if route is None:
        return "ROUTE_NOT_REGISTERED"
    if not isinstance(key, str) or not re.fullmatch(r"[a-z0-9_]{3,50}", key):
        return "SITE_ID_INVALID"
    if route.get("site_key") != key:
        return "ROUTE_IDENTITY_MISMATCH"
    if (route.get("platform") not in ("blogger", "wordpress")
            or route.get("publish_enabled") is not False
            or not isinstance(route.get("campaign"), str)
            or not re.fullmatch(r"[a-z0-9_-]{1,32}", route["campaign"])):
        return "ROUTE_UNSAFE"
    entries = [
        *(dict(x, platform="blogger") for x in policy["blogger"]["current_targets"]),
        *(dict(x, platform="wordpress") for x in policy["wordpress"]["current_targets"]),
    ]
    target = next((x for x in entries if x["site_key"] == key), None)
    if target is None:
        return "NOT_IN_CURRENT_VERIFIED_ACTIVE_INVENTORY"
    if target["platform"] != route["platform"] or target.get("id", target.get("url")) != rid:
        return "ROUTE_IDENTITY_MISMATCH"
    if target["route_registered"] is not True:
        return "ROUTE_NOT_VERIFIED"
    return "IN_SCOPE"


def is_route_in_active_scope(route: dict) -> bool:
    """Used by universal request queue, not a LIVE release permission."""
    return scope_status(load_policy(), route) == "IN_SCOPE"


def evaluate_preflight(policy: dict, route: dict | None, quality: dict, *, site_key: str) -> dict:
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


def simulation_cases(policy: dict, *, cycle_index: int = 0) -> list[dict]:
    """50 offline cases: all 24 deleted IDs every cycle + 7 current sites + risks.

    Future additional sites rotate through the 23 available active slots.
    No fixed limit on number of sites in the universal architecture.
    """
    validate_policy(policy)
    if type(cycle_index) is not int or not 0 <= cycle_index <= 1_000_000_000:
        raise EditorialScopeError("invalid_simulation_cycle_index")
    guard = load_tombstones(policy)
    active = [
        *(dict(x, platform="blogger") for x in policy["blogger"]["current_targets"]),
        *(dict(x, platform="wordpress") for x in policy["wordpress"]["current_targets"]),
    ]
    if not active:
        raise EditorialScopeError("no_current_site_targets")
    eligible_actors = []
    for x in active:
        route = {"site_key": x["site_key"], "platform": x["platform"],
                 "identifier": x.get("id", x.get("url")),
                 "campaign": "simulatedcamp", "publish_enabled": False}
        eligible_actors.append((x["site_key"], route, "registered_active"))
    size = min(len(eligible_actors), 23)
    start = cycle_index % len(eligible_actors)
    rotated = (eligible_actors[start:] + eligible_actors[:start])[:size]
    cases = [(actor, VARIANTS[(cycle_index + i) % 5])
             for i, actor in enumerate(rotated)]
    for x in guard["deleted_blogs"]:
        key = x["old_route_key"] or x["legacy_site_key"]
        route = {"site_key": key, "platform": "blogger",
                 "identifier": x["blog_id"],
                 "campaign": "legacyfixture", "publish_enabled": False}
        cases.append(((key, route, "deleted_by_owner"), "complete_simulated_preflight"))
    excluded = policy["blogger"]["exclusions"][0]
    cases.append(((excluded["site_key"], {
        "site_key": excluded["site_key"], "platform": "blogger",
        "identifier": excluded["id"], "campaign": "legacyfixture",
        "publish_enabled": False}, "explicitly_excluded"), "complete_simulated_preflight"))
    existing = policy["blogger"]["connected_active_blogs_pending_onboarding"][0]
    cases.append(((existing["site_key"], {
        "site_key": existing["site_key"], "platform": "blogger",
        "identifier": existing["id"],
        "campaign": "not_verified", "publish_enabled": False},
        "active_unonboarded"), "complete_simulated_preflight"))
    cases.append((("blogger_new_future_without_route", None, "unregistered"),
                  "complete_simulated_preflight"))
    if len(cases) > 50:
        raise EditorialScopeError("too_many_base_simulation_cases")
    i = 0
    while len(cases) < 50:
        actor = eligible_actors[(cycle_index + i) % len(eligible_actors)]
        cases.append((actor, VARIANTS[(i + 1) % 5]))
        i += 1
    out = []
    for i, (actor, variant) in enumerate(cases):
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
        out.append({
            "id": f"simulation_{i + 1:02d}",
            "site_key": key, "route": route, "quality": quality,
            "variant": variant, "expected": EXPECTED_BY_CLASS[kind][VARIANTS.index(variant)],
        })
    return out


def run_simulations(*, count: int = 50, policy: dict | None = None,
                    cycle_index: int = 0) -> dict:
    if type(count) is not int or not 10 <= count <= 50:
        raise EditorialScopeError("simulation_count_must_be_10_to_50")
    policy = load_policy() if policy is None else policy
    cases = simulation_cases(policy, cycle_index=cycle_index)[:count]
    totals = {}
    for case in cases:
        result = evaluate_preflight(policy, case["route"], case["quality"], site_key=case["site_key"])
        if result["status"] != case["expected"] or any((
                result["allows_cms_write"], result["allows_live"],
                result["allows_affiliate_mutation"], result["network_calls"])):
            raise EditorialScopeError("simulation_failed_closed_" + case["id"])
        totals[result["status"]] = totals.get(result["status"], 0) + 1
    tombstones = load_tombstones(policy)
    return {
        "phase": "C143",
        "mode": "OFFLINE_SIMULATIONS_NO_REMOTE_WRITES",
        "executed": len(cases), "passed": len(cases), "failed": 0,
        "cycle_index": cycle_index,
        "distinct_candidate_sites_simulated": len(set(c["site_key"] for c in cases) - {
            x["old_route_key"] or x["legacy_site_key"] for x in tombstones["deleted_blogs"]
        } - {"blogger_reference_only", "blogger_new_future_without_route",
             policy["blogger"]["exclusions"][0]["site_key"]}),
        "current_active_sites": len(policy["blogger"]["current_targets"]) + len(policy["wordpress"]["current_targets"]),
        "deleted_blogger_blocked": len(tombstones["deleted_blogs"]),
        "global_coverage_audit": {
            "global_candidates": len(policy["blogger"]["current_targets"]),
            "cross_account_pending": 0,
            "deleted_by_owner": len(tombstones["deleted_blogs"]),
            "current_wordpress": len(policy["wordpress"]["current_targets"]),
        },
        "outcomes": totals,
        "cms_writes": 0, "d1_writes": 0, "r2_writes": 0,
        "affiliate_mutations": 0, "live_authorized": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="V31 50 simulations current CMS and 24 deleted tombstones")
    parser.add_argument("--cases", type=int, default=50)
    parser.add_argument("--cycle-index", type=int, default=0)
    args = parser.parse_args()
    try:
        result = run_simulations(count=args.cases, cycle_index=args.cycle_index)
    except Exception:
        print("V31_SCOPE_SIMULATIONS_FAILED_CLOSED")
        return 1
    print("V31_SCOPE_SIMULATIONS=" + json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
