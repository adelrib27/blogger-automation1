import base64
import html
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from quality_gate import (
    cannibalization_reasons,
    draft_quality,
    publication_quality,
)

ROOT = Path(__file__).resolve().parents[2]
QUEUE_PATH = ROOT / "casa_decoracao" / "data" / "editorial_queue_100.json"
GENERATED_DIR = ROOT / "casa_decoracao" / "data" / "generated"
WP_URL = "https://casaedecoracao.radartechbr.com.br"
STATUS = os.getenv("CASA_WORDPRESS_STATUS", "draft").strip().lower()
PUBLISH_LIMIT = max(1, min(int(os.getenv("CASA_PUBLISH_LIMIT", "5")), 20))

CATEGORY_SLUGS = {
    "Decoração": "decoracao",
    "Organização": "organizacao",
    "Sala": "sala",
    "Quarto": "quarto",
    "Cozinha": "cozinha",
    "Banheiro": "banheiro",
    "Área Externa": "area-externa",
    "Cama, Mesa e Banho": "cama-mesa-banho",
    "Iluminação": "iluminacao",
    "Limpeza e Utilidades": "limpeza-utilidades",
}


def load_json(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def credentials():
    user = os.getenv("CASA_WORDPRESS_USERNAME", "").strip()
    password = os.getenv("CASA_WORDPRESS_APP_PASSWORD", "").strip()
    if not user or not password:
        raise RuntimeError("CASA_WORDPRESS_USERNAME/CASA_WORDPRESS_APP_PASSWORD ausentes")
    return user, password


def request(method, path, payload=None):
    user, password = credentials()
    token = base64.b64encode(f"{user}:{password}".encode()).decode()
    data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        WP_URL + "/wp-json" + path,
        data=data,
        method=method,
        headers={
            "Authorization": f"Basic {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "CasaEDecoracao-Publisher/2.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            raw = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:1200]
        raise RuntimeError(f"WordPress HTTP {exc.code}: {detail}") from exc
    return json.loads(raw) if raw else {}


def category_id(name):
    slug = CATEGORY_SLUGS.get(name)
    if not slug:
        raise RuntimeError(f"categoria sem slug: {name}")
    rows = request("GET", "/wp/v2/categories?slug=" + urllib.parse.quote(slug))
    if not isinstance(rows, list) or not rows:
        raise RuntimeError(f"categoria não encontrada no WordPress: {name} ({slug})")
    return int(rows[0]["id"])


def slugify(text):
    value = str(text or "").casefold()
    table = str.maketrans("áàâãéêíóôõúç", "aaaaeeiooouc")
    value = value.translate(table)
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value[:78].rstrip("-")


def find_existing(slug):
    statuses = "publish,draft,pending,private,future"
    path = "/wp/v2/posts?context=edit&per_page=5&slug=" + urllib.parse.quote(slug) + "&status=" + statuses
    rows = request("GET", path)
    if isinstance(rows, list) and rows:
        return rows[0]
    return None


def existing_posts_for_quality():
    statuses = urllib.parse.quote("publish,draft,pending,private,future", safe=",")
    fields = urllib.parse.quote("id,slug,title,excerpt,content,status,link", safe=",")
    path = f"/wp/v2/posts?context=edit&per_page=100&status={statuses}&_fields={fields}"
    rows = request("GET", path)
    return rows if isinstance(rows, list) else []


def related_posts(cat_id, current_slug, limit=2):
    fields = urllib.parse.quote("id,slug,title,link", safe=",")
    path = f"/wp/v2/posts?status=publish&per_page=8&categories={cat_id}&orderby=date&order=desc&_fields={fields}"
    rows = request("GET", path)
    if not isinstance(rows, list):
        return []
    return [row for row in rows if str(row.get("slug") or "") != current_slug][:limit]


def clean_rendered_title(value):
    if isinstance(value, dict):
        value = value.get("rendered") or ""
    value = re.sub(r"<[^>]+>", " ", str(value or ""))
    return html.unescape(re.sub(r"\s+", " ", value)).strip()


def add_related_internal_links(article, cat_id, stable_slug):
    content = str(article.get("content_html") or "")
    if "class=\"cd-links-internos\"" in content:
        return content
    rows = related_posts(cat_id, stable_slug, limit=2)
    if not rows:
        return content
    items = []
    for row in rows:
        title = html.escape(clean_rendered_title(row.get("title")))
        link = html.escape(str(row.get("link") or ""), quote=True)
        if title and link.startswith(WP_URL):
            items.append(f'<li><a href="{link}">{title}</a></li>')
    if not items:
        return content
    block = '<div class="cd-links-internos"><h2>Veja também</h2><ul>' + "".join(items) + "</ul></div>\n"
    marker = '<div class="cd-produto-relacionado"'
    if marker in content:
        return content.replace(marker, block + marker, 1)
    return content + "\n" + block


def set_aioseo(post_id, article):
    request("POST", "/aioseo/v1/post", {
        "id": int(post_id),
        "title": article["seo_title"],
        "description": article["meta_description"],
    })
    request("POST", f"/aioseo/v1/truseo/posts/{int(post_id)}", {
        "focus_keyword": article["focus_keyword"],
        "additional_keywords": [],
        "truseo_locale": "pt_BR",
    })


def set_featured_alt(article):
    media_id = int(article.get("featured_media_id") or 0)
    alt = str(article.get("featured_image_alt") or "").strip()
    if media_id and alt:
        request("POST", f"/wp/v2/media/{media_id}", {"alt_text": alt})


def publish_article(article, existing_posts):
    cat_id = category_id(article["category"])
    stable_slug = slugify(article.get("topic") or article["seo_title"])
    article["content_html"] = add_related_internal_links(article, cat_id, stable_slug)

    gate = draft_quality(article)
    if gate["status"] != "DRAFT_READY":
        raise RuntimeError("quality gate de rascunho: " + ", ".join(gate["reasons"]))

    duplicate_reasons = cannibalization_reasons(article, existing_posts, current_slug=stable_slug)
    if duplicate_reasons:
        raise RuntimeError("canibalização/duplicidade: " + ", ".join(duplicate_reasons))

    publication_gate = publication_quality(article, existing_posts, current_slug=stable_slug)
    article["quality"] = publication_gate
    if STATUS == "publish" and publication_gate["status"] != "QUALITY_APPROVED":
        raise RuntimeError("publicação ao vivo bloqueada: " + ", ".join(publication_gate["reasons"]))

    payload = {
        "title": article["seo_title"],
        "slug": stable_slug,
        "status": STATUS,
        "categories": [cat_id],
        "excerpt": article.get("excerpt") or article.get("meta_description") or "",
        "content": article["content_html"],
    }
    media_id = int(article.get("featured_media_id") or 0)
    if media_id:
        payload["featured_media"] = media_id

    existing = find_existing(stable_slug)
    if existing and existing.get("id"):
        result = request("POST", f"/wp/v2/posts/{int(existing['id'])}", payload)
        action = "updated"
    else:
        result = request("POST", "/wp/v2/posts", payload)
        action = "created"

    post_id = int(result.get("id") or 0)
    if not post_id:
        raise RuntimeError("WordPress não retornou ID do post")
    set_aioseo(post_id, article)
    set_featured_alt(article)

    return {
        "id": post_id,
        "status": result.get("status"),
        "url": result.get("link"),
        "slug": stable_slug,
        "action": action,
        "seo_synced": True,
        "quality_status": publication_gate["status"],
        "quality_reasons": publication_gate["reasons"],
    }


def main():
    if STATUS not in {"draft", "publish", "pending", "private"}:
        raise RuntimeError("CASA_WORDPRESS_STATUS deve ser draft/publish/pending/private")

    queue = load_json(QUEUE_PATH, {})
    items = queue.get("items") or []
    candidates = [x for x in items if x.get("status") == "GENERATED"][:PUBLISH_LIMIT]
    if not candidates:
        print("Nenhum artigo GENERATED para sincronizar.")
        return

    index = {int(x["id"]): x for x in items}
    existing_posts = existing_posts_for_quality()

    for item in candidates:
        item_id = int(item["id"])
        article_path = GENERATED_DIR / f"{item_id:03d}.json"
        article = load_json(article_path, {})
        if not article:
            index[item_id]["status"] = "QUARANTINE"
            index[item_id]["last_error"] = "arquivo gerado ausente"
            continue
        try:
            result = publish_article(article, existing_posts)
            article["wordpress"] = result
            article["status"] = "PUBLISHED" if result.get("status") == "publish" else "WORDPRESS_DRAFT"
            save_json(article_path, article)
            index[item_id]["status"] = article["status"]
            index[item_id]["wordpress"] = result
            index[item_id]["quality"] = article.get("quality")
            index[item_id].pop("last_error", None)
            print(f"WordPress {item_id}: {result}")

            existing_posts = existing_posts_for_quality()
        except Exception as exc:
            index[item_id]["status"] = "QUARANTINE"
            index[item_id]["last_error"] = str(exc)[:700]
            print(f"QUARANTINE {item_id}: {exc}")

    queue["items"] = [index[int(x["id"])] for x in items]
    save_json(QUEUE_PATH, queue)


if __name__ == "__main__":
    main()
