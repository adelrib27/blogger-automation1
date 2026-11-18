"""Catálogo local fail-closed. Nenhuma rede/publicação ocorre neste módulo."""
from __future__ import annotations

import csv
import hashlib
import json
import re
import sqlite3
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from .taxonomy import classify_title


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def normalized(value: str) -> str:
    value = unicodedata.normalize("NFKD", str(value or ""))
    return re.sub(r"[^a-z0-9]", "", "".join(c for c in value if not unicodedata.combining(c)).lower())


FIELDS = {
    "title": ("productName", "product_name", "title", "nome", "nomeProduto", "itemName"),
    "description": ("productDescription", "description", "descricao", "descricaoProduto"),
    "url": ("productLink", "productUrl", "product_link", "product_url", "itemUrl", "itemLink", "originUrl", "url", "linkProduto"),
    "image": ("imageUrl", "imageLink", "image", "productImage", "image_url", "imagem", "imagemUrl"),
    "item": ("itemId", "item_id", "productId", "product_id", "idProduto"),
    "shop": ("shopId", "shop_id", "sellerId", "seller_id", "idLoja"),
    "affiliate": ("affiliateLink", "affiliate_link", "shortLink", "short_link", "linkAfiliado", "link_afiliado", "offerLink"),
}
ALIASES = {key: [normalized(x) for x in values] for key, values in FIELDS.items()}
RISK_TERMS = (
    "medicamento", "remedio", "anabolizante", "esteroide", "suplemento", "creatina", "hormonal",
    "veneno", "pesticida", "arma de fogo", "municao", "explosivo", "narguile", "cigarro",
    "vape", "nicotina", "cannabis", "maconha", "falsificado", "replica de marca",
)


def host_allowed(url: str, *, allow_short: bool = False) -> bool:
    try:
        u = urlsplit(url.strip())
        if u.scheme != "https" or u.username or u.password or u.port not in (None, 443):
            return False
        host = (u.hostname or "").lower().rstrip(".")
        if host in {"shope.ee", "s.shopee.com.br"}:
            return allow_short
        return host == "shopee.com.br" or host.endswith(".shopee.com.br")
    except (ValueError, AttributeError):
        return False


def fields(row: dict[str, str]) -> dict[str, str]:
    norm = {normalized(k): str(v or "").strip() for k, v in row.items() if k is not None}
    return {field: next((norm[a] for a in aliases if norm.get(a)), "") for field, aliases in ALIASES.items()}


def ids_from_url(url: str) -> tuple[str, str]:
    try:
        u = urlsplit(url)
        match = re.search(r"(?:-i\.|/product/|/opaanlp/)(\d+)[./](\d+)(?:\b|/|$)", u.path, flags=re.I)
        if match:
            return match.group(1), match.group(2)
        q = {k.lower(): v for k, v in parse_qs(u.query).items()}
        return (q.get("shopid") or [""])[0], (q.get("itemid") or [""])[0]
    except ValueError:
        return "", ""


def classify(data: dict[str, str]) -> tuple[str, str, str]:
    url = data["url"]
    shop, item = data["shop"], data["item"]
    if not shop or not item:
        a, b = ids_from_url(url)
        shop, item = shop or a, item or b
    if shop and item and shop.isdigit() and item.isdigit():
        key = f"shopee:{shop}:{item}"
    elif host_allowed(url):
        u = urlsplit(url)
        # Produto sem ID: deduplicar por URL completa, sem usar somente título.
        key = "url:" + hashlib.sha256((u.netloc + u.path + "?" + u.query).encode()).hexdigest()
    else:
        key = "unresolved:" + hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    title = normalized(data["title"] + " " + data["description"])
    risky = [term for term in RISK_TERMS if normalized(term) in title]
    reasons = []
    if risky:
        reasons.append("categoria_sensivel")
    if not (data["title"] and host_allowed(url) and data["image"].startswith("https://")):
        reasons.append("dados_incompletos_ou_url_invalida")
    return key, ("review" if reasons else "eligible"), ",".join(reasons)


class Catalog:
    def __init__(self, path: Path | str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.path)
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS products (
            product_key TEXT PRIMARY KEY,
            shop_id TEXT NOT NULL DEFAULT '', item_id TEXT NOT NULL DEFAULT '',
            title TEXT NOT NULL, description TEXT NOT NULL, origin_url TEXT NOT NULL,
            image_url TEXT NOT NULL, moderation TEXT NOT NULL, moderation_reason TEXT NOT NULL,
            first_source TEXT NOT NULL, last_seen_utc TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS product_taxonomy (
            product_key TEXT PRIMARY KEY,
            category TEXT NOT NULL, niche TEXT NOT NULL,
            status TEXT NOT NULL, reason TEXT NOT NULL, version TEXT NOT NULL,
            FOREIGN KEY (product_key) REFERENCES products(product_key)
        );
        CREATE INDEX IF NOT EXISTS idx_product_taxonomy_route
          ON product_taxonomy(status,category,niche);
        CREATE TABLE IF NOT EXISTS affiliate_links (
            product_key TEXT NOT NULL, campaign TEXT NOT NULL, affiliate_url TEXT NOT NULL,
            verified_origin TEXT NOT NULL, updated_utc TEXT NOT NULL,
            PRIMARY KEY (product_key, campaign),
            FOREIGN KEY (product_key) REFERENCES products(product_key)
        );
        CREATE INDEX IF NOT EXISTS idx_products_moderation ON products(moderation);
        """)
        self.db.commit()

    def close(self):
        self.db.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def import_csv(self, path: Path | str, source: str, *, max_rows: int = 200_000) -> dict[str, int]:
        if not re.fullmatch(r"[a-zA-Z0-9_-]{1,40}", source):
            raise ValueError("Identificador de origem inválido")
        count = {"rows": 0, "added": 0, "duplicates": 0, "review": 0, "eligible": 0,
                 "taxonomy_matched": 0, "taxonomy_review": 0}
        # Com open strict: não importa feed truncado/encoding inválido.
        with Path(path).open("r", encoding="utf-8-sig", newline="") as stream:
            sample = stream.read(8192)
            stream.seek(0)
            try:
                dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
            except csv.Error:
                dialect = csv.excel
            reader=csv.DictReader(stream, delimiter=dialect.delimiter, quotechar='"', doublequote=True, strict=True)
            if not reader.fieldnames or not any(normalized(c) in ALIASES["title"] for c in reader.fieldnames):
                raise ValueError("CSV sem coluna reconhecida de título")
            if not any(normalized(c) in ALIASES["url"] for c in reader.fieldnames):
                raise ValueError("CSV sem coluna reconhecida de URL do produto")
            with self.db:
                for raw in reader:
                    if count["rows"] >= max_rows:
                        raise ValueError("CSV excede limite de linhas configurado")
                    if None in raw or any(v is None for v in raw.values()):
                        raise ValueError(f"CSV com quantidade incorreta de colunas na linha {count['rows'] + 2}")
                    count["rows"] += 1
                    data = fields(raw)
                    key, moderation, reason = classify(data)
                    route = classify_title(data["title"])
                    count["taxonomy_matched" if route.status == "matched" else "taxonomy_review"] += 1
                    if route.status != "matched":
                        moderation = "review"
                        reason = ",".join(filter(None, (reason, "taxonomy_" + route.reason)))
                    count[moderation] += 1
                    seen = self.db.execute("SELECT 1 FROM products WHERE product_key=?", (key,)).fetchone()
                    if seen:
                        count["duplicates"] += 1
                    else:
                        count["added"] += 1
                    shop, item = data["shop"], data["item"]
                    if not shop or not item:
                        a, b = ids_from_url(data["url"])
                        shop, item = shop or a, item or b
                    self.db.execute("""
                        INSERT INTO products
                        (product_key,shop_id,item_id,title,description,origin_url,image_url,moderation,moderation_reason,first_source,last_seen_utc)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?)
                        ON CONFLICT(product_key) DO UPDATE SET
                          title=CASE WHEN length(excluded.title)>length(products.title) THEN excluded.title ELSE products.title END,
                          description=CASE WHEN length(excluded.description)>length(products.description) THEN excluded.description ELSE products.description END,
                          origin_url=CASE WHEN products.origin_url='' THEN excluded.origin_url ELSE products.origin_url END,
                          image_url=CASE WHEN products.image_url='' THEN excluded.image_url ELSE products.image_url END,
                          moderation=CASE WHEN excluded.moderation='review' OR products.moderation='review' THEN 'review' ELSE 'eligible' END,
                          moderation_reason=CASE WHEN excluded.moderation='review' THEN excluded.moderation_reason ELSE products.moderation_reason END,
                          last_seen_utc=excluded.last_seen_utc
                        """, (key, shop, item, data["title"], data["description"], data["url"],
                              data["image"], moderation, reason, source, utc_now()))
                    self.db.execute("""
                        INSERT INTO product_taxonomy(product_key,category,niche,status,reason,version)
                        VALUES (?,?,?,?,?,?)
                        ON CONFLICT(product_key) DO UPDATE SET
                          category=CASE WHEN product_taxonomy.status='matched'
                            AND excluded.status='matched'
                            AND product_taxonomy.category=excluded.category
                            AND product_taxonomy.niche=excluded.niche
                            THEN excluded.category ELSE '' END,
                          niche=CASE WHEN product_taxonomy.status='matched'
                            AND excluded.status='matched'
                            AND product_taxonomy.category=excluded.category
                            AND product_taxonomy.niche=excluded.niche
                            THEN excluded.niche ELSE '' END,
                          status=CASE WHEN product_taxonomy.status='matched'
                            AND excluded.status='matched'
                            AND product_taxonomy.category=excluded.category
                            AND product_taxonomy.niche=excluded.niche
                            THEN 'matched' ELSE 'review' END,
                          reason=CASE WHEN product_taxonomy.status='matched'
                            AND excluded.status='matched'
                            AND product_taxonomy.category=excluded.category
                            AND product_taxonomy.niche=excluded.niche
                            THEN excluded.reason ELSE 'conflicting_or_unclassified_reimport' END,
                          version=excluded.version
                    """, (key, route.category, route.niche, route.status, route.reason, route.version))
        return count

    def stats(self) -> dict:
        total = self.db.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        eligible = self.db.execute("""SELECT COUNT(*) FROM products p
            JOIN product_taxonomy t ON t.product_key=p.product_key
            WHERE p.moderation='eligible' AND t.status='matched'""").fetchone()[0]
        links = self.db.execute("SELECT COUNT(*) FROM affiliate_links").fetchone()[0]
        return {"products": total, "eligible": eligible, "review": total - eligible, "cached_affiliate_links": links}

    def categories(self) -> list[dict]:
        rows = self.db.execute("""SELECT t.category,t.niche,COUNT(*) FROM products p
            JOIN product_taxonomy t ON t.product_key=p.product_key
            WHERE p.moderation='eligible' AND t.status='matched'
            GROUP BY t.category,t.niche ORDER BY t.category,t.niche""").fetchall()
        return [{"category": cat, "niche": niche, "products": count} for cat, niche, count in rows]

    def for_conversion(self, key: str) -> tuple[str, str, str] | None:
        # Fonte protegida ou conflitante nunca chega à mutação Shopee.
        # Links já gravados são preservados; não se transfere campanha.
        from .source_policy_gate import source_safe_for_use
        if not source_safe_for_use(self,key):
            return None
        row = self.db.execute("""SELECT p.origin_url,t.category,t.niche
            FROM products p JOIN product_taxonomy t ON t.product_key=p.product_key
            WHERE p.product_key=? AND p.moderation='eligible' AND t.status='matched'""", (key,)).fetchone()
        return tuple(row) if row else None

    def reclassify_missing(self) -> int:
        """Rotula produtos herdados sem taxonomia. Não libera registros já reprovados."""
        rows = self.db.execute("""SELECT p.product_key,p.title
            FROM products p LEFT JOIN product_taxonomy t ON t.product_key=p.product_key
            WHERE t.product_key IS NULL""").fetchall()
        with self.db:
            for key, title in rows:
                route = classify_title(title)
                self.db.execute("""INSERT OR IGNORE INTO product_taxonomy
                    (product_key,category,niche,status,reason,version)
                    VALUES (?,?,?,?,?,?)""",
                    (key, route.category, route.niche, route.status, route.reason, route.version))
                if route.status != "matched":
                    self.db.execute("""UPDATE products SET moderation='review',
                        moderation_reason=CASE WHEN moderation_reason=''
                          THEN ? ELSE moderation_reason || ',' || ? END
                        WHERE product_key=?""", ("taxonomy_"+route.reason,"taxonomy_"+route.reason,key))
        return len(rows)

    def cache_link(self, key: str, campaign: str, url: str, *, origin: str = "shopee_api") -> bool:
        if not re.fullmatch(r"[a-z0-9_-]{1,32}", campaign):
            raise ValueError("Campanha inválida")
        if origin not in {"shopee_api", "verified_legacy"}:
            raise ValueError("Proveniência inválida")
        if not host_allowed(url, allow_short=True):
            raise ValueError("Link de afiliado deve ser HTTPS do domínio Shopee")
        if not self.for_conversion(key):
            raise ValueError("Produto ausente ou ainda não aprovado para conversão")
        with self.db:
            result = self.db.execute("""INSERT OR IGNORE INTO affiliate_links
                (product_key,campaign,affiliate_url,verified_origin,updated_utc)
                VALUES(?,?,?,?,?)""", (key, campaign, url, origin, utc_now()))
        return result.rowcount > 0

    def cached_link(self, key: str, campaign: str) -> str | None:
        row = self.db.execute("SELECT affiliate_url FROM affiliate_links WHERE product_key=? AND campaign=?", (key, campaign)).fetchone()
        return row[0] if row else None

    def _safe_catalog_rows(self, cursor, limit: int) -> list[tuple]:
        """Filtra fontes antes do limite; nenhum acesso remoto ou escrita.

        A filtragem tardia com SQL LIMIT perderia candidatos corretos caso
        os primeiros SKUs estivessem bloqueados por categoria de origem.
        """
        from .source_policy_gate import source_safe_for_use
        selected = []
        for row in cursor:
            key, _title, origin, image = row[:4]
            if not host_allowed(origin) or not str(image).startswith("https://"):
                continue
            if not source_safe_for_use(self, key):
                continue
            selected.append(tuple(row))
            if len(selected) >= limit:
                break
        return selected

    def candidates(self, campaign: str, limit: int = 20, *, category: str | None = None,
                   niche: str | None = None):
        if not re.fullmatch(r"[a-z0-9_-]{1,32}", campaign):
            raise ValueError("Campanha inválida")
        if not 1 <= limit <= 100:
            raise ValueError("Limite inválido")
        for term in (category, niche):
            if term is not None and not re.fullmatch(r"[a-z0-9_]{2,50}", term):
                raise ValueError("Categoria ou nicho inválido")
        clauses = ["p.moderation='eligible'", "t.status='matched'", "l.product_key IS NULL"]
        params = [campaign]
        if category is not None:
            clauses.append("t.category=?")
            params.append(category)
        if niche is not None:
            clauses.append("t.niche=?")
            params.append(niche)
        cursor = self.db.execute("""SELECT p.product_key,p.title,p.origin_url,p.image_url
            FROM products p JOIN product_taxonomy t ON t.product_key=p.product_key
            LEFT JOIN affiliate_links l ON l.product_key=p.product_key AND l.campaign=?
            WHERE """ + " AND ".join(clauses) + " ORDER BY p.product_key", params)
        return self._safe_catalog_rows(cursor,limit)

    def select_products(self, campaign: str, limit: int = 20, *, category: str | None = None,
                        niche: str | None = None):
        """Catálogo editorial inclui convertidos E não convertidos.

        Devolve indicador de cache (0/1), nunca o URL afiliado comercial.
        É diferente de candidates(), que atende apenas a fila de conversão.
        """
        if not re.fullmatch(r"[a-z0-9_-]{1,32}", campaign):
            raise ValueError("Campanha inválida")
        if not 1 <= limit <= 100:
            raise ValueError("Limite inválido")
        for term in (category, niche):
            if term is not None and not re.fullmatch(r"[a-z0-9_]{2,50}", term):
                raise ValueError("Categoria ou nicho inválido")
        clauses = ["p.moderation='eligible'", "t.status='matched'"]
        params = [campaign]
        if category is not None:
            clauses.append("t.category=?")
            params.append(category)
        if niche is not None:
            clauses.append("t.niche=?")
            params.append(niche)
        cursor = self.db.execute("""SELECT p.product_key,p.title,p.origin_url,p.image_url,
              CASE WHEN l.product_key IS NULL THEN 0 ELSE 1 END AS has_cached
            FROM products p JOIN product_taxonomy t ON t.product_key=p.product_key
            LEFT JOIN affiliate_links l ON l.product_key=p.product_key AND l.campaign=?
            WHERE """ + " AND ".join(clauses) +
            " ORDER BY has_cached DESC,p.product_key", params)
        return self._safe_catalog_rows(cursor,limit)

    def select_by_source_path(self, campaign: str, level1: str,
                              level2: str, *, limit: int = 20):
        """Novos nichos por categoria OFICIAL, mas só itens já aprovados.

        Rota L1/L2 é descoberta na hora, não adicionada à taxonomia fixa.
        Outros bloqueios (categorias sensíveis ou origem conflitante) nunca
        são ignorados e o link de outra campanha não fica disponível.
        """
        from .taxonomy import normalize
        if not re.fullmatch(r"[a-z0-9_-]{1,32}",campaign):
            raise ValueError("Campanha inválida")
        if not 1<=limit<=100:
            raise ValueError("Limite inválido")
        for path in (level1,level2):
            if (not isinstance(path,str) or len(path)>120 or
                not re.fullmatch(r"[a-z0-9][a-z0-9 ]{0,119}",path) or
                normalize(path)!=path):
                raise ValueError("Categoria oficial inválida")
        exists=self.db.execute("""
          SELECT 1 FROM sqlite_master WHERE type='table'
          AND name='product_source_categories'
        """).fetchone()
        if not exists:
            return []
        cursor=self.db.execute("""
          SELECT p.product_key,p.title,p.origin_url,p.image_url,
            CASE WHEN l.product_key IS NULL THEN 0 ELSE 1 END AS has_cached
          FROM products p
          JOIN product_taxonomy t ON t.product_key=p.product_key
          LEFT JOIN affiliate_links l
            ON l.product_key=p.product_key AND l.campaign=?
          WHERE p.moderation='eligible' AND t.status='matched'
            AND EXISTS (
              SELECT 1 FROM product_source_categories s
              WHERE s.product_key=p.product_key AND s.status='matched'
                AND s.level1=? AND s.level2=?
            )
          ORDER BY has_cached DESC,p.product_key
        """,(campaign,level1,level2))
        return self._safe_catalog_rows(cursor,limit)

    def integrity(self) -> bool:
        return self.db.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
