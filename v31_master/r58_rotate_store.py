#!/usr/bin/env python3
"""R58 independent Shopee store writer (LAB R2 ONLY, separate from R49).

Dry-run is the default. No change to local Runner, theme, posts or other pages.
A single LIVE attempt needs BOTH a pinned state permission and an explicit
process-local confirmation. Once PUT starts, never retry automatically.
"""
from __future__ import annotations
import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import r58_store_policy as policy

BLOG_ID = policy.BLOG_ID
PAGE_ID = policy.PAGE_ID
PAGE_URL = policy.STORE_URL
BASE_API = "https://www.googleapis.com/blogger/v3/blogs/" + BLOG_ID + "/pages/" + PAGE_ID
TOKEN_URL = "https://oauth2.googleapis.com/token"
CONFIRM = "APPLY_R58_LAB_R58_EXISTING_STORE_ONLY"

class WriterError(RuntimeError):
    pass

def require_env(name):
    value = os.environ.get(name,"").strip()
    if not value:
        raise WriterError("MISSING_SECRET_" + name)
    return value

def postform(url, values):
    payload = urllib.parse.urlencode(values).encode()
    req = urllib.request.Request(url, data=payload, method="POST",
        headers={"Content-Type":"application/x-www-form-urlencoded"})
    try:
        with urllib.request.urlopen(req,timeout=25) as resp:
            if resp.status != 200:
                raise WriterError("OAUTH_BAD_HTTP")
            return json.loads(resp.read(30_000))
    except (urllib.error.URLError, ValueError, TimeoutError):
        raise WriterError("OAUTH_FAILED") from None

def oauth_token():
    r=postform(TOKEN_URL, {
        "client_id":require_env("BLOGGER_CLIENT_ID"),
        "client_secret":require_env("BLOGGER_CLIENT_SECRET"),
        "refresh_token":require_env("BLOGGER_REFRESH_TOKEN"),
        "grant_type":"refresh_token"})
    if not isinstance(r,dict) or not r.get("access_token"):
        raise WriterError("OAUTH_NO_ACCESS_TOKEN")
    return str(r["access_token"])

def api_page(token,method="GET",content=None):
    if method not in ("GET","PUT"):
        raise WriterError("METHOD_BLOCKED")
    body=None
    headers={"Authorization":"Bearer "+token, "Accept":"application/json"}
    if method=="PUT":
        if not isinstance(content,str) or len(content)>180_000:
            raise WriterError("PUT_CONTENT_INVALID")
        body=json.dumps({"title":"LOJA","content":content},ensure_ascii=False).encode("utf-8")
        headers["Content-Type"]="application/json; charset=utf-8"
    req=urllib.request.Request(BASE_API,method=method,data=body,headers=headers)
    try:
        with urllib.request.urlopen(req,timeout=30) as res:
            if res.status!=200:
                raise WriterError("BLOGGER_BAD_HTTP")
            out=json.loads(res.read(500_000))
    except urllib.error.HTTPError as e:
        raise WriterError("BLOGGER_HTTP_" + str(e.code)) from None
    except (urllib.error.URLError, ValueError, TimeoutError):
        raise WriterError("BLOGGER_API_FAILED") from None
    if not isinstance(out,dict):
        raise WriterError("BLOGGER_INVALID_JSON")
    return out

def validate_page(page):
    if str(page.get("id"))!=PAGE_ID or str((page.get("blog") or {}).get("id"))!=BLOG_ID:
        raise WriterError("WRONG_BLOG_PAGE_ID")
    if str(page.get("title","")).strip().upper()!="LOJA":
        raise WriterError("WRONG_PAGE_TITLE")
    page_status = str(page.get("status") or "").strip().upper()
    # Blogger pages.get often omits 'status' for published pages. In that
    # case require a publication timestamp, exact Page URL and exact IDs.
    if page_status and page_status != "LIVE":
        safe_status = re.sub(r"[^A-Z0-9_]", "", page_status)[:24]
        raise WriterError("PAGE_NOT_LIVE_" + safe_status)
    if not page_status and not page.get("published"):
        raise WriterError("PAGE_LIVE_NOT_PROVABLE")

    if page.get("url")!=PAGE_URL:
        raise WriterError("WRONG_PAGE_URL")
    content=page.get("content")
    if not isinstance(content,str):
        raise WriterError("MISSING_PAGE_CONTENT")
    return content

def public_read_once():
    req=urllib.request.Request(PAGE_URL+"?r57verify="+str(time.time_ns()),
        headers={"User-Agent":"Mozilla/5.0 R58-Lab-R2-Verify/1.0","Cache-Control":"no-cache"})
    try:
        with urllib.request.urlopen(req,timeout=25) as res:
            dest=urllib.parse.urlsplit(res.geturl())
            if res.status!=200 or dest.scheme!="https" or dest.hostname!="lab-v31-r58-shopee-e2e-20261106.blogspot.com" or dest.path!="/p/loja.html":
                raise WriterError("PUBLIC_REDIRECT_OR_STATUS_INVALID")
            return res.read(1_000_000).decode("utf-8",errors="replace")
    except urllib.error.HTTPError as e:
        raise WriterError("PUBLIC_HTTP_"+str(e.code)) from None
    except (urllib.error.URLError, TimeoutError, OSError):
        raise WriterError("PUBLIC_UNREACHABLE") from None

def check_public(candidate):
    expected=policy.ids(candidate)
    for wait in (0,4,7,12,18):
        if wait:time.sleep(wait)
        try:
            html=public_read_once()
            found=policy.validate_store_html(html)
            if found["items"]==expected and "ub-header" in html and "ub-store-content" in html:
                return True
        except (policy.GuardError, WriterError):
            pass
    return False

def run(*,candidate_path:Path,state_path:Path,dry_run:bool,out_dir:Path):
    state=policy.validate_state(json.loads(state_path.read_text(encoding="utf-8")))
    if not candidate_path.is_file():
        raise WriterError("CANDIDATE_ABSENT")
    candidate=candidate_path.read_text(encoding="utf-8")
    policy.validate_store_html(candidate)
    token=oauth_token()
    page=api_page(token)
    current=validate_page(page)
    proposed=policy.decision(current,candidate,state,allow_write=not dry_run)
    if proposed["status"]=="R58_NO_CHANGE":
        print(json.dumps({"status":"R58_NO_CHANGE","writes":0,"blog_id":BLOG_ID}))
        return 0
    if dry_run:
        print(json.dumps({"status":"R58_DRY_RUN_PASS_NO_WRITES","writes":0,
                          "blog_id":BLOG_ID,"new_items":proposed.get("new_item_count",0)}))
        return 0
    if os.environ.get("R58_LIVE_CONFIRM")!=CONFIRM:
        raise WriterError("EXPLICIT_WRITE_CONFIRMATION_MISSING")
    if not state.get("rotation_enabled") or not state.get("allow_auto_write"):
        raise WriterError("R58_LIVE_NOT_ENABLED_BY_POLICY")
    if proposed["status"]!="R58_CANDIDATE_READY_ONE_WRITE":
        raise WriterError("R58_LIVE_DECISION_DENIED")
    if any(out_dir.iterdir()):
        raise WriterError("OUTPUT_DIR_NOT_EMPTY")
    # Once begun, NEVER retry this step: a timeout after PUT is ambiguous.
    new_content=policy.replace_managed_region(current,candidate)
    policy.validate_store_html(new_content)
    backup=out_dir/"BACKUP_LOJA_R58_PRE_WRITE.json"
    backup.write_text(json.dumps({"page_id":PAGE_ID,"blog_id":BLOG_ID,
        "updated":page.get("updated"),"title":"LOJA","content":current},ensure_ascii=False),encoding="utf-8")
    # pre-write readback prevents overwriting known concurrent edits.
    before=api_page(token)
    if validate_page(before)!=current or before.get("updated")!=page.get("updated"):
        raise WriterError("CONCURRENT_PAGE_CHANGE")
    (out_dir/"R58_WRITE_STARTED_NO_RETRY").write_text("one-attempt\n",encoding="utf-8")
    result=api_page(token,"PUT",new_content)
    new_raw=validate_page(result)
    if policy.validate_store_html(new_raw)["items"]!=policy.ids(candidate):
        raise WriterError("WRITE_RESULT_NOT_CONFIRMED_NO_RETRY")
    check=api_page(token)
    after_raw=validate_page(check)
    if policy.validate_store_html(after_raw)["items"]!=policy.ids(candidate):
        raise WriterError("API_READBACK_NOT_CONFIRMED_NO_RETRY")
    if not check_public(candidate):
        raise WriterError("PUBLIC_NOT_CONFIRMED_NO_RETRY")
    new_state=policy.make_state(state,new_raw)
    new_state.update({"published_at":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),
                     "source":"Shopee Affiliate API R58 SAFE, public PASS after single Blogger PUT"})
    (out_dir/"R58_PUBLIC_PASS.json").write_text(json.dumps({"status":"R58_SINGLE_WRITE_PUBLIC_PASS",
         "blog_id":BLOG_ID,"page_id":PAGE_ID,"cards":16,"aff_links":32},indent=2)+"\n",encoding="utf-8")
    # Caller persists this new state only after R58_PUBLIC_PASS.
    (out_dir/"R58_ROTATION_STATE_NEXT.json").write_text(json.dumps(new_state,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":"R58_SINGLE_WRITE_PUBLIC_PASS","blog_id":BLOG_ID,"page_id":PAGE_ID,
                      "new_items":proposed["new_item_count"],"writes":1}))
    return 0

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--candidate",type=Path,required=True)
    ap.add_argument("--state",type=Path,required=True)
    ap.add_argument("--out-dir",type=Path,required=True)
    ap.add_argument("--apply-once",action="store_true")
    args=ap.parse_args()
    if args.apply_once and os.environ.get("R58_LIVE_CONFIRM")!=CONFIRM:
        raise WriterError("EXPLICIT_WRITE_CONFIRMATION_MISSING")
    args.out_dir.mkdir(parents=True,exist_ok=True)
    return run(candidate_path=args.candidate,state_path=args.state,
               dry_run=not args.apply_once,out_dir=args.out_dir)

if __name__=="__main__":
    try:
        raise SystemExit(main())
    except (WriterError, policy.GuardError, ValueError, OSError) as e:
        # Never print response bodies, OAuth secrets or page content.
        print(json.dumps({"status":"R58_FAIL_CLOSED","code":str(e),"retry":False},ensure_ascii=False))
        raise SystemExit(2)
