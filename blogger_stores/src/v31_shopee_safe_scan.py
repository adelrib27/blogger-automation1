#!/usr/bin/env python3
"""Blogger V31: Shopee V23 -> SAFE_READY (no Blogger writes).

Reusable per-blog scanner: profile/config instead of magic blog identifiers.
Calls the validated V23 ranking + standard Shopee link generator. Secrets are
read from environment and NEVER written to outputs. Fail-closed on shortfalls.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import sys
from typing import Callable
from urllib.parse import urlsplit


class SafeScanError(RuntimeError):
    pass


def require(ok: bool, why: str) -> None:
    if not ok:
        raise SafeScanError(why)


def load_json(path: Path) -> dict:
    doc = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(doc, dict), f"JSON inválido: {path.name}")
    return doc


def _host(url: str) -> str:
    try:
        p = urlsplit(str(url))
        return (p.hostname or "").lower() if p.scheme == "https" and not p.username and not p.password else ""
    except (ValueError, TypeError):
        return ""


def validate_setup(profile: dict, config: dict, rules: dict, history: dict) -> tuple[str,list[str],dict]:
    bid = str(profile.get("blog_id", "")); pid = str(profile.get("page_id", ""))
    require(bid.isdigit() and pid.isdigit(), "Perfil sem Blog/Page ID")
    require(str(profile.get("mode")) == "SAFE", "Perfil não está em SAFE")
    require(profile.get("page_url", "").startswith("https://") and
            _host(profile["page_url"]).endswith(".blogspot.com") and
            urlsplit(profile["page_url"]).path == "/p/loja.html" and
            _host(profile["page_url"]) == str(profile.get("blog_host", "")).lower(),
            "URL canônica ou host do blog incorreto")
    require(history.get("blogId") == bid and history.get("version") == 1 and isinstance(history.get("runs"), list),
            "Histórico não corresponde ao blog")
    cats = profile.get("categories"); mapping = config.get("categories")
    require(isinstance(cats, list) and len(cats) >= 1 and list(mapping or {}) == cats,
            "Configuração e perfil divergem nas categorias")
    quota = profile.get("per_category")
    require(isinstance(quota, dict) and list(quota) == cats and all(type(quota[c]) is int and quota[c] >= 1 for c in cats),
            "Distribuição inválida")
    require(sum(quota.values()) == profile.get("expected_products") and 4 <= profile["expected_products"] <= 100,
            "Meta total de produtos inválida")
    require(all(isinstance(mapping[c], list) and len(mapping[c]) == quota[c] and
                len(set(mapping[c])) == quota[c] and all(isinstance(k, str) and k.strip() for k in mapping[c])
                for c in cats), "Intenções incompletas ou duplicadas")
    require(isinstance(rules.get("rules"), dict) and
            all(k in rules["rules"] and rules["rules"][k].get("require_groups") and
                isinstance(rules["rules"][k].get("block_phrases"), list)
                for c in cats for k in mapping[c]), "Regras semânticas incompletas")
    require(config.get("market") == "BR" and config.get("currency") == "BRL", "Mercado/moeda divergente")
    return bid, cats, quota


def current_history_ids(history: dict, *, now: datetime, days: int = 14) -> tuple[set[str],set[str]]:
    cutoff = now - timedelta(days=days)
    recent: set[str] = set(); previous: set[str] = set()
    valid_runs=[]
    for run in history.get("runs", []):
        try: stamp=datetime.fromisoformat(run["timestamp"].replace("Z","+00:00"))
        except (ValueError, KeyError, TypeError): continue
        if stamp.tzinfo is None or stamp > now + timedelta(minutes=5): continue
        valid_runs.append((stamp, run))
        if stamp >= cutoff and run.get("source") in ("blogger_published", "seed_from_current_blogger_store"):
            recent.update(str(x["itemId"]) for x in run.get("items", []) if str(x.get("itemId", "")).isdigit())
    if valid_runs:
        last = max(valid_runs,key=lambda x:x[0])[1]
        previous={str(x["itemId"]) for x in last.get("items", []) if str(x.get("itemId", "")).isdigit()}
    return recent, previous


def eligible(p: dict) -> bool:
    """Primary API fields are mandatory, not fabricated from old Blogger cards."""
    iid=str(p.get("itemId", ""))
    return bool(re.fullmatch(r"\d{4,25}",iid) and str(p.get("productName", "")).strip() and
                str(p.get("shopName", "")).strip() and
                _host(p.get("productLink", "")) == "shopee.com.br" and
                _host(p.get("imageUrl", "")) in ("cf.shopee.com.br", "down-br.img.susercontent.com") and
                p.get("priceMin") is not None and float_positive(p.get("priceMin")))


def float_positive(n: object) -> bool:
    try:
        from decimal import Decimal
        v=Decimal(str(n));return v.is_finite() and 0<v<=Decimal("1000000")
    except Exception: return False


def choose(ranked: list[dict], profile: dict, config: dict, rules: dict, history: dict,*,
           semantic_check: Callable[[str,str,dict],dict], policy_check: Callable[[dict],None],
           now: datetime) -> tuple[dict,dict]:
    bid,cats,quota=validate_setup(profile,config,rules,history)
    recent,previous=current_history_ids(history,now=now)
    chosen={c:[] for c in cats}; coverage={c:[] for c in cats}; picked_ids:set[str]=set();shops={}
    for cat in cats:
        for keyword in config["categories"][cat]:
            pick=None; mode=None
            for pass_name in ("new", "fallback_older", "carry_forward_last"):
                for p in ranked:
                    iid=str(p.get("itemId", "")); shop=str(p.get("shopId") or p.get("shopName") or "")
                    if not eligible(p) or iid in picked_ids or cat not in (p.get("categories") or []):continue
                    if shops.get(shop,0)>=int(config.get("max_per_shop",2)):continue
                    if keyword not in (p.get("intentMatchedKeywords") or p.get("keywords") or []):continue
                    if pass_name=="new" and iid in recent:continue
                    if pass_name=="fallback_older" and iid in previous:continue
                    if pass_name=="carry_forward_last" and iid not in previous:continue
                    if semantic_check(p.get("productName", ""),keyword,rules).get("accepted") is not True:continue
                    try:policy_check(p)
                    except Exception:continue
                    pick=p;mode=pass_name;break
                if pick is not None:break
            require(pick is not None, f"Sem oferta segura para {cat} / {keyword}")
            item=dict(pick); item["category"]=cat;item["sourceKeyword"]=keyword
            item["rotationSelectionMode"]=mode
            chosen[cat].append(item); coverage[cat].append(keyword)
            iid=str(item["itemId"]); picked_ids.add(iid)
            shop=str(item.get("shopId") or item.get("shopName"));shops[shop]=shops.get(shop,0)+1
        require(len(chosen[cat])==quota[cat],f"Categoria incompleta: {cat}")
    require(len(picked_ids)==profile["expected_products"],"IDs únicos insuficientes")
    return chosen,{"keywordCoverage":coverage,"rotation":{
        "policy":"fresh_then_older_then_last_if_necessary", "recentBlocked":len(recent),
        "fallbackCount":sum(p["rotationSelectionMode"]!="new" for items in chosen.values() for p in items)}}



def coverage_report(ranked: list[dict], profile: dict, config: dict, rules: dict, *,
                    semantic_check: Callable, policy_check: Callable) -> dict:
    """Safe aggregate diagnostics, never product ids, links or credentials."""
    report={}
    for category in profile['categories']:
        report[category]={}
        for keyword in config['categories'][category]:
            matches=[p for p in ranked if category in (p.get('categories') or [])
                     and keyword in (p.get('intentMatchedKeywords') or p.get('keywords') or [])]
            valid=[]
            for p in matches:
                if not eligible(p):continue
                if semantic_check(p.get('productName',''),keyword,rules).get('accepted') is not True:continue
                try:policy_check(p)
                except Exception:continue
                valid.append(p)
            report[category][keyword]={"in_ranking":len(matches),
                        "eligible_with_photo_policy":len(valid),
                        "distinct_shops":len({str(p.get('shopId') or p.get('shopName')) for p in valid})}
    return report


def produce_safe_selection(profile: dict, config: dict, rules: dict, history: dict,ranked:list[dict],*,
                           semantic_check,policy_check,make_link,resolve_link,
                           app_id:str,now:datetime) -> dict:
    chosen,meta=choose(ranked,profile,config,rules,history,semantic_check=semantic_check,
                       policy_check=policy_check,now=now)
    normalized={};seen=set();count=0
    for cat,items in chosen.items():
        normalized[cat]=[]
        for p in items:
            iid=str(p["itemId"]);count+=1
            short=make_link(p["productLink"])
            require(_host(short)=="s.shopee.com.br",f"Link afiliado não-Shopee para item {iid}")
            ok,final_url,status=resolve_link(short)
            require(ok is True and (_host(final_url)=="shopee.com.br" or _host(final_url).endswith(".shopee.com.br")),
                    f"Link afiliado não comprovado: {iid}")
            out={"itemId":iid,"productName":p["productName"],"shopName":p["shopName"],
                 "priceMin":str(p["priceMin"]),"priceMax":str(p.get("priceMax") or p["priceMin"]),
                 "imageUrl":p["imageUrl"],"productLink":p["productLink"],"affiliateUrl":short,
                 "offerLink":short,"category":cat,"sourceKeyword":p["sourceKeyword"],
                 "rotationSelectionMode":p["rotationSelectionMode"],"source":"shopee_affiliate_open_api",
                 "discoveredAt":now.isoformat()}
            policy_check(out)
            require(iid not in seen,"Item duplicado durante links");seen.add(iid)
            normalized[cat].append(out)
    require(count==profile["expected_products"] and len(seen)==count,"Links insuficientes")
    return {"schemaVersion":1,"status":"SAFE_READY","publishReady":True,"dryRun":True,
            "blogId":profile["blog_id"],"timestamp":now.isoformat(),
            "itemsPerCategory":len(next(iter(normalized.values()))),"categoryCount":len(normalized),
            "totalItems":count,"uniqueItemIds":len(seen),"categories":normalized,
            **meta,"affiliateLinkGeneration":{"method":"generateShortLink","appId":app_id,
                                             "validatedCount":count,"allResolvedToShopee":True},
            "semanticValidation":{"rulesFile":"config/shopee_v31_lab_intent_rules.json",
                                  "strictAccessoriesBlocked":True,"oneProductPerKeyword":True,
                                  "finalProductGate":True},
            "gates":{"allLinksResolved":True,"semanticRulesApplied":True,"finalProductGate":True,
                     "failClosed":True,"allPhotosPresent":all(p["imageUrl"] for a in normalized.values() for p in a),
                     "expectedCategories":len(normalized)==len(profile["categories"]),
                     "expectedItems":count==profile["expected_products"]}}


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root",type=Path,required=True)
    parser.add_argument("--profile",type=Path,required=True)
    parser.add_argument("--config",type=Path,required=True)
    parser.add_argument("--rules",type=Path,required=True)
    parser.add_argument("--rotation",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    try:
        profile=load_json(args.profile);config=load_json(args.config)
        rules=load_json(args.rules);history=load_json(args.rotation)
        validate_setup(profile,config,rules,history)
        require(args.out.suffix==".json" and not args.out.exists(),"Arquivo de saída já existe")
        app_id=os.getenv("SHOPEE_APP_ID","").strip()
        secret=os.getenv("SHOPEE_SECRET","").strip()
        require(app_id and secret,"Shopee API credenciais indisponíveis")
        require(app_id==str(config.get("expected_app_id", "")),"Shopee App ID divergente")
        root=args.repo_root.resolve()
        require((root/"src"/"shopee_oportunidades_v23.py").is_file(),"Repositório Shopee V23 ausente")
        require((root/"src"/"blogger_policy_guard.py").is_file(),"Policy Guard central ausente")
        os.environ["SHOPEE_OPPORTUNITIES_CONFIG"]=str(args.config.resolve())
        os.environ["SHOPEE_INTENT_RULES"]=str(args.rules.resolve())
        os.environ["SHOPEE_OUTPUT_DIR"]=str((args.out.parent/"scan_v23").resolve())
        os.environ["SHOPEE_CATEGORY"]="all"
        os.environ["SHOPEE_TOP_N"]=str(config.get("top_n",180))
        sys.path[:0]=[str(root/"src"),str(root/"radar_tech_br"/"src")]
        import shopee_oportunidades_v23 as v23
        from blogger_policy_guard import require_product_allowed
        from refresh_blogger_offer_links import generate_short_link,resolved_to_shopee
        # Re-runs the existing semantic & policy guard, without the old post publisher.
        ranked=v23.scan_v23()
        print("V31_SAFE_KEYWORD_COVERAGE="+json.dumps(coverage_report(ranked,profile,config,rules,
            semantic_check=v23.evaluate_keyword, policy_check=require_product_allowed),ensure_ascii=False),flush=True)
        selection=produce_safe_selection(profile,config,rules,history,ranked,
            semantic_check=v23.evaluate_keyword,policy_check=require_product_allowed,
            make_link=lambda url:generate_short_link(app_id,secret,url),
            resolve_link=resolved_to_shopee,app_id=app_id,now=datetime.now(timezone.utc))
        # Validate the same V31 contract that the page publisher uses.
        sys.path.insert(0,str(root/"blogger_stores"/"v31_core"))
        from v31_from_v23_selection import convert_selection
        converted=convert_selection(selection,profile,require_product_allowed=require_product_allowed)
        require(len(converted["products"])==profile["expected_products"],"Adaptador V31 falhou")
        args.out.parent.mkdir(parents=True,exist_ok=True)
        temporary=args.out.with_suffix(".json.tmp")
        require(not temporary.exists(),"Arquivo temporário já existe")
        temporary.write_text(json.dumps(selection,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        os.replace(temporary,args.out)
        report={"status":"V31_LAB_SHOPEE_SAFE_READY","blog_id":profile["blog_id"],
                "products":len(converted["products"]),"photos":sum(bool(p["image_url"]) for p in converted["products"]),
                "affiliate_links":len(converted["products"]),"published":False,
                "selection_sha256":sha256(args.out.read_bytes()).hexdigest()}
        print(json.dumps(report,ensure_ascii=False))
        return 0
    except Exception as e:
        print(json.dumps({"status":"V31_SHOPEE_SAFE_BLOCKED","error_type":type(e).__name__,
                          "reason":str(e)[:250]},ensure_ascii=False),file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())