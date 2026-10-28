#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

import browser_provision as bp
from playwright.sync_api import sync_playwright

CDP_URL = bp.DEFAULT_CDP_URL
OUT_DIR = Path("logs/browser_diagnostics")

KEYWORDS = (
    "título", "title",
    "descrição", "description",
    "idioma do blog", "blog language",
    "visível para mecanismos de pesquisa", "visible to search engines",
    "redirecionamento para https", "https redirect",
    "endereço do blog", "blog address",
    "domínio personalizado", "custom domain",
    "rastreadores e indexação", "crawlers and indexing",
    "robots.txt", "robots",
    "tags de cabeçalho de robôs personalizadas", "custom robots header tags",
    "tags de robôs personalizadas", "custom robots tags",
    "favicon",
)


def norm(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def find_settings_href(page, blog_id: str) -> str | None:
    links = page.locator('a[href*="settings"]')
    fallback = None
    for i in range(links.count()):
        item = links.nth(i)
        try:
            href = item.get_attribute("href") or ""
            if not href:
                continue
            if fallback is None:
                fallback = href
            if blog_id in href:
                return href
        except Exception:
            continue
    return fallback


def inspect_settings(page) -> dict:
    data = page.evaluate(
        r"""(keywords) => {
          const norm = (v) => String(v || '').trim().replace(/\s+/g, ' ');
          const lower = (v) => norm(v).toLocaleLowerCase();
          const wanted = keywords.map(lower);
          const visible = (el) => {
            const r = el.getBoundingClientRect();
            const s = getComputedStyle(el);
            return r.width > 0 && r.height > 0 && s.display !== 'none' && s.visibility !== 'hidden';
          };
          const meta = (el) => {
            const r = el.getBoundingClientRect();
            return {
              tag: el.tagName,
              role: el.getAttribute('role') || '',
              text: norm(el.innerText || el.textContent).slice(0, 240),
              aria: norm(el.getAttribute('aria-label')).slice(0, 240),
              aria_checked: el.getAttribute('aria-checked') || '',
              aria_disabled: el.getAttribute('aria-disabled') || '',
              checked: 'checked' in el ? !!el.checked : null,
              disabled: 'disabled' in el ? !!el.disabled : null,
              tabindex: el.getAttribute('tabindex') || '',
              href: (el.getAttribute('href') || '').slice(0, 300),
              width: Math.round(r.width),
              height: Math.round(r.height)
            };
          };

          const controls = [];
          for (const el of document.querySelectorAll('input,button,a,[role="button"],[role="switch"],[role="checkbox"],[aria-checked]')) {
            if (!visible(el)) continue;
            const m = meta(el);
            const hay = lower(`${m.text} ${m.aria}`);
            if (wanted.some(k => hay.includes(k)) || m.aria_checked !== '') controls.push(m);
          }

          const matches = [];
          const seen = new Set();
          for (const el of document.querySelectorAll('body *')) {
            if (!visible(el)) continue;
            const text = norm(el.innerText || el.textContent);
            if (!text || text.length > 500) continue;
            const hay = lower(text);
            if (!wanted.some(k => hay.includes(k))) continue;
            const key = `${el.tagName}|${text}`;
            if (seen.has(key)) continue;
            seen.add(key);
            const parent = el.parentElement;
            matches.push({
              ...meta(el),
              parent: parent ? meta(parent) : null
            });
            if (matches.length >= 100) break;
          }

          return {controls, matches};
        }""",
        list(KEYWORDS),
    )
    return data


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        _, context = bp.connect_official_chrome(p, CDP_URL)
        page = bp.select_page(context)
        bp.require_blogger_session(page)

        blog_id = bp.extract_current_blog_id(page)
        if not blog_id:
            raise bp.SafeAutomationError("Não foi possível identificar o Blog ID atual.")

        settings_href = find_settings_href(page, blog_id)
        if not settings_href:
            raise bp.SafeAutomationError(
                "Link de Configurações não foi localizado com segurança. Nenhuma alteração foi feita."
            )

        page.goto(settings_href, wait_until="domcontentloaded", timeout=60_000)
        page.wait_for_timeout(1500)

        snapshot = inspect_settings(page)
        result = {
            "ok": True,
            "read_only": True,
            "blog_id": blog_id,
            "settings_url": bp.sanitize_url(page.url),
            "controls": snapshot.get("controls", []),
            "matches": snapshot.get("matches", []),
            "message": "Somente leitura. Nenhuma configuração foi alterada.",
        }

        (OUT_DIR / "settings_inspection.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
