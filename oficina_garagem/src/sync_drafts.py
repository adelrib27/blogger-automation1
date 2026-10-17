import base64
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from quality_gate import quality

ROOT = Path(__file__).resolve().parents[2]
QUEUE = ROOT / "oficina_garagem" / "data" / "editorial_queue.json"
GENERATED = ROOT / "oficina_garagem" / "data" / "generated"
WP_URL = "https://oficina.radartechbr.com.br"
ENABLED = os.getenv("OFICINA_DRAFT_SYNC_ENABLED", "false").strip().lower() in {"1","true","yes","on"}
LIMIT = max(1, min(int(os.getenv("OFICINA_DRAFT_SYNC_LIMIT", "2")), 10))
CATEGORY_SLUGS = {"Ferramentas":"ferramentas","Manutenção":"manutencao","Acessórios Automotivos":"acessorios-automotivos","Organização de Garagem":"organizacao-de-garagem","Limpeza e Conservação":"limpeza-e-conservacao","Segurança e Proteção":"seguranca-e-protecao"}


def load(path, default):
    try: return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError): return default


def save(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")


def credentials():
    user = os.getenv("OFICINA_WORDPRESS_USERNAME", "").strip()
    password = os.getenv("OFICINA_WORDPRESS_APP_PASSWORD", "").strip()
    if not user or not password: raise RuntimeError("Credenciais WordPress Oficina ausentes")
    return user, password


def request(method, path, payload=None):
    user, password = credentials()
    auth = base64.b64encode(f"{user}:{password}".encode()).decode()
    data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode()
    req = urllib.request.Request(WP_URL+"/wp-json"+path, data=data, method=method, headers={"Authorization":f"Basic {auth}","Content-Type":"application/json","Accept":"application/json","User-Agent":"OficinaGaragem-DraftSync/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=60) as response: raw = response.read().decode("utf-8","replace")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8","replace")[:800]
        raise RuntimeError(f"WordPress HTTP {exc.code}: {detail}") from exc
    return json.loads(raw) if raw else {}


def slugify(value):
    value = str(value or "").casefold().translate(str.maketrans("áàâãéêíóôõúç", "aaaaeeiooouc"))
    return re.sub(r"[^a-z0-9]+", "-", value).strip("-")[:78].rstrip("-")


def category_id(name):
    slug = CATEGORY_SLUGS[name]
    rows = request("GET", "/wp/v2/categories?slug="+urllib.parse.quote(slug))
    if not isinstance(rows, list) or not rows: raise RuntimeError("Categoria ausente no WordPress: "+name)
    return int(rows[0]["id"])


def existing(slug):
    rows = request("GET", "/wp/v2/posts?context=edit&status=draft,pending,private,publish&per_page=5&slug="+urllib.parse.quote(slug))
    return rows[0] if isinstance(rows,list) and rows else None


def set_aioseo(post_id, article):
    try:
        request("POST", "/aioseo/v1/post", {"id":int(post_id),"title":article["seo_title"],"description":article["meta_description"]})
        request("POST", f"/aioseo/v1/truseo/posts/{int(post_id)}", {"focus_keyword":article["focus_keyword"],"additional_keywords":[],"truseo_locale":"pt_BR"})
        return True
    except Exception as exc:
        print("Aviso AIOSEO:", exc)
        return False


def main():
    if not ENABLED:
        print("Sincronização WordPress desativada; nenhum write externo realizado.")
        return
    doc = load(QUEUE,{})
    done = 0
    for item in doc.get("items") or []:
        if done >= LIMIT: break
        if item.get("status") not in {"GENERATED","HUMAN_REVIEW"}: continue
        article_path = GENERATED / f"{int(item['id']):03d}.json"
        article = load(article_path,{})
        gate = quality(article)
        if gate["status"] == "REJECTED":
            item["status"]="BLOCKED"; item["last_error"]="quality gate antes do WordPress: "+", ".join(gate["reasons"]); continue
        slug = slugify(article.get("topic") or article.get("seo_title"))
        payload = {"title":article["seo_title"],"slug":slug,"status":"draft","categories":[category_id(article["category"])],"excerpt":article["excerpt"],"content":article["content_html"]}
        old = existing(slug)
        result = request("POST", f"/wp/v2/posts/{int(old['id'])}" if old else "/wp/v2/posts", payload)
        post_id = int(result.get("id") or 0)
        if not post_id: raise RuntimeError("WordPress não retornou post ID")
        item["wordpress_post_id"] = post_id
        item["wordpress_url"] = result.get("link")
        item["seo_synced"] = set_aioseo(post_id, article)
        item["status"] = "WORDPRESS_DRAFT_HUMAN_REVIEW" if gate["status"] == "HUMAN_REVIEW_REQUIRED" else "WORDPRESS_DRAFT"
        item["last_error"] = ""
        done += 1
    save(QUEUE,doc)
    print(f"Rascunhos sincronizados: {done}. Publicação ao vivo não existe neste script.")


if __name__ == "__main__": main()
