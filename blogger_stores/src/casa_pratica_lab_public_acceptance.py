#!/usr/bin/env python3
from __future__ import annotations

import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit, urlunsplit, parse_qsl
from urllib.request import Request, urlopen

from blogger_policy_guard import require_store_html_allowed

BASE = "https://casa-pratica-lab-20261102.blogspot.com"
STORE_PAGE = f"{BASE}/p/loja.html"
STORE_POST_PATH = "/2026/11/loja.html"
STORE_POST = f"{BASE}{STORE_POST_PATH}"
ARTICLES = [
    "como-organizar-uma-cozinha-pequena-sem",
    "air-fryer-7-pontos-para-conferir-antes",
    "ventilador-ou-climatizador-qual-faz",
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


def validate_page_bridge() -> None:
    raw = fetch_200(STORE_PAGE, "LAB_PAGE")
    if STORE_POST not in raw or "window.location.replace" not in raw:
        raise RuntimeError("Page LOJA não é bridge/redirecionamento para o Store Post.")
    if "data-item-id=" in raw or "data-hero-item-id=" in raw:
        raise RuntimeError("Page LOJA ainda contém a vitrine diretamente.")
    print("CASA_PRATICA_LAB_PAGE_BRIDGE_PASS")


def validate_store_post() -> None:
    raw = fetch_200(STORE_POST, "LAB_STORE")
    require_store_html_allowed(raw, expected_products=20, expected_hero=12)
    store = raw.count("data-item-id=")
    hero = raw.count("data-hero-item-id=")
    rels = raw.count('rel="nofollow sponsored noopener"')
    if (store, hero) != (20, 12) or rels < 32:
        raise RuntimeError(f"Store Post inválido: store={store} hero={hero} rels={rels}")
    required = [
        "BLOGGER_LIQ_LAYOUT_PATCH_START",
        "BLOGGER_LIQ_LAYOUT_PATCH_END",
        'id="blsSlider"',
        'class="bls-slide is-active"',
        ".bls-slide{display:none",
        ".bls-slide.is-active{display:grid",
        'class="bls-nav bls-prev"',
        'class="bls-nav bls-next"',
        'id="blsDots"',
        "setInterval(()=>show(i+1),6000)",
        "bls-casa-organizacao",
        "bls-cozinha-eletroportateis",
        "bls-iluminacao-decoracao",
        "bls-clima-conforto",
        "bls-utilidades-rotina",
    ]
    missing = [token for token in required if token not in raw]
    if missing:
        raise RuntimeError(f"Contrato visual público incompleto: {missing}")
    print("CASA_PRATICA_LAB_PUBLIC_STORE_VISUAL_PASS: 20+12 + layout amplo + carousel.")


def validate_home_and_articles() -> None:
    home = fetch_200(f"{BASE}/?m=1", "LAB_HOME")
    if STORE_POST_PATH in home:
        raise RuntimeError("Store Post Loja continua visível/referenciado na home.")
    for slug in ARTICLES:
        path = f"/2026/11/{slug}.html"
        if path not in home:
            raise RuntimeError(f"Artigo ausente da home: {path}")
        raw = fetch_200(f"{BASE}{path}", f"LAB_ARTICLE_{slug[:16].upper().replace('-', '_')}")
        if "post-hero" not in raw:
            raise RuntimeError(f"Artigo sem imagem editorial post-hero: {path}")
    print("CASA_PRATICA_LAB_HOME_AND_EDITORIAL_AUDIT_PASS: Loja fora da home; 3/3 artigos presentes e com imagem.")


def main() -> int:
    validate_page_bridge()
    validate_store_post()
    validate_home_and_articles()
    print("CASA_PRATICA_LAB_PUBLIC_E2E_MATURE_PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"CASA_PRATICA_LAB_PUBLIC_E2E_FAILED: {exc}", file=sys.stderr)
        raise
