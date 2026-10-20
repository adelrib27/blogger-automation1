import argparse
import hashlib
import html
import json
import os
import re
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

LAB_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = LAB_ROOT / "config" / "d1_state.json"
HISTORY_PATH = LAB_ROOT / "state" / "article_history.json"
SNAPSHOT_PATH = LAB_ROOT / "state" / "persistence_snapshot.json"
OUT_DIR = LAB_ROOT / "data" / "architecture_lab"
RANKING_PATH = LAB_ROOT / "data" / "shopee_oportunidades" / "ranking.json"


def now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path, default=None):
    path = Path(path)
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def cfg():
    doc = load_json(CONFIG_PATH, {}) or {}
    if not doc.get("database_id") or doc.get("persistence_enabled") is not True:
        raise SystemExit("D1 persistence config inválida")
    return doc


def creds():
    account = os.getenv("CLOUDFLARE_ACCOUNT_ID", "").strip()
    token = os.getenv("CLOUDFLARE_API_TOKEN", "").strip()
    if not account or not token:
        raise SystemExit("CLOUDFLARE_ACCOUNT_ID/CLOUDFLARE_API_TOKEN ausentes")
    return account, token


def d1(sql, params=None):
    account, token = creds()
    database_id = cfg()["database_id"]
    body = {"sql": sql}
    if params is not None:
        body["params"] = ["" if p is None else str(p) for p in params]
    req = urllib.request.Request(
        f"https://api.cloudflare.com/client/v4/accounts/{account}/d1/database/{database_id}/query",
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "VidaPetPratica-PersistenceLab/2.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as response:
            doc = json.loads(response.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:1800]
        raise RuntimeError(f"D1 HTTP {exc.code}: {detail}") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RuntimeError(f"D1 indisponível: {exc}") from exc
    if not doc.get("success"):
        raise RuntimeError("D1 query falhou: " + json.dumps(doc.get("errors") or doc, ensure_ascii=False)[:1800])
    for part in doc.get("result") or []:
        if not part.get("success", True):
            raise RuntimeError("D1 statement falhou: " + json.dumps(part, ensure_ascii=False)[:1800])
    return doc.get("result") or []


def rows(sql, params=None):
    result = d1(sql, params)
    return (result[0].get("results") or []) if result else []


def execute(sql, params=None):
    d1(sql, params)


def normalize(text):
    import unicodedata
    text = unicodedata.normalize("NFKD", str(text or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch)).lower()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", text)).strip()


def plain_html(raw):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", str(raw or "")))).strip()


def h(text):
    return hashlib.sha256(str(text or "").encode("utf-8")).hexdigest()


def angle_fp(angle):
    return h(normalize(angle))


def content_fp(content):
    return h(plain_html((content or {}).get("article_html") or ""))


def article_id(item_id, angle, content):
    return h(f"{item_id}|{angle_fp(angle)}|{content_fp(content)}")[:32]


def hydrate():
    data = rows(
        """
        SELECT a.article_id,a.item_id,a.angle,a.title,a.semantic_text,a.article_status,a.created_at,
               a.last_used_at,a.published_at,a.evidence_ids_json,
               p.product_name,p.category,p.keyword,p.evidence_status,p.evidence_checked_at,
               p.cooldown_until,p.source_payload_json
        FROM editorial_articles a
        JOIN editorial_products p ON p.item_id=a.item_id
        WHERE a.article_status NOT IN ('REJECTED','ARCHIVED')
        ORDER BY a.created_at,a.article_id
        """
    )
    history = []
    for row in data:
        try:
            source = json.loads(row.get("source_payload_json") or "{}")
        except Exception:
            source = {}
        try:
            evidence_ids = json.loads(row.get("evidence_ids_json") or "[]")
        except Exception:
            evidence_ids = []
        history.append({
            "articleId": row.get("article_id"),
            "itemId": row.get("item_id"),
            "productName": row.get("product_name"),
            "category": row.get("category"),
            "keyword": row.get("keyword"),
            "angle": row.get("angle"),
            "title": row.get("title"),
            "semanticText": row.get("semantic_text") or "",
            "articleStatus": row.get("article_status"),
            "evidenceStatus": row.get("evidence_status") or "",
            "evidenceCheckedAt": row.get("evidence_checked_at"),
            "authorizedEvidenceIds": evidence_ids,
            "createdAt": row.get("created_at"),
            "lastUsedAt": row.get("last_used_at"),
            "publishedAt": row.get("published_at"),
            "cooldownUntil": row.get("cooldown_until"),
            "sourcePayload": source,
        })
    save_json(HISTORY_PATH, history)
    snap = verify(write=False)
    snap["hydrated_history_rows"] = len(history)
    save_json(SNAPSHOT_PATH, snap)
    print(json.dumps({"status": "D1_HISTORY_HYDRATED", "rows": len(history), "ready": snap["ready_count"]}, ensure_ascii=False))


def find_source(item_id, ranking):
    for item in ranking:
        if str(item.get("itemId") or "") == str(item_id):
            return item
    found = rows("SELECT source_payload_json FROM editorial_products WHERE item_id=? LIMIT 1", [item_id])
    if found:
        try:
            return json.loads(found[0].get("source_payload_json") or "{}")
        except Exception:
            pass
    return {}


def upsert_product(item, package):
    item_id = str(item.get("itemId") or "")
    category = str((item.get("categories") or [""])[0] or "")
    keyword = str((item.get("intentMatchedKeywords") or item.get("keywords") or [""])[0] or "")
    now = now_iso()
    product_fingerprint = h(f"{item_id}|{item.get('productName') or ''}")
    execute(
        """
        INSERT INTO editorial_products(item_id,product_name,product_fingerprint,category,keyword,first_seen_at,last_seen_at,status,evidence_status,evidence_checked_at,source_payload_json)
        VALUES(?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(item_id) DO UPDATE SET product_name=excluded.product_name,product_fingerprint=excluded.product_fingerprint,
        category=excluded.category,keyword=excluded.keyword,last_seen_at=excluded.last_seen_at,status=excluded.status,
        evidence_status=excluded.evidence_status,evidence_checked_at=excluded.evidence_checked_at,source_payload_json=excluded.source_payload_json
        """,
        [item_id,item.get("productName") or "",product_fingerprint,category,keyword,now,now,"KNOWN",package.get("status") or "VERIFIED",package.get("verified_at") or now,json.dumps(item,ensure_ascii=False,separators=(",", ":"))],
    )


def upsert_evidence(item_id, package):
    checked = str(package.get("verified_at") or now_iso())
    for src in package.get("sources") or []:
        eid = str(src.get("evidence_id") or "")
        if not eid:
            continue
        execute(
            """
            INSERT INTO editorial_evidence(evidence_id,item_id,identity_level,allowed_in_article,source_url,source_title,source_type,claim_text,checked_at,payload_json)
            VALUES(?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(evidence_id) DO UPDATE SET item_id=excluded.item_id,identity_level=excluded.identity_level,
            allowed_in_article=excluded.allowed_in_article,source_url=excluded.source_url,source_title=excluded.source_title,
            source_type=excluded.source_type,claim_text=excluded.claim_text,checked_at=excluded.checked_at,payload_json=excluded.payload_json
            """,
            [eid,item_id,src.get("identity_level") or "UNKNOWN",1 if src.get("allowed_in_article") else 0,src.get("source_url") or "",src.get("source_title") or src.get("title") or "",src.get("source_domain") or "",src.get("support_text") or "",checked,json.dumps(src,ensure_ascii=False,separators=(",", ":"))],
        )


def persist():
    ranking_doc = load_json(RANKING_PATH, {}) or {}
    ranking = ranking_doc.get("ranking") or []
    post_dir = OUT_DIR / "posts"
    files = sorted(post_dir.glob("*.json")) if post_dir.exists() else []
    persisted = []
    for path in files:
        post = load_json(path, {}) or {}
        if post.get("status") != "VERIFIED_READY":
            continue
        item_id = str(post.get("itemId") or "")
        package = load_json(OUT_DIR / "evidence" / f"{item_id}.json", {}) or {}
        source = find_source(item_id, ranking)
        if not source or package.get("status") != "VERIFIED":
            raise RuntimeError(f"Persistência bloqueada para {item_id}: source/evidence inválido")
        upsert_product(source, package)
        upsert_evidence(item_id, package)
        content = post.get("content") or {}
        a_fp = angle_fp(post.get("angle") or "")
        c_fp = content_fp(content)
        aid = article_id(item_id, post.get("angle") or "", content)
        semantic = f"{content.get('title') or ''} {plain_html(content.get('article_html') or '')}".strip()
        gate = post.get("gate") or {}
        execute(
            """
            INSERT INTO editorial_articles(article_id,item_id,angle,angle_fingerprint,title,focus_keyword,content_fingerprint,evidence_ids_json,
            source_identity_status,article_status,provider,model,gate_version,builder_version,created_at,last_used_at,reject_reason,word_count,h2_count,similarity_max,content_json,semantic_text)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(item_id,angle_fingerprint) DO UPDATE SET title=excluded.title,focus_keyword=excluded.focus_keyword,
            content_fingerprint=excluded.content_fingerprint,evidence_ids_json=excluded.evidence_ids_json,source_identity_status=excluded.source_identity_status,
            article_status=excluded.article_status,last_used_at=excluded.last_used_at,word_count=excluded.word_count,h2_count=excluded.h2_count,
            similarity_max=excluded.similarity_max,content_json=excluded.content_json,semantic_text=excluded.semantic_text
            """,
            [aid,item_id,post.get("angle") or "",a_fp,content.get("title") or "",content.get("focus_keyword") or post.get("keyword") or "",c_fp,json.dumps(package.get("authorized_evidence_ids") or [],ensure_ascii=False,separators=(",", ":")),package.get("status") or "VERIFIED","VERIFIED_READY","groq",os.getenv("VIDAPET_GROQ_MODEL","openai/gpt-oss-120b"),gate.get("editorial_sanitizer") or "SAFE_V5_CATEGORY_AWARE","SAFE_V5_CATEGORY_AWARE",now_iso(),now_iso(),"",gate.get("word_count") or 0,gate.get("h2_count") or 0,gate.get("session_duplicate_guard") or 0.62,json.dumps(content,ensure_ascii=False,separators=(",", ":")),semantic],
        )
        actual = rows("SELECT article_id FROM editorial_articles WHERE item_id=? AND angle_fingerprint=? LIMIT 1", [item_id,a_fp])
        actual_id = actual[0]["article_id"] if actual else aid
        execute("INSERT INTO ready_queue(article_id,item_id,status,priority,queued_at) VALUES(?,?,?,?,?) ON CONFLICT(article_id) DO UPDATE SET status='READY',priority=excluded.priority,consumed_at=NULL", [actual_id,item_id,"READY",100,now_iso()])
        persisted.append(actual_id)
    if not persisted:
        raise SystemExit("Nenhum VERIFIED_READY desta execução para persistir")
    print(json.dumps({"status":"CURRENT_RUN_PERSISTED","articles":len(persisted),"article_ids":persisted},ensure_ascii=False))


def consume_ready_lab():
    execute("UPDATE ready_queue SET status='LAB_CONSUMED',consumed_at=? WHERE status='READY'", [now_iso()])
    print(json.dumps({"status":"READY_MARKED_LAB_CONSUMED"},ensure_ascii=False))


def verify(write=True):
    counts = {}
    for table in ["editorial_products","editorial_evidence","editorial_articles","ready_queue","automation_runs"]:
        result = rows(f"SELECT COUNT(*) AS c FROM {table}")
        counts[table] = int((result or [{"c":0}])[0].get("c") or 0)
    r = rows("SELECT COUNT(*) AS c FROM ready_queue WHERE status='READY'")
    migrations = rows("SELECT version,applied_at FROM schema_migrations ORDER BY applied_at,version")
    doc = {"status":"D1_PERSISTENCE_OK","database":cfg().get("name"),"database_id":cfg().get("database_id"),"counts":counts,"ready_count":int((r or [{"c":0}])[0].get("c") or 0),"migrations":migrations,"wordpress_written":False}
    if write:
        save_json(SNAPSHOT_PATH, doc)
    print(json.dumps(doc,ensure_ascii=False,indent=2))
    return doc


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["hydrate","persist","consume-ready-lab","verify"])
    args = parser.parse_args()
    {"hydrate":hydrate,"persist":persist,"consume-ready-lab":consume_ready_lab,"verify":verify}[args.command]()


if __name__ == "__main__":
    main()
