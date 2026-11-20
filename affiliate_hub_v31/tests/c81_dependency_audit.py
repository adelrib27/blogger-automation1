"""Read-only inventory for the two authorized DRAFT routes."""

import json
import os
import re
import tempfile
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

from affiliate_hub_v31.article_commerce import CommerceArticleError, _single_verified_offer
from affiliate_hub_v31.catalog import Catalog
from affiliate_hub_v31.r2_private_ready_backend import ACCOUNT_ID, BUCKET, _error_response
from affiliate_hub_v31.r2_state import R2State
from affiliate_hub_v31.site_launch_plan import preview_site_launch
from affiliate_hub_v31.site_request_queue import load_requests


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


def photo_is_reachable(url):
    try:
        request = Request(url, headers={"Range": "bytes=0-511"})
        with build_opener(NoRedirect()).open(request, timeout=12) as response:
            return (response.status in (200, 206)
                    and response.headers.get_content_type().startswith("image/")
                    and bool(response.read(512)))
    except HTTPError as error:
        error.close()
        return False
    except (URLError, TimeoutError):
        return False


def firecrawl_json(path, key, body=None):
    headers = {"Authorization": "Bearer " + key}
    if body is not None:
        headers["Content-Type"] = "application/json"
    request = Request("https://api.firecrawl.dev/v2/" + path, headers=headers,
                      data=json.dumps(body).encode("utf-8") if body is not None else None)
    try:
        with build_opener(NoRedirect()).open(request, timeout=35) as response:
            result = json.loads(response.read(1_000_000))
        if result.get("success") is not True or not isinstance(result.get("data"), dict):
            raise ValueError("invalid Firecrawl response")
        return result["data"]
    except HTTPError as error:
        error.close()
        if error.code == 429:
            raise RuntimeError("C81_FIRECRAWL_RATE_LIMIT_NO_RETRY") from None
        raise RuntimeError("C81_FIRECRAWL_HTTP_FAILURE") from None
    except (URLError, ValueError, KeyError, TypeError, TimeoutError):
        raise RuntimeError("C81_FIRECRAWL_RESPONSE_INVALID") from None


def main():
    candidates = []
    if (os.environ.get("V31_EDITORIAL_R2_ACCOUNT_ID") != ACCOUNT_ID
            or os.environ.get("V31_EDITORIAL_R2_BUCKET") != BUCKET):
        raise RuntimeError("C81_OFFICIAL_CATALOG_IDENTITY_MISMATCH")
    storage = R2State.from_env()
    research_key = None
    if os.environ.get("V31_C81_RESEARCH_SMOKE") == "1":
        run = os.environ.get("GITHUB_RUN_ID", "")
        if not re.fullmatch(r"[0-9]{1,20}", run):
            raise RuntimeError("C81_RESEARCH_RUN_ID_MISSING")
        research_key = f"v31/private-review/research/v1/{run}.json"
        try:
            storage.s3.head_object(Bucket=BUCKET, Key=research_key)
        except Exception as error:
            if _error_response(error) != ("404", 404):
                raise RuntimeError("C81_RESEARCH_BUNDLE_STATUS_UNKNOWN") from None
        else:
            print("C81_PRIVATE_RESEARCH_BUNDLE_ALREADY_STORED=PASS")
            return
    with tempfile.TemporaryDirectory(prefix="v31-c81-catalog-") as directory:
        path = Path(directory) / "official-catalog.sqlite3"
        if not storage.restore_to(path):
            raise RuntimeError("C81_OFFICIAL_CATALOG_MISSING")
        with Catalog(path) as catalog:
            print(json.dumps({"catalog": catalog.stats()}))
            for request in load_requests():
                report = preview_site_launch(
                    catalog, topic=request["topic"], platform=request["platform"],
                    site_key=request["site_key"],
                )
                offer_count = 0
                verified_image = False
                for item in report["approved_catalog_candidates"]:
                    try:
                        title, photo, affiliate = _single_verified_offer(
                            catalog, site_key=request["site_key"],
                            product_key=item["product_key"],
                        )
                    except CommerceArticleError:
                        continue
                    offer_count += 1
                    if not verified_image:
                        verified_image = photo_is_reachable(photo)
                        if verified_image:
                            candidates.append({
                                "site_key": request["site_key"],
                                "title": title,
                                "product_key": item["product_key"],
                                "product_url": item["original_product_url"],
                                "image": photo, "affiliate": affiliate,
                            })
                print(json.dumps({
                    "site_key": request["site_key"],
                    "approved_candidates": len(report["approved_catalog_candidates"]),
                    "eligible_exact_campaign_offers": offer_count,
                    "exact_sku_cdn_photo_reached": verified_image,
                }))
    key = os.environ.get("FIRECRAWL_API_KEY", "")
    if not key:
        raise RuntimeError("C81_FIRECRAWL_KEY_UNAVAILABLE")
    remaining = firecrawl_json("team/credit-usage", key).get("remainingCredits")
    if type(remaining) is not int:
        raise RuntimeError("C81_FIRECRAWL_CREDIT_READ_FAILED")
    print(json.dumps({"firecrawl_remaining_credits": remaining}))
    if research_key is not None:
        if remaining < 10:
            raise RuntimeError("C81_FIRECRAWL_SMOKE_BUDGET_UNAVAILABLE")
        for offer in candidates[:2]:
            result = firecrawl_json("search", key, {
                "query": offer["title"][:160], "limit": 2, "sources": [{"type": "web"}],
                "country": "BR", "timeout": 25000,
            })
            links = result.get("web")
            if not isinstance(links, list):
                raise RuntimeError("C81_FIRECRAWL_SEARCH_RESPONSE_INVALID")
            offer["search_candidates"] = [
                {"url": entry["url"], "title": entry.get("title", "")}
                for entry in links if isinstance(entry, dict) and isinstance(entry.get("url"), str)
            ]
            print(json.dumps({"site_key": offer["site_key"], "firecrawl_search_calls": 1,
                              "search_candidates": len(links), "approved_facts": 0}))
        # The research candidates are private inputs for factual review.
        # GitHub logs contain counts only, never affiliate URLs or article text.
        bundle = json.dumps({"offers": candidates[:2]}, ensure_ascii=False).encode("utf-8")
        storage.s3.put_object(Bucket=BUCKET, Key=research_key,
                              Body=bundle, IfNoneMatch="*", ContentType="application/json",
                              CacheControl="private, no-store")
        print("C81_PRIVATE_RESEARCH_BUNDLE_STORED=PASS")


if __name__ == "__main__":
    main()
