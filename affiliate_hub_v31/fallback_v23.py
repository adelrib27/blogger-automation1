"""V31 C6: adaptador universal de produtos CSV/R2 para filas legadas Shopee v2.3.

NÃO publica, NÃO consulta a API Shopee e NÃO converte links durante falhas.
Só entrega links afiliados reais previamente verificados no cache da
campanha do site (nunca um productLink orgânico disfarçado de afiliado).
Novos blogs são registrados por JSON em sites.d/, sem alterações neste módulo.
"""
from __future__ import annotations

import csv
from contextlib import closing
import json
import os
import re
import sqlite3
import tempfile
from types import SimpleNamespace
import unicodedata
from pathlib import Path
from urllib.parse import urlsplit

from .catalog import host_allowed
from .routing import sites
from .source_policy_gate import source_safe_for_use

MAX_SELECT = 100
MAX_CATEGORIES = 60
MAX_KEYWORDS = 500
MAX_ALTERNATIVES_PER_KEYWORD = 3  # lojas alternativas quando a primeira estiver bloqueada


class FallbackUnavailable(ValueError):
    """Mensagens constantes para logs, nunca expor valores comerciais."""


def normalize(text: str) -> str:
    value = unicodedata.normalize("NFKD", str(text or "").lower())
    value = "".join(c for c in value if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", value)).strip()


def contains_phrase(value: str, phrase: str) -> bool:
    norm = normalize(phrase)
    if not norm:
        return False
    return re.search(r"(?<![a-z0-9])" + re.escape(norm).replace(r"\ ", r"\s+") +
                     r"(?![a-z0-9])", normalize(value)) is not None


def semantic_score(title: str, keyword: str, intent_rules: dict) -> float:
    """Contrato equivalente ao filtro por intenção do v2.3, sem scores inventados."""
    name=normalize(title)
    target=normalize(keyword)
    if not name or not target:
        return 0.0
    rules=intent_rules.get("rules") or {}
    rule=rules.get(keyword) or rules.get(target)
    if not rule:
        tokens=set(name.split())
        sought={x for x in target.split() if len(x)>=3}
        if not sought:
            return 0.0
        score=len(tokens & sought)/len(sought)
        return round(score,4) if score>=0.6 else 0.0
    if not isinstance(rule,dict):
        raise FallbackUnavailable("intent_rule_invalid")
    blocked=rule.get("block_phrases") or []
    groups=rule.get("require_groups") or []
    if (not isinstance(blocked,list) or not isinstance(groups,list) or
            any(not isinstance(s,str) for s in blocked) or
            any(not isinstance(group,list) or not group or
                any(not isinstance(s,str) for s in group) for group in groups)):
        raise FallbackUnavailable("intent_rule_invalid")
    if any(contains_phrase(title,b) for b in blocked):
        return 0.0
    if any(not any(contains_phrase(title,w) for w in group) for group in groups):
        return 0.0
    return 1.0


def load_configuration(config_path: Path, rules_path: Path) -> tuple[dict,dict]:
    try:
        cfg=json.loads(Path(config_path).read_text(encoding="utf-8"))
        rules=json.loads(Path(rules_path).read_text(encoding="utf-8"))
    except (OSError,ValueError,UnicodeError):
        raise FallbackUnavailable("config_read_failed") from None
    if not isinstance(cfg,dict) or not isinstance(rules,dict):
        raise FallbackUnavailable("invalid_config")
    cats=cfg.get("categories")
    if not isinstance(cats,dict) or not 1<=len(cats)<=MAX_CATEGORIES:
        raise FallbackUnavailable("categories_invalid")
    n=0
    for cat, keywords in cats.items():
        if (not isinstance(cat,str) or not cat.strip() or
                not isinstance(keywords,list) or not keywords):
            raise FallbackUnavailable("keywords_invalid")
        if any(not isinstance(x,str) or not 2<=len(x.strip())<=100 for x in keywords):
            raise FallbackUnavailable("keywords_invalid")
        n+=len(keywords)
    if n>MAX_KEYWORDS:
        raise FallbackUnavailable("too_many_keywords")
    return cfg,rules


def candidates_from_catalog(db_path: Path, site_key: str,
                            config: dict, intent_rules: dict,
                            limit: int = 30) -> list[dict]:
    """Seleciona do catálogo apenas links já convertidos para o site indicado.

    A origem R2 é um snapshot do catálogo; não há chamada de rede aqui.
    Sem itens qualificados o resultado é vazio e deve bloquear o publicador.
    """
    site=sites().get(site_key)
    if site is None:
        raise FallbackUnavailable("site_not_registered")
    if not isinstance(limit,int) or not 1<=limit<=MAX_SELECT:
        raise FallbackUnavailable("limit_invalid")
    campaign=site["campaign"]
    allowed=set(site["allowed_niches"])
    config_categories=config.get("categories")
    if not isinstance(config_categories,dict):
        raise FallbackUnavailable("categories_invalid")
    uri="file:"+str(Path(db_path).resolve())+"?mode=ro"
    try:
        with closing(sqlite3.connect(uri,uri=True)) as conn:
            rows=conn.execute("""
                SELECT p.product_key,p.item_id,p.title,p.image_url,p.shop_id,
                       p.origin_url,l.affiliate_url,t.category,t.niche
                FROM affiliate_links l
                JOIN products p ON p.product_key=l.product_key
                JOIN product_taxonomy t ON t.product_key=p.product_key
                WHERE l.campaign=? AND p.moderation='eligible'
                    AND t.status='matched'
                ORDER BY p.product_key
            """,(campaign,)).fetchall()
            # Gate tambem vale para links convertidos anteriormente.
            # Usar a conexao somente leitura; nao instanciar Catalog.
            source_view=SimpleNamespace(db=conn)
            rows=[row for row in rows if source_safe_for_use(source_view,row[0])]
    except (sqlite3.Error,OSError):
        raise FallbackUnavailable("catalog_unavailable") from None

    by_keyword=[]
    used=set()
    for category, keywords in config_categories.items():
        for keyword in keywords:
            alternatives=0
            for key,item_id,title,image,shop,origin,offer,cat,niche in rows:
                if (key in used or f"{cat}/{niche}" not in allowed or
                        not str(item_id).isdigit() or
                        not str(shop).isdigit() or
                        not str(image).startswith("https://") or
                        not host_allowed(origin) or
                        not host_allowed(offer,allow_short=True)):
                    continue
                score=semantic_score(title,keyword,intent_rules)
                if score<=0:
                    continue
                used.add(key)
                by_keyword.append({
                    "itemId":str(item_id),
                    "shopId":str(shop),
                    "productLink":origin,
                    "productName":title,
                    "shopName":"",
                    "imageUrl":image,
                    "offerLink":offer,
                    "keywords":[keyword],
                    "intentMatchedKeywords":[keyword],
                    "sourceKeywords":[keyword],
                    "categories":[category],
                    "sourceModes":["csv_r2_verified_affiliate_cache"],
                    "priorityTier":"CSV_R2_CACHE",
                    "opportunityScore":None,
                    "semanticIntentScore":score,
                    "searchDemandProxy":None,
                    "priceMin":None,
                    "priceMax":None,
                    "commission":None,
                    "ratingStar":None,
                    "sales":None,
                })
                alternatives+=1
                if alternatives >= MAX_ALTERNATIVES_PER_KEYWORD or len(by_keyword)>=limit:
                    break
            if len(by_keyword)>=limit:
                break
        if len(by_keyword)>=limit:
            break
    return by_keyword


def emit_v23_outputs(rows: list[dict], config: dict, output: Path) -> int:
    """Compatível com ranking.json/intent_report.json consumidos pelas filas v2.3.

    Escreve arquivos só quando há dados, para impedir que filas antigas sigam
    usando saídas incompletas ou nenhuma conversão afiliada válida.
    """
    if not rows:
        raise FallbackUnavailable("no_verified_cached_affiliate_link")
    for row in rows:
        if (not isinstance(row,dict) or
                not str(row.get("itemId") or "").isdigit() or
                not str(row.get("productName") or "").strip() or
                not str(row.get("imageUrl") or "").startswith("https://") or
                not host_allowed(str(row.get("offerLink") or ""),allow_short=True) or
                not row.get("intentMatchedKeywords")):
            raise FallbackUnavailable("invalid_verified_offer")
    folder=Path(output)
    if folder.is_symlink():
        raise FallbackUnavailable("unsafe_output")
    folder.mkdir(parents=True,exist_ok=True)
    report=[{
        "rank":i,
        "itemId":row["itemId"],
        "productName":row["productName"],
        "priorityTier":row.get("priorityTier"),
        "semanticIntentScore":row.get("semanticIntentScore"),
        "intentMatchedKeywords":row["intentMatchedKeywords"],
        "opportunityScore":row.get("opportunityScore"),
        "shopName":row.get("shopName"),
        "offerLink":row["offerLink"],
    } for i,row in enumerate(rows,1)]
    ranking_json={
        "version":"v31-csv-r2-fallback",
        "generatedAt":__import__("time").time_ns()//1_000_000_000,
        "method":"confirmed affiliate cache only; no Shopee live pricing/commissions",
        "config":config,
        "ranking":rows,
        "priorityPolicy":{"commissionExtraFirst":False,
                          "standardCommissionOnlyToFillMissingSlots":False,
                          "extraCount":0,"reserveCount":len(rows)}
    }
    report_json={
        "version":"2.3",
        "policy":"CSV R2 fallback: verified affiliate links and semantic intent",
        "primarySemanticFilter":{"input":len(rows),"accepted":len(rows),"rejected":0},
        "reserveSemanticFilter":None,
        "diversity":{},
        "ranking":report,
        "rejectedSample":[],
    }
    fields=("rank","priorityTier","priorityRank","opportunityScore","itemId",
            "productName","shopName","priceMin","priceMax","sellerExtraCommissionPct",
            "shopeeCommissionPct","totalCommissionPct","commission","sales",
            "ratingStar","priceDiscountRate","searchDemandProxy","categories",
            "keywords","sourceModes","imageUrl","offerLink")
    # Staging local com replace atômico de cada arquivo; em erro o job termina
    # e os passos posteriores do workflow devem continuar bloqueados.
    with tempfile.TemporaryDirectory(prefix=".v31-csv-output-",dir=folder) as temp:
        staging=Path(temp)
        (staging/"ranking.json").write_text(
            json.dumps(ranking_json,ensure_ascii=False,indent=2),encoding="utf-8")
        (staging/"intent_report.json").write_text(
            json.dumps(report_json,ensure_ascii=False,indent=2),encoding="utf-8")
        (staging/"search_signals.json").write_text("{}",encoding="utf-8")
        (staging/"diversity_report.json").write_text(
            json.dumps({"source":"csv_r2_verified_affiliate_cache",
                        "note":"no live sales/commission/rating data",
                        "selected":len(rows)},ensure_ascii=False),encoding="utf-8")
        with (staging/"ranking.csv").open("w",encoding="utf-8-sig",newline="") as handle:
            writer=csv.DictWriter(handle,fieldnames=fields)
            writer.writeheader()
            for i,row in enumerate(rows,1):
                line={field:row.get(field) for field in fields}
                line["rank"]=i
                for name in ("categories","keywords","sourceModes"):
                    line[name]=" | ".join(row.get(name) or [])
                writer.writerow(line)
        for name in ("ranking.json","intent_report.json","search_signals.json",
                     "diversity_report.json","ranking.csv"):
            os.replace(staging/name,folder/name)
    return len(rows)


def run_cloud(site_key: str, config: Path, rules: Path, output: Path, limit: int) -> int:
    from .r2_state import R2State
    from .r2_state import verify_database
    site=sites().get(site_key)
    if site is None:
        raise FallbackUnavailable("site_not_registered")
    cfg,intents=load_configuration(config,rules)
    with tempfile.TemporaryDirectory(prefix="v31-csv-fallback-") as t:
        state=Path(t)/"catalog.sqlite3"
        if not R2State.from_env().restore_to(state):
            raise FallbackUnavailable("r2_state_missing")
        verify_database(state)
        rows=candidates_from_catalog(state,site_key,cfg,intents,limit=limit)
        return emit_v23_outputs(rows,cfg,output)
