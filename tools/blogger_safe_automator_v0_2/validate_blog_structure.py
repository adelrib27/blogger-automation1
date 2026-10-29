#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import browser_provision as bp
from playwright.sync_api import sync_playwright
from validate_core_settings_profile import select_expected_blog_page, validate_expected_blog_id

ROUTES = ("themes", "layout", "pages", "posts")
OUT_DIR = Path("logs/browser_diagnostics")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Diagnóstico somente leitura de Tema, Layout, Páginas e Postagens do Blogger."
    )
    parser.add_argument(
        "--expected-blog-id",
        required=True,
        help="Blog ID obrigatório; qualquer outro blog é bloqueado.",
    )
    return parser


def target_url(route: str, blog_id: str) -> str:
    if route not in ROUTES:
        raise bp.SafeAutomationError(f"Rota de diagnóstico não permitida: {route}")
    return f"https://draft.blogger.com/blog/{route}/{blog_id}"


def assert_expected_blog(page, expected_blog_id: str) -> None:
    current = bp.extract_current_blog_id(page)
    if current != expected_blog_id:
        raise bp.SafeAutomationError(
            f"Blog ID inesperado durante diagnóstico: esperado {expected_blog_id}, obtido {current or 'nenhum'}."
        )


def page_snapshot(page) -> dict:
    return page.evaluate(
        r"""() => {
          const norm = v => String(v || '').trim().replace(/\s+/g, ' ');
          const visible = el => {
            const r = el.getBoundingClientRect();
            const s = getComputedStyle(el);
            return r.width > 0 && r.height > 0 && s.display !== 'none' && s.visibility !== 'hidden';
          };
          const safeHref = raw => {
            if (!raw) return '';
            try { const u = new URL(raw, location.href); return `${u.origin}${u.pathname}`; }
            catch (_) { return ''; }
          };
          const nodes = [];
          for (const el of document.querySelectorAll('button,a,input,textarea,select,[contenteditable="true"],[role]')) {
            if (!visible(el)) continue;
            const r = el.getBoundingClientRect();
            nodes.push({
              tag: el.tagName,
              role: el.getAttribute('role') || '',
              text: norm(el.innerText || el.value || el.textContent).slice(0, 300),
              aria: norm(el.getAttribute('aria-label')).slice(0, 200),
              title: norm(el.getAttribute('title')).slice(0, 200),
              href: safeHref(el.getAttribute('href') || ''),
              type: el.getAttribute('type') || '',
              tabindex: el.getAttribute('tabindex') || '',
              disabled: el.matches(':disabled') || el.getAttribute('aria-disabled') === 'true',
              x: Math.round(r.x), y: Math.round(r.y), width: Math.round(r.width), height: Math.round(r.height)
            });
          }
          return {
            title: document.title,
            body_text: norm(document.body?.innerText || '').slice(0, 12000),
            nodes: nodes.slice(0, 700)
          };
        }"""
    )


def execute_diagnostic(expected_blog_id: str, *, cdp_url: str = bp.DEFAULT_CDP_URL) -> dict:
    expected_blog_id = validate_expected_blog_id(expected_blog_id)
    safe_cdp = bp.validate_cdp_url(cdp_url, allow_remote=False)
    original_url = None
    result = {
        "ok": True,
        "read_only": True,
        "expected_blog_id": expected_blog_id,
        "routes": {},
    }

    with sync_playwright() as p:
        browser, context = bp.connect_official_chrome(p, safe_cdp)
        page = select_expected_blog_page(context, expected_blog_id)
        original_url = page.url
        assert_expected_blog(page, expected_blog_id)

        try:
            for route in ROUTES:
                url = target_url(route, expected_blog_id)
                page.goto(url, wait_until="domcontentloaded", timeout=60_000)
                page.wait_for_timeout(1500)
                assert_expected_blog(page, expected_blog_id)
                snap = page_snapshot(page)
                result["routes"][route] = {
                    "url": bp.sanitize_url(page.url),
                    "title": snap["title"],
                    "body_text": snap["body_text"],
                    "nodes": snap["nodes"],
                }
        finally:
            if original_url and bp.extract_blog_id_from_url(original_url) == expected_blog_id:
                try:
                    page.goto(original_url, wait_until="domcontentloaded", timeout=60_000)
                    page.wait_for_timeout(600)
                except Exception:
                    pass

        result["browser_connected"] = browser.is_connected()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / f"blog_structure_{expected_blog_id}.json"
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    result["diagnostics_file"] = str(out_path.resolve())
    result["message"] = (
        "Somente leitura. Tema, Layout, Páginas e Postagens foram inspecionados; "
        "nenhum botão de salvar/publicar foi acionado."
    )
    return result


def main() -> int:
    args = build_parser().parse_args()
    result = execute_diagnostic(args.expected_blog_id)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
