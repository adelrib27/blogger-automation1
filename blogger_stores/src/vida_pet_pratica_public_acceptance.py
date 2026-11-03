#!/usr/bin/env python3
from __future__ import annotations

import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen

from blogger_policy_guard import require_store_html_allowed

BASE = "https://vida-pet-pratica.blogspot.com"
STORE_PAGE = f"{BASE}/p/loja.html"
STORE_POST_ID = "7332800716046515902"
ARTICLES = [
    "como-escolher-peitoral-e-guia-para",
    "enriquecimento-ambiental-para-gatos",
    "como-montar-um-cantinho-confortavel",
]
PET_TOKENS = [
    "bls-passeio-transporte", "bls-alimentacao-rotina", "bls-higiene-organizacao",
    "bls-conforto-descanso", "bls-brinquedos-enriquecimento",
]
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/131.0 Safari/537.36"


def with_probe(url: str, probe: str, attempt: int) -> str:
    parts = urlsplit(url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query["e2e_probe"] = f"{probe}-{int(time.time())}-{attempt}"
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


def fetch_200(url: str, probe: str, attempts: int = 10) -> str:
    last = ""
    for attempt in range(1, attempts + 1):
        target = with_probe(url, probe, attempt)
        req = Request(target, headers={"User-Agent": UA, "Cache-Control": "no-cache", "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.7"})
        try:
            with urlopen(req, timeout=40) as response:
                code = int(response.status)
                raw = response.read().decode("utf-8", errors="ignore")
            print(f"{probe}_HTTP_{attempt}: {code}")
            if code == 200:
                return raw
            last = f"HTTP {code}"
        except HTTPError as exc:
            last = f"HTTP {exc.code}"
            print(f"{probe}_HTTP_{attempt}: {exc.code}")
            if exc.code not in (429, 500, 502, 503, 504):
                raise
        except URLError as exc:
            last = f"URL error {exc.reason}"
            print(f"{probe}_URL_ERROR_{attempt}: {exc.reason}")
        if attempt < attempts:
            time.sleep(12 if "429" in last else 5)
    raise RuntimeError(f"{probe}: não obteve HTTP 200 após {attempts} tentativas ({last}).")


def validate_store_page() -> None:
    raw = fetch_200(STORE_PAGE, "PET_PAGE")
    require_store_html_allowed(raw, expected_products=20, expected_hero=12)
    store = raw.count("data-item-id=")
    hero = raw.count("data-hero-item-id=")
    rels = raw.count('rel="nofollow sponsored noopener"')
    if (store, hero) != (20, 12) or rels < 32:
        raise RuntimeError(f"Page LOJA inválida: store={store} hero={hero} rels={rels}")
    required = [
        "emporio-revisao-visual-20-modelo-final",
        "BLOGGER_MODELO_V20_BRAND_DESCRIPTION_FEED_RUNTIME",
        "BLOGGER_STORE_AUTO_START", "BLOGGER_STORE_AUTO_END",
        "BLOGGER_NEW_STORE_PAGE_THEME_FRAME_PRESERVED", 'id="blogger-new-store-page-carousel-fix"',
        "BLOGGER_LIQ_LAYOUT_PATCH_START", "BLOGGER_LIQ_LAYOUT_PATCH_END", 'id="blsSlider"',
        'class="bls-slide is-active"', ".bls-slide{display:none", ".bls-slide.is-active{display:grid",
        'class="bls-nav bls-prev"', 'class="bls-nav bls-next"', 'id="blsDots"',
        "document.addEventListener('click'", "closest('.bls-next')", "closest('.bls-prev')",
        "event.stopImmediatePropagation()", "new MutationObserver", "pageCarouselDelegated",
        "BLOGGER_STORE_SHARE_CARD_START", "BLOGGER_STORE_SHARE_CARD_END", 'id="blogger-store-share-card"',
        'data-blogger-store-share-card="1"', 'id="blogger-store-share-button"', 'aria-label="Compartilhar"',
        "navigator.share", "navigator.clipboard", "Vida Pet Prática", *PET_TOKENS,
    ]
    missing = [token for token in required if token not in raw]
    if missing:
        raise RuntimeError(f"Contrato visual/pet público incompleto: {missing}")
    forbidden = [
        'id="blogger-new-store-page-surface-fix"',
        ".bg-photo-container{display:none!important",
        ".bg-photo{display:none!important",
        "background:transparent!important;border:0!important;box-shadow:none!important",
        "casa-pratica-lab-20261102.blogspot.com", "conectaachados.blogspot.com",
        "Cozinha &amp; Eletroportáteis", "Tecnologia &amp; Acessórios",
    ]
    bad = [token for token in forbidden if token in raw]
    if bad:
        raise RuntimeError(f"Desvio visual/identidade de outro blog vazou para a Page: {bad}")
    if "document.getElementById('blsSlider')" in raw:
        raise RuntimeError("Controlador legado do carousel reapareceu na Page pública.")
    print("VIDA_PET_PRATICA_PUBLIC_PAGE_PASS: /p/loja.html 20+12 + Policy Guard + identidade pet + Tema V20 enquadrado + carousel/share.")


def validate_home_and_articles() -> None:
    home = fetch_200(f"{BASE}/?m=1", "PET_HOME")
    if f"post-wrapper hero post-{STORE_POST_ID}" in home or f"post-wrapper not-hero post-{STORE_POST_ID}" in home:
        raise RuntimeError("Store Post técnico continua renderizado na home.")
    if "BLOGGER_MODELO_V20_BRAND_DESCRIPTION_FEED_RUNTIME" not in home or "feed.subtitle" not in home:
        raise RuntimeError("Tema público não contém runtime de descrição isolada por blog.")
    for slug in ARTICLES:
        path = f"/2026/11/{slug}.html"
        if path not in home:
            raise RuntimeError(f"Artigo ausente da home: {path}")
        raw = fetch_200(f"{BASE}{path}", f"PET_ARTICLE_{slug[:14].upper().replace('-', '_')}")
        if "<img" not in raw or "images.unsplash.com" not in raw:
            raise RuntimeError(f"Artigo sem imagem editorial validável: {path}")
    print("VIDA_PET_PRATICA_HOME_EDITORIAL_PASS: staging fora da home; 3/3 artigos presentes e com imagens; identidade V20 runtime ativa.")


def main() -> int:
    validate_store_page()
    validate_home_and_articles()
    print("BLOGGER_NEW_BLOG_V20_E2E_ACCEPTED: Vida Pet Prática")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"VIDA_PET_PRATICA_PUBLIC_E2E_FAILED: {exc}", file=sys.stderr)
        raise
