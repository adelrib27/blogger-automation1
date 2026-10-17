import json
import urllib.parse
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

from publication_gate_v2 import QUALITY_GATE_VERSION, publication_quality_v2
from publish_generated import (
    GENERATED_DIR,
    QUEUE_PATH,
    category_id,
    load_json,
    request,
    slugify,
)

ROOT = Path(__file__).resolve().parents[2]
REPORT_PATH = ROOT / "casa_decoracao" / "data" / "publication_gate_report.json"


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def content_value(value):
    if isinstance(value, dict):
        return str(value.get("raw") or value.get("rendered") or "")
    return str(value or "")


def editorial_portion(content):
    content = str(content or "")
    markers = (
        '<div class="cd-produto-relacionado"',
        "<div class='cd-produto-relacionado'",
    )
    for marker in markers:
        if marker in content:
            return content.split(marker, 1)[0].strip()
    return content.strip()


def public_posts_for_quality():
    statuses = urllib.parse.quote("publish,future", safe=",")
    fields = urllib.parse.quote("id,slug,title,excerpt,content,status,link", safe=",")
    path = f"/wp/v2/posts?context=edit&per_page=100&status={statuses}&_fields={fields}"
    rows = request("GET", path)
    return rows if isinstance(rows, list) else []


def wp_post(post_id):
    fields = "id,slug,status,featured_media,title,excerpt,content,categories,link,aioseo_meta_data"
    return request("GET", f"/wp/v2/posts/{int(post_id)}?context=edit&_fields={fields}")


def wp_media(media_id):
    fields = "id,source_url,alt_text"
    return request("GET", f"/wp/v2/media/{int(media_id)}?context=edit&_fields={fields}")


def normalized_simple(value):
    return " ".join(str(value or "").casefold().split())


def audit_item(item, existing_posts):
    item_id = int(item.get("id") or 0)
    reasons = []
    article_path = GENERATED_DIR / f"{item_id:03d}.json"
    article = load_json(article_path, {})
    if not article:
        return {
            "id": item_id,
            "topic": item.get("topic"),
            "wordpress_id": (item.get("wordpress") or {}).get("id"),
            "eligible_for_live": False,
            "reasons": ["arquivo_gerado_ausente"],
        }

    post_id = int((item.get("wordpress") or article.get("wordpress") or {}).get("id") or 0)
    if not post_id:
        return {
            "id": item_id,
            "topic": item.get("topic"),
            "wordpress_id": None,
            "eligible_for_live": False,
            "reasons": ["wordpress_id_ausente"],
        }

    try:
        post = wp_post(post_id)
    except Exception as exc:
        return {
            "id": item_id,
            "topic": item.get("topic"),
            "wordpress_id": post_id,
            "eligible_for_live": False,
            "reasons": [f"falha_leitura_wordpress:{str(exc)[:180]}"],
        }

    if str(post.get("status") or "") != "draft":
        reasons.append(f"wordpress_status_invalido:{post.get('status')}")

    expected_slug = slugify(article.get("topic") or article.get("seo_title"))
    if str(post.get("slug") or "") != expected_slug:
        reasons.append("slug_divergente")

    try:
        expected_cat = category_id(str(article.get("category") or ""))
        if expected_cat not in [int(x) for x in (post.get("categories") or [])]:
            reasons.append("categoria_wordpress_divergente")
    except Exception:
        reasons.append("categoria_wordpress_nao_validada")

    article_eval = deepcopy(article)
    actual_content = content_value(post.get("content"))
    article_eval["content_html"] = actual_content
    article_eval["editorial_html"] = editorial_portion(actual_content)
    article_eval.pop("word_count", None)
    article_eval["last_error"] = str(article.get("last_error") or item.get("last_error") or "").strip()

    media_id = int(post.get("featured_media") or 0)
    if media_id:
        try:
            media = wp_media(media_id)
            article_eval["featured_media_id"] = media_id
            article_eval["featured_image_url"] = str(media.get("source_url") or "")
            article_eval["featured_image_alt"] = str(media.get("alt_text") or "")
        except Exception:
            reasons.append("imagem_destacada_nao_validada")

    aioseo = post.get("aioseo_meta_data") or {}
    actual_title = str(aioseo.get("title") or "").strip()
    actual_description = str(aioseo.get("description") or "").strip()
    actual_focus = str(aioseo.get("focus_keyword") or "").strip()
    if not actual_title:
        reasons.append("aioseo_title_ausente")
    if not actual_description:
        reasons.append("aioseo_description_ausente")
    if not actual_focus:
        reasons.append("aioseo_focus_keyword_ausente")

    if actual_title and normalized_simple(actual_title) != normalized_simple(article.get("seo_title")):
        reasons.append("aioseo_title_divergente")
    if actual_description and normalized_simple(actual_description) != normalized_simple(article.get("meta_description")):
        reasons.append("aioseo_description_divergente")
    if actual_focus and normalized_simple(actual_focus) != normalized_simple(article.get("focus_keyword")):
        reasons.append("aioseo_focus_keyword_divergente")

    gate = publication_quality_v2(article_eval, existing_posts, current_slug=expected_slug)
    reasons.extend(gate["reasons"])
    reasons = sorted(set(reasons))

    return {
        "id": item_id,
        "topic": item.get("topic"),
        "product": item.get("product"),
        "category": item.get("category"),
        "wordpress_id": post_id,
        "wordpress_status": post.get("status"),
        "slug": post.get("slug"),
        "quality_gate_version": QUALITY_GATE_VERSION,
        "generation_policy_version": int(article.get("generation_policy_version") or 0),
        "eligible_for_live": not reasons,
        "reasons": reasons,
        "metrics": gate.get("metrics") or {},
    }


def main():
    queue = load_json(QUEUE_PATH, {})
    items = queue.get("items") or []
    candidates = [x for x in items if x.get("status") == "WORDPRESS_DRAFT"]
    existing_posts = public_posts_for_quality()

    results = [audit_item(item, existing_posts) for item in candidates]
    eligible = [row for row in results if row.get("eligible_for_live")]
    blocked = [row for row in results if not row.get("eligible_for_live")]
    reasons = Counter(reason.split(":", 1)[0] for row in blocked for reason in row.get("reasons") or [])

    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "project": "Casa e Decoração",
        "mode": "READ_ONLY_RELEASE_AUDIT",
        "quality_gate_version": QUALITY_GATE_VERSION,
        "live_publication_changed": False,
        "summary": {
            "wordpress_drafts_in_queue": len(candidates),
            "eligible_for_live": len(eligible),
            "blocked_or_review": len(blocked),
        },
        "top_block_reasons": dict(reasons.most_common(20)),
        "eligible": eligible,
        "blocked": blocked,
    }
    save_json(REPORT_PATH, report)

    print(json.dumps(report["summary"], ensure_ascii=False))
    if eligible:
        print("Elegíveis:", ", ".join(str(row["id"]) for row in eligible))
    else:
        print("Nenhum rascunho liberado pelo gate v2.")
    print("Relatório:", REPORT_PATH)


if __name__ == "__main__":
    main()
