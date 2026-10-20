from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


class ObservedGraphError(RuntimeError):
    pass


def classify_relationship(source: dict[str, Any], target: dict[str, Any]) -> str:
    source_cluster = source.get('cluster')
    target_cluster = target.get('cluster')
    if not source_cluster or not target_cluster:
        return 'INVOLVES_UNCLASSIFIED'
    if source_cluster == target_cluster:
        return 'SAME_CLUSTER'
    if source.get('silo') == target.get('silo'):
        return 'SAME_SILO_CROSS_CLUSTER'
    return 'CROSS_SILO'


def validate_observed_graph(snapshot: dict[str, Any]) -> dict[str, Any]:
    if snapshot.get('v') != '1.0':
        raise ObservedGraphError('schema_version_unsupported')
    if snapshot.get('mode') != 'LAB_READ_ONLY_OBSERVED_EDITORIAL_GRAPH':
        raise ObservedGraphError('mode_not_lab_readonly')
    if snapshot.get('source') != 'blogger_api_readonly':
        raise ObservedGraphError('source_not_blogger_readonly')
    if snapshot.get('complete') is not True:
        raise ObservedGraphError('editorial_inventory_incomplete')

    safety = snapshot.get('safety') or {}
    expected_false = ('cms_write', 'publish', 'production_modified', 'full_content_hash', 'http_canonical', 'plan_ready')
    for key in expected_false:
        if safety.get(key) is not False:
            raise ObservedGraphError(f'unsafe_{key}')

    anchor_obs = snapshot.get('anchor_observation') or {}
    if anchor_obs.get('all_edges_exact_target_title') is not True:
        raise ObservedGraphError('anchor_observation_not_exact_target_title')

    articles = snapshot.get('articles')
    edges = snapshot.get('edges')
    if not isinstance(articles, list) or not isinstance(edges, list):
        raise ObservedGraphError('articles_or_edges_not_list')

    by_id: dict[str, dict[str, Any]] = {}
    paths: set[str] = set()
    for article in articles:
        article_id = str(article.get('id') or '').strip()
        path = str(article.get('path') or '').strip()
        if not article_id or article_id in by_id:
            raise ObservedGraphError('duplicate_or_missing_article_id')
        if not path.startswith('/') or path in paths:
            raise ObservedGraphError('duplicate_or_invalid_article_path')
        if article.get('live') is not True:
            raise ObservedGraphError('article_not_live_verified')
        by_id[article_id] = article
        paths.add(path)

    seen_pairs: set[tuple[str, str]] = set()
    inbound = Counter()
    outbound = Counter()
    relationships = Counter()
    for edge in edges:
        if not isinstance(edge, list) or len(edge) != 3:
            raise ObservedGraphError('edge_shape_invalid')
        source_id, target_id, stored_relationship = map(str, edge)
        if source_id not in by_id or target_id not in by_id:
            raise ObservedGraphError('edge_unknown_source_or_target')
        if source_id == target_id:
            raise ObservedGraphError('self_link_not_allowed')
        pair = (source_id, target_id)
        if pair in seen_pairs:
            raise ObservedGraphError('duplicate_source_target')
        seen_pairs.add(pair)
        expected_relationship = classify_relationship(by_id[source_id], by_id[target_id])
        if stored_relationship != expected_relationship:
            raise ObservedGraphError('relationship_mismatch')
        inbound[target_id] += 1
        outbound[source_id] += 1
        relationships[expected_relationship] += 1

    repeated_targets = int(anchor_obs.get('targets_repeated') or 0)
    computed = {
        'editorial_articles_total': len(articles),
        'classified_articles': sum(bool(a.get('cluster')) for a in articles),
        'unclassified_articles': sum(not bool(a.get('cluster')) for a in articles),
        'editorial_edges_total': len(edges),
        'sources_with_editorial_links': sum(outbound[a['id']] > 0 for a in articles),
        'sources_without_editorial_links': sum(outbound[a['id']] == 0 for a in articles),
        'orphan_articles_inbound_zero': sum(inbound[a['id']] == 0 for a in articles),
        'same_cluster_edges': relationships['SAME_CLUSTER'],
        'same_silo_cross_cluster_edges': relationships['SAME_SILO_CROSS_CLUSTER'],
        'cross_silo_edges': relationships['CROSS_SILO'],
        'edges_involving_unclassified': relationships['INVOLVES_UNCLASSIFIED'],
        'unknown_internal_targets': 0,
        'duplicate_source_target_edges': 0,
        'targets_with_repeated_exact_anchor': repeated_targets,
        'http_canonical_verified_edges': 0,
    }
    if snapshot.get('metrics') != computed:
        raise ObservedGraphError('stored_metrics_mismatch')
    return computed


def main() -> int:
    parser = argparse.ArgumentParser(description='Validate a compact readonly observed Blogger editorial graph')
    parser.add_argument('--snapshot', type=Path, required=True)
    args = parser.parse_args()
    snapshot = json.loads(args.snapshot.read_text(encoding='utf-8'))
    metrics = validate_observed_graph(snapshot)
    print(json.dumps({'status': 'PASS', 'metrics': metrics}, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
