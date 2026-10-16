import base64
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

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
            "User-Agent": "CasaEDecoracao-Publisher/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            raw = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:800]
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


def publish_article(article):
    cat_id = category_id(article["category"])
    payload = {
        "title": article["seo_title"],
        "slug": slugify(article["seo_title"]),
        "status": STATUS,
        "categories": [cat_id],
        "excerpt": article.get("excerpt") or article.get("meta_description") or "",
        "content": article["content_html"],
    }
    result = request("POST", "/wp/v2/posts", payload)
    return {
        "id": result.get("id"),
        "status": result.get("status"),
        "url": result.get("link"),
    }


def main():
    if STATUS not in {"draft", "publish", "pending", "private"}:
        raise RuntimeError("CASA_WORDPRESS_STATUS deve ser draft/publish/pending/private")
    queue = load_json(QUEUE_PATH, {})
    items = queue.get("items") or []
    candidates = [x for x in items if x.get("status") == "GENERATED"][:PUBLISH_LIMIT]
    if not candidates:
        print("Nenhum artigo GENERATED para publicar.")
        return
    index = {int(x["id"]): x for x in items}
    for item in candidates:
        item_id = int(item["id"])
        article_path = GENERATED_DIR / f"{item_id:03d}.json"
        article = load_json(article_path, {})
        if not article:
            index[item_id]["status"] = "QUARANTINE"
            index[item_id]["last_error"] = "arquivo gerado ausente"
            continue
        try:
            result = publish_article(article)
            article["wordpress"] = result
            article["status"] = "PUBLISHED" if result.get("status") == "publish" else "WORDPRESS_DRAFT"
            save_json(article_path, article)
            index[item_id]["status"] = article["status"]
            index[item_id]["wordpress"] = result
            print(f"WordPress {item_id}: {result}")
        except Exception as exc:
            index[item_id]["status"] = "QUARANTINE"
            index[item_id]["last_error"] = str(exc)[:500]
            print(f"QUARANTINE {item_id}: {exc}")
    queue["items"] = [index[int(x["id"])] for x in items]
    save_json(QUEUE_PATH, queue)


if __name__ == "__main__":
    main()
