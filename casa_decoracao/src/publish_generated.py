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
IMAGE_MODEL = os.getenv("CASA_IMAGE_MODEL", "@cf/black-forest-labs/flux-1-schnell").strip()

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


def cloudflare_credentials():
    account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID", "").strip()
    token = os.getenv("CLOUDFLARE_API_TOKEN", "").strip()
    if not account_id or not token:
        raise RuntimeError("CLOUDFLARE_ACCOUNT_ID/CLOUDFLARE_API_TOKEN ausentes para imagem")
    return account_id, token


def auth_header():
    user, password = credentials()
    token = base64.b64encode(f"{user}:{password}".encode()).decode()
    return f"Basic {token}"


def request(method, path, payload=None):
    data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        WP_URL + "/wp-json" + path,
        data=data,
        method=method,
        headers={
            "Authorization": auth_header(),
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "CasaEDecoracao-Publisher/2.1",
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


def image_prompt(article):
    topic = str(article.get("topic") or article.get("seo_title") or "Casa e decoração").strip()
    product = str(article.get("product") or "item para casa").strip()
    category = str(article.get("category") or "Casa e Decoração").strip()
    return (
        f"Fotografia editorial horizontal, ultra-realista e elegante para um artigo brasileiro de casa e decoração. "
        f"Tema: {topic}. Categoria: {category}. Contexto visual relacionado a {product}, mostrado apenas de forma genérica "
        "e não como reprodução de um produto comercial específico. Ambiente doméstico realista, organizado e acolhedor, "
        "luz natural suave, materiais e proporções plausíveis, composição de revista de decoração, alta qualidade. "
        "Sem texto, sem letras, sem logotipos, sem marcas, sem etiquetas, sem preço, sem embalagem identificável, sem watermark. "
        "Não inventar especificações técnicas nem características exclusivas de um produto real."
    )


def generate_featured_image(article):
    account_id, token = cloudflare_credentials()
    endpoint = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{IMAGE_MODEL}"
    seed = int(article.get("id") or 1) * 1009 % 2147483647
    body = json.dumps({
        "prompt": image_prompt(article),
        "steps": 6,
        "seed": seed,
    }, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(endpoint, data=body, method="POST", headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "CasaEDecoracao-FeaturedImage/1.0",
    })
    try:
        with urllib.request.urlopen(req, timeout=180) as response:
            raw = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:1200]
        raise RuntimeError(f"Workers AI imagem HTTP {exc.code}: {detail}") from exc
    payload = json.loads(raw)
    result = payload.get("result") if isinstance(payload, dict) else None
    image_b64 = result.get("image") if isinstance(result, dict) else None
    if not isinstance(image_b64, str) or not image_b64.strip():
        raise RuntimeError("Workers AI não retornou imagem base64")
    try:
        return base64.b64decode(image_b64)
    except Exception as exc:
        raise RuntimeError("imagem base64 inválida") from exc


def upload_featured_media(article, image_bytes):
    if not image_bytes:
        raise RuntimeError("imagem destacada vazia")
    filename = (slugify(article.get("topic") or article.get("seo_title")) or f"casa-{article.get('id', 'post')}")[:60] + ".jpg"
    req = urllib.request.Request(
        WP_URL + "/wp-json/wp/v2/media",
        data=image_bytes,
        method="POST",
        headers={
            "Authorization": auth_header(),
            "Content-Type": "image/jpeg",
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Accept": "application/json",
            "User-Agent": "CasaEDecoracao-Publisher/2.1",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            raw = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:1200]
        raise RuntimeError(f"WordPress upload imagem HTTP {exc.code}: {detail}") from exc
    media = json.loads(raw) if raw else {}
    media_id = int(media.get("id") or 0)
    if not media_id:
        raise RuntimeError("WordPress não retornou ID da imagem")
    alt = f"Imagem editorial sobre {str(article.get('topic') or article.get('seo_title') or 'casa e decoração').strip()}"
    alt = re.sub(r"\s+", " ", alt).strip()[:180]
    request("POST", f"/wp/v2/media/{media_id}", {"alt_text": alt})
    return {
        "id": media_id,
        "url": str(media.get("source_url") or ""),
        "alt": alt,
    }


def ensure_featured_image(article):
    media_id = int(article.get("featured_media_id") or 0)
    featured_url = str(article.get("featured_image_url") or "").strip()
    if media_id or featured_url:
        return
    image_bytes = generate_featured_image(article)
    media = upload_featured_media(article, image_bytes)
    article["featured_media_id"] = media["id"]
    article["featured_image_url"] = media["url"]
    article["featured_image_alt"] = media["alt"]
    article["featured_image_source"] = IMAGE_MODEL


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

    ensure_featured_image(article)
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
        "featured_media_id": media_id,
        "quality_status": publication_gate["status"],
        "quality_reasons": publication_gate["reasons"],
    }


def needs_image_repair(item):
    if item.get("status") != "WORDPRESS_DRAFT":
        return False
    quality = item.get("quality") or {}
    reasons = quality.get("reasons") or []
    return "imagem_destacada_ausente" in reasons


def main():
    if STATUS not in {"draft", "publish", "pending", "private"}:
        raise RuntimeError("CASA_WORDPRESS_STATUS deve ser draft/publish/pending/private")

    queue = load_json(QUEUE_PATH, {})
    items = queue.get("items") or []
    candidates = [x for x in items if x.get("status") == "GENERATED" or needs_image_repair(x)][:PUBLISH_LIMIT]
    if not candidates:
        print("Nenhum artigo GENERATED ou rascunho pendente de imagem para sincronizar.")
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
