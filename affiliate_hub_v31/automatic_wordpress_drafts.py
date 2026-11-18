"""C60 — writer WordPress para qualquer site real registrado (DRAFT, nunca LIVE).

R2 e campanha real fornecem produto/foto/URL; Workers AI fornece apenas
parágrafos. O WordPress REST autenticado é a fonte do histórico e das URLs
internas. Rascunhos são opcionais; por padrão tudo é somente leitura.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import ipaddress
import json
import os
import re
import tempfile
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

from .article_commerce import CommerceArticleError, product_offer_html, related_articles_html
from .automatic_blogger_drafts import generate_original_paragraphs, validate_generated_paragraphs
from .catalog import Catalog
from .r2_state import R2State, verify_database
from .routing import sites
from .site_launch_plan import preview_site_launch
from .site_request_queue import load_requests
from .taxonomy import normalize

PRODUCT_KEY_RE = re.compile(r'data-v31-product-key="(shopee:[0-9]+:[0-9]+)"')
MAX_PAGES = 25
MAX_POSTS_PER_PAGE = 100


class WordPressDraftError(ValueError):
    """Static error labels only: never include HTTP bodies or credentials."""


def home_url(route: dict) -> str:
    if (not isinstance(route, dict) or
        route.get("platform") != "wordpress" or
        route.get("publish_enabled") is not False):
        raise WordPressDraftError("registered_safe_wordpress_required")
    raw = route.get("identifier")
    try:
        u = urlsplit(raw)
        hostname = (u.hostname or "").lower().rstrip(".")
        if (u.scheme != "https" or not hostname or
            u.path != "/" or u.query or u.fragment or
            u.username or u.password or u.port not in (None, 443) or
            u.netloc != hostname):
            raise ValueError()
        try:
            address = ipaddress.ip_address(hostname)
        except ValueError:
            if hostname == "localhost" or hostname.endswith(".localhost"):
                raise ValueError()
        else:
            if not address.is_global:
                raise ValueError()
    except (ValueError, AttributeError, TypeError):
        raise WordPressDraftError("wordpress_home_invalid") from None
    return "https://" + hostname + "/"


def load_site_credentials(site_key: str, raw: str | None = None) -> tuple[str, str]:
    """Single GitHub Environment secret: JSON map site_key -> application password."""
    try:
        doc = json.loads(raw if raw is not None else
                         os.getenv("V31_WP_CREDENTIALS_JSON", ""))
        creds = doc[site_key]
        if (not isinstance(doc, dict) or not isinstance(creds, dict) or
            set(creds) != {"username", "app_password"} or
            not isinstance(creds["username"], str) or
            not 1 <= len(creds["username"].strip()) <= 100 or
            not isinstance(creds["app_password"], str) or
            len(creds["app_password"].strip()) < 16):
            raise ValueError()
        return creds["username"], creds["app_password"]
    except (KeyError, TypeError, ValueError):
        raise WordPressDraftError("wordpress_site_credentials_missing") from None


class WPClient:
    """No automatic POST retries or redirects. No credentials leave registered host."""

    def __init__(self, route: dict, credentials: tuple[str, str], session=None):
        self.home = home_url(route)
        if (not isinstance(credentials, tuple) or len(credentials) != 2 or
            any(not isinstance(x, str) or not x.strip() for x in credentials)):
            raise WordPressDraftError("wordpress_credentials_invalid")
        self.auth = credentials
        if session is None:
            import requests
            session = requests.Session()
        self.session = session

    def _call(self, method: str, path: str, *, params=None, payload=None):
        if (method not in ("GET", "POST") or not isinstance(path, str) or
            not re.fullmatch(r"(?:wp-json/(?:wp/v2/(?:posts(?:/[0-9]+)?|users/me))?)?", path)):
            raise WordPressDraftError("wordpress_api_path_invalid")
        url = self.home + path
        kw = {"auth": self.auth, "timeout": 30, "allow_redirects": False,
              "headers": {"Accept": "application/json"}}
        if params is not None:
            kw["params"] = params
        if payload is not None:
            kw["json"] = payload
        try:
            response = (self.session.get(url, **kw) if method == "GET" else
                        self.session.post(url, **kw))
            if response.status_code < 200 or response.status_code >= 300:
                raise WordPressDraftError("wordpress_api_http_failure")
            value = response.json()
        except WordPressDraftError:
            raise
        except Exception:
            # Could be a timeout after a POST actually succeeded. Never retry blindly.
            raise WordPressDraftError("wordpress_api_transport_or_json_failure") from None
        return value, response

    def verify_site(self) -> None:
        root, _ = self._call("GET", "wp-json/")
        if not isinstance(root, dict) or root.get("url") != self.home.rstrip("/"):
            raise WordPressDraftError("wordpress_remote_site_identity_mismatch")
        user, _ = self._call("GET", "wp-json/wp/v2/users/me",
                             params={"context": "edit"})
        if not isinstance(user, dict) or type(user.get("id")) is not int or user["id"] <= 0:
            raise WordPressDraftError("wordpress_remote_user_not_authenticated")

    def list_posts(self) -> list[dict]:
        """Fail closed on incomplete pagination/raw content: quotas need full history."""
        all_posts = []
        total_pages = None
        for page in range(1, MAX_PAGES + 1):
            batch, response = self._call("GET", "wp-json/wp/v2/posts",
                params={"context": "edit", "status": "any",
                        "per_page": MAX_POSTS_PER_PAGE, "page": page,
                        "_fields": "id,slug,status,link,title,content"})
            try:
                total = int(response.headers["X-WP-TotalPages"])
            except (KeyError, TypeError, ValueError):
                raise WordPressDraftError("wordpress_pagination_unverified") from None
            if (total < 1 or total > MAX_PAGES or
                (total_pages is not None and total != total_pages) or
                not isinstance(batch, list) or len(batch) > MAX_POSTS_PER_PAGE):
                raise WordPressDraftError("wordpress_pagination_invalid")
            total_pages = total
            for post in batch:
                if (not isinstance(post, dict) or
                    type(post.get("id")) is not int or post["id"] <= 0 or
                    not isinstance(post.get("slug"), str) or
                    not isinstance(post.get("status"), str) or
                    not isinstance(post.get("link"), str) or
                    not isinstance(post.get("title"), dict) or
                    not isinstance(post.get("content"), dict) or
                    not isinstance(post["content"].get("raw"), str)):
                    raise WordPressDraftError("wordpress_history_incomplete")
                all_posts.append(post)
            if page >= total_pages:
                return all_posts
        raise WordPressDraftError("wordpress_history_limit_exceeded")

    def create_draft(self, payload: dict) -> dict:
        if (not isinstance(payload, dict) or
            set(payload) != {"title", "slug", "content", "status"} or
            payload.get("status") != "draft" or
            not isinstance(payload.get("content"), str) or
            'data-v31-request="' not in payload["content"] or
            'data-v31-product-key="' not in payload["content"]):
            raise WordPressDraftError("wordpress_draft_payload_unsafe")
        created, _ = self._call("POST", "wp-json/wp/v2/posts", payload=payload)
        if (not isinstance(created, dict) or type(created.get("id")) is not int or
            created["id"] <= 0 or created.get("status") != "draft" or
            created.get("slug") != payload["slug"]):
            raise WordPressDraftError("wordpress_draft_creation_unconfirmed")
        # Verify returned record, not merely the response to the POST.
        confirmed, _ = self._call("GET", "wp-json/wp/v2/posts/" + str(created["id"]),
                                  params={"context": "edit"})
        if (not isinstance(confirmed, dict) or
            confirmed.get("id") != created["id"] or
            confirmed.get("status") != "draft" or
            confirmed.get("slug") != payload["slug"]):
            raise WordPressDraftError("wordpress_draft_read_after_write_failed")
        return confirmed


def _request_tag(site_key: str, topic: str) -> str:
    normalized = normalize(topic)
    if not normalized:
        raise WordPressDraftError("wordpress_request_topic_invalid")
    return hashlib.sha256((site_key + "|" + normalized).encode()).hexdigest()[:16]


def select_next(catalog: Catalog, *, site_key: str, request: dict,
                history: list[dict]) -> dict:
    route = sites().get(site_key)
    if (not route or route.get("platform") != "wordpress" or
        route.get("publish_enabled") is not False or
        not isinstance(request, dict) or request.get("site_key") != site_key or
        request.get("platform") != "wordpress" or request.get("enabled") is not True or
        type(request.get("articles")) is not int or
        not 1 <= request["articles"] <= 24 or
        not isinstance(request.get("topic"), str) or
        not isinstance(history, list)):
        raise WordPressDraftError("wordpress_real_request_required")
    tag = _request_tag(site_key, request["topic"])
    prefix = "v31-" + tag + "-"
    # Count ONLY V31 posts for the same request topic; legacy posts remain.
    matched = [p for p in history if p["slug"].startswith(prefix) or
               ('data-v31-request="' + tag + '"') in p["content"]["raw"]]
    if len({p["id"] for p in matched}) >= request["articles"]:
        return {"status": "OWNER_QUOTA_REACHED", "product_key": None}
    all_seen = set()
    all_slugs = set()
    for p in history:
        all_slugs.add(p["slug"])
        all_seen.update(PRODUCT_KEY_RE.findall(p["content"]["raw"]))
    plan = preview_site_launch(catalog, topic=request["topic"],
        platform="wordpress", site_key=site_key, max_items=24, max_per_shop=1)
    if plan["registered_site"] is not True or plan["can_publish"] is not False:
        raise WordPressDraftError("wordpress_selection_unsafe")
    for item in plan["approved_catalog_candidates"]:
        key = item["product_key"]
        if (key in all_seen or
            item.get("affiliate_status") != "verified_for_campaign" or
            catalog.for_conversion(key) is None or
            catalog.cached_link(key, route["campaign"]) != item.get("affiliate_url")):
            continue
        try:
            offer = product_offer_html(catalog, site_key=site_key,
                                       product_key=key, topic=item["title"][:110],
                                       verified_site_route=route)
        except CommerceArticleError:
            continue
        slug = prefix + hashlib.sha256(key.encode()).hexdigest()[:12]
        if slug in all_slugs:
            continue
        return {"status": "READY_FOR_ORIGINAL_DRAFT_REVIEW",
                "product_key": key, "product_title": item["title"],
                "keyword": item["title"][:110], "slug": slug,
                "request_tag": tag, "offer_html": offer,
                "title": "Guia de compra: " + item["title"][:75].rstrip(" ,;:-")}
    return {"status": "NO_VERIFIED_CAMPAIGN_PRODUCT_YET", "product_key": None}


def _related(history: list[dict], *, home: str, current_title: str) -> str:
    links = []
    for p in reversed(history):
        if p["status"] != "publish":
            continue
        raw_title = p["title"].get("rendered") or p["title"].get("raw") or ""
        title = html.unescape(re.sub(r"<[^>]*>", "", str(raw_title))).strip()
        if len(title) < 3 or normalize(title) == normalize(current_title):
            continue
        try:
            related_articles_html([(title, p["link"])], blog_home_url=home)
        except CommerceArticleError:
            continue
        links.append((title, p["link"]))
        if len(links) == 2:
            break
    return related_articles_html(links, blog_home_url=home)


def compose(plan: dict, paragraphs: list[str], *, request_topic: str,
            home: str, history: list[dict]) -> dict:
    if plan.get("status") != "READY_FOR_ORIGINAL_DRAFT_REVIEW":
        raise WordPressDraftError("wordpress_article_plan_required")
    # Revalidate even when a caller injects a writer.
    try:
        text = json.dumps({"paragraphs": paragraphs}, ensure_ascii=False)
        paragraphs = validate_generated_paragraphs(text, keyword=request_topic)
    except Exception:
        raise WordPressDraftError("wordpress_original_article_gate_failed") from None
    headings = ("Antes de escolher", "Medidas e compatibilidade", "Materiais e acabamento",
                "Uso no dia a dia", "Manutenção e cuidados", "Como analisar o anúncio",
                "Erros comuns", "Comparações e alternativas", "Perguntas ao vendedor",
                "Conclusão")
    blocks = "".join("<h2>" + html.escape(headings[i]) + "</h2><p>" +
                     html.escape(p, quote=True) + "</p>"
                     for i, p in enumerate(paragraphs))
    related = _related(history, home=home, current_title=plan["title"])
    content = ('<article lang="pt-BR" data-v31-request="' + plan["request_tag"] +
               '">' + blocks + plan["offer_html"] + related + "</article>")
    return {"title": plan["title"], "slug": plan["slug"], "content": content,
            "status": "draft"}


def draft_next(*, site_key: str, execute: bool = False, catalog: Catalog | None = None,
               wp_client: WPClient | None = None, workers_writer=None,
               requests: list[dict] | None = None) -> dict:
    if type(execute) is not bool:
        raise WordPressDraftError("wordpress_execution_flag_invalid")
    route = sites().get(site_key)
    if route is None or route.get("platform") != "wordpress":
        raise WordPressDraftError("registered_wordpress_required")
    request = next((r for r in (requests if requests is not None else load_requests())
                    if r["site_key"] == site_key and r["platform"] == "wordpress"), None)
    if request is None or request.get("enabled") is not True:
        raise WordPressDraftError("enabled_owner_request_required")
    client = wp_client or WPClient(route, load_site_credentials(site_key))
    client.verify_site()
    history = client.list_posts()

    def run(cat):
        plan = select_next(cat, site_key=site_key, request=request, history=history)
        if plan["status"] != "READY_FOR_ORIGINAL_DRAFT_REVIEW" or not execute:
            return {"mode": "C60_DRY_RUN" if not execute else "C60_SAFE_AUTODRAFT",
                    "status": plan["status"], "draft_creation_calls": 0,
                    "publication_calls": 0, "campaign_from_registry": True}
        writer = workers_writer or generate_original_paragraphs
        paragraphs = writer(product_name=plan["product_title"],
                            topic=request["topic"],
                            account_id=os.getenv("CLOUDFLARE_ACCOUNT_ID", ""),
                            api_token=os.getenv("CLOUDFLARE_API_TOKEN", ""))
        article = compose(plan, paragraphs, request_topic=request["topic"],
                          home=client.home, history=history)
        # Never trust a stale history across an expensive AI generation.
        latest = client.list_posts()
        again = select_next(cat, site_key=site_key, request=request, history=latest)
        if again.get("product_key") != plan["product_key"] or \
           again.get("slug") != plan["slug"]:
            raise WordPressDraftError("wordpress_draft_race_detected")
        confirmed = client.create_draft(article)
        return {"mode": "C60_SAFE_AUTODRAFT", "status": "DRAFT_CREATED",
                "draft_id": confirmed["id"], "draft_creation_calls": 1,
                "publication_calls": 0, "campaign_from_registry": True,
                "has_real_csv_photo": True, "has_keyword_link_and_cta": True,
                "internal_links_from_real_posts": bool(_related(
                    latest, home=client.home, current_title=plan["title"]))}

    if catalog is not None:
        return run(catalog)
    with tempfile.TemporaryDirectory(prefix="v31-c60-wp-") as temp:
        path = Path(temp) / "catalog.sqlite3"
        if not R2State.from_env().restore_to(path):
            raise WordPressDraftError("r2_catalog_unavailable")
        verify_database(path)
        with Catalog(path) as cat:
            return run(cat)


def main() -> int:
    parser = argparse.ArgumentParser(description="V31 WordPress: 1 DRAFT por execução, nunca LIVE")
    parser.add_argument("--site-key", default=None)
    parser.add_argument("--execute-draft", action="store_true")
    args = parser.parse_args()
    try:
        if args.site_key:
            site_key = args.site_key
        else:
            enabled = sorted(r["site_key"] for r in load_requests()
                             if r["platform"] == "wordpress")
            if not enabled:
                print("V31_C60_NO_REAL_WORDPRESS_REQUESTS")
                return 0
            site_key = enabled[date.today().toordinal() % len(enabled)]
        result = draft_next(site_key=site_key, execute=args.execute_draft)
        print("V31_C60_WORDPRESS_DRAFT_AUTOMATION_SAFE_PASS")
        # Do not log sensitive site/product/draft identifiers.
        print(json.dumps({key: value for key, value in result.items()
                          if key != "draft_id"}, sort_keys=True))
        return 0
    except Exception as exc:
        print("V31_C60_WORDPRESS_DRAFT_AUTOMATION_FAILED_" + type(exc).__name__)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
