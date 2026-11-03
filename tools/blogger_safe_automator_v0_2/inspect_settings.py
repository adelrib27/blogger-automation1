#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

import browser_provision as bp
from playwright.sync_api import sync_playwright

CDP_URL = bp.DEFAULT_CDP_URL
OUT_DIR = Path("logs/browser_diagnostics")
SETTINGS_RE = re.compile(r"^(Configura[cç][oõ]es|Settings)$", re.I)


def first_visible(locator):
    try:
        for i in range(locator.count()):
            item = locator.nth(i)
            try:
                if item.is_visible():
                    return item
            except Exception:
                continue
    except Exception:
        pass
    return None


def open_settings(page, blog_id: str) -> None:
    """Abre Configurações pela própria UI do Blogger, sem alterar valores."""
    candidates = [
        page.get_by_role("menuitem", name=SETTINGS_RE),
        page.get_by_text(SETTINGS_RE, exact=True),
        page.locator(f'a[href*="settings"][href*="{blog_id}"]'),
    ]

    target = None
    for candidate in candidates:
        target = first_visible(candidate)
        if target is not None:
            break

    if target is None:
        raise bp.SafeAutomationError(
            "Item Configurações não foi localizado com segurança. Nenhuma alteração foi feita."
        )

    try:
        target.click(timeout=5_000)
    except Exception:
        try:
            target.evaluate("el => el.click()")
        except Exception as exc:
            raise bp.SafeAutomationError(
                "Configurações foi localizado, mas não pôde ser aberto com segurança."
            ) from exc

    deadline_ms = 12_000
    elapsed = 0
    while elapsed < deadline_ms:
        current = page.url.lower()
        if "settings" in current and blog_id in current:
            return
        page.wait_for_timeout(250)
        elapsed += 250

    markers = page.get_by_text(
        re.compile(r"^(B[aá]sicas|Privacidade|Publica[cç][aã]o|HTTPS|Rastreadores e indexa[cç][aã]o)$", re.I),
        exact=True,
    )
    if first_visible(markers) is None:
        raise bp.SafeAutomationError(
            "A navegação para Configurações não pôde ser confirmada. Nenhuma alteração foi feita."
        )


def inspect_settings(page) -> dict:
    """Inventário integral e somente leitura da página Configurações.

    Não filtra por SEO. Coleta:
    - todos os controles interativos visíveis;
    - todas as linhas clicáveis/tabindex=0 visíveis;
    - candidatos a cabeçalhos de seção curtos.
    """
    return page.evaluate(
        r"""() => {
          const norm = (v) => String(v || '').trim().replace(/\s+/g, ' ');
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
              text: norm(el.innerText || el.textContent || el.value).slice(0, 500),
              aria: norm(el.getAttribute('aria-label')).slice(0, 300),
              aria_checked: el.getAttribute('aria-checked') || '',
              aria_disabled: el.getAttribute('aria-disabled') || '',
              checked: 'checked' in el ? !!el.checked : null,
              disabled: 'disabled' in el ? !!el.disabled : null,
              tabindex: el.getAttribute('tabindex') || '',
              type: el.getAttribute('type') || '',
              name: el.getAttribute('name') || '',
              href: (el.getAttribute('href') || '').slice(0, 300),
              width: Math.round(r.width),
              height: Math.round(r.height),
              top: Math.round(r.top + window.scrollY)
            };
          };

          const dedupe = (items) => {
            const seen = new Set();
            const out = [];
            for (const item of items) {
              const key = [
                item.tag, item.role, item.text, item.aria, item.aria_checked,
                item.tabindex, item.type, item.name, item.href, item.top
              ].join('|');
              if (seen.has(key)) continue;
              seen.add(key);
              out.push(item);
            }
            return out;
          };

          const controls = [];
          const controlSelector = [
            'input', 'textarea', 'select', 'button', 'a[href]',
            '[role="button"]', '[role="switch"]', '[role="checkbox"]',
            '[role="radio"]', '[role="combobox"]', '[role="listbox"]',
            '[role="menuitem"]', '[aria-checked]'
          ].join(',');
          for (const el of document.querySelectorAll(controlSelector)) {
            if (!visible(el)) continue;
            controls.push(meta(el));
          }

          const rows = [];
          for (const el of document.querySelectorAll('[tabindex="0"], [role="button"], [role="checkbox"], [role="switch"]')) {
            if (!visible(el)) continue;
            const m = meta(el);
            if (!m.text && !m.aria) continue;
            rows.push(m);
          }

          const sectionCandidates = [];
          for (const el of document.querySelectorAll('h1,h2,h3,h4,h5,h6,div,span')) {
            if (!visible(el)) continue;
            const text = norm(el.innerText || el.textContent);
            if (!text || text.length > 90) continue;
            const childText = [...el.children].map(c => norm(c.innerText || c.textContent)).join(' ');
            if (childText && childText === text) continue;
            const style = getComputedStyle(el);
            const weight = parseInt(style.fontWeight || '400', 10) || 400;
            const size = parseFloat(style.fontSize || '0') || 0;
            if (!/^H[1-6]$/.test(el.tagName) && weight < 500 && size < 18) continue;
            sectionCandidates.push(meta(el));
          }

          return {
            controls: dedupe(controls).sort((a, b) => a.top - b.top),
            rows: dedupe(rows).sort((a, b) => a.top - b.top),
            section_candidates: dedupe(sectionCandidates).sort((a, b) => a.top - b.top),
            page_text: norm(document.body.innerText).slice(0, 30000)
          };
        }"""
    )


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        _, context = bp.connect_official_chrome(p, CDP_URL)
        page = bp.select_page(context)
        bp.require_blogger_session(page)

        blog_id = bp.extract_current_blog_id(page)
        if not blog_id:
            raise bp.SafeAutomationError("Não foi possível identificar o Blog ID atual.")

        open_settings(page, blog_id)
        page.wait_for_timeout(1500)

        snapshot = inspect_settings(page)
        result = {
            "ok": True,
            "read_only": True,
            "inventory_mode": "full",
            "blog_id": blog_id,
            "settings_url": bp.sanitize_url(page.url),
            "control_count": len(snapshot.get("controls", [])),
            "row_count": len(snapshot.get("rows", [])),
            "section_candidate_count": len(snapshot.get("section_candidates", [])),
            "controls": snapshot.get("controls", []),
            "rows": snapshot.get("rows", []),
            "section_candidates": snapshot.get("section_candidates", []),
            "page_text": snapshot.get("page_text", ""),
            "message": "Inventário completo em somente leitura. Nenhuma configuração foi alterada.",
        }

        (OUT_DIR / "settings_full_inventory.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
