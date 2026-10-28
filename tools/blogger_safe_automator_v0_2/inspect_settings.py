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

SETTINGS_RE = re.compile(r"^(Configura[cç][oõ]es|Settings)$", re.I)


def norm(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


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
    """Abre Configurações pela própria UI do Blogger.

    Evita navegar diretamente por hrefs relativos usados pelo SPA do Blogger.
    Esta ação apenas navega; não altera nenhuma configuração.
    """
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

    # Alguns estados do SPA não atualizam a URL imediatamente. Aceita a tela
    # somente se um marcador inequívoco de Configurações estiver visível.
    markers = page.get_by_text(
        re.compile(r"^(B[aá]sicas|Privacidade|Publica[cç][aã]o|HTTPS|Rastreadores e indexa[cç][aã]o)$", re.I),
        exact=True,
    )
    if first_visible(markers) is None:
        raise bp.SafeAutomationError(
            "A navegação para Configurações não pôde ser confirmada. Nenhuma alteração foi feita."
        )


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

        open_settings(page, blog_id)
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
