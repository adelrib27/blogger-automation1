"""Read-only inventory for the two authorized DRAFT routes."""

import json
import os
import tempfile
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

from affiliate_hub_v31.article_commerce import CommerceArticleError, _single_verified_offer
from affiliate_hub_v31.catalog import Catalog
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


def main():
    with tempfile.TemporaryDirectory(prefix="v31-c81-catalog-") as directory:
        path = Path(directory) / "official-catalog.sqlite3"
        if not R2State.from_env().restore_to(path):
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
                        _, photo, _ = _single_verified_offer(
                            catalog, site_key=request["site_key"],
                            product_key=item["product_key"],
                        )
                    except CommerceArticleError:
                        continue
                    offer_count += 1
                    if not verified_image:
                        verified_image = photo_is_reachable(photo)
                print(json.dumps({
                    "site_key": request["site_key"],
                    "approved_candidates": len(report["approved_catalog_candidates"]),
                    "eligible_exact_campaign_offers": offer_count,
                    "exact_sku_cdn_photo_reached": verified_image,
                }))
    key = os.environ.get("FIRECRAWL_API_KEY", "")
    if not key:
        raise RuntimeError("C81_FIRECRAWL_KEY_UNAVAILABLE")
    request = Request("https://api.firecrawl.dev/v2/team/credit-usage",
                      headers={"Authorization": "Bearer " + key})
    try:
        with build_opener(NoRedirect()).open(request, timeout=15) as response:
            payload = json.load(response)
        remaining = payload["data"]["remainingCredits"]
        if payload.get("success") is not True or type(remaining) is not int:
            raise ValueError("invalid credit response")
    except (URLError, ValueError, KeyError, TypeError, TimeoutError):
        raise RuntimeError("C81_FIRECRAWL_CREDIT_READ_FAILED") from None
    print(json.dumps({"firecrawl_remaining_credits": remaining, "firecrawl_search_calls": 0}))


if __name__ == "__main__":
    main()
