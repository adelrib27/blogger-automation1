#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from googleapiclient.errors import HttpError

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from criar_rascunho import criar_servico_blogger  # noqa: E402

SOURCE_BLOG_ID = "9144338307944682868"
SOURCE_POST_ID = "115613719594316807"
SOURCE_PAGE_ID = "8344701886444887322"
TARGET_FILE = Path(os.getenv("BLOGGER_STORE_CLONE_TARGET", ROOT / "blogger_store_clone" / "target.json"))

KNOWN_TARGETS = {
    "1426630233929943394": ("Achados para Casa", "https://achadosparacasa2026.blogspot.com"),
    "1719259388907013414": ("Conecta Achados", "https://conectaachados.blogspot.com"),
    "2562496977098748229": ("Achadinhos de Beleza", "https://canal-attitude.blogspot.com"),
    "7487888217273188851": ("Radar Tech BR", "https://portalradartechbr.blogspot.com"),
    "2858597309582499028": ("Moda e Ofertas", "https://moda-ofertas.blogspot.com"),
    "3552757910439359679": ("Cozinha Sem Complicação", "https://cozinha-sem-complicacao.blogspot.com"),
    "7757953554206491487": ("Robô Aspirador WAP Robot W90", "https://robo-aspirador-wap-w90.blogspot.com"),
    "9113728635217260884": ("Air Fryer Elgin Cube Fry 4,2 L", "https://airfryer-elgin-cube-fry-42l.blogspot.com"),
    "4473989735719981382": ("Ventilador Mondial Super Power VSP-40-B 40cm", "https://ventilador-mondial-vsp-40-b.blogspot.com"),
    "6319734511998091378": ("Tá Na Moda | Morte Súbita Lola 450g", "https://tanamoda-mascara-lola.blogspot.com"),
    "5271798990390532475": ("Liquidificador Philips Walita RI2242", "https://liquidificador-philips-walita-ri2242.blogspot.com"),
    "8658632621591002634": ("Liquidificador Britânia 1400W 3L 12 Velocidades BLQ1300P", "https://liquidificador-britania-blq1300p.blogspot.com"),
    "1453188702831337099": ("Guia de Achados & Ofertas", "https://guia-de-achados-e-ofertas.blogspot.com"),
    "7527651041649593600": ("Achados que Valem", "https://achados-que-valem.blogspot.com"),
    "5151950717041967683": ("Escolha Certa Online", "https://escolha-certa-online.blogspot.com"),
    "4177382081459143374": ("Casa em Ordem", "https://casa-em-ordem-pratica.blogspot.com"),
    "4830103887652146866": ("Estilo no Dia a Dia", "https://estilo-no-dia-a-dia-0071220800-2.blogspot.com"),
}


def api_call(factory, label: str):
    delays = [0, 8, 16, 32, 64]
    for attempt, delay in enumerate(delays, start=1):
        if delay:
            print(f"RATE_LIMIT_BACKOFF label={label} attempt={attempt} sleep={delay}s", flush=True)
            time.sleep(delay)
        try:
            return factory().execute()
        except HttpError as exc:
            status = int(getattr(exc.resp, "status", 0) or 0)
            body = str(getattr(exc, "content", b""))
            retryable = status == 429 or (status == 403 and "rateLimit" in body)
            if not retryable or attempt == len(delays):
                raise
    raise RuntimeError(f"Falha inesperada em {label}")


def list_all(request_factory, label: str) -> list[dict]:
    items: list[dict] = []
    token = None
    while True:
        response = api_call(lambda: request_factory(token), label)
        items.extend(response.get("items", []) or [])
        token = response.get("nextPageToken")
        if not token:
            return items


def exact_lojas(items: list[dict]) -> list[dict]:
    return [x for x in items if str(x.get("title") or "").strip().lower() == "loja"]


def public_fetch(url: str) -> tuple[str, str]:
    delays = [0, 5, 10, 20, 40]
    last_error: Exception | None = None
    for attempt, delay in enumerate(delays, start=1):
        if delay:
            print(f"PUBLIC_BACKOFF attempt={attempt} sleep={delay}s", flush=True)
            time.sleep(delay)
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 StoreCloneValidator/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=40) as response:
                body = response.read().decode("utf-8", errors="ignore")
                return response.geturl(), body
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code not in (429, 503) or attempt == len(delays):
                raise
            print(f"PUBLIC_RETRY status={exc.code} attempt={attempt}", flush=True)
        except urllib.error.URLError as exc:
            last_error = exc
            if attempt == len(delays):
                raise
            print(f"PUBLIC_RETRY network_error attempt={attempt}", flush=True)
    if last_error:
        raise last_error
    raise RuntimeError("Falha inesperada na validação pública")


def main() -> int:
    cfg = json.loads(TARGET_FILE.read_text(encoding="utf-8"))
    target_blog_id = str(cfg.get("blog_id") or "").strip()
    if not target_blog_id.isdigit() or target_blog_id == SOURCE_BLOG_ID:
        raise RuntimeError("target.json inválido ou aponta para o próprio Vitrine Prática")

    blogger = criar_servico_blogger()
    source_post = api_call(lambda: blogger.posts().get(blogId=SOURCE_BLOG_ID, postId=SOURCE_POST_ID), "source-post")
    source_page = api_call(lambda: blogger.pages().get(blogId=SOURCE_BLOG_ID, pageId=SOURCE_PAGE_ID), "source-page")

    known = KNOWN_TARGETS.get(target_blog_id)
    if known:
        target_title, target_home = known
    else:
        target_blog = api_call(lambda: blogger.blogs().get(blogId=target_blog_id), "target-blog")
        target_title = str(target_blog.get("name") or target_blog.get("title") or target_blog_id).strip()
        target_home = str(target_blog.get("url") or "").rstrip("/")

    if not target_home.startswith("http"):
        raise RuntimeError("Blog alvo sem URL pública válida")
    target_store_page_url = target_home + "/p/loja.html"

    posts = list_all(
        lambda token: blogger.posts().list(blogId=target_blog_id, maxResults=100, status=["LIVE"], pageToken=token),
        "target-posts-list",
    )
    lojas = exact_lojas(posts)
    if len(lojas) > 1:
        raise RuntimeError(f"Mais de um post LIVE Loja no alvo: {len(lojas)}")

    source_content = str(source_post.get("content") or "")
    if source_content.count('data-item-id=') != 20 or source_content.count('data-hero-item-id=') != 12:
        raise RuntimeError("Fonte Vitrine não está no contrato 20+12")
    required_source = (
        "BLOGGER_LIQ_LAYOUT_PATCH_START",
        "BLOGGER_LIQ_STORE_AUTO_START",
        "grid-template-columns:minmax(0,1fr)!important",
        "body.ga-post-page:has(.bls-page) .centered-bottom",
    )
    missing_source = [x for x in required_source if x not in source_content]
    if missing_source:
        raise RuntimeError(f"Fonte Vitrine sem contrato validado: {missing_source}")

    adapted = source_content.replace("https://vitrine-pratica.blogspot.com/p/loja.html", target_store_page_url)

    if lojas:
        target_post = lojas[0]
        target_post_id = str(target_post.get("id") or "")
        body = {"title": target_post.get("title") or "Loja", "content": adapted}
        if target_post.get("labels") is not None:
            body["labels"] = target_post.get("labels")
        target_post = api_call(
            lambda: blogger.posts().update(blogId=target_blog_id, postId=target_post_id, body=body),
            "target-post-update",
        )
        action_post = "updated"
    else:
        target_post = api_call(
            lambda: blogger.posts().insert(blogId=target_blog_id, isDraft=False, body={"title": "Loja", "content": adapted, "labels": ["Loja"]}),
            "target-post-insert",
        )
        target_post_id = str(target_post.get("id") or "")
        action_post = "created"

    target_post_url = str(target_post.get("url") or "")
    if not target_post_id or not target_post_url.startswith("http"):
        raise RuntimeError("Post Loja alvo sem id/url após escrita")

    pages = list_all(
        lambda token: blogger.pages().list(blogId=target_blog_id, maxResults=100, status=["LIVE"], pageToken=token),
        "target-pages-list",
    )
    loja_pages = exact_lojas(pages)
    if len(loja_pages) > 1:
        raise RuntimeError(f"Mais de uma página LIVE Loja no alvo: {len(loja_pages)}")

    source_page_content = str(source_page.get("content") or "")
    page_content = source_page_content.replace(
        "https://vitrine-pratica.blogspot.com/2026/11/loja.html",
        target_post_url,
    ).replace(
        "https://vitrine-pratica.blogspot.com/p/loja.html",
        target_store_page_url,
    )

    if loja_pages:
        target_page_id = str(loja_pages[0].get("id") or "")
        target_page = api_call(
            lambda: blogger.pages().update(blogId=target_blog_id, pageId=target_page_id, body={"title": loja_pages[0].get("title") or "LOJA", "content": page_content}),
            "target-page-update",
        )
        action_page = "updated"
    else:
        target_page = api_call(
            lambda: blogger.pages().insert(blogId=target_blog_id, isDraft=False, body={"title": "LOJA", "content": page_content}),
            "target-page-insert",
        )
        target_page_id = str(target_page.get("id") or "")
        action_page = "created"

    if not target_page_id:
        target_page_id = str(target_page.get("id") or "")
    target_page_url = str(target_page.get("url") or target_store_page_url)

    verify_post = api_call(lambda: blogger.posts().get(blogId=target_blog_id, postId=target_post_id), "verify-post")
    verify_raw = str(verify_post.get("content") or "")
    checks = {
        "cards20": verify_raw.count('data-item-id=') == 20,
        "hero12": verify_raw.count('data-hero-item-id=') == 12,
        "bls": 'class="bls-page"' in verify_raw,
        "grid1col": "grid-template-columns:minmax(0,1fr)!important" in verify_raw,
        "sidebar_hidden": "body.ga-post-page:has(.bls-page) .sidebar-container" in verify_raw,
        "no_onclick": "onclick=" not in verify_raw,
        "target_store_url": target_store_page_url in verify_raw,
        "source_host_absent": "vitrine-pratica.blogspot.com" not in verify_raw,
    }
    bad = [k for k, v in checks.items() if not v]
    if bad:
        raise RuntimeError(f"Validação API do post falhou: {bad}")

    verify_page = api_call(lambda: blogger.pages().get(blogId=target_blog_id, pageId=target_page_id), "verify-page")
    verify_page_raw = str(verify_page.get("content") or "")
    if target_post_url not in verify_page_raw:
        raise RuntimeError("Página estável Loja não aponta para o post Loja atual")

    cache = int(time.time())
    final_post_url, public_html = public_fetch(target_post_url + ("&" if "?" in target_post_url else "?") + f"clone_validate={cache}")
    public_checks = {
        "theme_v20": "emporio-revisao-visual-20-modelo-final" in public_html,
        "cards20": public_html.count('data-item-id=') == 20,
        "hero12": public_html.count('data-hero-item-id=') == 12,
        "bls": 'class="bls-page"' in public_html,
        "grid1col": "grid-template-columns:minmax(0,1fr)!important" in public_html,
        "sidebar_hidden": "body.ga-post-page:has(.bls-page) .sidebar-container" in public_html,
        "target_store_url": target_store_page_url in public_html,
    }
    bad_public = [k for k, v in public_checks.items() if not v]
    if bad_public:
        raise RuntimeError(f"Validação pública do post falhou: {bad_public}")

    _, stable_html = public_fetch(target_page_url + ("&" if "?" in target_page_url else "?") + f"clone_validate={cache}")
    if target_post_url not in stable_html:
        raise RuntimeError("Validação pública da página estável falhou")

    result = {
        "status": "PASS",
        "blog_id": target_blog_id,
        "blog_title": target_title,
        "blog_url": target_home + "/",
        "post_id": target_post_id,
        "post_url": target_post_url,
        "page_id": target_page_id,
        "page_url": target_page_url,
        "post_action": action_post,
        "page_action": action_page,
        "cards": 20,
        "hero_cards": 12,
        "theme_v20": True,
        "grid_columns": 1,
        "sidebar_hidden": True,
        "final_public_post_url": final_post_url,
    }
    print("VITRINE_CLONE_PASS " + json.dumps(result, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
