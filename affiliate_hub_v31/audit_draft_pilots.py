"""Auditoria universal e somente leitura: jobs D1 USED contra DRAFTs CMS.

Não depende de um checkpoint temporário ou da presença de active_work.draft_pilots.
USED é autorização de tentativa, NUNCA prova de artigo criado. Só GET remoto,
identidade CMS, SKU e SHA-256 exatos produzem DRAFT_VERIFIED.
Nenhum POST, mutação D1, conversão ou liberação LIVE ocorre aqui.
"""
from __future__ import annotations

import hashlib
import json
import re

from . import automatic_blogger_drafts as blogger
from . import automatic_wordpress_drafts as wordpress
from .d1_http_runner import CloudflareD1HTTPRunner
from .editorial_scope_validation import is_route_in_active_scope
from .routing import sites
from .site_request_queue import load_requests

MAX_USED_JOBS_PER_SITE = 40
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
SKU = re.compile(r"shopee:[0-9]+:[0-9]+\Z")


class DraftPilotAuditError(ValueError):
    """Erro sanitizado, sem IDs remotos, HTML, URLs privadas ou credenciais."""


def _validated_job(job: dict, route: dict) -> None:
    if (not isinstance(job, dict) or
            job.get("site_key") != route["site_key"] or
            job.get("campaign") != route["campaign"] or
            job.get("status") != "USED" or
            not isinstance(job.get("fingerprint"), str) or
            not HEX64.fullmatch(job["fingerprint"]) or
            not isinstance(job.get("product_key"), str) or
            not SKU.fullmatch(job["product_key"]) or
            not isinstance(job.get("html_sha256"), str) or
            not HEX64.fullmatch(job["html_sha256"])):
        raise DraftPilotAuditError("d1_used_job_untrusted")


def _verified_exact_content(*, job: dict, content: object) -> bool:
    return (
        isinstance(content, str) and
        hashlib.sha256(content.encode("utf-8")).hexdigest() ==
        job["html_sha256"] and
        blogger.KEY_PATTERN.findall(content) == [job["product_key"]]
    )


def _wordpress_outcome(job: dict, route: dict, client) -> str:
    settings = client.site_settings()
    if not isinstance(settings, dict) or not wordpress._verify_blog_url(
            settings.get("url", ""), route["identifier"]):
        return "CMS_IDENTITY_CONFLICT"
    slug = wordpress._product_slug(route["site_key"], job["product_key"])
    posts = client.list_posts(include_unpublished=True, slug=slug)
    if not isinstance(posts, list) or any(not isinstance(p, dict) for p in posts):
        raise DraftPilotAuditError("cms_history_untrusted")
    matches = [p for p in posts
               if slug in (p.get("slug"), p.get("generated_slug"))]
    if not matches:
        return "USED_WITHOUT_CMS_MATCH"
    if len(matches) != 1 or len(posts) != 1:
        return "MULTIPLE_OR_AMBIGUOUS_CMS_MATCHES"
    post_id = matches[0].get("id")
    if type(post_id) is not int or post_id <= 0:
        raise DraftPilotAuditError("cms_post_id_invalid")
    post = client.get_post(post_id)
    if (not isinstance(post, dict) or post.get("id") != post_id or
            slug not in (post.get("slug"), post.get("generated_slug"))):
        return "CMS_IDENTITY_CONFLICT"
    if post.get("status") != "draft":
        return "EXISTING_NON_DRAFT_POST"
    title = post.get("title")
    raw = post.get("content")
    if (not isinstance(title, dict) or
            not isinstance(title.get("raw"), str) or
            not title["raw"].strip() or not isinstance(raw, dict)):
        return "CMS_CONTENT_UNVERIFIABLE"
    if not _verified_exact_content(job=job, content=raw.get("raw")):
        return "CMS_HTML_OR_SKU_CONFLICT"
    return "DRAFT_VERIFIED"


def _blogger_outcome(job: dict, route: dict, service) -> str:
    blog_id = route["identifier"]
    blog = service.blogs().get(blogId=blog_id).execute()
    blogger.validate_remote_identity(route, blog)
    marker = "v31-" + job["fingerprint"][:32]
    posts = blogger._list_posts(
        service, blog_id, label=marker, include_scheduled=True)
    if not isinstance(posts, list) or any(not isinstance(p, dict) for p in posts):
        raise DraftPilotAuditError("cms_history_untrusted")
    matches = [p for p in posts if marker in (p.get("labels") or [])]
    if not matches:
        return "USED_WITHOUT_CMS_MATCH"
    if len(posts) != 1 or len(matches) != 1:
        return "MULTIPLE_OR_AMBIGUOUS_CMS_MATCHES"
    post_id = matches[0].get("id")
    if not isinstance(post_id, str) or not post_id.isascii() or not post_id.isdecimal():
        raise DraftPilotAuditError("cms_post_id_invalid")
    post = service.posts().get(
        blogId=blog_id, postId=post_id, view="ADMIN").execute()
    if (str(post.get("id")) != post_id or
            str((post.get("blog") or {}).get("id")) != blog_id or
            marker not in (post.get("labels") or [])):
        return "CMS_IDENTITY_CONFLICT"
    if str(post.get("status", "")).lower() != "draft":
        return "EXISTING_NON_DRAFT_POST"
    if not isinstance(post.get("title"), str) or not post["title"].strip():
        return "CMS_CONTENT_UNVERIFIABLE"
    if not _verified_exact_content(job=job, content=post.get("content")):
        return "CMS_HTML_OR_SKU_CONFLICT"
    return "DRAFT_VERIFIED"


def audit(*, query=None, requests=None, routes=None,
          blogger_service_factory=None, wordpress_client_factory=None) -> dict:
    """Consulta até 40 jobs USED por demanda real e verifica cada CMS por GET.

    Fábricas injetáveis permitem testes sem credenciais, rede ou writes.
    Nenhum resultado vazio é representado como artigo confirmado.
    """
    registry = sites() if routes is None else routes
    active = load_requests() if requests is None else requests
    if not isinstance(registry, dict) or not isinstance(active, list):
        raise DraftPilotAuditError("audit_registry_invalid")
    if len(active) > 100:
        raise DraftPilotAuditError("too_many_audit_sites")
    query = (CloudflareD1HTTPRunner.from_environment(allow_mutations=False)
             if query is None else query)
    if not callable(query):
        raise DraftPilotAuditError("d1_read_only_runner_required")
    summaries = []
    total = 0
    verified = 0
    seen = set()
    for requested in active:
        if not isinstance(requested, dict):
            raise DraftPilotAuditError("audit_request_untrusted")
        site_key = requested.get("site_key")
        route = registry.get(site_key)
        if (not isinstance(site_key, str) or site_key in seen or
                not isinstance(route, dict) or
                route.get("site_key") != site_key or
                route.get("publish_enabled") is not False or
                route.get("platform") not in ("blogger", "wordpress") or
                not is_route_in_active_scope(route)):
            raise DraftPilotAuditError("audit_site_scope_invalid")
        seen.add(site_key)
        campaign = route["campaign"]
        rows = query("""
            SELECT site_key, campaign, fingerprint, product_key, html_sha256, status
            FROM v31_ready_jobs WHERE site_key=? AND campaign=? AND status='USED'
            ORDER BY used_epoch DESC LIMIT ?
        """, (site_key, campaign, MAX_USED_JOBS_PER_SITE + 1))
        if (not isinstance(rows, list) or
                len(rows) > MAX_USED_JOBS_PER_SITE or
                any(not isinstance(j, dict) for j in rows)):
            raise DraftPilotAuditError("d1_used_inventory_incomplete")
        fingerprints = set()
        for job in rows:
            _validated_job(job, route)
            if job["fingerprint"] in fingerprints:
                raise DraftPilotAuditError("d1_duplicate_used_fingerprint")
            fingerprints.add(job["fingerprint"])
        counts = {}
        if rows:
            if route["platform"] == "blogger":
                service = (blogger._get_blogger_service() if
                           blogger_service_factory is None else
                           blogger_service_factory(site_key))
                for job in rows:
                    outcome = _blogger_outcome(job, route, service)
                    counts[outcome] = counts.get(outcome, 0) + 1
            else:
                if wordpress_client_factory is None:
                    username, password = wordpress.credentials_for(site_key)
                    client = wordpress.WordPressRestClient(
                        base_url=route["identifier"], username=username,
                        application_password=password)
                else:
                    client = wordpress_client_factory(site_key)
                for job in rows:
                    outcome = _wordpress_outcome(job, route, client)
                    counts[outcome] = counts.get(outcome, 0) + 1
        total += len(rows)
        verified += counts.get("DRAFT_VERIFIED", 0)
        summaries.append({
            "site_key": site_key,
            "used_jobs_checked": len(rows),
            "drafts_verified": counts.get("DRAFT_VERIFIED", 0),
            "outcomes": counts,
        })
    if verified < total:
        status = "BLOCKED_RECONCILIATION"
    elif total == 0:
        status = "NO_USED_JOBS_TO_VERIFY"
    else:
        status = "ALL_USED_DRAFTS_VERIFIED"
    return {
        "mode": "READ_ONLY_D1_USED_CMS_GET",
        "status": status,
        "sites_checked": len(summaries),
        "used_jobs_checked": total,
        "drafts_verified": verified,
        "reports": summaries,
        "all_used_jobs_verified": total > 0 and verified == total,
        "no_new_post_authorized": True,
        "cms_writes": 0, "d1_writes": 0, "shopee_writes": 0,
        "automatic_live_authorized": False,
    }


def main() -> int:
    try:
        result = audit()
    except Exception:
        # Nunca revelar body CMS, hostname, token, consulta SQL ou HTML.
        print("V31_DRAFT_AUDIT_FAILED_CLOSED")
        return 2
    print("V31_DRAFT_AUDIT=" + json.dumps(
        result, ensure_ascii=False, sort_keys=True))
    return 3 if result["status"] == "BLOCKED_RECONCILIATION" else 0


if __name__ == "__main__":
    raise SystemExit(main())
