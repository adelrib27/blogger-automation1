#!/usr/bin/env python3
"""V31 LAB daily-cycle preflight: no Shopify/Shopee calls, Git writes or Blogger PUT.

Read the existing validated V31 profile, ledger and rotation history; allow a
fresh *SAFE-only* Shopee scan at most once per Recife local calendar day.
This gate does NOT authorize publication, Git reservation or a scheduler.
"""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import datetime, timedelta
import json
from pathlib import Path
from zoneinfo import ZoneInfo

REPO = "adelrib27/blogger-automation1"
BRANCH = "lab/v31r1-shopee-safe-20261103"
BLOG = "4739187376492839837"
PAGE = "2446067640331732447"
HOST = "blog-teste-tema-worpress.blogspot.com"
RECIFE = ZoneInfo("America/Recife")
PROOF_TRANSPORT = "CLOUDFLARE_BROWSER_RENDERING"


class DailyGateBlocked(ValueError):
    pass


def need(condition: bool, reason: str) -> None:
    if not condition:
        raise DailyGateBlocked(reason)


def iso(value: object) -> datetime:
    need(isinstance(value, str) and bool(value), "Missing timestamp")
    try:
        instant = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise DailyGateBlocked("Malformed timestamp") from exc
    need(instant.tzinfo is not None, "Naive timestamp")
    return instant


def sha64(value: object) -> bool:
    return (isinstance(value, str) and len(value) == 64 and
            all(c in "0123456789abcdef" for c in value))


def gate(profile: dict, ledger: dict, history: dict, *, now: datetime,
         repo: str = REPO, branch: str = BRANCH) -> dict:
    need(repo == REPO and branch == BRANCH, "Not the immutable V31 LAB identity")
    need(isinstance(now, datetime) and now.tzinfo is not None, "Aware time required")
    need(isinstance(profile, dict) and isinstance(ledger, dict) and isinstance(history, dict),
         "Malformed profile/ledger/history")
    need(profile.get("mode") == "SAFE" and profile.get("blog_id") == BLOG and
         profile.get("page_id") == PAGE and profile.get("blog_host") == HOST and
         profile.get("page_url") == f"https://{HOST}/p/loja.html", "Wrong profile target")
    cats = profile.get("categories")
    counts = profile.get("per_category")
    expected = profile.get("expected_products")
    need(cats == ["Decoração", "Organização", "Cozinha", "Quarto"] and
         expected == 16 and isinstance(counts, dict) and
         list(counts) == cats and all(type(counts[c]) is int and counts[c] == 4 for c in cats),
         "Changed V31 category contract")
    need(ledger.get("schema") == 1 and ledger.get("blogId") == BLOG and
         ledger.get("pageId") == PAGE and isinstance(ledger.get("operations"), list),
         "Wrong ledger")
    need(history.get("version") == 1 and history.get("blogId") == BLOG and
         isinstance(history.get("runs"), list), "Wrong history")
    operations = ledger["operations"]
    runs = history["runs"]
    need(len(operations) >= 2 and len(runs) == len(operations) + 1,
         "Incomplete historical reconciliation")
    need(runs[0].get("source") == "seed_from_current_blogger_store" and
         runs[0].get("pageId") == PAGE and "operationId" not in runs[0],
         "Missing unique Blogger seed")
    op_ids = [op.get("operationId") for op in operations]
    need(all(sha64(i) for i in op_ids) and len(set(op_ids)) == len(op_ids),
         "Duplicate/invalid operation")
    previous_time = None
    for n, run in enumerate(runs):
        need(isinstance(run, dict) and run.get("pageId") == PAGE, "Wrong history page")
        moment = iso(run.get("timestamp"))
        need(previous_time is None or moment > previous_time, "Out-of-order history")
        previous_time = moment
        products = run.get("items")
        need(isinstance(products, list) and len(products) == expected, "Incomplete history products")
        ids = [str(item.get("itemId", "")) for item in products if isinstance(item, dict)]
        need(len(ids) == expected and len(set(ids)) == expected and
             all(x.isdigit() and 4 <= len(x) <= 25 for x in ids), "Invalid/duplicate product IDs")
        actual = Counter(item.get("category") for item in products)
        need(actual == Counter(counts), "History category count mismatch")
        if n == 0:
            continue
        op = operations[n-1]
        need(isinstance(op, dict) and op.get("status") == "PERSISTED", "Unfinished operation")
        need(run.get("source") == "blogger_published" and
             run.get("operationId") == op["operationId"] and
             run.get("selectionSha") == op.get("selectionSha") and
             sha64(op.get("selectionSha")) and
             sha64(op.get("candidateSha")) and sha64(op.get("originalSha")),
             "History and ledger are inconsistent")
        need(run.get("timestamp") == op.get("pageUpdatedAt"), "Blogger update time mismatch")
        if n > 1:
            need(op.get("originalSha") == operations[n-2].get("candidateSha"),
                 "Broken sequence of published page hashes")
        public = op.get("publicProof")
        need(isinstance(public, dict) and public.get("transport") == PROOF_TRANSPORT and
             sha64(public.get("htmlSha256")) and
             type(public.get("sourceRun")) is int and public["sourceRun"] > 0 and
             isinstance(public.get("verifiedAt"), str), "Missing public proof")
        iso(public["verifiedAt"])
        for field in ("cards", "images", "links"):
            if field in public:
                need(public[field] == expected, f"Public proof {field} mismatch")
        if "categories" in public:
            need(public["categories"] == len(cats), "Public proof categories mismatch")
        if "publicHttp" in public:
            need(public["publicHttp"] == 200, "Public proof HTTP mismatch")
        claim = op.get("prewriteClaim")
        if claim is not None:
            need(isinstance(claim, dict) and
                 claim.get("state") == "ATTEMPT_CLAIMED_BEFORE_PUT" and
                 claim.get("backupSha256") == op.get("originalSha"),
                 "Invalid durable claim history")
    last = iso(runs[-1]["timestamp"])
    local_now = now.astimezone(RECIFE)
    local_last = last.astimezone(RECIFE)
    need(last <= now + timedelta(minutes=5), "Latest Blogger publication is in the future")
    need(local_now.date() >= local_last.date(), "Clock precedes last published day")
    skip = local_now.date() == local_last.date()
    return {
        "status": "SKIP_ALREADY_UPDATED_TODAY" if skip else "READY_FOR_SAFE_SHOPEE_SCAN",
        "repository": REPO,
        "branch": BRANCH,
        "blogId": BLOG,
        "pageId": PAGE,
        "dayRecife": local_now.date().isoformat(),
        "lastPublishedDayRecife": local_last.date().isoformat(),
        "persistedOperations": len(operations),
        "historyEntries": len(runs),
        "safeScanAllowed": not skip,
        "bloggerPutAllowed": False,
        "remoteGitWriteAllowed": False,
        "cronEnabled": False,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--profile", type=Path, required=True)
    ap.add_argument("--ledger", type=Path, required=True)
    ap.add_argument("--history", type=Path, required=True)
    ap.add_argument("--report", type=Path, required=True)
    args = ap.parse_args()
    try:
        need(not args.report.exists(), "Refuse report overwrite")
        data = [json.loads(p.read_text(encoding="utf-8")) for p in
                (args.profile, args.ledger, args.history)]
        result = gate(*data, now=datetime.now(RECIFE))
        # Report is a new scratch file: never in tracked source directories.
        args.report.parent.mkdir(parents=True, exist_ok=True)
        with args.report.open("x", encoding="utf-8") as out:
            json.dump(result, out, sort_keys=True, ensure_ascii=False)
            out.write("\n")
        print("V31_DAILY_SAFE_GATE="+json.dumps(result, sort_keys=True))
        return 0
    except (DailyGateBlocked, ValueError, OSError, json.JSONDecodeError) as exc:
        print("V31_DAILY_SAFE_BLOCKED="+type(exc).__name__)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
