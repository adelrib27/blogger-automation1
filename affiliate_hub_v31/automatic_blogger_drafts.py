"""C55 — rotina genérica de rascunhos Blogger V31, nunca publicação LIVE.

Não antecipa nicho: lê pedidos reais em site_requests.d, observa limite
de artigos solicitado e histórico Blogger, escolhe SKU aprovado do R2
com foto CSV + link da campanha exata, gera TEXTO ORIGINAL via Workers AI,
liga os artigos LIVE do mesmo blog e cria no máximo 1 rascunho/dia.

Sem geração por IA bem-sucedida, sem credenciais legítimas ou sem produto
compatível: nenhum post. Em qualquer circunstância isDraft=True.
"""
from __future__ import annotations

import argparse
import html
import json
import os
import re
import tempfile
from pathlib import Path
from urllib.parse import urlsplit

from .article_commerce import (
    CommerceArticleError, product_offer_html, related_articles_html,
)
from .catalog import Catalog
from .r2_state import R2State,verify_database
from .routing import sites
from .site_request_queue import load_requests
from .site_launch_plan import preview_site_launch
from .taxonomy import normalize

MAX_DRAFTS_PER_RUN=1
WORKERS_MODEL="@cf/meta/llama-3.3-70b-instruct-fp8-fast"
KEY_PATTERN=re.compile(r'data-v31-product-key="(shopee:[0-9]+:[0-9]+)"')


class AutoDraftError(ValueError):
    pass


def validate_remote_identity(site:dict,blog:dict)->str:
    if (not isinstance(site,dict) or
        site.get("platform")!="blogger" or
        site.get("publish_enabled") is not False or
        not re.fullmatch(r"[0-9]{8,22}",str(site.get("identifier",""))) or
        not isinstance(blog,dict) or
        str(blog.get("id"))!=site["identifier"]):
        raise AutoDraftError("blogger_identity_invalid")
    url=blog.get("url","")
    try:
        u=urlsplit(url)
        if (u.scheme!="https" or not u.hostname or u.username or u.password
            or u.port not in (None,443)):
            raise ValueError()
    except (ValueError,TypeError):
        raise AutoDraftError("blogger_url_unverified") from None
    return "https://"+u.hostname.lower().rstrip(".")+"/"


def relevant_live_links(posts:list[dict],*,blog_home_url:str,
                        current_title:str,limit:int=2)->list[tuple[str,str]]:
    """Posts reais já LIVE do mesmo blog; nunca inventar URL para link interno."""
    if type(limit) is not int or not 1<=limit<=3:
        raise AutoDraftError("related_link_limit_invalid")
    base=urlsplit(blog_home_url).hostname
    choices=[]
    for p in posts:
        if not isinstance(p,dict) or str(p.get("status","")).lower()!="live":
            continue
        title,url=p.get("title"),p.get("url")
        if not isinstance(title,str) or not isinstance(url,str):
            continue
        pu=urlsplit(url)
        if (pu.scheme!="https" or pu.hostname!=base or
            not pu.path.endswith(".html") or pu.query or pu.fragment or
            normalize(title)==normalize(current_title)):
            continue
        choices.append((title,url))
    # Deterministic order supplied by Blogger (most recent first).
    return choices[:limit]


def select_next(catalog:Catalog,*,site_key:str,request:dict,
                existing_posts:list[dict])->dict:
    route=sites().get(site_key)
    if not route or route.get("platform")!="blogger":
        raise AutoDraftError("registered_blogger_required")
    if (request.get("site_key")!=site_key or
        request.get("platform")!="blogger" or
        request.get("enabled") is not True or
        not (request.get("articles") is None or
             (type(request["articles"]) is int and 1<=request["articles"]<=24))):
        raise AutoDraftError("real_request_required")
    if (not isinstance(existing_posts,list) or
        any(not isinstance(p,dict) for p in existing_posts)):
        raise AutoDraftError("blogger_history_required")
    # Quota finita opcional: articles=null significa geração contínua (1 rascunho por ciclo).
    if (request["articles"] is not None and
        len({str(p["id"]) for p in existing_posts if p.get("id")}) >= request["articles"]):
        return {"status":"OWNER_QUOTA_REACHED","publication_calls":0,
                "draft_creation_calls":0,"product_key":None}
    seen=set()
    titles=set()
    for post in existing_posts:
        match=KEY_PATTERN.search(post.get("content") or "")
        if match: seen.add(match.group(1))
        title=post.get("title")
        if isinstance(title,str): titles.add(normalize(title))
    plan=preview_site_launch(
        catalog,topic=request["topic"],platform="blogger",
        site_key=site_key,max_items=24,max_per_shop=1)
    if not plan["registered_site"] or plan["can_publish"] is not False:
        raise AutoDraftError("unsafe_site_preview")
    from .site_request_queue import reserved_pilot_sku
    reserved = reserved_pilot_sku(site_key)
    for item in plan["approved_catalog_candidates"]:
        key=item["product_key"]
        if (key == reserved or key in seen or item["affiliate_status"]!="verified_for_campaign"
            or catalog.for_conversion(key) is None or
            catalog.cached_link(key,route["campaign"])!=item["affiliate_url"]):
            continue
        name=str(item["title"])
        title="Guia de compra: "+name[:75].rstrip(" ,;:-")
        if normalize(title) in titles:
            continue
        # Validates the exact image, campaign and product-topic overlap.
        try:
            section=product_offer_html(catalog,site_key=site_key,
                product_key=key,topic=name[:110])
        except CommerceArticleError:
            continue
        return {
            "status":"READY_FOR_ORIGINAL_DRAFT_REVIEW",
            "product_key":key,"product_title":name,
            "keyword":name[:110],"title":title,
            "offer_html":section,"site_key":site_key,
            "publication_calls":0,"draft_creation_calls":0,
        }
    return {"status":"NO_VERIFIED_CAMPAIGN_PRODUCT_YET",
            "product_key":None,"publication_calls":0,"draft_creation_calls":0}


def _ai_response_text(response:dict)->str:
    if not isinstance(response,dict):
        raise AutoDraftError("ai_invalid_response")
    result=response.get("result")
    if isinstance(result,dict):
        # JSON Mode may return a parsed object rather than a JSON string.
        if isinstance(result.get("response"),dict):
            return json.dumps(result["response"],ensure_ascii=False)
        text=result.get("response") or result.get("text")
        if isinstance(text,str) and text.strip():
            return text.strip()
        options=result.get("choices") or []
        if options and isinstance(options[0],dict):
            value=options[0].get("message",{}).get("content")
            if isinstance(value,str): return value
    raise AutoDraftError("ai_output_missing")


def _reject_commercial_title_in_body(paragraphs:list[str], product_name:str)->None:
    """Não deixar o texto editorial virar repetição do título comercial.

    Produto permanece no bloco de oferta verificado da campanha; corpo usa
    classe genérica e critérios de escolha. Sem afirmação de performance.
    """
    if not isinstance(product_name,str):
        raise AutoDraftError("ai_product_title_invalid")
    canonical=normalize(product_name)
    if len(canonical)>=40 and canonical in normalize(" ".join(paragraphs)):
        raise AutoDraftError("ai_product_title_copied_into_editorial_body")


def validate_generated_paragraphs(text:str,*,keyword:str,product_name:str="")->list[str]:
    """Worker AI never supplies HTML/links/product imagery; those come from R2."""
    if not isinstance(text,str) or len(text)>24000:
        raise AutoDraftError("ai_text_length_invalid")
    cleaned=text.strip()
    if cleaned.startswith("```"):
        cleaned=re.sub(r"^```(?:json)?\s*","",cleaned,flags=re.I)
        cleaned=re.sub(r"\s*```$","",cleaned)
    # Qwen may include thinking text; accept only a plain JSON object.
    if not cleaned.startswith("{") or not cleaned.endswith("}"):
        raise AutoDraftError("ai_must_return_json_only")
    try: doc=json.loads(cleaned)
    except ValueError:
        raise AutoDraftError("ai_json_invalid") from None
    if not isinstance(doc,dict) or set(doc)!={"paragraphs"}:
        raise AutoDraftError("ai_contract_invalid")
    paragraphs=doc["paragraphs"]
    if (not isinstance(paragraphs,list) or
        not 6<=len(paragraphs)<=10 or
        any(not isinstance(p,str) or
            not 110<=len(p.strip())<=2200 for p in paragraphs)):
        raise AutoDraftError("ai_paragraphs_invalid")
    normalized_body = set(normalize(" ".join(paragraphs)).split())
    meaningful_keyword = {t for t in normalize(keyword).split() if len(t)>=3}
    if (len(" ".join(paragraphs).split())<420 or
        not meaningful_keyword or not meaningful_keyword.intersection(normalized_body)):
        raise AutoDraftError("ai_content_insufficient_or_offtopic")
    if any("http://" in p or "https://" in p or
           "<script" in p.lower() or
           "R$" in p or
           "compre agora" in normalize(p)
           for p in paragraphs):
        raise AutoDraftError("ai_unverified_commercial_claim")
    _reject_commercial_title_in_body(paragraphs, product_name)
    return [" ".join(p.split()) for p in paragraphs]


# Sequência universal: corresponde à ordem obrigatória do prompt Workers AI.
EDITORIAL_EIGHT_HEADINGS = (
    "O que observar antes da escolha",
    "Medidas e espaço disponível",
    "Compatibilidade com o ambiente e o uso",
    "Materiais e acabamento",
    "Cuidados e manutenção",
    "Erros comuns na escolha",
    "Como conferir as informações do anúncio",
    "Conclusão",
)


def editorial_headings(count: int) -> tuple[str, ...]:
    """O último parágrafo é conclusivo, nunca um checklist ou perguntas."""
    if type(count) is not int or not 6 <= count <= 10:
        raise AutoDraftError("editorial_headings_count_invalid")
    if count <= 8:
        return EDITORIAL_EIGHT_HEADINGS[:count - 1] + ("Conclusão",)
    if count == 9:
        return EDITORIAL_EIGHT_HEADINGS[:7] + (
            "Checklist antes da compra", "Conclusão",
        )
    return EDITORIAL_EIGHT_HEADINGS[:7] + (
        "Dúvidas para confirmar com o vendedor",
        "Checklist antes da compra", "Conclusão",
    )


def generate_original_paragraphs(*,product_name:str,topic:str,
                                 account_id:str,api_token:str)->list[str]:
    if not account_id.strip() or not api_token.strip():
        raise AutoDraftError("workers_ai_credentials_missing")
    import requests  # optional dependency; no import/network in offline tests
    prompt=(
        "Redija um guia de compra original, educativo e prudente em "
        "português do Brasil sobre o assunto a seguir. Produza JSON puro "
        'exatamente {"paragraphs":["...",...]}, sem Markdown e sem HTML. '
        "Escreva EXATAMENTE 8 parágrafos independentes de pelo menos "
        "70 palavras cada, total 500 a 900 palavras. Cada parágrafo deve "
        "cobrir APENAS sua seção, na ORDEM OBRIGATÓRIA: "
        "1) objetivo e necessidade; 2) medidas e espaço disponível; "
        "3) compatibilidade com o ambiente e o uso; 4) materiais e "
        "acabamento; 5) cuidados e manutenção; 6) erros comuns; "
        "7) como conferir as informações do anúncio; 8) conclusão. "
        "Não troque a posição das seções nem antecipe a conclusão. "
        "Não invente "
        "preço, descontos, avaliações, estoque, especificações não "
        "informadas, certificados, relatos pessoais ou marcas distintas. "
        "Não insira links nem chamadas para comprar (serão agregados "
        "com dados verificados do catálogo). "
        "Use o nome do produto somente como contexto para entender a categoria: "
        "NUNCA repita o título comercial completo nos parágrafos. "
        "Explique critérios da classe genérica de produto em linguagem original. "
        "O nome abaixo é copiado do anúncio, não representa avaliação. "
        "Produto: "+product_name+"; tema: "+topic+"."
    )
    url=("https://api.cloudflare.com/client/v4/accounts/"+
         account_id+"/ai/run/"+WORKERS_MODEL)
    response=requests.post(url,headers={
       "Authorization":"Bearer "+api_token,
       "Content-Type":"application/json"},json={
       "messages":[
          {"role":"system","content":"Redator neutro de guias de compra. JSON puro; fatos não verificados são proibidos."},
          {"role":"user","content":prompt},
       ],
       "response_format":{
          "type":"json_schema",
          "json_schema":{
             "type":"object",
             "properties":{"paragraphs":{
                "type":"array","items":{"type":"string"},
                "minItems":8,"maxItems":8,
             }},
             "required":["paragraphs"],
          },
       },
       "max_tokens":4200,"temperature":0.35},timeout=150)
    if response.status_code!=200:
        raise AutoDraftError("workers_ai_unavailable")
    return validate_generated_paragraphs(
        _ai_response_text(response.json()),keyword=topic,
        product_name=product_name)


def compose_draft_html(plan:dict,paragraphs:list[str],*,
                       blog_home_url:str,published_posts:list[dict])->str:
    if plan.get("status")!="READY_FOR_ORIGINAL_DRAFT_REVIEW":
        raise AutoDraftError("approved_product_plan_required")
    if not 6<=len(paragraphs)<=10:
        raise AutoDraftError("original_body_required")
    _reject_commercial_title_in_body(paragraphs, str(plan.get("product_title") or ""))
    related=relevant_live_links(
        published_posts,blog_home_url=blog_home_url,
        current_title=plan["title"],limit=2)
    links=related_articles_html(related,blog_home_url=blog_home_url)
    headings=editorial_headings(len(paragraphs))
    blocks=[]
    for i,text in enumerate(paragraphs):
        blocks.append("<h2>"+html.escape(headings[i])+"</h2><p>"+
                      html.escape(text,quote=True)+"</p>")
    return ('<article lang="pt-BR">'+''.join(blocks)+
        plan["offer_html"]+links+'</article>')


def _get_blogger_service():
    from src.criar_rascunho import criar_servico_blogger
    return criar_servico_blogger()


def _list_posts(service,blog_id:str,*,label:str|None=None,include_scheduled:bool=False)->list[dict]:
    result=[]
    statuses = ("LIVE", "DRAFT", "SCHEDULED") if include_scheduled else ("LIVE", "DRAFT")
    for status in statuses:
        token=None
        for _ in range(100): # paginar histórico completo, sem teto de 3/24 artigos
            args={"blogId":blog_id,"status":[status],
                  "maxResults":100,"fetchBodies":True}
            if include_scheduled:
                args["view"] = "ADMIN"
            if label is not None:
                args["labels"]=label
            if token: args["pageToken"]=token
            batch=service.posts().list(**args).execute()
            items=batch.get("items",[])
            if (not isinstance(items,list) or
                any(not isinstance(item,dict) for item in items)):
                raise AutoDraftError("blogger_history_invalid")
            for item in items:
                # A resposta do Blogger pode omitir status por item. O filtro
                # LIVE/DRAFT enviado à API é a fonte autoritativa do estado.
                detected=str(item.get("status") or status).upper()
                if detected!=status:
                    raise AutoDraftError("blogger_history_status_mismatch")
                result.append({**item,"status":status.lower()})
            token=batch.get("nextPageToken")
            if not token: break
        else:
            raise AutoDraftError("blogger_history_pagination_limit")
    return result


def draft_next(*,site_key:str,execute:bool=False,
               blogger_service=None,workers_writer=None,
               catalog:Catalog|None=None)->dict:
    if type(execute)is not bool:
        raise AutoDraftError("execution_flag_invalid")
    route=sites().get(site_key)
    if not route or route.get("platform")!="blogger":
        raise AutoDraftError("real_blogger_required")
    request=next((r for r in load_requests()
                  if r["site_key"]==site_key),None)
    if request is None:
        raise AutoDraftError("enabled_owner_request_required")
    service=blogger_service or _get_blogger_service()
    blog=service.blogs().get(blogId=route["identifier"]).execute()
    home=validate_remote_identity(route,blog)
    history=_list_posts(service,route["identifier"])
    def proceed(cat):
        plan=select_next(cat,site_key=site_key,request=request,
                         existing_posts=history)
        if plan["status"]!="READY_FOR_ORIGINAL_DRAFT_REVIEW":
            return {
                "mode":"C55_DRY_RUN" if not execute else "C55_SAFE_AUTODRAFT",
                "status":plan["status"],"publication_calls":0,
                "draft_creation_calls":0,"campaign_from_registry":True}
        if not execute:
            return {"mode":"C55_DRY_RUN","status":plan["status"],
                    "publication_calls":0,"draft_creation_calls":0,
                    "campaign_from_registry":True}
        generator=workers_writer or generate_original_paragraphs
        body=generator(product_name=plan["product_title"],
            topic=plan["keyword"],
            account_id=os.getenv("CLOUDFLARE_ACCOUNT_ID",""),
            api_token=os.getenv("CLOUDFLARE_API_TOKEN",""))
        content=compose_draft_html(plan,body,blog_home_url=home,
            published_posts=history)
        # Before mutation, recheck Blogger identity/history for races.
        recent=_list_posts(service,route["identifier"])
        again=select_next(cat,site_key=site_key,
            request=request,existing_posts=recent)
        if again.get("product_key")!=plan["product_key"]:
            raise AutoDraftError("blogger_draft_race_detected")
        result=service.posts().insert(
            blogId=route["identifier"],
            body={"kind":"blogger#post",
                  "title":plan["title"],"content":content,
                  "labels":["Guias de compra", "Produtos"],
                 },isDraft=True).execute()
        if str(result.get("status","")).lower()!="draft" or not result.get("id"):
            raise AutoDraftError("blogger_draft_not_confirmed")
        return {
            "mode":"C55_SAFE_AUTODRAFT","status":"DRAFT_CREATED",
            "draft_id":str(result["id"]),
            "publication_calls":0,"draft_creation_calls":1,
            "has_real_csv_photo":True,"has_keyword_link_and_cta":True,
            "internal_links_from_real_posts":bool(relevant_live_links(
                recent,blog_home_url=home,current_title=plan["title"])),
            "campaign_from_registry":True,
        }
    if catalog is not None:
        return proceed(catalog)
    with tempfile.TemporaryDirectory(prefix="v31-c55-drafter-") as td:
        path=Path(td)/"catalog.sqlite3"
        if not R2State.from_env().restore_to(path):
            raise AutoDraftError("r2_catalog_missing")
        verify_database(path)
        with Catalog(path) as cat:
            return proceed(cat)


def main()->int:
    p=argparse.ArgumentParser(description="V31 Blogger: gerar NO MÁXIMO 1 draft original, nunca LIVE")
    p.add_argument("--site-key",default=None)
    p.add_argument("--execute-draft",action="store_true")
    args=p.parse_args()
    try:
        from .site_request_queue import autonomous_sites_for_writes
        migrated = autonomous_sites_for_writes() if args.execute_draft else set()
        if args.site_key is not None:
            target=args.site_key
            if target in migrated:
                print("AUTONOMOUS_DRAFT_ROUTE_USE_NEW_WORKFLOW")
                return 0
        else:
            from datetime import date
            eligible=sorted(r["site_key"] for r in load_requests()
                            if r["platform"]=="blogger" and r["site_key"] not in migrated)
            if not eligible:
                print("V31_C55_NO_REAL_BLOGGER_REQUESTS")
                return 0
            target=eligible[date.today().toordinal()%len(eligible)]
        result=draft_next(site_key=target,
                          execute=args.execute_draft)
        print("V31_C55_BLOGGER_DRAFT_AUTOMATION_SAFE_PASS")
        # IDs de drafts e produtos não vão para logs públicos de CI.
        print(json.dumps({k:v for k,v in result.items()
               if k not in ("draft_id","product_key")},
               sort_keys=True,ensure_ascii=False))
        return 0
    except Exception as exc:
        print("V31_C55_BLOGGER_DRAFT_AUTOMATION_FAILED_"+
              type(exc).__name__)
        return 3


if __name__=="__main__":
    raise SystemExit(main())
