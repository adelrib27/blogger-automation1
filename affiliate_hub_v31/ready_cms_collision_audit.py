"""C135 — diagnóstico universal READY x histórico CMS (SOMENTE LEITURA).

Não autoriza entrega DRAFT nem LIVE, não altera D1/R2 e não consome quotas.
Dados de produto, HTML e títulos nunca são impressos pelo CLI.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re

from . import automatic_blogger_drafts as blogger
from . import automatic_wordpress_drafts as wordpress
from .d1_http_runner import CloudflareD1HTTPRunner
from .routing import sites


HEX64 = re.compile(r"[0-9a-f]{64}\Z")
SKU = re.compile(r"shopee:[0-9]+:[0-9]+\Z")
READ_ONLY_LIMIT = 100


class ReadyCMSAuditError(ValueError):
    pass


def _raw_post(platform: str, post: dict) -> str | None:
    if platform == "blogger":
        content = post.get("content")
        return content if isinstance(content, str) else None
    content = post.get("content")
    if not isinstance(content, dict):
        return None
    raw = content.get("raw")
    return raw if isinstance(raw, str) else None


def _matches(*, route: dict, job: dict, post: dict) -> bool:
    content = _raw_post(route["platform"], post)
    # Sem conteúdo RAW não é possível concluir ausência do produto.
    if content is None:
        raise ReadyCMSAuditError("cms_raw_history_missing_fail_closed")
    key = job["product_key"]
    if key in blogger.KEY_PATTERN.findall(content):
        return True
    if route["platform"] == "wordpress":
        return post.get("slug") == wordpress._product_slug(route["site_key"], key)
    labels = post.get("labels") or []
    if not isinstance(labels, list):
        raise ReadyCMSAuditError("cms_labels_untrusted")
    return "v31-" + job["fingerprint"][:32] in labels


def audit_ready_jobs(*, route: dict, ready_jobs: list[dict],
                     cms_posts: list[dict]) -> dict:
    """Separar colisões de conteúdo do estado READY, sem 'greenlight'.

    A ausência de SKU na lista atual não torna a oferta elegível para escrita.
    É uma auditoria de histórico, não uma decisão de criar DRAFT.
    """
    if (not isinstance(route, dict) or route.get("publish_enabled") is not False
            or route.get("platform") not in {"wordpress", "blogger"}
            or not isinstance(route.get("site_key"), str)
            or not isinstance(route.get("campaign"), str)
            or not isinstance(ready_jobs, list) or len(ready_jobs) > READ_ONLY_LIMIT
            or not isinstance(cms_posts, list)):
        raise ReadyCMSAuditError("audit_input_invalid")
    if any(not isinstance(p, dict) or not isinstance(p.get("id"), (int, str))
           for p in cms_posts):
        raise ReadyCMSAuditError("cms_history_untrusted")
    if len({str(p["id"]) for p in cms_posts}) != len(cms_posts):
        raise ReadyCMSAuditError("cms_history_duplicate_ids")
    status_counts: dict[str, int] = {}
    summaries = []
    for job in ready_jobs:
        if (not isinstance(job, dict) or job.get("site_key") != route["site_key"]
                or job.get("campaign") != route["campaign"]
                or job.get("status") != "READY"
                or not isinstance(job.get("product_key"), str)
                or not SKU.fullmatch(job["product_key"])
                or not isinstance(job.get("fingerprint"), str)
                or not HEX64.fullmatch(job["fingerprint"])
                or not isinstance(job.get("html_sha256"), str)
                or not HEX64.fullmatch(job["html_sha256"])):
            raise ReadyCMSAuditError("ready_job_untrusted")
        matches = [post for post in cms_posts if _matches(route=route, job=job, post=post)]
        if not matches:
            outcome = "NOT_PRESENT_IN_ACTIVE_HISTORY"
            matched_ids = []
        elif len(matches) > 1:
            outcome = "MULTIPLE_CMS_MATCHES"
            matched_ids = sorted(str(p["id"]) for p in matches)
        else:
            post = matches[0]
            matched_ids = [str(post["id"])]
            raw = _raw_post(route["platform"], post)
            keys = blogger.KEY_PATTERN.findall(raw)
            expected_key = job["product_key"]
            if keys != [expected_key]:
                outcome = "CONFLICTING_PRODUCT_IDENTITY"
            elif route["platform"] == "wordpress" and post.get("slug") != wordpress._product_slug(route["site_key"], expected_key):
                outcome = "CONFLICTING_SLUG"
            elif str(post.get("status", "")).lower() != "draft":
                outcome = "EXISTING_NON_DRAFT_POST"
            elif hashlib.sha256(raw.encode("utf-8")).hexdigest() == job["html_sha256"]:
                outcome = "IDENTICAL_DRAFT_ALREADY_PRESENT"
            else:
                outcome = "CONFLICTING_DRAFT_HTML"
        status_counts[outcome] = status_counts.get(outcome, 0) + 1
        summaries.append({"status": outcome, "cms_ids": matched_ids})
    return {
        "mode": "READ_ONLY_NO_DELIVERY_NO_LIVE",
        "site_key": route["site_key"],
        "platform": route["platform"],
        "ready_jobs_checked": len(summaries),
        "outcomes": status_counts,
        "jobs": summaries,
        "ready_delivery_authorized": False,
        "automatic_live_authorized": False,
        "d1_writes": 0,
        "cms_writes": 0,
    }


def authenticated_posts(route: dict) -> list[dict]:
    """Somente chamadas GET, identidade do CMS verificada antes do histórico."""
    if route["platform"] == "wordpress":
        user, password = wordpress.credentials_for(route["site_key"])
        client = wordpress.WordPressRestClient(
            base_url=route["identifier"], username=user,
            application_password=password)
        settings = client.site_settings()
        if not wordpress._verify_blog_url(settings.get("url", ""), route["identifier"]):
            raise ReadyCMSAuditError("wordpress_identity_mismatch")
        return client.list_posts(include_unpublished=True)
    if route["platform"] == "blogger":
        service = blogger._get_blogger_service()
        blog = service.blogs().get(blogId=route["identifier"]).execute()
        blogger.validate_remote_identity(route, blog)
        return blogger._list_posts(service, route["identifier"], include_scheduled=True)
    raise ReadyCMSAuditError("cms_route_invalid")


def audit_site(*, site_key: str) -> dict:
    route = sites().get(site_key)
    if not route or route.get("publish_enabled") is not False:
        raise ReadyCMSAuditError("registered_safe_route_required")
    # Constructor de D1 não aceita mutações: SELECT é a ÚNICA operação.
    query = CloudflareD1HTTPRunner.from_environment(allow_mutations=False)
    rows = query("""
        SELECT site_key, campaign, fingerprint, product_key, html_sha256, status
        FROM v31_ready_jobs
        WHERE site_key=? AND campaign=? AND status='READY'
        ORDER BY fingerprint LIMIT 101
    """, (site_key, route["campaign"]))
    if len(rows) > READ_ONLY_LIMIT:
        raise ReadyCMSAuditError("ready_audit_limit_exceeded_fail_closed")
    posts = authenticated_posts(route)
    return audit_ready_jobs(route=route, ready_jobs=rows, cms_posts=posts)


def main() -> int:
    parser = argparse.ArgumentParser(description="Auditoria READY/CMS somente leitura")
    parser.add_argument("--site-key", required=True)
    args = parser.parse_args()
    try:
        result = audit_site(site_key=args.site_key)
    except Exception:
        # Nem erros de credenciais/HTTP devem expor URLs ou payloads privados.
        print("C135_READY_CMS_AUDIT_FAILED_CLOSED")
        return 1
    print("C135_READY_CMS_AUDIT=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
