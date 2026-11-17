"""C18 — descoberta editorial independente de blogs, com ranking explicável.

Categorias Shopee = descoberta; taxonomia + moderação = permissão atual.
Não promove item sob revisão; não converte link; não inventa preço,
comissão, vendas, CTR, receita ou elegibilidade de campanha. Se campanha
específica não tem link convertido, retorna requires_conversion, jamais o
URL afiliado de outro blog. Nenhum blog/nicho futuro é predeterminado.
"""
from __future__ import annotations

from collections import Counter

from .catalog import Catalog, host_allowed
from .converter import valid_campaign
from .curation_audit import PROTECTED_ROOTS
from .source_category_index import create_source_category_schema
from .taxonomy import normalize
from .title_index import fts_condition

STOPWORDS = frozenset((
    "com","sem","para","como","que","uma","uns","umas","por","sobre",
    "dos","das","da","de","do","em","nas","nos","seu","sua",
    "melhor","melhores","produto","produtos","artigo","blog",
))


class DiscoveryError(ValueError):
    pass


def _terms(text: str) -> tuple[str,...]:
    return tuple(dict.fromkeys(w for w in normalize(text).split()
                 if len(w)>=3 and w not in STOPWORDS))


def _facet_rows(catalog: Catalog, *, category: str | None,
                subcategory: str | None, include_review: bool,
                terms: tuple[str,...]):
    create_source_category_schema(catalog)
    where=["1=1"]
    params=[]
    if category is not None:
        where.append("f.level1=?")
        params.append(normalize(category))
    if subcategory is not None:
        where.append("f.level2=?")
        params.append(normalize(subcategory))
    if not include_review:
        where+=["p.moderation='eligible'","t.status='matched'"]
    indexed_condition,indexed_args=fts_condition(catalog,terms)
    if indexed_condition:
        where.append(indexed_condition)
        params.extend(indexed_args)
    # Rejeitar divergências L1/L2/L3 entre feeds; não escolher um produto
    # com classificação contraditória somente por uma das fontes.
    # Sem faceta oficial, produto antigo aprovado ainda pode aparecer no
    # resultado de uma busca pelo título, sem inventar categoria de origem.
    return catalog.db.execute("""
        WITH facets AS (
          SELECT product_key,MIN(level1) AS level1,MIN(level2) AS level2,
            MAX(level3) AS level3,
            COUNT(DISTINCT level1 || char(31) || level2) AS branches,
            COUNT(DISTINCT CASE WHEN level3 != '' THEN level3 END) AS leaves
          FROM product_source_categories
          WHERE status='matched' GROUP BY product_key
        )
        SELECT p.product_key,p.shop_id,p.title,p.description,p.origin_url,
               p.image_url,p.moderation,COALESCE(t.status,'review'),
               COALESCE(f.level1,''),COALESCE(f.level2,''),
               COALESCE(f.level3,'')
        FROM products p
        LEFT JOIN product_taxonomy t ON t.product_key=p.product_key
        LEFT JOIN facets f ON f.product_key=p.product_key
        WHERE (f.branches IS NULL OR (f.branches=1 AND f.leaves<=1))
          AND """+" AND ".join(where)+"""
        ORDER BY p.product_key
    """,params)


def discover(catalog: Catalog, *, topic: str,
             category: str | None = None,
             subcategory: str | None = None,
             campaign: str | None = None,
             limit: int = 12, max_per_shop: int = 2,
             include_review: bool = False) -> list[dict]:
    """Retorna produtos por intenção editorial; não executa ação comercial.

    include_review habilita análise, nunca autorização para publicar.
    Produtos sob revisão não carregam URL afiliada. can_publish é False:
    SEO, redação, campanha e gates de publicação são etapas posteriores.
    """
    if not isinstance(topic,str) or len(topic)>160:
        raise DiscoveryError("topic_invalid")
    terms=_terms(topic)
    if not terms:
        raise DiscoveryError("meaningful_topic_required")
    if not isinstance(limit,int) or not 1<=limit<=50:
        raise DiscoveryError("limit_invalid")
    if not isinstance(max_per_shop,int) or not 1<=max_per_shop<=10:
        raise DiscoveryError("max_per_shop_invalid")
    if subcategory and not category:
        raise DiscoveryError("subcategory_requires_parent")
    for value in (category,subcategory):
        if value is not None and (
            not isinstance(value,str) or not 2<=len(value)<=120 or
            not normalize(value)
        ):
            raise DiscoveryError("category_invalid")
    if campaign is not None:
        valid_campaign(campaign)

    ranked=[]
    for row in _facet_rows(catalog,category=category,
                           subcategory=subcategory,
                           include_review=include_review,terms=terms):
        (key,shop,title,description,origin,image,moderation,tax_status,
         l1,l2,l3)=row
        if not host_allowed(origin) or not str(image).startswith("https://"):
            continue
        title_words=set(_terms(title))
        description_words=set(_terms(description))
        matched=sum(1 for t in terms if t in title_words)
        auxiliary=sum(1 for t in terms if t not in title_words and
                      t in description_words)
        if matched+auxiliary==0:
            continue
        source_protected=l1 in PROTECTED_ROOTS
        approved=(moderation=="eligible" and tax_status=="matched" and
                  not source_protected)
        if not approved and not include_review:
            continue
        exact=normalize(topic) in normalize(title)
        semantic_score=100*matched+25*auxiliary+(35 if exact else 0)
        # Cache válido só para a campanha do blog explicitamente conhecido.
        link=catalog.cached_link(key,campaign) if campaign and approved else None
        if link and not host_allowed(link,allow_short=True):
            raise DiscoveryError("unsafe_cached_link")
        ready=bool(link)
        ranked.append({
            "product_key":key,"shop_id":shop,"title":title,
            "image_url":image,"product_origin_url":origin,
            "source_category_l1":l1,"source_category_l2":l2,
            "source_category_l3":l3,
            "curation":"approved" if approved else "review_required",
            "affiliate_status":(
                "verified_for_campaign" if ready else
                "requires_conversion" if approved and campaign else
                "review_required" if not approved else "campaign_not_selected"
            ),
            "semantic_score":semantic_score,
            "affiliate_url":link,
            "can_publish":False,
            "commercial_metrics_available":False,
        })
    # Relevância semântica > cache > desempate estável por ID interno.
    ranked.sort(key=lambda r:(-r["semantic_score"],
                              -int(r["affiliate_url"] is not None),
                              r["product_key"]))
    selected=[]
    shops=Counter()
    for product in ranked:
        shop=product["shop_id"]
        if shops[shop]>=max_per_shop:
            continue
        selected.append(product)
        shops[shop]+=1
        if len(selected)>=limit:
            break
    return selected



def suggest_category_paths(catalog: Catalog, *, topic: str,
                           limit: int = 8) -> list[dict]:
    """Descobre caminhos L1/L2 usando títulos REAIS; não prediz blogs futuros.

    Se o usuário pedir um blog novo, o tema solicitado determina quais
    subcategorias do CSV são pertinentes. Não cria/converte links nem posts.
    Produtos pendentes ajudam a encontrar o ramo, sem serem liberados
    para publicação. Categorias sensíveis permanecem marcadas.
    """
    if not isinstance(topic,str) or len(topic)>160:
        raise DiscoveryError("topic_invalid")
    terms=_terms(topic)
    if not terms:
        raise DiscoveryError("meaningful_topic_required")
    if not isinstance(limit,int) or not 1<=limit<=30:
        raise DiscoveryError("limit_invalid")
    min_hits=1 if len(terms)==1 else max(2,(len(terms)*2+2)//3)
    create_source_category_schema(catalog)
    indexed_condition,indexed_args=fts_condition(catalog,terms)
    indexed_where=(" WHERE "+indexed_condition) if indexed_condition else ""
    rows=catalog.db.execute("""
        WITH facets AS (
          SELECT product_key,MIN(level1) AS l1,MIN(level2) AS l2,
                 COUNT(DISTINCT level1 || char(31) || level2) AS branches
          FROM product_source_categories WHERE status='matched'
          GROUP BY product_key
        )
        SELECT p.title,p.moderation,COALESCE(t.status,'review'),
               f.l1,f.l2
        FROM products p
        JOIN facets f ON f.product_key=p.product_key AND f.branches=1
        LEFT JOIN product_taxonomy t ON t.product_key=p.product_key
    """+indexed_where,indexed_args)
    counts=Counter()
    approved=Counter()
    for title,moderation,status,l1,l2 in rows:
        title_words=set(_terms(title))
        hits=sum(word in title_words for word in terms)
        if hits<min_hits:
            continue
        path=(l1,l2)
        counts[path]+=1
        if (moderation=="eligible" and status=="matched" and
                l1 not in PROTECTED_ROOTS):
            approved[path]+=1
    ranked=sorted(counts,key=lambda path:(
        -counts[path],-approved[path],path
    ))[:limit]
    return [{
        "category":l1,"subcategory":l2,
        "title_matches_in_catalog":counts[(l1,l2)],
        "previously_approved_matching_products":approved[(l1,l2)],
        "manual_review_required_for_root":l1 in PROTECTED_ROOTS,
        "commercial_metrics_available":False,
    } for l1,l2 in ranked]
