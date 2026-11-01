#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import urljoin, urlparse

import browser_provision as bp
from run_with_cdp_resilience_v08 import connect_official_chrome_resilient

bp.connect_official_chrome = connect_official_chrome_resilient

MARKER = "emporio-revisao-visual-20-modelo-final"
STORE_MARKER = "BLOGGER_MODELO_V20_STORE_EXTENSION"
VISIBLE_NAV_MARKER = "BLOGGER_MODELO_V20_STORE_VISIBLE_NAV"
SOURCE_TITLE = "Guia de Achados & Ofertas"
SOURCE_URL = "https://guia-de-achados-e-ofertas.blogspot.com/"


def run(cmd: list[str]) -> None:
    shown = " ".join(f'"{x}"' if " " in x else x for x in cmd)
    print("\n>>> " + shown, flush=True)
    proc = subprocess.run(cmd, text=True, capture_output=True)
    if proc.stdout:
        print(proc.stdout.rstrip(), flush=True)
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip()
        if len(detail) > 2400:
            detail = detail[-2400:]
        name = Path(cmd[1]).name if len(cmd) > 1 else Path(cmd[0]).name
        raise SystemExit(f"Etapa V20 falhou em {name}: {detail or 'sem detalhe adicional'}")


def maybe_change_identity(python: str, here: Path, expected_blog_id: str, title: str, blog_url: str) -> None:
    # Migração pontual autorizada: preserva o mesmo Blog ID e valida a nova URL publicamente.
    target_id = "4473989735719981382"
    target_title = "Ventiladores em Foco"
    target_url = "https://ventiladores-em-foco.blogspot.com/"
    if str(expected_blog_id) != target_id or title != target_title or blog_url.rstrip("/") + "/" != target_url:
        return
    identity = here / "update_blog_identity_safe.py"
    if not identity.exists():
        raise SystemExit("Migração de identidade bloqueada: update_blog_identity_safe.py ausente no runtime.")
    host = (urlparse(target_url).hostname or "").lower()
    suffix = ".blogspot.com"
    if not host.endswith(suffix):
        raise SystemExit("Migração de identidade bloqueada: domínio Blogspot inválido.")
    address = host[:-len(suffix)]
    run([python, str(identity), "--expected-blog-id", target_id, "--title", target_title,
         "--address", address, "--confirm", "CHANGE BLOG IDENTITY"])


def try_normalize_existing(python: str, normalize_backup: Path, source: Path, output: Path) -> bool:
    if not source.exists() or source.stat().st_size < 1024:
        return False
    proc = subprocess.run(
        [python, str(normalize_backup), "--source", str(source), "--output", str(output)],
        text=True,
        capture_output=True,
    )
    if proc.returncode == 0 and output.exists() and output.stat().st_size >= 1024:
        print("\n>>> backup V20 existente reutilizado após validação/normalização segura", flush=True)
        if proc.stdout:
            print(proc.stdout.rstrip(), flush=True)
        return True
    return False


def public_runtime_probe(blog_url: str, expected_title: str) -> dict:
    cdp_url = bp.validate_cdp_url(bp.DEFAULT_CDP_URL, allow_remote=False)
    cdp = bp.probe_cdp(cdp_url)
    store_url = urljoin(blog_url.rstrip("/") + "/", "p/loja.html")
    with bp.sync_playwright() as playwright:
        _browser, context = bp.connect_official_chrome(playwright, cdp_url)
        page = context.new_page()
        try:
            response = page.goto(store_url, wait_until="domcontentloaded", timeout=60_000)
            page.wait_for_timeout(4_500)
            data = page.evaluate(
                r"""() => {
                  const norm = s => (s || '').replace(/\s+/g, ' ').trim();
                  const host = document.getElementById('ga-static-feed-host-v20');
                  const root = host || document;
                  const footer = document.querySelector('.ga-static-footer,.ga-post-footer,.ga-home-footer');
                  const footerNav = footer
                    ? [...footer.querySelectorAll('.ga-static-footer-links a,.ga-post-footer-links a,.ga-home-footer-links a')]
                        .map(a => norm(a.textContent)).filter(Boolean)
                    : [];
                  const brandNode = footer && footer.querySelector(
                    '.ga-static-footer-brand h3,.ga-post-footer-brand h3,.ga-home-footer-brand h3'
                  );
                  const headerNavs = [...document.querySelectorAll('nav')]
                    .map(nav => [...nav.querySelectorAll('a[href]')].map(a => norm(a.textContent)).filter(Boolean))
                    .filter(items => items.includes('LOJA'));
                  return {
                    path: location.pathname.replace(/\/+$/, '') || '/',
                    title: document.title || '',
                    static_page: document.body.classList.contains('ga-static-page'),
                    host_present: !!host,
                    host_html_length: host ? host.innerHTML.length : 0,
                    canonical_feed_source: document.documentElement.getAttribute('data-ga-static-page-feed-source') || '',
                    store_scope_present: !!root.querySelector('.ga-store-v20'),
                    bls_page_present: !!document.querySelector('.bls-page'),
                    card_count: root.querySelectorAll('[data-item-id]').length,
                    hero_card_count: document.querySelectorAll('[data-hero-item-id]').length,
                    category_count: root.querySelectorAll('.ca-category').length,
                    shopee_button_count: [...root.querySelectorAll('a[href]')].filter(a =>
                      /shopee/i.test(a.textContent || '') || /shopee/i.test(a.getAttribute('href') || '')
                    ).length,
                    footer_brand: brandNode ? norm(brandNode.textContent) : '',
                    footer_nav: footerNav,
                    header_navs: headerNavs,
                  };
                }"""
            )
            status = int(response.status) if response is not None else 0
        finally:
            page.close()

    data.update({"store_url": store_url, "http_status": status, "cdp_browser": cdp.get("browser")})
    if status == 404:
        data["store_page_available"] = False
        data["validation"] = "STORE_PAGE_NOT_CREATED_YET"
        return data
    if status and status >= 400:
        raise SystemExit(f"Validação pública V20 falhou: LOJA respondeu HTTP {status}.")

    data["store_page_available"] = True
    if not data.get("static_page"):
        path = str(data.get("path") or "")
        if (
            re.fullmatch(r"/\d{4}/\d{2}/loja\.html", path)
            and data.get("bls_page_present")
            and int(data.get("card_count") or 0) == 20
            and int(data.get("hero_card_count") or 0) == 12
        ):
            data["validation"] = "PUBLIC_RUNTIME_PASS_POST_STORE"
            return data
        raise SystemExit("Validação pública V20 falhou: /p/loja.html não renderizou página estática nem redirecionou para POST Loja validado 20+12.")
    if not data.get("host_present") or int(data.get("host_html_length") or 0) < 20:
        raise SystemExit("Validação pública V20 falhou: host estável da página estática não renderizou conteúdo.")
    if data.get("canonical_feed_source") != "canonical-host":
        raise SystemExit("Validação pública V20 falhou: corpo da página não veio do feed canônico no host estável.")
    footer_brand = str(data.get("footer_brand") or "").strip()
    if footer_brand and footer_brand != expected_title:
        raise SystemExit(f"Validação pública V20 falhou: marca do rodapé esperada {expected_title!r}, obtida {footer_brand!r}.")
    footer_nav = data.get("footer_nav") or []
    if "Início" in footer_nav and "LOJA" in footer_nav and footer_nav.index("LOJA") != footer_nav.index("Início") + 1:
        raise SystemExit("Validação pública V20 falhou: LOJA não está imediatamente após Início no rodapé.")
    data["validation"] = "PUBLIC_RUNTIME_PASS"
    return data


def main() -> int:
    p = argparse.ArgumentParser(description="Adota o TEMA MODELO V20 em um blog existente, preservando todos os posts.")
    p.add_argument("--expected-blog-id", required=True)
    p.add_argument("--blog-title", required=True)
    p.add_argument("--blog-url", required=True)
    p.add_argument("--palette", default="auto")
    p.add_argument("--confirm", required=True)
    args = p.parse_args()

    if args.confirm != "ADOPT MODEL V20":
        raise SystemExit('Confirmação inválida. Use exatamente: ADOPT MODEL V20')

    here = Path(__file__).resolve().parent
    root = here.parents[1]
    python = sys.executable
    maybe_change_identity(python, here, args.expected_blog_id, args.blog_title, args.blog_url)
    source_theme = root / "themes" / "blogger_emporio_v1_0" / "generated" / "theme.xml"
    template_theme = root / "themes" / "blogger_modelo_v20" / "theme.xml.tpl"
    rendered_theme = root / "themes" / "blogger_modelo_v20" / "rendered" / str(args.expected_blog_id) / "theme.xml"
    backup_theme = root.parent / "backups" / "blogger" / args.expected_blog_id / "theme-before-modelo-v20-adoption.xml"
    normalized_backup = backup_theme.with_name("theme-before-modelo-v20-adoption.normalized.xml")
    freeze = here / "freeze_modelo_v20_theme.py"
    render = here / "render_modelo_v20_theme.py"
    extend_store = here / "extend_modelo_v20_store.py"
    extend_visible_nav = here / "extend_modelo_v20_store_visible_nav.py"
    resilient = here / "run_with_cdp_resilience_v08.py"
    backup = here / "backup_theme_auto.py"
    normalize_backup = here / "normalize_blogger_backup_v08.py"
    apply = here / "apply_theme_auto.py"

    for required in (source_theme, freeze, render, extend_store, extend_visible_nav, resilient, backup, normalize_backup, apply):
        if not required.exists():
            raise SystemExit(f"Arquivo obrigatório ausente: {required}")

    if not template_theme.exists():
        template_theme.parent.mkdir(parents=True, exist_ok=True)
        run([python, str(freeze), "--source-theme", str(source_theme), "--source-title", SOURCE_TITLE,
             "--source-url", SOURCE_URL, "--output-template", str(template_theme)])
    else:
        print(f"Template V20 já existe: {template_theme}")

    rendered_theme.parent.mkdir(parents=True, exist_ok=True)
    run([python, str(render), "--template-theme", str(template_theme), "--blog-title", args.blog_title,
         "--blog-url", args.blog_url, "--output-theme", str(rendered_theme), "--palette", args.palette])
    run([python, str(extend_store), "--theme-path", str(rendered_theme)])
    run([python, str(extend_visible_nav), "--theme-path", str(rendered_theme)])

    backup_theme.parent.mkdir(parents=True, exist_ok=True)
    reused_backup = try_normalize_existing(python, normalize_backup, backup_theme, normalized_backup)
    if not reused_backup:
        run([python, str(resilient), "backup", "--expected-blog-id", args.expected_blog_id, "--output", str(backup_theme)])
        run([python, str(normalize_backup), "--source", str(backup_theme), "--output", str(normalized_backup)])

    run([python, str(resilient), "apply", "--expected-blog-id", args.expected_blog_id, "--theme-path", str(rendered_theme),
         "--backup-path", str(normalized_backup), "--public-url", args.blog_url, "--public-marker", MARKER,
         "--confirm", "APPLY THEME"])

    rendered_text = rendered_theme.read_text(encoding="utf-8")
    if STORE_MARKER not in rendered_text:
        raise SystemExit("Adoção V20 terminou sem a extensão LOJA no tema renderizado.")
    if VISIBLE_NAV_MARKER not in rendered_text:
        raise SystemExit("Adoção V20 terminou sem a extensão do menu LOJA visível.")

    runtime_validation = public_runtime_probe(args.blog_url, args.blog_title)

    print(json.dumps({
        "status": "BLOGGER_MODELO_V20_ADOPTED",
        "blog_id": args.expected_blog_id,
        "blog_title": args.blog_title,
        "blog_url": args.blog_url,
        "palette": args.palette,
        "template_theme": str(template_theme),
        "rendered_theme": str(rendered_theme),
        "backup_theme_original": str(backup_theme),
        "backup_theme_normalized": str(normalized_backup),
        "backup_reused": reused_backup,
        "public_marker": MARKER,
        "store_extension_marker": STORE_MARKER,
        "store_visible_nav_marker": VISIBLE_NAV_MARKER,
        "store_menu_path": "/p/loja.html",
        "store_menu_position": "after-home",
        "store_menu_target": "nav.ga-home-v6-nav",
        "store_menu_highlighted": True,
        "store_layout": {"max_width": 1280, "desktop_columns": 4, "tablet_columns": 2, "mobile_columns": 2},
        "store_sidebar_hidden_only": True,
        "existing_posts_policy": "PRESERVE_ALL",
        "posts_deleted": False,
        "posts_copied_from_reference": False,
        "public_runtime_validation": runtime_validation,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
