"""Measure the WordPress pilot and API limits using the writer's runtime, read-only."""
import argparse
import json
import os
from pathlib import Path
import tempfile
import time
from datetime import datetime, timezone

from .autonomous_review import PROFILE, _read, verify_affiliate_target, VerificationError
from .catalog import Catalog
from .automatic_wordpress_drafts import WordPressRestClient, credentials_for
from .d1_http_runner import CloudflareD1HTTPRunner
from .d1_universal_ready import UniversalD1ReadyState
from .editorial_cadence import draft_window_status
from .r2_state import R2State
from .routing import sites


def audit(site_key):
    route = sites()[site_key]
    campaign = route["campaign"]
    now = datetime.now(timezone.utc)
    day = now.date().isoformat()
    profiles = json.loads(PROFILE.read_text(encoding="utf-8"))
    report = {"site_key": site_key, "day_utc": day, "writes": 0, "services": {}}

    def measure(service, callback):
        start = time.monotonic()
        try:
            result = {"status": "PASS", **callback()}
        except Exception:
            result = {"status": "READ_FAILED"}
        report["services"][service] = dict(result, elapsed_seconds=round(time.monotonic() - start, 3))

    def wordpress():
        user, password = credentials_for(site_key)
        client = WordPressRestClient(base_url=route["identifier"], username=user,
                                     application_password=password)
        client.site_settings()
        posts = client.list_posts(include_unpublished=True)
        return {"status_counts": {status: sum(p.get("status") == status for p in posts)
                                  for status in ("publish", "draft", "future", "pending", "private")},
                "aioseo_head_observed": any("aioseo_head_json" in p for p in posts)}

    def firecrawl():
        token = os.environ["FIRECRAWL_API_KEY"]
        response = json.loads(_read(
            "https://api.firecrawl.dev/v2/team/credit-usage", hosts={"api.firecrawl.dev"},
            mime={"application/json"}, headers={"Authorization": "Bearer " + token},
        ))
        data = response["data"]
        remaining = data["remainingCredits"]
        plan = data["planCredits"]
        if response.get("success") is not True or type(remaining) is not int or type(plan) is not int:
            raise ValueError("credit_balance_invalid")
        return {"remaining_credits": remaining, "plan_credits": plan}

    def d1():
        query = CloudflareD1HTTPRunner.from_environment(allow_mutations=False)
        tenant = (site_key, campaign)
        jobs = query("SELECT status, COUNT(*) AS total FROM v31_ready_jobs "
                     "WHERE site_key=? AND campaign=? GROUP BY status", tenant)
        budget = query("SELECT kind, used, max_allowed FROM v31_search_budget "
                       "WHERE site_key=? AND campaign=? AND day_utc=? ORDER BY kind", (*tenant, day))
        conversions = query("SELECT COUNT(*) AS total FROM v31_shopee_conversion_attempts "
                            "WHERE campaign=? AND day_utc=?", (campaign, day))
        window = draft_window_status(
            state=UniversalD1ReadyState(query), route=route,
            profile=profiles.get(site_key, {}), now_epoch=int(now.timestamp()),
        )
        return {"jobs": jobs, "research_today": budget,
                "configured_daily_research_cap": profiles.get(site_key, {}).get("daily_research_attempts"),
                "conversion_attempts_today": conversions[0]["total"], "dispatch_window": window}

    def r2():
        storage = R2State.from_env()
        manifest = storage._read_manifest()
        if not manifest:
            raise ValueError("snapshot_missing")
        response = storage.s3.head_object(Bucket=storage.bucket, Key=manifest["key"])
        return {"snapshot_bytes": response["ContentLength"]}

    def offer():
        profile = profiles[site_key]
        sku = profile["pilot_sku"]
        storage = R2State.from_env()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "catalog.sqlite3"
            if not storage.restore_to(path):
                raise ValueError("snapshot_missing")
            with Catalog(path) as catalog:
                affiliate = catalog.cached_link(sku, campaign)
                if not affiliate:
                    return {"cache_exact_campaign": False, "affiliate_target": "NOT_CHECKED"}
                try:
                    verify_affiliate_target(affiliate, sku)
                    target = "EXACT_SKU"
                except VerificationError as error:
                    target = str(error)
                return {"cache_exact_campaign": True, "affiliate_target": target}

    for service, check in (("wordpress", wordpress), ("firecrawl", firecrawl), ("d1", d1), ("r2", r2), ("pilot_offer", offer)):
        measure(service, check)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site-key", required=True)
    args = parser.parse_args()
    report = audit(args.site_key)
    print(json.dumps(report, sort_keys=True))
    return int(any(service["status"] != "PASS" for service in report["services"].values()))


if __name__ == "__main__":
    raise SystemExit(main())
