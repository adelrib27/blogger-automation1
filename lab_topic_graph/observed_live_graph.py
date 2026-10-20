from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


class ObservedGraphError(RuntimeError):
    pass


def classify_relationship(source: dict[str, Any], target: dict[str, Any]) -> str:
    source_silo = source.get("silo_id")
    source_cluster = source.get("cluster_id")
    target_silo = target.get("silo_id")
    target_cluster = target.get("cluster_id")
    if not source_silo or not source_cluster or not target_silo or not target_cluster:
        return "INVOLVES_UNCLASSIFIED"
    if source_silo != target_silo:
        return "CROSS_SILO"
    if source_cluster != target_cluster:
        return "SAME_SILO_CROSS_CLUSTER"
    return "SAME_CLUSTER"


def validate_observed_graph(snapshot: dict[str, Any]) -> dict[str, Any]:
    if snapshot.get("schema_version") != "1.0":
        raise ObservedGraphError("unsupported_schema")
    if snapshot.get("mode") != "LAB_READ_ONLY_OBSERVED_EDITORIAL_GRAPH":
        raise ObservedGraphError("unsafe_mode")
    if snapshot.get("source") != "blogger_api_readonly":
        raise ObservedGraphError("source_not_blogger_readonly")
    if snapshot.get("editorial_inventory_complete") is not True:
        raise ObservedGraphError("editorial_inventory_incomplete")

    safety = snapshot.get("safety") or {}
    if safety.get("cms_write_capability") is not False:
        raise ObservedGraphError("cms_write_capability_must_be_false")
    if safety.get("publishing") is not False:
        raise ObservedGraphError("publishing_must_be_false")
    if safety.get("production_modification") is not False:
        raise ObservedGraphError("production_modification_must_be_false")
    if safety.get("plan_ready_allowed") is not False:
        raise ObservedGraphError("plan_ready_must_be_false")
    if safety.get("full_source_content_hash_available") is not False:
        raise ObservedGraphError("full_content_hash_must_remain_unverified")
    if safety.get("http_canonical_verified") is not False:
        raise ObservedGraphError("http_canonical_must_remain_unverified")

    articles = snapshot.get("articles")
    edges = snapshot.get("edges")
    if not isinstance(articles, list) or not isinstance(edges, list):
        raise ObservedGraphError("articles_or_edges_invalid")

    by_id: dict[str, dict[str, Any]] = {}
    by_url: dict[str, dict[str, Any]] = {}
    for article in articles:
        article_id = str(article.get("article_id") or "")
        url = str(article.get("url") or "")
        if not article_id or article_id in by_id:
            raise ObservedGraphError("duplicate_or_missing_article_id")
        if not url or url in by_url:
            raise ObservedGraphError("duplicate_or_missing_article_url")
        if article.get("status") != "LIVE":
            raise ObservedGraphError("article_not_live")
        if article.get("blogger_live_verified") is not True:
            raise ObservedGraphError("article_not_blogger_live_verified")
        if article.get("http_canonical_verified") is not False:
            raise ObservedGraphError("article_http_canonical_not_fail_closed")
        by_id[article_id] = article
        by_url[url] = article

    seen_edges: set[tuple[str, str]] = set()
    inbound = Counter()
    outbound = Counter()
    relationships = Counter()
    repeated_target_anchors = Counter()

    for edge in edges:
        source_id = str(edge.get("source_article_id") or "")
        target_id = str(edge.get("target_article_id") or "")
        if source_id not in by_id or target_id not in by_id:
            raise ObservedGraphError("unknown_source_or_target")
        if source_id == target_id:
            raise ObservedGraphError("self_link")
        edge_key = (source_id, target_id)
        if edge_key in seen_edges:
            raise ObservedGraphError("duplicate_source_target")
        seen_edges.add(edge_key)
        if edge.get("target_blogger_live_verified") is not True:
            raise ObservedGraphError("target_not_blogger_live_verified")
        if edge.get("http_canonical_verified") is not False:
            raise ObservedGraphError("edge_http_canonical_not_fail_closed")
        if str(edge.get("target_url") or "") != str(by_id[target_id].get("url") or ""):
            raise ObservedGraphError("target_url_mismatch")
        expected_relationship = classify_relationship(by_id[source_id], by_id[target_id])
        if edge.get("relationship_observed") != expected_relationship:
            raise ObservedGraphError("relationship_tampering_or_mismatch")
        anchor_text = str(edge.get("anchor_text") or "").strip()
        if not anchor_text:
            raise ObservedGraphError("empty_anchor")
        inbound[target_id] += 1
        outbound[source_id] += 1
        relationships[expected_relationship] += 1
        if anchor_text == str(by_id[target_id].get("title") or ""):
            repeated_target_anchors[target_id] += 1

    classified = sum(bool(a.get("silo_id") and a.get("cluster_id")) for a in articles)
    orphan_ids = sorted(aid for aid in by_id if inbound[aid] == 0)
    sources_with_links = sum(1 for aid in by_id if outbound[aid] > 0)
    repeated_anchor_targets = sum(1 for count in repeated_target_anchors.values() if count > 1)

    computed = {
        "editorial_articles": len(articles),
        "classified_articles": classified,
        "unclassified_articles": len(articles) - classified,
        "editorial_edges": len(edges),
        "sources_with_editorial_links": sources_with_links,
        "sources_without_editorial_links": len(articles) - sources_with_links,
        "inbound_orphan_articles": len(orphan_ids),
        "unknown_internal_targets": 0,
        "duplicate_source_target_edges": 0,
        "http_canonical_verified_edges": 0,
        "exact_target_title_anchor_targets_repeated": repeated_anchor_targets,
        "relationship_distribution": {
            "SAME_CLUSTER": relationships["SAME_CLUSTER"],
            "SAME_SILO_CROSS_CLUSTER": relationships["SAME_SILO_CROSS_CLUSTER"],
            "CROSS_SILO": relationships["CROSS_SILO"],
            "INVOLVES_UNCLASSIFIED": relationships["INVOLVES_UNCLASSIFIED"],
        },
    }
    if snapshot.get("metrics") != computed:
        raise ObservedGraphError(f"metrics_mismatch:{computed!r}")
    stored_orphans = sorted(str(item) for item in snapshot.get("inbound_orphan_article_ids", []))
    if stored_orphans != orphan_ids:
        raise ObservedGraphError("orphan_list_mismatch")
    return computed


def run(path: Path) -> dict[str, Any]:
    snapshot = json.loads(path.read_text(encoding="utf-8"))
    return validate_observed_graph(snapshot)


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Validate the readonly observed Blogger editorial graph")
    parser.add_argument("--snapshot", required=True, type=Path)
    args = parser.parse_args()
    metrics = run(args.snapshot)
    print(json.dumps(metrics, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
