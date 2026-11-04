#!/usr/bin/env python3
"""One-shot Blogger v3 Pages.update stale If-Match probe, LAB sacrificial page ONLY.

This is an explicitly scoped live experiment, not permission to publish the LOJA.
Creates ONE isolated Blogger page if none exists; keeps it for audit (no delete).
One conditional PUT against that page only. No retry or rollback, no secrets logged.
"""
from __future__ import annotations

from hashlib import sha256
from urllib import request, error, parse
from datetime import datetime, timezone
import json
import os
import re
import sys

BLOG = "4739187376492839837"
BRANCH = "refs/heads/lab/v31r1-shopee-safe-20261103"
REPO = "adelrib27/blogger-automation1"
TITLE = "V31-IF-MATCH-TEST-SACRIFICIAL"
API = "https://www.googleapis.com/blogger/v3/blogs/" + BLOG + "/pages"
PROTECTED = frozenset({
    "2446067640331732447", "2986843712929543286", "6280557664516445465",
    "5303118031131491498", "7850045876114690994", "1601621877328706822",
})
HTML = "<p>Laboratório V31: página técnica isolada para observar If-Match. Nenhuma oferta.</p>"
EXPECTED_LIVE = {
    "2446067640331732447", "2986843712929543286", "6280557664516445465",
    "5303118031131491498", "7850045876114690994", "1601621877328706822",
}

class FailClosed(Exception): pass

def require(pred, message):
    if not pred: raise FailClosed(message)

def digest(content: str) -> str:
    return sha256(content.encode("utf-8")).hexdigest()

def strong_etag(tag):
    return isinstance(tag, str) and re.fullmatch(r'"[\x21\x23-\x7e]+"', tag) is not None


def transport(url, method, *, token=None, obj=None, headers=None):
    data = json.dumps(obj, ensure_ascii=False).encode("utf-8") if obj is not None else None
    h = {"Accept": "application/json", "User-Agent": "V31-LAB-SACRIFICIAL-ETAG-PROBE/1"}
    if token: h["Authorization"] = "Bearer " + token
    if data is not None: h["Content-Type"] = "application/json; charset=utf-8"
    if headers: h.update(headers)
    req = request.Request(url=url, data=data, headers=h, method=method)
    try:
        with request.urlopen(req, timeout=25) as resp:
            raw = resp.read(350_000)
            return resp.status, json.loads(raw) if raw else {}
    except error.HTTPError as exc:
        # Intentionally avoid logging error body or auth headers.
        return exc.code, {}


def oauth_access_token():
    env = {k: os.getenv(k, "") for k in (
        "BLOGGER_CLIENT_ID", "BLOGGER_CLIENT_SECRET", "BLOGGER_REFRESH_TOKEN"
    )}
    require(all(env.values()), "OAuth secrets not present; no Blogger write attempted")
    body = parse.urlencode({
        "client_id": env["BLOGGER_CLIENT_ID"],
        "client_secret": env["BLOGGER_CLIENT_SECRET"],
        "refresh_token": env["BLOGGER_REFRESH_TOKEN"],
        "grant_type": "refresh_token",
    }).encode("utf-8")
    req = request.Request(
        "https://oauth2.googleapis.com/token",
        data=body, method="POST", headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    try:
        with request.urlopen(req, timeout=25) as r:
            obj = json.loads(r.read(5000))
    except error.HTTPError as exc:
        raise FailClosed("OAuth refresh failed; HTTP " + str(exc.code)) from None
    token = obj.get("access_token", "")
    require(isinstance(token, str) and len(token) > 30, "OAuth token unavailable")
    return token


def list_pages(token, status):
    result = []
    seen_tokens = set()
    page_token = ""
    for _ in range(10):
        query = {"status": status, "maxResults": "100"}
        if page_token: query["pageToken"] = page_token
        code, obj = transport(API + "?" + parse.urlencode(query), "GET", token=token)
        require(code == 200 and isinstance(obj.get("items", []), list),
                "Cannot independently inventory " + status + " pages")
        result.extend(obj.get("items", []))
        page_token = obj.get("nextPageToken", "")
        if not page_token: return result
        require(page_token not in seen_tokens, "Pagination cycle")
        seen_tokens.add(page_token)
    raise FailClosed("Page pagination not complete")


def page_snapshot(obj, page_id):
    require(str(obj.get("id")) == page_id, "Wrong page ID in GET")
    require(str(obj.get("blog", {}).get("id")) == BLOG, "Wrong blog in GET")
    require(obj.get("title") == TITLE, "Sacrificial page title differs")
    require(str(obj.get("url", "")).startswith("https://blog-teste-tema-worpress.blogspot.com/p/"),
            "Sacrificial URL is unexpected")
    require(isinstance(obj.get("content"), str), "No HTML content")
    require(strong_etag(obj.get("etag")), "Strong Blogger etag unavailable")
    require(isinstance(obj.get("updated"), str) and len(obj["updated"]) >= 20,
            "Blogger updated value missing")
    return {"sha": digest(obj["content"]), "etag": obj["etag"], "updated": obj["updated"]}


def run():
    require(os.environ.get("GITHUB_REPOSITORY") == REPO, "Wrong repository")
    require(os.environ.get("GITHUB_REF") == BRANCH, "Wrong branch")
    require(os.environ.get("GITHUB_EVENT_NAME") == "push", "Only exact LAB push allowed")
    require(os.environ.get("GITHUB_RUN_ATTEMPT") == "1", "Rerun forbidden; one-shot")
    require(os.environ.get("V31_SACRIFICIAL_PROBE_ONLY") == "YES_SINGLE_PAGE_SINGLE_PUT",
            "Explicit test scope missing")
    token = oauth_access_token()
    live = list_pages(token, "live")
    drafts = list_pages(token, "draft")
    live_ids = {str(item.get("id")) for item in live}
    require(live_ids == EXPECTED_LIVE, "Live page inventory changed; refuse creation")
    require(len(drafts) == 0, "Draft page inventory changed; refuse creation")
    require(not any(item.get("title") == TITLE for item in live + drafts),
            "Sacrificial page already exists; no retry/new page")
    # One POST only. If the response is uncertain, STOP. Never retry creation.
    code, created = transport(API, "POST", token=token, obj={
        "kind": "blogger#page", "blog": {"id": BLOG},
        "title": TITLE, "content": HTML,
        # Pages.insert has no documented isDraft parameter; it may publish LIVE.
    })
    require(code in (200, 201) and isinstance(created, dict),
            "Sacrificial page create not confirmed; STOP, inspect before retry")
    pid = str(created.get("id", ""))
    require(re.fullmatch(r"\d{10,24}", pid) and pid not in PROTECTED,
            "Created page ID invalid or protected")
    endpoint = API + "/" + pid
    code, before = transport(endpoint, "GET", token=token)
    require(code == 200, "Sacrificial GET failed; no PUT")
    a = page_snapshot(before, pid)
    require(a["sha"] == digest(HTML), "New page HTML differs; no PUT")
    # Deliberately invalid strong ETag: one attempt on ONLY the sacrificial page.
    stale = '"V31-SACRIFICIAL-STALE-20261104-DO-NOT-ACCEPT"'
    require(stale != a["etag"] and strong_etag(stale), "Stale ETag generator invalid")
    # Same content: if Blogger ignores If-Match, no visible content changes.
    put_code, _ = transport(endpoint, "PUT", token=token,
                             obj={"kind": "blogger#page", "blog": {"id": BLOG},
                                  "id": pid, "title": TITLE, "content": HTML},
                             headers={"If-Match": stale})
    code, after = transport(endpoint, "GET", token=token)
    require(code == 200, "Post-attempt authenticated GET unavailable; stop")
    b = page_snapshot(after, pid)
    unchanged = a == b
    verdict = "OBSERVED_412_AND_NO_CHANGE" if put_code == 412 and unchanged else "IF_MATCH_NOT_PROVEN"
    report = {
        "verdict": verdict, "source": "Blogger Pages.update live API",
        "blogId": BLOG, "pageId": pid, "pageTitle": TITLE,
        "pageUrl": before.get("url"), "pageStatus": before.get("status"),
        "conditionalPutHttpStatus": put_code, "readbackIdentical": unchanged,
        "beforeHtmlSha256": a["sha"], "afterHtmlSha256": b["sha"],
        "beforeEtagSha256": digest(a["etag"]), "afterEtagSha256": digest(b["etag"]),
        "beforeUpdatedAt": a["updated"], "afterUpdatedAt": b["updated"],
        "lojaPut": False, "lojaModified": False, "repeatAllowed": False,
        "sacrificialPageRetainedForAudit": True,
        "publicationAuthorization": False,
    }
    line = "V31_SACRIFICIAL_LIVE_IF_MATCH_RESULT=" + json.dumps(report,sort_keys=True)
    print(line, flush=True)
    summary_path = os.getenv("GITHUB_STEP_SUMMARY", "")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as fp:
            fp.write("### V31 LAB — observação If-Match (somente página sacrificial)\n\n")
            fp.write("```json\n" + json.dumps(report, indent=2) + "\n```\n")
    require(verdict == "OBSERVED_412_AND_NO_CHANGE",
            "If-Match server behavior NOT proven; LOJA publication remains BLOCKED")

if __name__ == "__main__":
    try: run()
    except FailClosed as exc:
        print("V31_SACRIFICIAL_PROBE_BLOCKED=" + str(exc), file=sys.stderr)
        raise SystemExit(2)
