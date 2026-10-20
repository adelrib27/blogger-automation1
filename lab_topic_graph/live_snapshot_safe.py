from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from lab_topic_graph.topic_graph_safe import LabSafetyError, dump_json, normalize_text, validate_anchor


class AnchorParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._active: dict[str, Any] | None = None
        self.links: list[dict[str, Any]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a" or self._active is not None:
            return
        values = {key.lower(): value for key, value in attrs}
        href = str(values.get("href") or "").strip()
        if not href:
            return
        self._active = {"href": href, "rel": str(values.get("rel") or "").strip(), "text_parts": []}

    def handle_data(self, data: str) -> None:
        if self._active is not None:
            self._active["text_parts"].append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() != "a" or self._active is None:
            return
        text = " ".join(part.strip() for part in self._active["text_parts"] if part.strip())
        self.links.append({
            "href": self._active["href"],
            "anchor_text": " ".join(text.split()),
            "rel": self._active["rel"],
        })
        self._active = None


def extract_links(html: str) -> list[dict[str, Any]]:
    parser = AnchorParser()
    parser.feed(str(html or ""))
    parser.close()
    return parser.links


def content_hash(html: str) -> str:
    return hashlib.sha256(str(html or "").encode("utf-8")).hexdigest()


def _same_host(url: str, site_host: str) -> bool:
    try:
        parsed = urlparse(str(url or "").strip())
    except ValueError:
        return False
    return parsed.scheme in {"http", "https"} and parsed.netloc == site_host and bool(parsed.path)


def validate_snapshot(snapshot: dict[str, Any]) -> None:
    if snapshot.get("schema_version") != "1.0":
        raise LabSafetyError("snapshot_schema_version_unsupported")
    if snapshot.get("source") != "blogger_api_readonly":
        raise LabSafetyError("snapshot_source_not_readonly_blogger")
    site_host = str(snapshot.get("site_host") or "").strip()
    if not site_host:
        raise LabSafetyError("snapshot_site_host_missing")
    if snapshot.get("complete") is not True:
        raise LabSafetyError("snapshot_incomplete")
    posts = snapshot.get("posts")
    if not isinstance(posts, list):
        raise LabSafetyError("snapshot_posts_not_list")

    ids: set[str] = set()
    urls: set[str] = set()
    for post in posts:
        post_id = str(post.get("id") or "").strip()
        url = str(post.get("url") or "").strip()
        if not post_id or post_id in ids:
            raise LabSafetyError("snapshot_post_id_invalid_or_duplicate")
        if not _same_host(url, site_host) or url in urls:
            raise LabSafetyError("snapshot_post_url_invalid_or_duplicate")
        ids.add(post_id)
        urls.add(url)


def build_snapshot_audit(snapshot: dict[str, Any], content_registry: dict[str, Any]) -> dict[str, Any]:
    validate_snapshot(snapshot)
    site_host = snapshot["site_host"]
    posts = snapshot["posts"]
    registry_articles = content_registry.get("articles", [])
    registry_by_id = {str(item.get("article_id")): item for item in registry_articles}
    registry_by_url = {str(item.get("url")): item for item in registry_articles if item.get("url")}
    snapshot_by_id = {str(item.get("id")): item for item in posts}
    snapshot_by_url = {str(item.get("url")): item for item in posts}

    health_rows = []
    hashes = []
    for article_id, article in registry_by_id.items():
        post = snapshot_by_id.get(article_id)
        reasons = []
        status = "BLOGGER_LIVE_MATCHED"
        if post is None:
            status = "BLOCKED_NOT_IN_SNAPSHOT"
            reasons.append("post_id_missing")
        else:
            if post.get("status") != "live":
                status = "BLOCKED_NOT_LIVE"
                reasons.append("status_not_live")
            if str(post.get("url")) != str(article.get("url")):
                status = "BLOCKED_URL_MISMATCH"
                reasons.append("url_mismatch")

        health_rows.append({
            "article_id": article_id,
            "registered_url": article.get("url"),
            "snapshot_url": post.get("url") if post else None,
            "status": status,
            "blocking_reasons": reasons,
            "http_canonical_verified": False,
        })
        if post is not None:
            hashes.append({
                "article_id": article_id,
                "content_hash": content_hash(str(post.get("content") or "")),
                "fetched_at": snapshot.get("fetched_at"),
            })

    edges = []
    metrics = Counter()
    source_with_internal_links: set[str] = set()
    source_ids = set(registry_by_id)

    for source_id in sorted(source_ids):
        source_post = snapshot_by_id.get(source_id)
        if source_post is None or source_post.get("status") != "live":
            continue
        seen_targets: set[str] = set()
        for link in extract_links(str(source_post.get("content") or "")):
            href = link["href"]
            if not _same_host(href, site_host):
                continue
            metrics["internal_links_total"] += 1
            source_with_internal_links.add(source_id)
            target_registry = registry_by_url.get(href)
            target_snapshot = snapshot_by_url.get(href)
            target_id = str(target_registry.get("article_id")) if target_registry else None
            if target_registry and target_snapshot and target_snapshot.get("status") == "live":
                resolution = "RESOLVED_EDITORIAL_LIVE"
                metrics["resolved_editorial_live"] += 1
            elif target_snapshot and not target_registry:
                resolution = "NON_EDITORIAL_INTERNAL"
                metrics["non_editorial_internal"] += 1
            elif target_registry and not target_snapshot:
                resolution = "BLOCKED_TARGET_NOT_IN_SNAPSHOT"
                metrics["blocked_target_not_in_snapshot"] += 1
            else:
                resolution = "BLOCKED_UNKNOWN_INTERNAL_TARGET"
                metrics["blocked_unknown_internal_target"] += 1

            duplicate = bool(target_id and target_id in seen_targets)
            if duplicate:
                metrics["duplicate_source_target"] += 1
            if target_id:
                seen_targets.add(target_id)

            anchor_ok, anchor_reasons = validate_anchor(link["anchor_text"])
            if not anchor_ok:
                metrics["anchor_policy_violations"] += 1

            edges.append({
                "source_article_id": source_id,
                "target_article_id": target_id,
                "target_url": href,
                "anchor_text": link["anchor_text"],
                "anchor_normalized": normalize_text(link["anchor_text"]),
                "anchor_policy_ok": anchor_ok,
                "anchor_blocking_reasons": anchor_reasons,
                "resolution": resolution,
                "duplicate_source_target": duplicate,
            })

    metrics["editorial_sources_in_registry"] = len(registry_by_id)
    metrics["snapshot_posts_total"] = len(posts)
    metrics["sources_with_internal_links"] = len(source_with_internal_links)
    metrics["sources_without_internal_links"] = len(registry_by_id) - len(source_with_internal_links)
    metrics["blogger_live_matched"] = sum(row["status"] == "BLOGGER_LIVE_MATCHED" for row in health_rows)
    metrics["health_blocked"] = len(health_rows) - metrics["blogger_live_matched"]

    return {
        "schema_version": "1.0",
        "mode": "LAB_READ_ONLY_SNAPSHOT_AUDIT",
        "site_id": snapshot.get("site_id"),
        "fetched_at": snapshot.get("fetched_at"),
        "safety": {
            "source_readonly": True,
            "cms_write_capability": False,
            "http_canonical_verified": False,
            "plan_ready_allowed": False,
        },
        "metrics": dict(metrics),
        "health": health_rows,
        "content_hashes": hashes,
        "edges": edges,
    }


def run(snapshot_path: Path, content_registry_path: Path, output_path: Path) -> dict[str, Any]:
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    content_registry = json.loads(content_registry_path.read_text(encoding="utf-8"))
    result = build_snapshot_audit(snapshot, content_registry)
    dump_json(output_path, result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit a complete Blogger readonly snapshot without CMS writes")
    parser.add_argument("--snapshot", required=True, type=Path)
    parser.add_argument("--content-registry", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = run(args.snapshot, args.content_registry, args.output)
    print(json.dumps({"metrics": result["metrics"], "safety": result["safety"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
