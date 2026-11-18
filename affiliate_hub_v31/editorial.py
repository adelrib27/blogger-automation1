"""V31 C2.2 — Planejamento editorial com originalidade de assunto e título.

O mesmo produto pode sustentar vários artigos com intenções distintas.
A duplicação comercial de produtos NÃO é uma barreira editorial.
Sem publicações; o ledger persiste dentro do mesmo snapshot SQLite/R2.
"""
from __future__ import annotations

import hashlib
import re
import sqlite3
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import urlsplit

from .catalog import Catalog
from .routing import sites

# Associação a intenção de busca, não sinônimos superficiais.
ANGLES = (
    ("criterios", "critérios de escolha", "o que avaliar antes de escolher", "quais características conferir"),
    ("uso", "cenários de uso", "para quais necessidades considerar", "em que situações faz sentido"),
    ("comparacao", "comparação de alternativas", "como comparar opções semelhantes", "quais diferenças verificar"),
    ("espaco", "espaço e instalação", "como avaliar espaço e instalação", "quais medidas conferir"),
    ("cuidados", "conservação e cuidados", "quais cuidados observar no dia a dia", "o que verificar na limpeza e conservação"),
    ("custo", "custo e manutenção", "como analisar custo e manutenção", "quais gastos além do preço considerar"),
    ("erros", "erros de compra", "erros comuns ao escolher", "quais confusões evitar"),
    ("perguntas", "dúvidas frequentes", "dúvidas para pesquisar antes de comprar", "quais perguntas fazer ao vendedor"),
)

# Palavras-chave essenciais (não usar um título genérico sem termo principal).
KEYWORD_BY_NICHE = {
    "cozinha/air_fryers": "air fryer",
    "cozinha/liquidificadores": "liquidificador",
    "cozinha/outros_eletroportateis": "eletroportátil",
    "cozinha/organizacao_utensilios": "organizador de cozinha",
    "cafe/preparo": "café",
    "casa/decoracao": "decoração",
    "casa/organizacao": "organização",
    "limpeza/equipamentos": "limpeza",
    "climatizacao/ventilacao": "ventilador",
    "beleza/cabelos": "cabelo",
    "beleza/maquiagem": "maquiagem",
    "moda/vestuario_calcados": "moda",
    "ferramentas/eletricas_manuais": "ferramenta",
    "automotivo/acessorios": "acessório automotivo",
    "tecnologia/gadgets": "tecnologia",
    "pets/cuidados_acessorios": "pet",
    "jardim/horta_jardinagem": "jardinagem",
    "viagem/malas_acessorios": "viagem",
    "musica/violao_instrumentos": "violão",
    "ciclismo/equipamentos": "ciclismo",
}
MAX_TITLE = 120


def fold(raw: str) -> str:
    n = unicodedata.normalize("NFKD", str(raw or "").casefold())
    n = "".join(c for c in n if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", n)).strip()


def title_key(title: str) -> str:
    return hashlib.sha256(fold(title).encode("utf-8")).hexdigest()


def slug(title: str) -> str:
    return "-".join(fold(title).split())[:110].strip("-")


def truncated_name(name: str, keyword: str) -> str:
    """Encurtar mantendo o termo obrigatório inteiro (sem completar especificações)."""
    name = re.sub(r"\s+", " ", name).strip()
    if not fold(name) or not fold(keyword):
        raise ValueError("Nome ou palavra-chave inválidos")
    # Evita nomes comerciais enormes; porém preserva a palavra-chave.
    if len(name) <= 72:
        result = name
    else:
        cutoff = name[:72].rsplit(" ", 1)[0].rstrip(" ,;-:")
        if fold(keyword) not in fold(cutoff):
            result = keyword.capitalize() + " — " + name[:48].rsplit(" ", 1)[0]
        else:
            result = cutoff
    if fold(keyword) not in fold(result):
        result = keyword.capitalize() + ": " + result
    return result


@dataclass(frozen=True)
class Brief:
    site_key: str
    product_key: str
    angle: str
    title: str
    keyword: str
    topic: str
    category: str
    niche: str
    slug: str
    status: str = "REVIEW_REQUIRED"

    def safe_dict(self) -> dict:
        return dict(site_key=self.site_key, product_key=self.product_key, angle=self.angle,
                    title=self.title, keyword=self.keyword, topic=self.topic, category=self.category,
                    niche=self.niche, slug=self.slug, status=self.status)


class EditorialError(ValueError):
    """Códigos estáticos, sem dados de produto/segredos."""


def make_brief(site_key: str, product_key: str, name: str, category: str, niche: str,
               angle_id: str) -> Brief:
    route = sites().get(site_key)
    if route is None:
        raise EditorialError("unknown_site")
    if f"{category}/{niche}" not in route["allowed_niches"]:
        raise EditorialError("niche_outside_site")
    keyword = KEYWORD_BY_NICHE.get(f"{category}/{niche}")
    if not keyword:
        raise EditorialError("missing_keyword")
    angle = next((x for x in ANGLES if x[0] == angle_id), None)
    if angle is None:
        raise EditorialError("unknown_angle")
    if not re.fullmatch(r"(?:shopee:[0-9]+:[0-9]+|url:[a-f0-9]{64})", product_key):
        raise EditorialError("unrecognized_product_key")
    subject = truncated_name(name, keyword)
    # Não repetir apenas o nome comercial: o título explicita nova intenção de busca.
    title = f"{subject}: {angle[2]}"
    if len(title) > MAX_TITLE:
        subject = truncated_name(subject[:max(25, 110-len(angle[2]))], keyword)
        title = f"{subject}: {angle[2]}"
    if len(title) > MAX_TITLE or fold(keyword) not in fold(title):
        raise EditorialError("seo_keyword_or_title_length")
    topic = f"{keyword} | {angle[1]} | {fold(subject)}"
    return Brief(site_key=site_key, product_key=product_key, angle=angle_id, title=title,
                 keyword=keyword, topic=topic, category=category, niche=niche, slug=slug(title))


class EditorialLedger:
    """Ledger transacional; salva junto ao mesmo DB e snapshot R2 do catálogo.

    Distinção:
    - produto comercial pode repetir em mais de um artigo;
    - mesma pauta (produto, ângulo) não pode repetir em toda a rede;
    - título normalizado e slug são exclusivos por rede;
    - conteúdo gerado precisa de revisão antes da publicação.
    """
    def __init__(self, catalog: Catalog):
        self.catalog = catalog
        self.db = catalog.db
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS editorial_briefs (
            brief_id TEXT PRIMARY KEY,
            site_key TEXT NOT NULL,
            product_key TEXT NOT NULL,
            angle TEXT NOT NULL,
            title TEXT NOT NULL,
            normalized_title TEXT NOT NULL UNIQUE,
            slug TEXT NOT NULL UNIQUE,
            keyword TEXT NOT NULL,
            topic TEXT NOT NULL,
            category TEXT NOT NULL,
            niche TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN
             ('REVIEW_REQUIRED','APPROVED','DRAFT_CREATED','SCHEDULED','PUBLISHED','REJECTED')),
            remote_id TEXT NOT NULL DEFAULT '',
            created_utc TEXT NOT NULL,
            updated_utc TEXT NOT NULL,
            UNIQUE(product_key,angle)
        );
        CREATE INDEX IF NOT EXISTS idx_editorial_site_status
            ON editorial_briefs(site_key,status,created_utc);
        """)
        self.db.commit()

    def _approved_product(self, brief: Brief) -> tuple[str,str,str]:
        site=sites().get(brief.site_key)
        if not site or f"{brief.category}/{brief.niche}" not in site["allowed_niches"]:
            raise EditorialError("site_route_invalid")
        row = self.db.execute("""
            SELECT p.title,t.category,t.niche FROM products p
            JOIN product_taxonomy t ON t.product_key=p.product_key
            WHERE p.product_key=? AND p.moderation='eligible' AND t.status='matched'
        """, (brief.product_key,)).fetchone()
        if row is None or row[1:] != (brief.category,brief.niche):
            raise EditorialError("product_not_eligible")
        if self.catalog.for_conversion(brief.product_key) is None:
            raise EditorialError("product_source_policy_blocked")
        return row

    def reserve(self, brief: Brief) -> str:
        if brief.status != "REVIEW_REQUIRED":
            raise EditorialError("unsafe_initial_status")
        original_name,cat,niche=self._approved_product(brief)
        expected=make_brief(brief.site_key,brief.product_key,original_name,cat,niche,brief.angle)
        if brief != expected:
            raise EditorialError("brief_mismatch")
        identity=title_key(brief.title)
        brief_id=hashlib.sha256(f"{brief.product_key}|{brief.angle}|{brief.site_key}".encode()).hexdigest()[:32]
        now=datetime.now(timezone.utc).isoformat(timespec="seconds")
        # transação serializada; falha fechada em conflitos entre workers.
        try:
            self.db.execute("BEGIN IMMEDIATE")
            self._approved_product(brief)
            recent=self.db.execute("""SELECT normalized_title,topic FROM editorial_briefs
                WHERE site_key=? AND status!='REJECTED'""",(brief.site_key,)).fetchall()
            # Previne títulos por mera troca de uma palavra (mesmo keyword e intenção).
            tokens=set(fold(brief.title).split())
            for stored_title,old_topic in recent:
                if stored_title == identity:
                    raise EditorialError("duplicate_title_or_subject")
                old_tokens=set(fold(old_topic).split())
                new_tokens=set(fold(brief.topic).split())
                if old_tokens and new_tokens and len(old_tokens & new_tokens) / len(old_tokens | new_tokens) >= 0.88:
                    raise EditorialError("near_duplicate_topic")
            self.db.execute("""
                INSERT INTO editorial_briefs
                (brief_id,site_key,product_key,angle,title,normalized_title,slug,keyword,topic,
                category,niche,status,created_utc,updated_utc)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,(brief_id,brief.site_key,brief.product_key,brief.angle,brief.title,identity,
                 brief.slug,brief.keyword,brief.topic,brief.category,brief.niche,
                 "REVIEW_REQUIRED",now,now))
            self.db.commit()
        except sqlite3.IntegrityError:
            self.db.rollback()
            raise EditorialError("duplicate_title_or_subject") from None
        except Exception:
            self.db.rollback()
            raise
        return brief_id

    def next_brief(self, site_key: str, product_key: str) -> tuple[Brief,str]:
        """Tenta ângulos distintos, sem impedir reutilização do produto."""
        if site_key not in sites():
            raise EditorialError("unknown_site")
        row=self.db.execute("""
            SELECT p.title,t.category,t.niche FROM products p
            JOIN product_taxonomy t ON t.product_key=p.product_key
            WHERE p.product_key=? AND p.moderation='eligible' AND t.status='matched'
        """,(product_key,)).fetchone()
        if not row:
            raise EditorialError("product_not_eligible")
        if self.catalog.for_conversion(product_key) is None:
            raise EditorialError("product_source_policy_blocked")
        for angle_id,*_ in ANGLES:
            brief=make_brief(site_key,product_key,row[0],row[1],row[2],angle_id)
            try:
                return brief,self.reserve(brief)
            except EditorialError as exc:
                if str(exc) in ("duplicate_title_or_subject","near_duplicate_topic"):
                    continue
                raise
        raise EditorialError("editorial_angles_exhausted")

    def update_status(self, brief_id: str, next_status: str, remote_id: str = "") -> None:
        """Transições explícitas; nunca publica automaticamente."""
        allowed = {
            "REVIEW_REQUIRED": {"APPROVED","REJECTED"},
            "APPROVED": {"DRAFT_CREATED","REJECTED"},
            "DRAFT_CREATED": {"SCHEDULED","REJECTED"},
            "SCHEDULED": {"PUBLISHED"},
            "REJECTED": set(), "PUBLISHED": set()
        }
        row=self.db.execute("SELECT status,site_key FROM editorial_briefs WHERE brief_id=?",
                            (brief_id,)).fetchone()
        if not row or next_status not in allowed.get(row[0],set()):
            raise EditorialError("invalid_transition")
        # Apenas registro; postagem requer adaptador separado e API autorizada.
        with self.db:
            self.db.execute("""UPDATE editorial_briefs SET status=?, remote_id=?, updated_utc=?
             WHERE brief_id=? AND status=?""",
             (next_status,remote_id,datetime.now(timezone.utc).isoformat(timespec="seconds"),
              brief_id,row[0]))

    def statistics(self) -> dict:
        rows=self.db.execute("SELECT status,COUNT(*) FROM editorial_briefs GROUP BY status").fetchall()
        return {status:count for status,count in rows}
