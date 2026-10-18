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

from cta_context import CTA_PRODUCT_TITLE_CLASS
from quality_gate import quality

ROOT = Path(__file__).resolve().parents[2]
QUEUE = ROOT / "oficina_garagem" / "data" / "editorial_queue.json"
GENERATED = ROOT / "oficina_garagem" / "data" / "generated"
HISTORY = ROOT / "oficina_garagem" / "data" / "publication_history.json"
WP_URL = "https://oficina.radartechbr.com.br"
ENABLED = os.getenv("OFICINA_LIVE_PUBLISH_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}
LIMIT = max(1, min(int(os.getenv("OFICINA_PUBLISH_LIMIT", "1")), 2))
STATUS = os.getenv("OFICINA_WORDPRESS_STATUS", "draft").strip().lower()
CATEGORY_SLUGS = {
    "Ferramentas": "ferramentas",
    "Manutenção": "manutencao",
    "Acessórios Automotivos": "acessorios-automotivos",
    "Organização de Garagem": "organizacao-de-garagem",
    "Limpeza e Conservação": "limpeza-e-conservacao",
    "Segurança e Proteção": "seguranca-e-protecao",
}


def load(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def credentials():
    user = os.getenv("OFICINA_WORDPRESS_USERNAME", "").strip()
    password = os.getenv("OFICINA_WORDPRESS_APP_PASSWORD", "").strip()
    if not user or not password:
        raise RuntimeError("Credenciais WordPress Oficina ausentes")
    return user, password


def request(method, path, payload=None):
    user, password = credentials()
    auth = base64.b64encode(f"{user}:{password}".encode()).decode()
    data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode()
    req = urllib.request.Request(
        WP_URL + "/wp-json" + path,
        data=data,
        method=method,
        headers={
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "OficinaGaragem-AutonomousPublisher/1.0",
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
    slug = CATEGORY_SLUGS[name]
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


def set_aioseo(post_id, article):
    try:
        request(
            "POST",
            "/aioseo/v1/post",
            {"id": int(post_id), "title": article["seo_title"], "description": article["meta_description"]},
        )
        request(
            "POST",
            f"/aioseo/v1/truseo/posts/{int(post_id)}",
            {"focus_keyword": article["focus_keyword"], "additional_keywords": [], "truseo_locale": "pt_BR"},
        )
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
        rf'<p\s+class="{re.escape(CTA_PRODUCT_TITLE_CLASS)}"[^>]*>\s*{re.escape(product)}\s*</p>',
        re.I,
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


def append_history(history, item, article, post_id, url, source="automatic_gate"):
    if str(item.get("shopee_item_id") or "") in history_ids(history):
        return
    history.setdefault("version", 1)
    history.setdefault("project", "Oficina & Garagem")
    history.setdefault("items", []).append(
        {
            "shopee_item_id": str(item.get("shopee_item_id") or ""),
            "product": str(item.get("product") or ""),
            "editorial_title": str(article.get("editorial_title") or article.get("seo_title") or ""),
            "wordpress_post_id": int(post_id),
            "wordpress_url": str(url or ""),
            "published_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "source": source,
        }
    )


def main():
    if not ENABLED:
        print("Publicação ao vivo desativada por OFICINA_LIVE_PUBLISH_ENABLED=false.")
        return
    if STATUS != "publish":
        raise RuntimeError("Trava de publicação: OFICINA_WORDPRESS_STATUS deve ser publish")
    credentials()
    doc = load(QUEUE, {})
    history = load(HISTORY, {"version": 1, "project": "Oficina & Garagem", "items": []})
    published = history_ids(history)
    done = 0

    for item in doc.get("items") or []:
        if done >= LIMIT:
            break
        if item.get("status") != "GENERATED":
            continue
        item_id = str(item.get("shopee_item_id") or "").strip()
        if item_id and item_id in published:
            item["status"] = "PUBLISHED"
            item["last_error"] = ""
            continue

        article_path = GENERATED / f"{int(item['id']):03d}.json"
        article = load(article_path, {})
        gate = quality(article)
        if gate["status"] == "HUMAN_REVIEW_REQUIRED":
            item["status"] = "HUMAN_REVIEW"
            item["last_error"] = "revisão humana obrigatória antes de publicação"
            continue
        if gate["status"] != "DRAFT_READY":
            item["status"] = "BLOCKED"
            item["last_error"] = "quality gate antes da publicação: " + ", ".join(gate.get("reasons") or [])
            continue

        try:
            validate_card_product_title(article)
            slug = slugify(article.get("topic") or article.get("seo_title"))
            old = existing(slug)
            if old and old.get("status") == "publish":
                old_title = html.unescape(re.sub(r"<[^>]+>", "", str((old.get("title") or {}).get("rendered") or ""))).strip()
                if old_title and old_title != str(article.get("seo_title") or "").strip():
                    raise RuntimeError("slug já pertence a outro artigo publicado")
                post_id = int(old["id"])
                url = old.get("link")
                append_history(history, item, article, post_id, url, source="automatic_existing")
                item["wordpress_post_id"] = post_id
                item["wordpress_url"] = url
                item["status"] = "PUBLISHED"
                item["last_error"] = ""
                published.add(item_id)
                continue

            payload = {
                "title": article["seo_title"],
                "slug": slug,
                "status": "publish",
                "categories": [category_id(article["category"])],
                "excerpt": article["excerpt"],
                "content": article["content_html"],
            }
            result = request("POST", f"/wp/v2/posts/{int(old['id'])}" if old else "/wp/v2/posts", payload)
            post_id = int(result.get("id") or 0)
            if not post_id or result.get("status") != "publish":
                raise RuntimeError("WordPress não confirmou publicação")
            url = result.get("link")
            item["wordpress_post_id"] = post_id
            item["wordpress_url"] = url
            item["seo_synced"] = set_aioseo(post_id, article)
            item["status"] = "PUBLISHED"
            item["last_error"] = ""
            append_history(history, item, article, post_id, url)
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
    print(f"Publicações confirmadas nesta execução: {done}")


if __name__ == "__main__":
    main()
