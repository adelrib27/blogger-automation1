from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


class ObservedGraphError(RuntimeError):
    pass


def classify_relationship(source: dict[str, Any], target: dict[str, Any]) -> str:
    source_cluster = source.get('cluster_id')
    target_cluster = target.get('cluster_id')
    if not source_cluster or not target_cluster:
        return 'INVOLVES_UNCLASSIFIED'
    if source_cluster == target_cluster:
        return 'SAME_CLUSTER'
    if source.get('silo_id') == target.get('silo_id'):
        return 'SAME_SILO_CROSS_CLUSTER'
    return 'CROSS_SILO'


def validate_observed_graph(snapshot: dict[str, Any]) -> dict[str, Any]:
    if snapshot.get('schema_version') != '1.0':
        raise ObservedGraphError('schema_version_unsupported')
    if snapshot.get('mode') != 'LAB_READ_ONLY_OBSERVED_EDITORIAL_GRAPH':
        raise ObservedGraphError('mode_not_lab_readonly')
    if snapshot.get('source') != 'blogger_api_readonly':
        raise ObservedGraphError('source_not_blogger_readonly')

    collection = snapshot.get('collection') or {}
    if collection.get('editorial_inventory_complete') is not True:
        raise ObservedGraphError('editorial_inventory_incomplete')
    if int(collection.get('articles_expected') or 0) != int(collection.get('articles_observed') or -1):
        raise ObservedGraphError('article_count_mismatch')

    safety = snapshot.get('safety') or {}
    if safety.get('cms_write_capability') is not False:
        raise ObservedGraphError('cms_write_capability_must_be_false')
    if safety.get('publishing_capability') is not False:
        raise ObservedGraphError('publishing_capability_must_be_false')
    if safety.get('production_modified') is not False:
        raise ObservedGraphError('production_modified_must_be_false')
    if safety.get('plan_ready_allowed') is not False:
        raise ObservedGraphError('plan_ready_must_be_false')
    if safety.get('full_source_content_hash_available') is not False:
        raise ObservedGraphError('content_hash_must_remain_unavailable_for_link_only_observation')

    articles = snapshot.get('articles')
    edges = snapshot.get('edges')
    if not isinstance(articles, list) or not isinstance(edges, list):
        raise ObservedGraphError('articles_or_edges_not_list')

    by_id: dict[str, dict[str, Any]] = {}
    urls: set[str] = set()
    for article in articles:
        article_id = str(article.get('article_id') or '').strip()
        url = str(article.get('url') or '').strip()
        if not article_id or article_id in by_id:
            raise ObservedGraphError('duplicate_or_missing_article_id')
        if not url or url in urls:
            raise ObservedGraphError('duplicate_or_missing_article_url')
        if article.get('blogger_live_verified') is not True:
            raise ObservedGraphError('article_not_blogger_live_verified')
        by_id[article_id] = article
        urls.add(url)

    seen_pairs: set[tuple[str, str]] = set()
    inbound = Counter()
    outbound = Counter()
    relationships = Counter()
    repeated_anchors = Counter()
    for edge in edges:
        source_id = str(edge.get('source_article_id') or '')
        target_id = str(edge.get('target_article_id') or '')
        if source_id not in by_id or target_id not in by_id:
            raise ObservedGraphError('edge_unknown_source_or_target')
        if source_id == target_id:
            raise ObservedGraphError('self_link_not_allowed')
        pair = (source_id, target_id)
        if pair in seen_pairs:
            raise ObservedGraphError('duplicate_source_target')
        seen_pairs.add(pair)
        if edge.get('target_blogger_live_verified') is not True:
            raise ObservedGraphError('edge_target_not_live_verified')
        if edge.get('http_canonical_verified') is not False:
            raise ObservedGraphError('canonical_verification_must_remain_false_in_observation')
        expected_rel = classify_relationship(by_id[source_id], by_id[target_id])
        if edge.get('relationship_observed') != expected_rel:
            raise ObservedGraphError('relationship_mismatch')
        anchor = str(edge.get('anchor_text') or '').strip()
        if not anchor:
            raise ObservedGraphError('empty_anchor')
        inbound[target_id] += 1
        outbound[source_id] += 1
        relationships[expected_rel] += 1
        repeated_anchors[(target_id, anchor)] += 1

    computed = {
        'editorial_articles_total': len(articles),
        'classified_articles': sum(bool(a.get('cluster_id')) for a in articles),
        'unclassified_articles': sum(not bool(a.get('cluster_id')) for a in articles),
        'editorial_edges_total': len(edges),
        'sources_with_editorial_links': sum(outbound[a['article_id']] > 0 for a in articles),
        'sources_without_editorial_links': sum(outbound[a['article_id']] == 0 for a in articles),
        'orphan_articles_inbound_zero': sum(inbound[a['article_id']] == 0 for a in articles),
        'same_cluster_edges': relationships['SAME_CLUSTER'],
        'same_silo_cross_cluster_edges': relationships['SAME_SILO_CROSS_CLUSTER'],
        'cross_silo_edges': relationships['CROSS_SILO'],
        'edges_involving_unclassified': relationships['INVOLVES_UNCLASSIFIED'],
        'unknown_internal_targets': 0,
        'duplicate_source_target_edges': 0,
        'targets_with_repeated_exact_anchor': sum(n > 1 for n in repeated_anchors.values()),
        'http_canonical_verified_edges': 0,
    }
    if snapshot.get('metrics') != computed:
        raise ObservedGraphError('stored_metrics_mismatch')
    return computed


def main() -> int:
    parser = argparse.ArgumentParser(description='Validate a read-only observed Blogger editorial graph')
    parser.add_argument('--snapshot', type=Path, required=True)
    args = parser.parse_args()
    snapshot = json.loads(args.snapshot.read_text(encoding='utf-8'))
    metrics = validate_observed_graph(snapshot)
    print(json.dumps({'status': 'PASS', 'metrics': metrics}, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
