"""V31 C60 — um escritor de RASCUNHOS para QUALQUER WordPress registrado.

Nenhum site, nicho, domínio ou campanha é presumido: sites() e os pedidos
site_requests.d são as fontes de autorização. As credenciais por site
devem existir em segredo GitHub, NUNCA no repositório. Default é PREVIEW,
e mesmo execute=True só faz POST status="draft", nunca "publish".

Uma nova demanda de artigos é contada pelos slugs V31 identificáveis;
blogs legados não são sobrescritos. Retentativas após falha não podem criar
duplicatas da mesma oferta. Sem pedido real/credenciais, não há writes.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import html
import json
import os
import re
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import unicodedata
from datetime import date
from pathlib import Path

from .article_commerce import (
    CommerceArticleError,product_offer_html,related_articles_html
)
from .automatic_blogger_drafts import generate_original_paragraphs, editorial_headings
from .catalog import Catalog
from .r2_state import R2State,verify_database
from .routing import sites
from .site_launch_plan import preview_site_launch
from .site_request_queue import load_requests
from .taxonomy import normalize


class WordPressAutoDraftError(ValueError):
    pass


def site_route(site_key: str) -> dict:
    route=sites().get(site_key)
    if (not route or route.get("platform")!="wordpress" or
        route.get("publish_enabled") is not False):
        raise WordPressAutoDraftError("real_wordpress_route_required")
    return route


def _slug_prefix(site_key: str) -> str:
    # ID estável por site: não expõe dados de conta e não confunde legados.
    return "v31-"+hashlib.sha256(site_key.encode("utf-8")).hexdigest()[:12]+"-"


def _product_slug(site_key: str,product_key: str) -> str:
    if not re.fullmatch(r"shopee:[0-9]+:[0-9]+",product_key):
        raise WordPressAutoDraftError("invalid_product_id")
    return _slug_prefix(site_key)+product_key.split(":")[-1]


def _verify_blog_url(url: str, expected: str) -> bool:
    try:
        a=urllib.parse.urlsplit(url)
        b=urllib.parse.urlsplit(expected)
        return (a.scheme=="https" and b.scheme=="https" and
            a.hostname==b.hostname and
            a.port in (None,443) and b.port in (None,443) and
            not a.username and not a.password and
            not a.query and not a.fragment and
            a.path.rstrip("/") in ("","/") and b.path=="/")
    except (TypeError,ValueError,AttributeError):
        return False


class WordPressRestClient:
    """Único destino: domínio HTTPS exato da rota V31 já registrada."""
    def __init__(self, *, base_url: str, username: str="",
                 application_password: str=""):
        if not _verify_blog_url(base_url,base_url):
            raise WordPressAutoDraftError("wordpress_base_url_invalid")
        self.base_url=base_url.rstrip("/")
        self.username=username
        self.application_password=application_password

    @property
    def authenticated(self) -> bool:
        return bool(self.username and self.application_password)

    def _call(self,method:str,path:str,body:dict|None=None):
        if (method not in ("GET","POST") or
            not isinstance(path,str) or not path.startswith("/wp-json/wp/v2/")
            or ".." in path or "\\" in path or
            "#" in path or "@" in path):
            raise WordPressAutoDraftError("wordpress_api_path_invalid")
        if method=="POST" and not self.authenticated:
            raise WordPressAutoDraftError("wordpress_credentials_required")
        url=self.base_url+path
        headers={"Accept":"application/json",
                 "User-Agent":"V31-Universal-WordPress-Draft/1.0"}
        if self.authenticated:
            token=base64.b64encode(
                (self.username+":"+self.application_password).encode()
            ).decode()
            headers["Authorization"]="Basic "+token
        data=None
        if body is not None:
            headers["Content-Type"]="application/json"
            data=json.dumps(body,ensure_ascii=False).encode("utf-8")
        request=urllib.request.Request(
            url,headers=headers,method=method,data=data)
        try:
            with urllib.request.urlopen(request,timeout=35) as resp:
                self._last_wp_total_pages=resp.headers.get("X-WP-TotalPages")
                payload=json.loads(resp.read().decode("utf-8","replace"))
        except Exception as exc:
            # Não imprimir senha, URL completa, headers nem corpo.
            raise WordPressAutoDraftError(
                "wordpress_http_"+type(exc).__name__) from None
        if not isinstance(payload,(dict,list)):
            raise WordPressAutoDraftError("wordpress_invalid_response")
        return payload

    def site_settings(self)->dict:
        if not self.authenticated:
            raise WordPressAutoDraftError("wordpress_credentials_required")
        d=self._call("GET","/wp-json/wp/v2/settings")
        if not isinstance(d,dict) or not _verify_blog_url(
                str(d.get("url","")),self.base_url+"/"):
            raise WordPressAutoDraftError("wordpress_identity_mismatch")
        return d

    def list_posts(self,*,include_unpublished:bool,slug:str|None=None)->list[dict]:
        if include_unpublished and not self.authenticated:
            raise WordPressAutoDraftError("wordpress_credentials_required")
        statuses="publish,draft,pending,private,future" if include_unpublished else "publish"
        result=[]
        expected_pages=None
        for page in range(1,21):
            # A API pode devolver EXATAMENTE 100 posts em uma única página.
            # Um lote cheio não implica outra página: conferir total REST.
            self._last_wp_total_pages=None
            params={
                "status":statuses,"per_page":100,"page":page,
                "context":"edit" if include_unpublished else "view",
            }
            if slug is not None:
                params["slug"]=slug
            q=urllib.parse.urlencode(params)
            batch=self._call("GET","/wp-json/wp/v2/posts?"+q)
            if (not isinstance(batch,list) or len(batch)>100 or
                any(not isinstance(post,dict) for post in batch)):
                raise WordPressAutoDraftError("wordpress_posts_schema_invalid")
            result.extend(batch)
            raw_pages=self._last_wp_total_pages
            if raw_pages is not None:
                try:
                    pages=int(raw_pages)
                except (ValueError,TypeError):
                    raise WordPressAutoDraftError("wordpress_pages_invalid") from None
                if pages == 0 and page == 1 and not batch:
                    return []
                if (pages<1 or pages>20 or page>pages or
                    (expected_pages is not None and pages!=expected_pages)):
                    raise WordPressAutoDraftError("wordpress_pages_invalid")
                expected_pages=pages
                if page==pages:
                    return result
                if len(batch)!=100:
                    raise WordPressAutoDraftError("wordpress_pages_incomplete")
            elif len(batch)<100:
                return result
            else:
                # Não arriscar duplicação com histórico incompleto.
                raise WordPressAutoDraftError("wordpress_pagination_unverified")
        raise WordPressAutoDraftError("wordpress_posts_pagination_limit")

    def get_post(self,post_id:int)->dict:
        if type(post_id)is not int or post_id<=0:
            raise WordPressAutoDraftError("post_id_invalid")
        post=self._call("GET",f"/wp-json/wp/v2/posts/{post_id}?context=edit")
        if not isinstance(post,dict) or post.get("id")!=post_id:
            raise WordPressAutoDraftError("wordpress_post_identity_mismatch")
        return post

    def create_draft(self,*,title:str,slug:str,content:str)->dict:
        if (not isinstance(title,str) or not 20<=len(title)<=110 or
            not isinstance(slug,str) or
            not re.fullmatch(r"v31-[a-f0-9]{12}-[0-9]+",slug) or
            not isinstance(content,str) or
            'data-v31-product-key="' not in content or
            'rel="nofollow sponsored' not in content or
            'Ver produto na Shopee' not in content):
            raise WordPressAutoDraftError("draft_payload_invalid")
        body={"title":title,"slug":slug,"status":"draft",
              "content":content,"comment_status":"closed"}
        result=self._call("POST","/wp-json/wp/v2/posts",body)
        if not isinstance(result,dict) or not isinstance(result.get("id"),int):
            raise WordPressAutoDraftError("draft_not_created")
        if result.get("status")!="draft":
            raise WordPressAutoDraftError("wordpress_draft_status_invalid")
        return result



def _draft_title(product_title: str) -> str:
    """Título legível: nunca cortar uma palavra nem terminar em conectivo."""
    if not isinstance(product_title, str):
        raise WordPressAutoDraftError("draft_title_invalid")
    cleaned = re.sub(r"\s+", " ", product_title).strip()
    prefix = "Guia prático: "
    max_length = 75
    room = max_length - len(prefix)
    if len(cleaned) > room:
        fragment = cleaned[:room + 1]
        if " " not in fragment:
            raise WordPressAutoDraftError("draft_title_untrimmable")
        cleaned = fragment.rsplit(" ", 1)[0]
    cleaned = cleaned.rstrip(" -–:;,.")
    endings = {"a", "as", "o", "os", "de", "da", "das", "do", "dos",
               "e", "em", "ou", "com", "para", "por", "sem", "um", "uma"}
    while cleaned and cleaned.split()[-1].casefold() in endings:
        cleaned = cleaned.rsplit(" ", 1)[0].rstrip(" -–:;,.")
    title = prefix + cleaned
    if not 20 <= len(title) <= max_length:
        raise WordPressAutoDraftError("draft_title_invalid")
    return title

def _html_text(post:dict)->str:
    value=post.get("content",{})
    if isinstance(value,str):
        return value
    if isinstance(value,dict):
        return str(value.get("raw") or value.get("rendered") or "")
    return ""


def _title(post:dict)->str:
    value=post.get("title",{})
    return str(value.get("raw") or value.get("rendered") or ""
               if isinstance(value,dict) else value)


def _check_history(posts:list[dict],*,site_key:str,
                   limit:int)->tuple[set[str],set[str],int,list[tuple[str,str]]]:
    if not isinstance(posts,list) or len(posts)>2000:
        raise WordPressAutoDraftError("wordpress_history_invalid")
    prefix=_slug_prefix(site_key)
    own_slugs=set()
    prior_links=set()
    public=[]
    for post in posts:
        if (not isinstance(post,dict) or
            not isinstance(post.get("id"),int) or
            post.get("status") not in (
                "publish","draft","pending","future","private")):
            raise WordPressAutoDraftError("wordpress_history_invalid")
        slug=str(post.get("slug") or "")
        if slug.startswith(prefix):
            own_slugs.add(slug)
        body=_html_text(post)
        for m in re.finditer(r'href=["\'](https://s\.shopee\.com\.br/[^"\']+)["\']',body,re.I):
            prior_links.add(m.group(1))
        if post["status"]=="publish":
            title=_title(post)
            link=post.get("link","")
            if title and isinstance(link,str):
                public.append((title,link))
    return own_slugs,prior_links,len(own_slugs),public[:limit]


def select_next(catalog:Catalog, *,site_key:str,topic:str,
                posts:list[dict],requested_total:int|None=1)->dict:
    route=site_route(site_key)
    if (not isinstance(topic,str) or not topic.strip()
        or len(topic)>160 or not (requested_total is None or
            (type(requested_total) is int and 1<=requested_total<=24))):
        raise WordPressAutoDraftError("real_topic_or_quota_invalid")
    own,prior,used,related=_check_history(posts,site_key=site_key,limit=6)
    if requested_total is not None and used>=requested_total:
        return {"status":"OWNER_QUOTA_REACHED","posts_created":0,
                "publication_calls":0}
    plan=preview_site_launch(catalog,site_key=site_key,
        topic=topic,platform="wordpress",max_items=24,max_per_shop=1)
    if (not plan["registered_site"] or
        plan["can_publish"] is not False or
        plan["campaign"]!=route["campaign"]):
        raise WordPressAutoDraftError("catalog_site_match_failed")
    from .site_request_queue import reserved_pilot_sku
    reserved = reserved_pilot_sku(site_key)
    for item in plan["approved_catalog_candidates"]:
        key=item["product_key"]
        if (key == reserved or item["affiliate_status"]!="verified_for_campaign" or
            not item["affiliate_url"] or
            item["affiliate_url"] in prior or
            _product_slug(site_key,key) in own or
            catalog.for_conversion(key) is None):
            continue
        try:
            offer=product_offer_html(catalog,site_key=site_key,
                product_key=key,topic=str(item["title"])[:110],
                verified_site_route=route)
        except CommerceArticleError:
            continue
        valid=[]
        for title,url in related:
            try:
                related_articles_html([(title,url)],
                    blog_home_url=route["identifier"])
                valid.append((title,url))
            except CommerceArticleError:
                continue
        return {
            "status":"READY_FOR_DRAFT_REVIEW",
            "product_key":key,
            "title":str(item["title"]),
            "offer_html":offer,
            "slug":_product_slug(site_key,key),
            "related":valid[:2],
            "campaign_verified":True,
            "posts_created":0,"publication_calls":0,
        }
    return {"status":"NO_APPROVED_CACHED_PRODUCT_FOR_TOPIC",
            "posts_created":0,"publication_calls":0}


def _normalized_editorial_text(value: str) -> str:
    folded = unicodedata.normalize("NFKD", value.casefold())
    folded = "".join(ch for ch in folded if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", re.sub(r"[^\w]+", " ", folded)).strip()


# Padrões deliberadamente conservadores: alegações extraordinárias não
# comprovadas pelo catálogo são recusadas antes de escrever no WordPress.
# Um gate regex não é validação factual completa; a publicação LIVE ainda
# exige aprovação separada.
_UNSUPPORTED_EDITORIAL_CLAIMS = (
    r"\b(?:nos testamos|testamos o produto|em nossos testes|comprovamos)\b",
    r"\b(?:100\s*% seguro|totalmente seguro|seguranca garantida)\b",
    r"\b(?:antibacterian[oa]s?|bactericidas?|resistente[s]? a bacterias)\b",
    r"\b(?:garante|garantem)\s+(?:a\s+)?(?:durabilidade|seguranca|resultado)\b",
    r"\b(?:reduz|economiza|elimina|evita)\w*\b.{0,65}\b(?:tempo|esforco|bacterias|odores|acidentes)\b",
    r"\b(?:tem se destacado|opcao popular|mais vendido|melhor do mercado)\b",
    r"\b(?:instalacao|montagem|fixacao)\s+(?:e|ser[aá])\s+(?:facil|simples|segura)\b",
)


def validate_wordpress_paragraphs(paragraphs: list[str], *,
                                   product_title: str) -> list[str]:
    """Gate editorial universal de DRAFT, anterior a qualquer POST.

    Confirma estrutura, legibilidade e padrões de risco explícitos.
    Não finge comprovação factual: qualquer lançamento LIVE requer revisão.
    """
    if (not isinstance(paragraphs, list)
            or not 6 <= len(paragraphs) <= 10
            or not isinstance(product_title, str)):
        raise WordPressAutoDraftError("wordpress_editorial_structure_invalid")
    cleaned = []
    folded_seen = set()
    for paragraph in paragraphs:
        if not isinstance(paragraph, str):
            raise WordPressAutoDraftError("wordpress_editorial_structure_invalid")
        text = " ".join(paragraph.split())
        if not 110 <= len(text) <= 2200:
            raise WordPressAutoDraftError("wordpress_editorial_paragraph_invalid")
        fold = _normalized_editorial_text(text)
        if fold in folded_seen:
            raise WordPressAutoDraftError("wordpress_editorial_duplicate_paragraph")
        folded_seen.add(fold)
        if ("<" in text or ">" in text or "http://" in text.lower()
                or "https://" in text.lower() or "R$" in text
                or re.search(r"\bcompre agora\b", fold)):
            raise WordPressAutoDraftError("wordpress_editorial_html_or_sales")
        if any(re.search(pattern, fold) for pattern in _UNSUPPORTED_EDITORIAL_CLAIMS):
            raise WordPressAutoDraftError("wordpress_editorial_claim_unverified")
        cleaned.append(text)
    full_text = " ".join(cleaned)
    if not 420 <= len(full_text.split()) <= 1250:
        raise WordPressAutoDraftError("wordpress_editorial_word_count_invalid")
    # Nome comercial exato no corpo não deve virar endosso repetido.
    # Nomes curtos podem ser linguagem genérica; proteger só títulos
    # comerciais suficientemente específicos.
    product_fold = _normalized_editorial_text(product_title)
    if len(product_fold) >= 40 and product_fold in _normalized_editorial_text(full_text):
        raise WordPressAutoDraftError("wordpress_editorial_copied_offer_title")
    return cleaned


def compose_article(plan:dict,paragraphs:list[str], *,
                    site_url:str)->str:
    if (plan.get("status")!="READY_FOR_DRAFT_REVIEW"
        or not isinstance(paragraphs,list)
        or not 6<=len(paragraphs)<=10):
        raise WordPressAutoDraftError("original_article_required")
    paragraphs=validate_wordpress_paragraphs(
        paragraphs,product_title=str(plan.get("title") or ""))
    headings=editorial_headings(len(paragraphs))
    body="".join("<h2>"+html.escape(headings[i])+"</h2><p>"+
                 html.escape(text)+"</p>"
                 for i,text in enumerate(paragraphs))
    internal=related_articles_html(plan["related"],
        blog_home_url=site_url)
    return ('<article lang="pt-BR"><section class="v31-original-guide">'
        +body+'</section>'+plan["offer_html"]+internal+"</article>")


def credentials_for(site_key:str,*,raw:str|None=None)->tuple[str,str]:
    # Um segredo JSON adiciona sites livremente sem mudar código; nunca logar.
    secret=raw if raw is not None else os.getenv(
        "V31_WORDPRESS_SITE_CREDENTIALS_JSON","")
    if not secret:
        # Ponte estrita: o Casa WordPress real já possui credenciais legadas
        # separadas no Environment GitHub (C62). Não propagar para outro
        # domínio: sites futuros usam SEMPRE o JSON universal por site.
        if site_key == "wordpress_casa_decoracao":
            legacy_user = os.getenv("CASA_WORDPRESS_USERNAME", "")
            legacy_password = os.getenv("CASA_WORDPRESS_APP_PASSWORD", "")
            if legacy_user.strip() and legacy_password.strip():
                return legacy_user, legacy_password
        raise WordPressAutoDraftError("wordpress_credentials_not_configured")
    try:
        mapping=json.loads(secret)
    except (ValueError,TypeError):
        raise WordPressAutoDraftError("wordpress_credentials_schema_invalid") from None
    if not isinstance(mapping,dict):
        raise WordPressAutoDraftError("wordpress_credentials_schema_invalid")
    config=mapping.get(site_key)
    if (not isinstance(config,dict) or
        set(config)!={"username","application_password"} or
        not all(isinstance(config[k],str) and config[k].strip()
                for k in ("username","application_password"))):
        raise WordPressAutoDraftError("wordpress_site_credentials_missing")
    return config["username"],config["application_password"]


def run(*,site_key:str,preview_topic:str|None=None,
        execute_draft:bool=False,wp_client=None,catalog:Catalog|None=None,
        writer=None)->dict:
    route=site_route(site_key)
    if type(execute_draft)is not bool:
        raise WordPressAutoDraftError("invalid_execution_flag")
    request=next((r for r in load_requests()
                  if r["site_key"]==site_key),None)
    if execute_draft:
        if (request is None or request["platform"]!="wordpress"
            or request.get("enabled") is not True):
            raise WordPressAutoDraftError("enabled_owner_request_required")
        topic=request["topic"]
        requested=request["articles"]
    else:
        if request is not None:
            topic=request["topic"]
            requested=request["articles"]
        elif isinstance(preview_topic,str) and preview_topic.strip():
            topic=preview_topic
            requested=1
        else:
            return {"mode":"DRY_RUN","status":"NO_REAL_WORDPRESS_REQUEST",
                    "wordpress_posts_created":0,"publication_calls":0}
    if wp_client is None:
        if execute_draft:
            username,password=credentials_for(site_key)
        else:
            username,password="",""
        wp_client=WordPressRestClient(
            base_url=route["identifier"],username=username,
            application_password=password)
    if execute_draft:
        identity=wp_client.site_settings()
        if not _verify_blog_url(str(identity.get("url") or ""),
                                route["identifier"]):
            raise WordPressAutoDraftError("wordpress_registered_site_mismatch")
    history=wp_client.list_posts(include_unpublished=execute_draft)
    def handle(cat):
        plan=select_next(cat,site_key=site_key,topic=topic,
            posts=history,requested_total=requested)
        if plan["status"]!="READY_FOR_DRAFT_REVIEW":
            return {"mode":"DRAFT_ONLY" if execute_draft else "DRY_RUN",
                    "status":plan["status"],
                    "wordpress_posts_created":0,"publication_calls":0}
        if not execute_draft:
            return {"mode":"DRY_RUN","status":"READY_FOR_DRAFT_REVIEW",
                "real_product_image":True,"exact_campaign":True,
                "internal_links":len(plan["related"]),
                "wordpress_posts_created":0,"publication_calls":0}
        generator=writer or generate_original_paragraphs
        # O modelo pode devolver alegação arriscada de forma intermitente.
        # Só refazer a redação gerada por IA (nunca POST/afiliado/R2);
        # manter TODOS os gates e recusar após no máximo 3 tentativas.
        content=None
        for attempt in range(3 if writer is None else 1):
            try:
                paragraphs=generator(
                    product_name=plan["title"],topic=topic,
                    account_id=os.getenv("CLOUDFLARE_ACCOUNT_ID",""),
                    api_token=os.getenv("CLOUDFLARE_API_TOKEN",""))
                content=compose_article(plan,paragraphs,
                    site_url=route["identifier"])
                break
            except WordPressAutoDraftError as error:
                if (writer is not None or attempt==2 or
                        not str(error).startswith("wordpress_editorial_")):
                    raise
        if content is None:
            raise WordPressAutoDraftError("wordpress_editorial_generation_blocked")
        # Evitar corrida com outra execução e alterações durante a geração.
        recent=wp_client.list_posts(include_unpublished=True)
        last=select_next(cat,site_key=site_key,topic=topic,
            posts=recent,requested_total=requested)
        if (last.get("status")!="READY_FOR_DRAFT_REVIEW"
            or last.get("product_key")!=plan["product_key"]):
            raise WordPressAutoDraftError("wordpress_draft_race_detected")
        created=wp_client.create_draft(
            title=_draft_title(plan["title"]),
            slug=plan["slug"],content=content)
        reread=wp_client.get_post(created["id"])
        raw_html=_html_text(reread)
        if (reread.get("status")!="draft" or
            reread.get("slug")!=plan["slug"] or
            plan["product_key"] not in raw_html or
            "Ver produto na Shopee" not in raw_html):
            raise WordPressAutoDraftError("wordpress_draft_readback_failed")
        return {"mode":"DRAFT_ONLY","status":"DRAFT_CREATED",
            "wordpress_posts_created":1,"publication_calls":0,
            "real_product_image":True,"exact_campaign":True,
            "internal_links":len(plan["related"])}
    if catalog is not None:
        return handle(catalog)
    with tempfile.TemporaryDirectory(prefix="v31-wp-autodraft-") as td:
        local=Path(td)/"catalog.sqlite3"
        if not R2State.from_env().restore_to(local):
            raise WordPressAutoDraftError("r2_catalog_missing")
        verify_database(local)
        with Catalog(local) as cat:
            return handle(cat)


def main()->int:
    parser=argparse.ArgumentParser(
        description="V31 WordPress UNIVERSAL: preview ou rascunho, NUNCA LIVE")
    parser.add_argument("--site-key")
    parser.add_argument("--topic",help="Preview apenas, nunca autoriza POST")
    parser.add_argument("--execute-draft",action="store_true")
    args=parser.parse_args()
    try:
        from .site_request_queue import autonomous_sites_for_writes
        migrated = autonomous_sites_for_writes() if args.execute_draft else set()
        site_key=args.site_key
        if site_key in migrated:
            print("AUTONOMOUS_DRAFT_ROUTE_USE_NEW_WORKFLOW")
            return 0
        if not site_key:
            requests=sorted(r["site_key"] for r in load_requests()
                if r["platform"]=="wordpress" and r["site_key"] not in migrated)
            if not requests:
                print("V31_C60_NO_REAL_WORDPRESS_REQUESTS")
                return 0
            site_key=requests[date.today().toordinal()%len(requests)]
        if args.execute_draft and args.topic:
            raise WordPressAutoDraftError("override_cannot_authorize_write")
        result=run(site_key=site_key,preview_topic=args.topic,
                   execute_draft=args.execute_draft)
        print("V31_C60_UNIVERSAL_WORDPRESS_SAFE_PASS")
        print(json.dumps(result,sort_keys=True,ensure_ascii=False))
        return 0
    except Exception as error:
        # Diagnóstico sem revelar body, URL de produto, token ou credenciais.
        # Erros próprios do writer são somente códigos estáticos controlados.
        code=str(error) if isinstance(error,WordPressAutoDraftError) else ""
        if not re.fullmatch(r"[a-z0-9_]{3,100}",code):
            code=type(error).__name__
        print("V31_C60_WORDPRESS_SAFE_FAILED_"+code)
        return 3


if __name__=="__main__":
    raise SystemExit(main())
