from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from lab_topic_graph.topic_graph_safe import (
    dump_json,
    legacy_relevance,
    normalize_text,
    semantic_overlap,
)


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _relation_bucket(source: dict[str, Any], target: dict[str, Any]) -> str:
    source_ok = source.get("classification", {}).get("status") == "APPROVED"
    target_ok = target.get("classification", {}).get("status") == "APPROVED"
    if not source_ok or not target_ok:
        return "legacy_unclassified_endpoint"
    if source.get("cluster_id") == target.get("cluster_id"):
        return "legacy_same_cluster"
    if source.get("silo_id") == target.get("silo_id"):
        return "legacy_cross_cluster_same_silo"
    return "legacy_cross_silo"


def build_enhanced_ab(content_registry: dict[str, Any], comparison: dict[str, Any]) -> dict[str, Any]:
    articles = content_registry.get("articles", [])
    by_id = {str(article.get("article_id")): article for article in articles}
    counts = Counter()
    reviewed_rows = []

    for row in comparison.get("rows", []):
        source = by_id.get(str(row.get("source_article_id")))
        if not source:
            continue
        row_counts = Counter()
        for candidate in row.get("legacy_selected", []):
            target = by_id.get(str(candidate.get("target_article_id")))
            if not target:
                row_counts["legacy_missing_target"] += 1
                continue
            row_counts[_relation_bucket(source, target)] += 1
        counts.update(row_counts)
        reviewed_rows.append({"source_article_id": source["article_id"], **dict(row_counts)})

    total = sum(counts.values())
    return {
        "schema_version": "2.0",
        "evaluation_mode": "CURRENT_CORPUS_COUNTERFACTUAL",
        "note": (
            "Structural review signals only. Cross-silo does not equal a proven false positive; "
            "manual semantic review is required before labeling quality errors. This current-corpus "
            "view is not a historical reconstruction because it can include targets published later."
        ),
        "aggregate": {"legacy_links_accounted": total, **dict(counts)},
        "rows": reviewed_rows,
    }


def _parse_datetime(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None


def build_publication_time_ab(content_registry: dict[str, Any], history: list[dict[str, Any]]) -> dict[str, Any]:
    articles = content_registry.get("articles", [])
    by_id = {str(article.get("article_id")): article for article in articles}
    history_by_id = {str(item.get("id") or ""): item for item in history}
    published = {
        article_id: _parse_datetime(history_by_id.get(article_id, {}).get("publicado_em"))
        for article_id in by_id
    }
    counts = Counter()
    rows = []

    for source_id, source in by_id.items():
        source_time = published.get(source_id)
        if source.get("status") != "LIVE" or source_time is None:
            continue

        eligible = []
        for target_id, target in by_id.items():
            if target_id == source_id or target.get("status") != "LIVE":
                continue
            target_time = published.get(target_id)
            if target_time is None or target_time >= source_time:
                continue
            score = legacy_relevance(source, target)
            if score > 0:
                eligible.append({"target_article_id": target_id, "score": score})
        eligible.sort(key=lambda item: (-item["score"], item["target_article_id"]))
        legacy = eligible[:3]

        row_counts = Counter()
        for candidate in legacy:
            target = by_id[candidate["target_article_id"]]
            row_counts[_relation_bucket(source, target)] += 1
        counts.update(row_counts)

        topic_candidates = []
        if source.get("classification", {}).get("status") == "APPROVED":
            for target_id, target in by_id.items():
                if target_id == source_id:
                    continue
                target_time = published.get(target_id)
                if target_time is None or target_time >= source_time:
                    continue
                if target.get("classification", {}).get("status") != "APPROVED":
                    continue
                if target.get("site_id") != source.get("site_id"):
                    continue
                if target.get("silo_id") != source.get("silo_id"):
                    continue
                if target.get("cluster_id") != source.get("cluster_id"):
                    continue
                topic_candidates.append({
                    "target_article_id": target_id,
                    "semantic_score": semantic_overlap(source, target),
                })
            topic_candidates.sort(key=lambda item: (-item["semantic_score"], item["target_article_id"]))
            topic_candidates = topic_candidates[:3]

        rows.append({
            "source_article_id": source_id,
            "source_published_at": history_by_id[source_id].get("publicado_em"),
            "legacy_selected": legacy,
            **dict(row_counts),
            "topic_structural_candidates": topic_candidates,
        })
        counts["sources_evaluated"] += 1
        counts["legacy_links_selected"] += len(legacy)
        counts["topic_structural_candidates"] += len(topic_candidates)

    return {
        "schema_version": "2.0",
        "evaluation_mode": "PUBLICATION_TIME_SHADOW",
        "note": (
            "Only targets published before each source are eligible. This better approximates the "
            "candidate set available to the live selector at publication time. It still does not "
            "prove semantic quality and does not reconstruct edits made outside the pipeline."
        ),
        "aggregate": dict(counts),
        "rows": rows,
    }


def build_anchor_registry(link_graph: dict[str, Any]) -> dict[str, Any]:
    anchors: dict[str, dict[str, Any]] = {}
    for edge in link_graph.get("edges", []):
        anchor = str(edge.get("anchor_text") or "").strip()
        if not anchor:
            continue
        key = normalize_text(anchor)
        item = anchors.setdefault(key, {
            "anchor_text": anchor,
            "anchor_type": edge.get("anchor_type"),
            "uses": 0,
            "target_article_ids": [],
            "edge_statuses": Counter(),
        })
        item["uses"] += 1
        target_id = str(edge.get("target_article_id") or "")
        if target_id and target_id not in item["target_article_ids"]:
            item["target_article_ids"].append(target_id)
        item["edge_statuses"][str(edge.get("status") or "UNKNOWN")] += 1

    rows = []
    for key in sorted(anchors):
        item = anchors[key]
        item["edge_statuses"] = dict(item["edge_statuses"])
        rows.append(item)
    return {"schema_version": "1.0", "rows": rows}


def build_link_health(content_registry: dict[str, Any]) -> dict[str, Any]:
    rows = []
    counts = Counter()
    for article in content_registry.get("articles", []):
        health = str(article.get("target_health") or "UNKNOWN")
        counts[health] += 1
        rows.append({
            "article_id": article.get("article_id"),
            "url": article.get("url"),
            "canonical_url": article.get("canonical_url"),
            "content_status": article.get("status"),
            "target_health": health,
            "last_verified_at": article.get("last_verified_at"),
        })
    return {
        "schema_version": "1.0",
        "verification_mode": "OFFLINE_REGISTERED_ONLY",
        "status_counts": dict(counts),
        "rows": rows,
    }


def run(output_dir: Path, history_path: Path) -> None:
    content = load(output_dir / "content_registry.json")
    graph = load(output_dir / "link_graph.json")
    comparison = load(output_dir / "comparison_ab.json")
    history = load(history_path)
    dump_json(output_dir / "comparison_ab_v2.json", build_enhanced_ab(content, comparison))
    dump_json(output_dir / "comparison_publication_time_v2.json", build_publication_time_ab(content, history))
    dump_json(output_dir / "anchor_registry.json", build_anchor_registry(graph))
    dump_json(output_dir / "link_health.json", build_link_health(content))


def main() -> int:
    parser = argparse.ArgumentParser(description="Additional read-only Topic Graph LAB diagnostics")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--history", required=True, type=Path)
    args = parser.parse_args()
    run(args.output, args.history)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
