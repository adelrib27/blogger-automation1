#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

import browser_provision as bp
import validate_core_settings_profile as core
from playwright.sync_api import sync_playwright

CDP_URL = bp.DEFAULT_CDP_URL
OUT_DIR = Path("logs/browser_diagnostics")


def find_timezone_matches(page) -> list[dict]:
    return page.evaluate(
        r"""() => {
          const norm = v => String(v || '').trim().replace(/\s+/g, ' ');
          const visible = el => {
            const r = el.getBoundingClientRect();
            const s = getComputedStyle(el);
            return r.width > 0 && r.height > 0 && s.display !== 'none' && s.visibility !== 'hidden';
          };
          const wanted = /(GMT-03|Bras[ií]lia|S[aã]o Paulo|Sao Paulo)/i;
          const out = [];
          const seen = new Set();
          for (const el of document.querySelectorAll('[role="dialog"] *')) {
            if (!visible(el)) continue;
            const text = norm(el.innerText || el.textContent);
            const aria = norm(el.getAttribute('aria-label'));
            const hay = `${text} ${aria}`;
            if (!wanted.test(hay)) continue;
            if (!text && !aria) continue;
            const key = `${el.tagName}|${el.getAttribute('role') || ''}|${text}|${aria}`;
            if (seen.has(key)) continue;
            seen.add(key);
            const r = el.getBoundingClientRect();
            out.push({
              tag: el.tagName,
              role: el.getAttribute('role') || '',
              text: text.slice(0, 500),
              aria: aria.slice(0, 300),
              aria_selected: el.getAttribute('aria-selected') || '',
              tabindex: el.getAttribute('tabindex') || '',
              disabled: el.matches(':disabled') || el.getAttribute('aria-disabled') === 'true',
              width: Math.round(r.width),
              height: Math.round(r.height),
            });
          }
          return out;
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

        core.goto_settings(page, blog_id)
        current_timezone = core.row_text(page, "Fuso horário")
        opened = core.click_row_prefix(page, "Fuso horário")
        matches = find_timezone_matches(page) if opened else []
        core.close_overlay(page)

        result = {
            "ok": bool(opened and matches),
            "read_only": True,
            "blog_id": blog_id,
            "current_timezone": current_timezone,
            "target_matches": matches,
            "message": (
                "Somente leitura. O seletor de fuso horário foi aberto e fechado; "
                "nenhuma opção foi selecionada e nada foi salvo."
            ),
        }

        (OUT_DIR / "timezone_target.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
