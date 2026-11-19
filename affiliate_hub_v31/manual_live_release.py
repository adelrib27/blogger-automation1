"""C65 — publicação LIVE por aprovação INDIVIDUAL e leitura remota.

Nunca é importado/executado por crons de rascunho. O owner deve aprovar
explicitamente o conteúdo imutável de um DRAFT específico, dentro de uma
rota real, com catálogo R2 da campanha exata. Sem manifesto/CONFIRM não
existe chamada de publicação. Sem o flag --execute, 0 mutações.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from .automatic_blogger_drafts import (
    _get_blogger_service, validate_remote_identity,
)
from .automatic_wordpress_drafts import (
    WordPressRestClient, credentials_for, validate_wordpress_paragraphs,
)
from .catalog import Catalog
from .r2_state import R2State, verify_database
from .routing import sites

APPROVAL_DIR = Path(__file__).with_name("live_approvals.d")
KEY_RE = re.compile(r'data-v31-product-key="(shopee:[0-9]+:[0-9]+)"')
URL_RE = re.compile(r'href=["\x27](https://[^"\x27]+)["\x27]', re.I)
P_RE = re.compile(r"<h2(?:\s+[^>]*)?>.*?</h2>\s*<p(?:\s+[^>]*)?>(.*?)</p>", re.I | re.S)
SHA_RE = re.compile(r"[a-f0-9]{64}")


class LiveReleaseError(ValueError):
    pass


def approval_path(site_key: str, post_id: str, directory: Path = APPROVAL_DIR) -> Path:
    if (not isinstance(site_key, str)
            or not re.fullmatch(r"[a-z0-9_]{3,50}", site_key)
            or not isinstance(post_id, str)
            or not re.fullmatch(r"[0-9]{1,22}", post_id)
            or int(post_id) == 0):
        raise LiveReleaseError("release_target_invalid")
    return directory / (site_key + "__" + post_id + ".json")


def load_approval(site_key: str, post_id: str,
                  directory: Path = APPROVAL_DIR) -> dict:
    file = approval_path(site_key, post_id, directory)
    if not file.is_file() or file.is_symlink():
        raise LiveReleaseError("release_owner_approval_missing")
    try:
        a = json.loads(file.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        raise LiveReleaseError("release_approval_invalid") from None
    expected = {
        "site_key", "platform", "post_id", "content_sha256",
        "approved_utc", "owner_authorized", "editorial_reviewed",
        "commercial_reviewed",
    }
    route = sites().get(site_key)
    if (not isinstance(a, dict) or set(a) != expected or
            route is None or a["site_key"] != site_key or
            a["platform"] != route["platform"] or
            a["post_id"] != post_id or
            not isinstance(a["content_sha256"], str) or
            not SHA_RE.fullmatch(a["content_sha256"]) or
            any(a[k] is not True for k in (
                "owner_authorized", "editorial_reviewed", "commercial_reviewed"
            ))):
        raise LiveReleaseError("release_approval_invalid")
    try:
        dt = datetime.fromisoformat(a["approved_utc"].replace("Z", "+00:00"))
        if dt.tzinfo is None or dt.utcoffset() != timezone.utc.utcoffset(dt):
            raise ValueError()
        # Não aceitar manifesto de autorização datado no futuro.
        if dt > datetime.now(timezone.utc):
            raise ValueError()
    except (TypeError, AttributeError, ValueError):
        raise LiveReleaseError("release_approval_date_invalid") from None
    return a


def _content(post: dict, platform: str) -> str:
    value = post.get("content")
    if platform == "wordpress":
        if not isinstance(value, dict):
            raise LiveReleaseError("release_content_unavailable")
        value = value.get("raw")
    if not isinstance(value, str) or not value.strip():
        raise LiveReleaseError("release_content_unavailable")
    return value


def _title(post: dict, platform: str) -> str:
    val = post.get("title")
    if platform == "wordpress":
        val = val.get("raw") if isinstance(val, dict) else None
    if not isinstance(val, str) or len(val.strip()) < 15:
        raise LiveReleaseError("release_title_unavailable")
    return html.unescape(val)


def _plain(value: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", " ", value)).strip()


def audit_draft(post: dict, *, route: dict, catalog: Catalog) -> dict:
    """Audita payload vivo; não publica e não aprova por conta própria."""
    platform = route["platform"]
    if not isinstance(post, dict) or str(post.get("status", "")).lower() != "draft":
        raise LiveReleaseError("release_post_not_draft")
    body = _content(post, platform)
    title = _title(post, platform)
    match = KEY_RE.search(body)
    if not match or body.count('data-v31-product-key="') != 1:
        raise LiveReleaseError("release_product_identity_invalid")
    key = match.group(1)
    if catalog.for_conversion(key) is None:
        raise LiveReleaseError("release_product_not_approved")
    affiliate = catalog.cached_link(key, route["campaign"])
    if not affiliate or not affiliate.startswith("https://s.shopee.com.br/"):
        raise LiveReleaseError("release_exact_campaign_link_missing")
    outbound = URL_RE.findall(body)
    if affiliate not in outbound:
        raise LiveReleaseError("release_exact_campaign_link_missing")
    if any(urlsplit(link).hostname not in (
            "s.shopee.com.br", urlsplit(route["identifier"]).hostname
            if platform == "wordpress" else None
        ) for link in outbound if link != affiliate):
        # Blogger's real domain is checked below via blog_url in audit call.
        raise LiveReleaseError("release_external_links_unverified")
    if ("https://cf.shopee.com.br/" not in body or
            "Ver produto na Shopee" not in body or
            "link de afiliado" not in body.lower() or
            "comissão" not in body.lower()):
        raise LiveReleaseError("release_commercial_fields_missing")
    paragraphs = [_plain(p) for p in P_RE.findall(body)]
    if not paragraphs:
        raise LiveReleaseError("release_editorial_missing")
    try:
        validate_wordpress_paragraphs(paragraphs, product_title=title)
    except ValueError:
        raise LiveReleaseError("release_editorial_quality_not_approved") from None
    return {
        "post_id": str(post["id"]),
        "site_key": route["site_key"],
        "platform": platform,
        "content_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
        "approved_sku": True,
        "exact_campaign": True,
        "sections": len(paragraphs),
        "publication_calls": 0,
        "status": "ELIGIBLE_FOR_OWNER_REVIEW",
    }


def preview_or_publish(*, site_key: str, post_id: str,
                       catalog: Catalog, execute: bool = False,
                       approval_directory: Path = APPROVAL_DIR,
                       wp_client=None, blogger_service=None,
                       confirm: str = "") -> dict:
    """DRAFT -> LIVE só com aprovação arquivo+hash e dois comandos explícitos."""
    route = sites().get(site_key)
    if not route or type(execute) is not bool:
        raise LiveReleaseError("release_registered_site_required")
    approval_path(site_key, post_id, approval_directory)
    if route["publish_enabled"] is not False:
        raise LiveReleaseError("release_unexpected_auto_publish_enabled")
    if execute and confirm != "PUBLISH:" + site_key + ":" + post_id:
        raise LiveReleaseError("release_explicit_confirmation_required")
    if route["platform"] == "wordpress":
        if wp_client is None:
            username, password = credentials_for(site_key)
            wp_client = WordPressRestClient(
                base_url=route["identifier"], username=username,
                application_password=password)
        wp_client.site_settings()
        post = wp_client.get_post(int(post_id))
    else:
        service = blogger_service or _get_blogger_service()
        blog = service.blogs().get(blogId=route["identifier"]).execute()
        home = validate_remote_identity(route, blog)
        post = service.posts().get(blogId=route["identifier"],
                                   postId=post_id).execute()
    if str(post.get("id")) != post_id:
        raise LiveReleaseError("release_post_identity_mismatch")
    audit = audit_draft(post, route=route, catalog=catalog)
    if route["platform"] == "blogger":
        # Blogger não cadastra URL no registry; a API autenticada é autoridade.
        for link in URL_RE.findall(_content(post, "blogger")):
            if urlsplit(link).hostname not in (
                    "s.shopee.com.br", urlsplit(home).hostname):
                raise LiveReleaseError("release_foreign_internal_link")
    if not execute:
        return {**audit, "status": "AWAITING_OWNER_APPROVAL",
                "owner_approval_loaded": False}
    a = load_approval(site_key, post_id, approval_directory)
    if audit["content_sha256"] != a["content_sha256"]:
        raise LiveReleaseError("release_content_changed_after_approval")
    if route["platform"] == "wordpress":
        # Read-after-read antes da mutação: se mudou, cancela.
        updated = wp_client.get_post(int(post_id))
        if audit_draft(updated, route=route, catalog=catalog)["content_sha256"] != a["content_sha256"]:
            raise LiveReleaseError("release_race_detected")
        wp_client._call("POST", "/wp-json/wp/v2/posts/" + post_id,
                        {"status": "publish"})
        after = wp_client.get_post(int(post_id))
        correct_status = after.get("status") == "publish"
    else:
        updated = service.posts().get(blogId=route["identifier"],
                                      postId=post_id).execute()
        if audit_draft(updated, route=route, catalog=catalog)["content_sha256"] != a["content_sha256"]:
            raise LiveReleaseError("release_race_detected")
        service.posts().publish(blogId=route["identifier"],
                                postId=post_id).execute()
        after = service.posts().get(blogId=route["identifier"],
                                    postId=post_id).execute()
        correct_status = str(after.get("status", "")).lower() == "live"
    if (not correct_status or str(after.get("id")) != post_id or
            hashlib.sha256(_content(after, route["platform"]).encode("utf-8")).hexdigest()
            != a["content_sha256"]):
        # Não fazer retry automático: o POST pode ter aplicado parcialmente.
        raise LiveReleaseError("release_readback_requires_manual_investigation")
    return {**audit, "status": "LIVE_CONFIRMED", "publication_calls": 1,
            "owner_approval_loaded": True}


def main() -> int:
    p = argparse.ArgumentParser(description="V31: LIVE APENAS com aprovação exata, nunca cron")
    p.add_argument("--site-key", required=True)
    p.add_argument("--post-id", required=True)
    p.add_argument("--execute", action="store_true")
    args = p.parse_args()
    try:
        with tempfile.TemporaryDirectory(prefix="v31-live-release-") as td:
            local = Path(td) / "catalog.sqlite3"
            if not R2State.from_env().restore_to(local):
                raise LiveReleaseError("release_catalog_unavailable")
            verify_database(local)
            with Catalog(local) as catalog:
                report = preview_or_publish(
                    site_key=args.site_key, post_id=args.post_id,
                    catalog=catalog, execute=args.execute,
                    confirm=os.getenv("V31_LIVE_ONE_POST_CONFIRM", ""))
        print("V31_LIVE_RELEASE_SAFE_PASS")
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
        return 0
    except Exception as e:
        # Nenhum conteúdo de API, senha ou rascunho no log.
        print("V31_LIVE_RELEASE_BLOCKED_" + type(e).__name__)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
