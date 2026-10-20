from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse


ALLOWED_CLASSIFICATION = {
    "APPROVED",
    "UNCLASSIFIED_NO_MATCH",
    "BLOCKED_AMBIGUOUS",
    "BLOCKED_CATEGORY_CONFLICT",
}
ALLOWED_ROLES = {"PILLAR", "SATELLITE"}
ALLOWED_RELATIONSHIPS = {
    "SATELLITE_TO_PILLAR",
    "SATELLITE_TO_SATELLITE",
    "PILLAR_TO_SATELLITE",
}
BAD_ANCHORS = {
    "clique aqui",
    "saiba mais",
    "veja aqui",
    "confira aqui",
    "acesse aqui",
    "link",
}
STOPWORDS = {
    "a", "ao", "aos", "as", "com", "como", "da", "das", "de", "do", "dos",
    "e", "em", "o", "os", "para", "por", "que", "um", "uma", "uns", "umas",
    "vale", "pena", "review", "analise", "completa", "completo", "oferta",
}
DEFAULT_BUDGETS = {"SATELLITE": 3, "PILLAR": 8}


class LabSafetyError(RuntimeError):
    """Raised when a LAB invariant is violated."""


@dataclass(frozen=True)
class Classification:
    status: str
    silo_id: str | None = None
    cluster_id: str | None = None
    score: float = 0.0
    matched_terms: tuple[str, ...] = ()
    reasons: tuple[str, ...] = ()


def normalize_text(value: Any) -> str:
    text = str(value or "").lower().strip()
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_terms(value: Any) -> set[str]:
    return {
        token
        for token in normalize_text(value).split()
        if len(token) >= 3 and token not in STOPWORDS
    }


def stable_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def dump_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=False)
        handle.write("\n")


def is_same_site_url(url: str, site_host: str) -> bool:
    try:
        parsed = urlparse(str(url or "").strip())
    except ValueError:
        return False
    return parsed.scheme == "https" and parsed.netloc == site_host and bool(parsed.path)


def validate_cluster_registry(registry: dict[str, Any]) -> None:
    if registry.get("schema_version") != "1.0":
        raise LabSafetyError("registry_schema_version_unsupported")
    if not registry.get("site_id"):
        raise LabSafetyError("registry_site_id_missing")
    site_host = registry.get("site_host")
    if not site_host or "." not in site_host:
        raise LabSafetyError("registry_site_host_invalid")

    silos = registry.get("silos")
    if not isinstance(silos, list) or not silos:
        raise LabSafetyError("registry_silos_missing")

    seen_silos: set[str] = set()
    seen_clusters: set[str] = set()
    for silo in silos:
        silo_id = str(silo.get("silo_id") or "").strip()
        if not silo_id or silo_id in seen_silos:
            raise LabSafetyError("registry_silo_id_invalid_or_duplicate")
        seen_silos.add(silo_id)
        clusters = silo.get("clusters")
        if not isinstance(clusters, list) or not clusters:
            raise LabSafetyError(f"registry_clusters_missing:{silo_id}")
        for cluster in clusters:
            cluster_id = str(cluster.get("cluster_id") or "").strip()
            if not cluster_id or cluster_id in seen_clusters:
                raise LabSafetyError("registry_cluster_id_invalid_or_duplicate")
            seen_clusters.add(cluster_id)
            include_terms = cluster.get("include_terms")
            if not isinstance(include_terms, list) or not any(str(x).strip() for x in include_terms):
                raise LabSafetyError(f"registry_include_terms_missing:{cluster_id}")
            pillar_id = cluster.get("pillar_article_id")
            if pillar_id is not None and not str(pillar_id).strip():
                raise LabSafetyError(f"registry_pillar_article_id_invalid:{cluster_id}")


def iter_clusters(registry: dict[str, Any]) -> Iterable[tuple[dict[str, Any], dict[str, Any]]]:
    for silo in registry["silos"]:
        for cluster in silo["clusters"]:
            yield silo, cluster


def _phrase_present(normalized_text: str, phrase: str) -> bool:
    phrase_normalized = normalize_text(phrase)
    if not phrase_normalized:
        return False
    return re.search(rf"(?:^|\s){re.escape(phrase_normalized)}(?:$|\s)", normalized_text) is not None


def classify_article(article: dict[str, Any], registry: dict[str, Any]) -> Classification:
    title = str(article.get("titulo") or article.get("title") or "").strip()
    keyword = str(article.get("palavra_chave") or article.get("primary_keyword") or "").strip()
    category = str(article.get("categoria") or article.get("category") or "").strip()
    normalized_blob = normalize_text(f"{title} {keyword}")
    normalized_category = normalize_text(category)

    candidates: list[dict[str, Any]] = []
    for silo, cluster in iter_clusters(registry):
        forbidden = [str(x) for x in cluster.get("forbidden_terms", []) if str(x).strip()]
        if any(_phrase_present(normalized_blob, term) for term in forbidden):
            continue

        matches = [
            str(term)
            for term in cluster.get("include_terms", [])
            if str(term).strip() and _phrase_present(normalized_blob, str(term))
        ]
        min_hits = int(cluster.get("min_term_hits", 1))
        if len(matches) < min_hits:
            continue

        score = float(sum(2.0 if " " in normalize_text(term) else 1.0 for term in matches))
        categories = [normalize_text(x) for x in cluster.get("source_categories", []) if str(x).strip()]
        category_match = bool(normalized_category and normalized_category in categories)
        if category_match:
            score += 1.0

        candidates.append(
            {
                "silo_id": silo["silo_id"],
                "cluster_id": cluster["cluster_id"],
                "score": score,
                "matches": tuple(sorted(set(matches))),
                "category_match": category_match,
                "allow_category_drift": bool(cluster.get("allow_category_drift", False)),
                "accepted_categories": tuple(categories),
            }
        )

    if not candidates:
        return Classification(status="UNCLASSIFIED_NO_MATCH", reasons=("no_cluster_term_match",))

    candidates.sort(key=lambda item: (-item["score"], item["cluster_id"]))
    top = candidates[0]
    tied = [item for item in candidates if item["score"] == top["score"]]
    if len(tied) > 1:
        return Classification(
            status="BLOCKED_AMBIGUOUS",
            score=top["score"],
            matched_terms=top["matches"],
            reasons=("top_score_tie",),
        )

    if normalized_category and top["accepted_categories"] and not top["category_match"] and not top["allow_category_drift"]:
        return Classification(
            status="BLOCKED_CATEGORY_CONFLICT",
            silo_id=top["silo_id"],
            cluster_id=top["cluster_id"],
            score=top["score"],
            matched_terms=top["matches"],
            reasons=("source_category_not_allowed",),
        )

    return Classification(
        status="APPROVED",
        silo_id=top["silo_id"],
        cluster_id=top["cluster_id"],
        score=top["score"],
        matched_terms=top["matches"],
        reasons=("structural_term_match",),
    )


def _cluster_by_id(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for silo, cluster in iter_clusters(registry):
        enriched = dict(cluster)
        enriched["silo_id"] = silo["silo_id"]
        result[cluster["cluster_id"]] = enriched
    return result


def _article_id(article: dict[str, Any]) -> str:
    raw = article.get("id") or article.get("article_id") or article.get("cms_id")
    return str(raw or "").strip()


def build_content_registry(history: list[dict[str, Any]], registry: dict[str, Any]) -> list[dict[str, Any]]:
    validate_cluster_registry(registry)
    cluster_index = _cluster_by_id(registry)
    site_id = registry["site_id"]
    site_host = registry["site_host"]
    entries: list[dict[str, Any]] = []

    for article in history:
        article_id = _article_id(article)
        if not article_id:
            article_id = "meta-" + stable_hash(
                {
                    "titulo": article.get("titulo"),
                    "url": article.get("url"),
                    "publicado_em": article.get("publicado_em"),
                }
            )[:20]

        classification = classify_article(article, registry)
        cluster = cluster_index.get(classification.cluster_id or "")
        pillar_article_id = str(cluster.get("pillar_article_id") or "").strip() if cluster else ""
        role = "PILLAR" if pillar_article_id and article_id == pillar_article_id else "SATELLITE"
        url = str(article.get("url") or "").strip()
        url_valid = is_same_site_url(url, site_host)
        metadata_fingerprint = {
            "id": article_id,
            "titulo": article.get("titulo", ""),
            "url": url,
            "categoria": article.get("categoria", ""),
            "palavra_chave": article.get("palavra_chave", ""),
            "publicado_em": article.get("publicado_em", ""),
            "atualizado_em": article.get("atualizado_em", ""),
        }
        entries.append(
            {
                "article_id": article_id,
                "site_id": site_id,
                "cms_id": article_id,
                "url": url,
                "canonical_url": url if url_valid else None,
                "status": "LIVE" if url_valid else "BLOCKED_URL_INVALID",
                "title": str(article.get("titulo") or "").strip(),
                "category": str(article.get("categoria") or "").strip(),
                "primary_keyword": str(article.get("palavra_chave") or "").strip(),
                "silo_id": classification.silo_id,
                "cluster_id": classification.cluster_id,
                "role": role,
                "primary_intent": None,
                "classification": {
                    "version": registry["schema_version"],
                    "method": "deterministic_shadow",
                    "status": classification.status,
                    "score": classification.score,
                    "matched_terms": list(classification.matched_terms),
                    "reasons": list(classification.reasons),
                },
                "content_hash": None,
                "metadata_hash": stable_hash(metadata_fingerprint),
                "target_health": "REGISTERED_ONLY" if url_valid else "INVALID_URL",
                "last_verified_at": None,
            }
        )
    return entries


def legacy_relevance(source: dict[str, Any], target: dict[str, Any]) -> int:
    source_terms = extract_terms(
        f"{source.get('title', '')} {source.get('primary_keyword', '')} {source.get('category', '')}"
    )
    target_terms = extract_terms(
        f"{target.get('title', '')} {target.get('primary_keyword', '')} {target.get('category', '')}"
    )
    score = len(source_terms.intersection(target_terms)) * 3

    source_category = normalize_text(source.get("category", ""))
    target_category = normalize_text(target.get("category", ""))
    if source_category and target_category and source_category == target_category:
        score += 2

    keyword = normalize_text(source.get("primary_keyword", ""))
    if keyword:
        for term in extract_terms(keyword):
            if term in target_terms:
                score += 2
    return score


def legacy_select(source: dict[str, Any], entries: list[dict[str, Any]], limit: int = 3) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for target in entries:
        if target["article_id"] == source["article_id"]:
            continue
        if target["status"] != "LIVE":
            continue
        score = legacy_relevance(source, target)
        if score <= 0:
            continue
        candidates.append({"target_article_id": target["article_id"], "score": score})
    candidates.sort(key=lambda item: (-item["score"], item["target_article_id"]))
    return candidates[:limit]


def semantic_overlap(source: dict[str, Any], target: dict[str, Any]) -> float:
    left = extract_terms(f"{source.get('title', '')} {source.get('primary_keyword', '')}")
    right = extract_terms(f"{target.get('title', '')} {target.get('primary_keyword', '')}")
    if not left or not right:
        return 0.0
    union = left.union(right)
    return round(len(left.intersection(right)) / len(union), 4) if union else 0.0


def validate_anchor(anchor_text: str) -> tuple[bool, list[str]]:
    anchor = normalize_text(anchor_text)
    reasons: list[str] = []
    if not anchor:
        reasons.append("anchor_empty")
    if anchor in BAD_ANCHORS:
        reasons.append("anchor_generic")
    if anchor.startswith("http") or "www " in anchor:
        reasons.append("anchor_raw_url")
    if len(anchor_text.strip()) > 120:
        reasons.append("anchor_too_long")
    return (not reasons, reasons)


def _relationship(source: dict[str, Any], target: dict[str, Any]) -> str | None:
    if source["role"] == "SATELLITE" and target["role"] == "PILLAR":
        return "SATELLITE_TO_PILLAR"
    if source["role"] == "SATELLITE" and target["role"] == "SATELLITE":
        return "SATELLITE_TO_SATELLITE"
    if source["role"] == "PILLAR" and target["role"] == "SATELLITE":
        return "PILLAR_TO_SATELLITE"
    return None


def _candidate_anchor(target: dict[str, Any]) -> str:
    title = str(target.get("title") or "").strip()
    return title[:120].strip()


def validate_edge(
    source: dict[str, Any],
    target: dict[str, Any],
    relationship: str,
    existing_target_ids: set[str] | None = None,
) -> tuple[str, list[str]]:
    reasons: list[str] = []
    if source.get("site_id") != target.get("site_id"):
        reasons.append("cross_site_denied")
    if not source.get("silo_id") or source.get("silo_id") != target.get("silo_id"):
        reasons.append("cross_silo_denied")
    if not source.get("cluster_id") or source.get("cluster_id") != target.get("cluster_id"):
        reasons.append("cross_cluster_denied")
    if source.get("classification", {}).get("status") != "APPROVED":
        reasons.append("source_classification_not_approved")
    if target.get("classification", {}).get("status") != "APPROVED":
        reasons.append("target_classification_not_approved")
    if target.get("status") != "LIVE":
        reasons.append("target_not_live")
    if target.get("target_health") != "VERIFIED":
        reasons.append("target_unverified")
    if relationship not in ALLOWED_RELATIONSHIPS:
        reasons.append("relationship_invalid")
    if existing_target_ids and target["article_id"] in existing_target_ids:
        reasons.append("duplicate_target")

    anchor_ok, anchor_reasons = validate_anchor(_candidate_anchor(target))
    if not anchor_ok:
        reasons.extend(anchor_reasons)

    if reasons:
        first = reasons[0]
        mapping = {
            "cross_site_denied": "BLOCKED_CROSS_SITE",
            "cross_silo_denied": "BLOCKED_CROSS_SILO",
            "cross_cluster_denied": "BLOCKED_CROSS_CLUSTER",
            "source_classification_not_approved": "BLOCKED_CLASSIFICATION",
            "target_classification_not_approved": "BLOCKED_CLASSIFICATION",
            "target_not_live": "BLOCKED_TARGET_NOT_LIVE",
            "target_unverified": "BLOCKED_TARGET_UNVERIFIED",
            "duplicate_target": "BLOCKED_DUPLICATE",
            "anchor_empty": "BLOCKED_ANCHOR",
            "anchor_generic": "BLOCKED_ANCHOR",
            "anchor_raw_url": "BLOCKED_ANCHOR",
            "anchor_too_long": "BLOCKED_ANCHOR",
            "relationship_invalid": "BLOCKED_RELATIONSHIP",
        }
        return mapping.get(first, "BLOCKED_POLICY"), reasons
    return "PLAN_READY", []


def plan_link_graph(entries: list[dict[str, Any]], registry: dict[str, Any]) -> dict[str, Any]:
    cluster_index = _cluster_by_id(registry)
    by_cluster: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for entry in entries:
        if entry.get("cluster_id"):
            by_cluster[entry["cluster_id"]].append(entry)

    edges: list[dict[str, Any]] = []
    diagnostics: list[dict[str, Any]] = []

    for source in entries:
        if source.get("classification", {}).get("status") != "APPROVED":
            continue
        cluster_id = source.get("cluster_id")
        cluster = cluster_index.get(cluster_id or "")
        if not cluster:
            diagnostics.append(
                {
                    "source_article_id": source["article_id"],
                    "status": "BLOCKED_CLUSTER_MISSING",
                }
            )
            continue

        peers = [x for x in by_cluster[cluster_id] if x["article_id"] != source["article_id"]]
        budget = int(cluster.get("link_budget", {}).get(source["role"], DEFAULT_BUDGETS[source["role"]]))
        used_targets: set[str] = set()
        selected: list[tuple[dict[str, Any], str]] = []

        pillar_id = str(cluster.get("pillar_article_id") or "").strip()
        if source["role"] == "SATELLITE":
            if pillar_id:
                pillar = next((x for x in peers if x["article_id"] == pillar_id), None)
                if pillar is None:
                    diagnostics.append(
                        {
                            "source_article_id": source["article_id"],
                            "cluster_id": cluster_id,
                            "status": "BLOCKED_PILLAR_MISSING",
                            "pillar_article_id": pillar_id,
                        }
                    )
                else:
                    selected.append((pillar, "SATELLITE_TO_PILLAR"))
            else:
                diagnostics.append(
                    {
                        "source_article_id": source["article_id"],
                        "cluster_id": cluster_id,
                        "status": "PILLAR_NOT_APPROVED",
                    }
                )

        peer_candidates = [x for x in peers if x["role"] == "SATELLITE"]
        peer_candidates.sort(
            key=lambda target: (-semantic_overlap(source, target), target["article_id"])
        )
        relationship = "PILLAR_TO_SATELLITE" if source["role"] == "PILLAR" else "SATELLITE_TO_SATELLITE"
        satellite_cap = 2 if source["role"] == "SATELLITE" else budget
        for target in peer_candidates[:satellite_cap]:
            selected.append((target, relationship))

        for target, relation in selected:
            if len(used_targets) >= budget:
                diagnostics.append(
                    {
                        "source_article_id": source["article_id"],
                        "target_article_id": target["article_id"],
                        "status": "BLOCKED_BUDGET",
                    }
                )
                continue
            status, blocking = validate_edge(source, target, relation, used_targets)
            edge = {
                "edge_id": "edge-" + stable_hash(
                    [source["article_id"], target["article_id"], relation]
                )[:20],
                "source_article_id": source["article_id"],
                "target_article_id": target["article_id"],
                "relationship": relation,
                "anchor_text": _candidate_anchor(target),
                "anchor_type": "TITLE_VARIANT",
                "semantic_score": semantic_overlap(source, target),
                "target_health": target.get("target_health"),
                "status": status,
                "blocking_reasons": blocking,
            }
            edges.append(edge)
            if status == "PLAN_READY":
                used_targets.add(target["article_id"])

    return {"schema_version": "1.0", "edges": edges, "diagnostics": diagnostics}


def plan_backfill(
    new_article_id: str,
    entries: list[dict[str, Any]],
    current_source_hashes: dict[str, str] | None = None,
) -> dict[str, Any]:
    current_source_hashes = current_source_hashes or {}
    new_article = next((x for x in entries if x["article_id"] == new_article_id), None)
    if not new_article:
        raise LabSafetyError("backfill_new_article_missing")
    if new_article.get("classification", {}).get("status") != "APPROVED":
        raise LabSafetyError("backfill_new_article_unclassified")

    jobs: list[dict[str, Any]] = []
    for source in entries:
        if source["article_id"] == new_article_id:
            continue
        if source.get("classification", {}).get("status") != "APPROVED":
            continue
        if source.get("site_id") != new_article.get("site_id"):
            continue
        if source.get("silo_id") != new_article.get("silo_id"):
            continue
        if source.get("cluster_id") != new_article.get("cluster_id"):
            continue

        stored_hash = source.get("content_hash")
        current_hash = current_source_hashes.get(source["article_id"])
        blocking: list[str] = []
        if not stored_hash:
            blocking.append("source_content_hash_missing")
        elif not current_hash:
            blocking.append("current_source_hash_missing")
        elif stored_hash != current_hash:
            blocking.append("source_hash_stale")

        jobs.append(
            {
                "job_id": "backfill-" + stable_hash([source["article_id"], new_article_id])[:20],
                "source_article_id": source["article_id"],
                "expected_source_hash": stored_hash,
                "target_article_id": new_article_id,
                "reason": "NEW_SATELLITE",
                "proposed_anchor": _candidate_anchor(new_article),
                "status": "DRY_RUN_ONLY" if not blocking else "BLOCKED_STALE_SOURCE",
                "blocking_reasons": blocking,
            }
        )
    return {"schema_version": "1.0", "jobs": jobs}


def build_baseline(entries: list[dict[str, Any]], link_graph: dict[str, Any]) -> dict[str, Any]:
    total = len(entries)
    category_count = sum(1 for item in entries if item.get("category"))
    keyword_count = sum(1 for item in entries if item.get("primary_keyword"))
    live_count = sum(1 for item in entries if item.get("status") == "LIVE")
    classifications = Counter(item.get("classification", {}).get("status") for item in entries)
    categories = Counter(item.get("category") or "(vazia)" for item in entries)
    clusters = Counter(item.get("cluster_id") or "(sem cluster)" for item in entries)
    edge_status = Counter(edge["status"] for edge in link_graph.get("edges", []))
    return {
        "total_articles": total,
        "live_valid_urls": live_count,
        "with_category": category_count,
        "with_keyword": keyword_count,
        "category_coverage_rate": round(category_count / total, 4) if total else 0.0,
        "keyword_coverage_rate": round(keyword_count / total, 4) if total else 0.0,
        "classification_status": dict(classifications),
        "categories": dict(categories),
        "clusters": dict(clusters),
        "link_edge_status": dict(edge_status),
    }


def compare_legacy_vs_topic(entries: list[dict[str, Any]]) -> dict[str, Any]:
    by_id = {item["article_id"]: item for item in entries}
    rows: list[dict[str, Any]] = []
    aggregate = Counter()

    for source in entries:
        if source.get("status") != "LIVE":
            continue
        legacy = legacy_select(source, entries, limit=3)
        source_approved = source.get("classification", {}).get("status") == "APPROVED"
        legacy_same_cluster = 0
        legacy_cross_silo = 0
        legacy_unclassified_endpoint = 0
        for candidate in legacy:
            target = by_id[candidate["target_article_id"]]
            target_approved = target.get("classification", {}).get("status") == "APPROVED"
            if source_approved and target_approved:
                if source.get("cluster_id") == target.get("cluster_id"):
                    legacy_same_cluster += 1
                elif source.get("silo_id") != target.get("silo_id"):
                    legacy_cross_silo += 1
            else:
                legacy_unclassified_endpoint += 1

        topic_candidates = []
        if source_approved:
            for target in entries:
                if target["article_id"] == source["article_id"]:
                    continue
                if target.get("classification", {}).get("status") != "APPROVED":
                    continue
                if target.get("site_id") != source.get("site_id"):
                    continue
                if target.get("silo_id") != source.get("silo_id"):
                    continue
                if target.get("cluster_id") != source.get("cluster_id"):
                    continue
                topic_candidates.append(
                    {
                        "target_article_id": target["article_id"],
                        "semantic_score": semantic_overlap(source, target),
                    }
                )
            topic_candidates.sort(key=lambda x: (-x["semantic_score"], x["target_article_id"]))
            topic_candidates = topic_candidates[:3]

        rows.append(
            {
                "source_article_id": source["article_id"],
                "source_classification": source.get("classification", {}).get("status"),
                "legacy_selected": legacy,
                "legacy_same_cluster": legacy_same_cluster,
                "legacy_cross_silo": legacy_cross_silo,
                "legacy_unclassified_endpoint": legacy_unclassified_endpoint,
                "topic_structural_candidates": topic_candidates,
            }
        )
        aggregate["sources"] += 1
        aggregate["legacy_links_selected"] += len(legacy)
        aggregate["legacy_same_cluster"] += legacy_same_cluster
        aggregate["legacy_cross_silo"] += legacy_cross_silo
        aggregate["legacy_unclassified_endpoint"] += legacy_unclassified_endpoint
        aggregate["topic_structural_candidates"] += len(topic_candidates)

    return {
        "schema_version": "1.0",
        "note": "Offline selector comparison only; no CMS content or HTTP health verification is performed.",
        "aggregate": dict(aggregate),
        "rows": rows,
    }


def classification_report(entries: list[dict[str, Any]]) -> dict[str, Any]:
    rows = []
    for entry in entries:
        rows.append(
            {
                "article_id": entry["article_id"],
                "title": entry["title"],
                "category": entry["category"],
                "status": entry["classification"]["status"],
                "silo_id": entry.get("silo_id"),
                "cluster_id": entry.get("cluster_id"),
                "score": entry["classification"].get("score"),
                "matched_terms": entry["classification"].get("matched_terms", []),
                "reasons": entry["classification"].get("reasons", []),
            }
        )
    return {"schema_version": "1.0", "rows": rows}


def assert_lab_safety() -> None:
    import os

    dangerous = {
        "LAB_TOPIC_GRAPH_WRITE_CMS": os.getenv("LAB_TOPIC_GRAPH_WRITE_CMS"),
        "LAB_TOPIC_GRAPH_PUBLISH": os.getenv("LAB_TOPIC_GRAPH_PUBLISH"),
    }
    enabled = {key: value for key, value in dangerous.items() if normalize_text(value) in {"1", "true", "yes", "on"}}
    if enabled:
        raise LabSafetyError("cms_write_or_publish_requested_in_safe_lab")


def run_safe(history_path: Path, registry_path: Path, output_dir: Path) -> dict[str, Any]:
    assert_lab_safety()
    history = load_json(history_path)
    registry = load_json(registry_path)
    if not isinstance(history, list):
        raise LabSafetyError("history_must_be_list")
    if not isinstance(registry, dict):
        raise LabSafetyError("registry_must_be_object")
    validate_cluster_registry(registry)

    entries = build_content_registry(history, registry)
    link_graph = plan_link_graph(entries, registry)
    baseline = build_baseline(entries, link_graph)
    comparison = compare_legacy_vs_topic(entries)
    classifications = classification_report(entries)
    manifest = {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "LAB_SAFE_OFFLINE",
        "site_id": registry["site_id"],
        "inputs": {
            "history_path": str(history_path),
            "registry_path": str(registry_path),
            "history_sha256": stable_hash(history),
            "registry_sha256": stable_hash(registry),
        },
        "safety": {
            "cms_write_capability": False,
            "publishing": False,
            "http_health_checks": False,
            "external_api_calls": False,
            "fail_closed_unverified_targets": True,
        },
        "decision": "ainda não validado",
    }

    dump_json(output_dir / "content_registry.json", {"schema_version": "1.0", "articles": entries})
    dump_json(output_dir / "link_graph.json", link_graph)
    dump_json(output_dir / "baseline.json", baseline)
    dump_json(output_dir / "classification_report.json", classifications)
    dump_json(output_dir / "comparison_ab.json", comparison)
    dump_json(output_dir / "run_manifest.json", manifest)
    return {
        "baseline": baseline,
        "comparison": comparison["aggregate"],
        "manifest": manifest,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Topic Graph LAB SAFE offline runner")
    parser.add_argument("--history", required=True, type=Path)
    parser.add_argument("--registry", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = run_safe(args.history, args.registry, args.output)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
