from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from lab_topic_graph.topic_graph_safe import dump_json, normalize_text


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


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
            source_ok = source.get("classification", {}).get("status") == "APPROVED"
            target_ok = target.get("classification", {}).get("status") == "APPROVED"
            if not source_ok or not target_ok:
                row_counts["legacy_unclassified_endpoint"] += 1
            elif source.get("cluster_id") == target.get("cluster_id"):
                row_counts["legacy_same_cluster"] += 1
            elif source.get("silo_id") == target.get("silo_id"):
                row_counts["legacy_cross_cluster_same_silo"] += 1
            else:
                row_counts["legacy_cross_silo"] += 1
        counts.update(row_counts)
        reviewed_rows.append({
            "source_article_id": source["article_id"],
            **dict(row_counts),
        })

    total = sum(
        counts[key]
        for key in (
            "legacy_same_cluster",
            "legacy_cross_cluster_same_silo",
            "legacy_cross_silo",
            "legacy_unclassified_endpoint",
            "legacy_missing_target",
        )
    )
    return {
        "schema_version": "2.0",
        "note": (
            "Structural review signals only. Cross-silo does not equal a proven false positive; "
            "manual semantic review is required before labeling quality errors."
        ),
        "aggregate": {
            "legacy_links_accounted": total,
            **dict(counts),
        },
        "rows": reviewed_rows,
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


def run(output_dir: Path) -> None:
    content = load(output_dir / "content_registry.json")
    graph = load(output_dir / "link_graph.json")
    comparison = load(output_dir / "comparison_ab.json")
    dump_json(output_dir / "comparison_ab_v2.json", build_enhanced_ab(content, comparison))
    dump_json(output_dir / "anchor_registry.json", build_anchor_registry(graph))
    dump_json(output_dir / "link_health.json", build_link_health(content))


def main() -> int:
    parser = argparse.ArgumentParser(description="Additional read-only Topic Graph LAB diagnostics")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    run(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
