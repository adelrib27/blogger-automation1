import base64
import html
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from category_rotation import load_state, mark_published, order_items, save_state
from cta_context import CTA_PRODUCT_TITLE_CLASS
from quality_gate import quality

ROOT = Path(__file__).resolve().parents[2]
QUEUE = ROOT / "casa_decoracao" / "data" / "editorial_queue.json"
GENERATED = ROOT / "casa_decoracao" / "data" / "generated"
HISTORY = ROOT / "casa_decoracao" / "data" / "publication_history.json"
ROTATION = ROOT / "casa_decoracao" / "data" / "category_rotation.json"
WP_URL = "https://casaedecoracao.radartechbr.com.br"
ENABLED = os.getenv("CASA_LIVE_PUBLISH_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}
LIMIT = max(1, min(int(os.getenv("CASA_PUBLISH_LIMIT", "1")), 3))
DAILY_CAP = max(1, min(int(os.getenv("CASA_DAILY_PUBLISH_CAP", "3")), 3))
STATUS = os.getenv("CASA_WORDPRESS_STATUS", "draft").strip().lower()
LOCAL_TZ = ZoneInfo("America/Recife")
CATEGORY_SLUGS = {
    "Decoração": "decoracao",
    "Organização": "organizacao",
    "Sala": "sala",
    "Quarto": "quarto",
    "Cozinha": "cozinha",
    "Banheiro": "banheiro",
    "Área Externa": "area-externa",
    "Cama, Mesa e Banho": "cama-mesa-banho",
}
IMAGE_EXTENSIONS = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}


def load(path, default):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def save(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def credentials():
    user = os.getenv("CASA_WORDPRESS_USERNAME", "").strip()
    password = os.getenv("CASA_WORDPRESS_APP_PASSWORD", "").strip()
    if not user or not password:
        raise RuntimeError("Credenciais WordPress Casa e Decoração ausentes")
    return user, password


def auth_header():
    user, password = credentials()
    token = base64.b64encode(f"{user}:{password}".encode()).decode()
    return f"Basic {token}"


def request(method, path, payload=None):
    data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode()
    req = urllib.request.Request(
        WP_URL + "/wp-json" + path,
        data=data,
        method=method,
        headers={
            "Authorization": auth_header(),
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "CasaEDecoracao-AutonomousPublisher/3.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            raw = response.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:800]
        raise RuntimeError(f"WordPress HTTP {exc.code}: {detail}") from exc
    return json.loads(raw) if raw else {}


def slugify(value):
    value = str(value or "").casefold().translate(str.maketrans("áàâãéêíóôõúç", "aaaaeeiooouc"))
    return re.sub(r"[^a-z0-9]+", "-", value).strip("-")[:78].rstrip("-")


def category_id(name):
    slug = CATEGORY_SLUGS.get(name)
    if not slug:
        raise RuntimeError("Categoria fora das 8 categorias oficiais: " + str(name))
    rows = request("GET", "/wp/v2/categories?slug=" + urllib.parse.quote(slug))
    if not isinstance(rows, list) or not rows:
        raise RuntimeError("Categoria ausente no WordPress: " + name)
    return int(rows[0]["id"])


def existing(slug):
    rows = request(
        "GET",
        "/wp/v2/posts?context=edit&status=draft,pending,private,future,publish&per_page=5&slug="
        + urllib.parse.quote(slug),
    )
    return rows[0] if isinstance(rows, list) and rows else None


def rendered_title(post):
    title = post.get("title") or {}
    if isinstance(title, dict):
        title = title.get("rendered") or title.get("raw") or ""
    return html.unescape(re.sub(r"<[^>]+>", "", str(title or ""))).strip()


def download_image(url):
    if not str(url or "").startswith("https://"):
        raise RuntimeError("URL de imagem inválida ou ausente")
    req = urllib.request.Request(
        str(url),
        headers={"User-Agent": "Mozilla/5.0 CasaEDecoracao/3.0", "Accept": "image/*"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            content_type = str(response.headers.get_content_type() or "").lower()
            data = response.read(12 * 1024 * 1024 + 1)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"Falha ao baixar imagem do produto: HTTP {exc.code}") from exc
    if not content_type.startswith("image/"):
        raise RuntimeError("URL do produto não retornou uma imagem")
    if len(data) > 12 * 1024 * 1024:
        raise RuntimeError("Imagem do produto excede 12 MB")
    if not data:
        raise RuntimeError("Imagem do produto vazia")
    return data, content_type


def upload_featured_image(post_id, article):
    image_url = str(article.get("image_url") or "").strip()
    image_data, content_type = download_image(image_url)
    extension = IMAGE_EXTENSIONS.get(content_type, ".jpg")
    base_name = slugify(article.get("product") or article.get("seo_title") or "imagem-produto")[:64] or "imagem-produto"
    filename = base_name + extension
    req = urllib.request.Request(
        WP_URL + f"/wp-json/wp/v2/media?post={int(post_id)}",
        data=image_data,
        method="POST",
        headers={
            "Authorization": auth_header(),
            "Content-Type": content_type,
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Accept": "application/json",
            "User-Agent": "CasaEDecoracao-AutonomousPublisher/3.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as response:
            media = json.loads(response.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:800]
        raise RuntimeError(f"Falha ao enviar imagem destacada: WordPress HTTP {exc.code}: {detail}") from exc
    media_id = int(media.get("id") or 0)
    if not media_id:
        raise RuntimeError("WordPress não confirmou o upload da imagem destacada")
    request("POST", f"/wp/v2/media/{media_id}", {"alt_text": str(article.get("product") or article.get("seo_title") or "")[:180]})
    updated = request("POST", f"/wp/v2/posts/{int(post_id)}", {"featured_media": media_id})
    if int(updated.get("featured_media") or 0) != media_id:
        raise RuntimeError("WordPress não confirmou a imagem destacada no post")
    return media_id


def set_aioseo(post_id, article):
    try:
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
        return True
    except Exception as exc:
        print("Aviso AIOSEO:", exc)
        return False


def validate_card_product_title(article):
    content = str(article.get("content_html") or "")
    product = html.escape(str(article.get("product") or "").strip())
    marker = f'class="{CTA_PRODUCT_TITLE_CLASS}"'
    if content.count(marker) != 2:
        raise RuntimeError("título original do produto ausente ou duplicado nos cards CTA")
    pattern = re.compile(
        rf'<p\s+class="{re.escape(CTA_PRODUCT_TITLE_CLASS)}"[^>]*>\s*{re.escape(product)}\s*</p>', re.I
    )
    if len(pattern.findall(content)) != 2:
        raise RuntimeError("título original do produto não está fiel nos dois cards CTA")
    if re.search(rf"<h[1-6][^>]*>[^<]*{re.escape(product)}", content, re.I):
        raise RuntimeError("título comercial do produto não pode ser heading editorial")


def history_ids(history):
    return {
        str(row.get("shopee_item_id") or "").strip()
        for row in (history.get("items") or [])
        if str(row.get("shopee_item_id") or "").strip()
    }


def count_publications_for_local_date(history, local_date):
    count = 0
    for row in history.get("items") or []:
        if str(row.get("source") or "") == "automatic_existing":
            continue
        raw = str(row.get("published_at") or "").strip()
        if not raw:
            continue
        try:
            stamp = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            if stamp.tzinfo is None:
                stamp = stamp.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        if stamp.astimezone(LOCAL_TZ).date() == local_date:
            count += 1
    return count


def publications_today(history):
    return count_publications_for_local_date(history, datetime.now(LOCAL_TZ).date())


def append_history(history, item, article, post_id, url, source="automatic_gate"):
    item_id = str(item.get("shopee_item_id") or "").strip()
    if item_id and item_id in history_ids(history):
        return
    history.setdefault("version", 2)
    history.setdefault("project", "Casa e Decoração")
    history.setdefault("items", []).append({
        "shopee_item_id": item_id,
        "product": str(item.get("product") or ""),
        "category": str(article.get("category") or item.get("category") or ""),
        "editorial_title": str(article.get("editorial_title") or article.get("seo_title") or ""),
        "wordpress_post_id": int(post_id),
        "wordpress_url": str(url or ""),
        "published_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source": source,
    })


def main():
    if not ENABLED:
        print("Publicação ao vivo desativada por CASA_LIVE_PUBLISH_ENABLED=false.")
        return
    if STATUS != "publish":
        raise RuntimeError("Trava de publicação: CASA_WORDPRESS_STATUS deve ser publish")
    credentials()

    doc = load(QUEUE, {})
    history = load(HISTORY, {"version": 2, "project": "Casa e Decoração", "items": []})
    rotation = load_state(ROTATION)
    used_today = publications_today(history)
    remaining_today = max(0, DAILY_CAP - used_today)
    effective_limit = min(LIMIT, remaining_today)
    if effective_limit <= 0:
        print(f"Limite diário atingido: {used_today}/{DAILY_CAP} publicações em America/Recife; nenhuma nova publicação.")
        return

    published = history_ids(history)
    done = 0

    while done < effective_limit:
        candidates = order_items(
            [item for item in (doc.get("items") or []) if item.get("status") == "GENERATED"],
            rotation,
            pending_only=True,
        )
        if not candidates:
            break
        item = candidates[0]
        item_id = str(item.get("shopee_item_id") or "").strip()
        if item_id and item_id in published:
            item["status"] = "PUBLISHED"
            item["last_error"] = ""
            continue

        article_path = GENERATED / f"{int(item['id']):03d}.json"
        article = load(article_path, {})
        gate = quality(article)
        if gate["status"] != "DRAFT_READY":
            item["status"] = "BLOCKED"
            item["last_error"] = "quality gate antes da publicação: " + ", ".join(gate.get("reasons") or [])
            continue

        try:
            category = str(article.get("category") or item.get("category") or "")
            if category not in rotation.get("pending_categories", []):
                raise RuntimeError("categoria já coberta no ciclo atual de rotação")
            validate_card_product_title(article)
            slug = slugify(article.get("topic") or article.get("seo_title"))
            old = existing(slug)
            if old:
                old_title = rendered_title(old)
                if old_title and old_title != str(article.get("seo_title") or "").strip():
                    raise RuntimeError("slug já pertence a outro artigo")
                if old.get("status") == "publish":
                    post_id = int(old["id"])
                    if not int(old.get("featured_media") or 0):
                        item["featured_media"] = upload_featured_image(post_id, article)
                    else:
                        item["featured_media"] = int(old.get("featured_media") or 0)
                    url = old.get("link")
                    append_history(history, item, article, post_id, url, source="automatic_existing")
                    item["wordpress_post_id"] = post_id
                    item["wordpress_url"] = url
                    item["status"] = "PUBLISHED"
                    item["last_error"] = ""
                    if item_id:
                        published.add(item_id)
                    continue

            payload = {
                "title": article["seo_title"],
                "slug": slug,
                "status": "draft",
                "categories": [category_id(category)],
                "excerpt": article["excerpt"],
                "content": article["content_html"],
            }
            result = request("POST", f"/wp/v2/posts/{int(old['id'])}" if old else "/wp/v2/posts", payload)
            post_id = int(result.get("id") or 0)
            if not post_id:
                raise RuntimeError("WordPress não confirmou criação do rascunho")

            media_id = upload_featured_image(post_id, article)
            result = request("POST", f"/wp/v2/posts/{post_id}", {"status": "publish", "featured_media": media_id})
            if result.get("status") != "publish" or int(result.get("featured_media") or 0) != media_id:
                raise RuntimeError("WordPress não confirmou publicação com imagem destacada")

            url = result.get("link")
            item["wordpress_post_id"] = post_id
            item["wordpress_url"] = url
            item["featured_media"] = media_id
            item["seo_synced"] = set_aioseo(post_id, article)
            item["status"] = "PUBLISHED"
            item["last_error"] = ""
            append_history(history, item, article, post_id, url)
            rotation = mark_published(rotation, category)
            if item_id:
                published.add(item_id)
            done += 1
        except Exception as exc:
            item["publication_attempts"] = int(item.get("publication_attempts") or 0) + 1
            item["last_error"] = str(exc)[:800]
            if item["publication_attempts"] >= 3:
                item["status"] = "PUBLISH_BLOCKED"

    save(QUEUE, doc)
    save(HISTORY, history)
    save_state(ROTATION, rotation)
    print(f"Publicações confirmadas nesta execução: {done} | hoje={used_today + done}/{DAILY_CAP} | ciclo={rotation.get('cycle')} | pendentes={rotation.get('pending_categories')}")


if __name__ == "__main__":
    main()
