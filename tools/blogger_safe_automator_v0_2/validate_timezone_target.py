#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import browser_provision as bp
import validate_core_settings_profile as core
from playwright.sync_api import sync_playwright

CDP_URL = bp.DEFAULT_CDP_URL
OUT_DIR = Path("logs/browser_diagnostics")


def scan_timezone_dialog(page) -> dict:
    """Percorre somente por rolagem o seletor de fuso e procura GMT-03/Brasil.

    Não clica, não seleciona opção e não salva nada.
    """
    return page.evaluate(
        r"""async () => {
          const norm = v => String(v || '').trim().replace(/\s+/g, ' ');
          const wanted = /(GMT-03(?::00)?|Bras[ií]lia|S[aã]o Paulo|Sao Paulo)/i;
          const dialogs = [...document.querySelectorAll('[role="dialog"]')];
          const dialog = dialogs.find(el => /Fuso hor[aá]rio/i.test(norm(el.innerText || el.textContent)));
          if (!dialog) return {dialog_found:false, matches:[], scroll_steps:0, scrollables:0};

          const out = [];
          const seen = new Set();
          const collect = () => {
            for (const el of dialog.querySelectorAll('*')) {
              const text = norm(el.innerText || el.textContent);
              const aria = norm(el.getAttribute('aria-label'));
              const hay = `${text} ${aria}`;
              if (!wanted.test(hay) || (!text && !aria)) continue;
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
          };

          collect();

          const scrollables = [dialog, ...dialog.querySelectorAll('*')].filter(el => {
            const s = getComputedStyle(el);
            return el.scrollHeight > el.clientHeight + 4 && /(auto|scroll)/.test(s.overflowY);
          });

          let steps = 0;
          for (const scroller of scrollables) {
            const original = scroller.scrollTop;
            const max = Math.max(0, scroller.scrollHeight - scroller.clientHeight);
            const step = Math.max(120, Math.floor(scroller.clientHeight * 0.75));
            for (let pos = 0; pos <= max; pos += step) {
              scroller.scrollTop = Math.min(pos, max);
              scroller.dispatchEvent(new Event('scroll', {bubbles:true}));
              await new Promise(r => setTimeout(r, 45));
              collect();
              steps += 1;
              if (out.some(x => /Bras[ií]lia|S[aã]o Paulo|Sao Paulo/i.test(`${x.text} ${x.aria}`))) break;
            }
            scroller.scrollTop = original;
            scroller.dispatchEvent(new Event('scroll', {bubbles:true}));
            await new Promise(r => setTimeout(r, 30));
            if (out.some(x => /Bras[ií]lia|S[aã]o Paulo|Sao Paulo/i.test(`${x.text} ${x.aria}`))) break;
          }

          collect();
          return {
            dialog_found:true,
            matches:out,
            scroll_steps:steps,
            scrollables:scrollables.length,
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

        core.goto_settings(page, blog_id)
        opened = core.click_row_prefix(page, "Fuso horário")
        scan = scan_timezone_dialog(page) if opened else {
            "dialog_found": False,
            "matches": [],
            "scroll_steps": 0,
            "scrollables": 0,
        }
        core.close_overlay(page)

        matches = scan.get("matches", [])
        brazil_matches = [
            item for item in matches
            if any(token in (item.get("text", "") + " " + item.get("aria", "")).lower()
                   for token in ("brasília", "brasilia", "são paulo", "sao paulo"))
        ]

        result = {
            "ok": bool(opened and scan.get("dialog_found") and brazil_matches),
            "read_only": True,
            "blog_id": blog_id,
            "dialog_opened": opened,
            "dialog_found": scan.get("dialog_found"),
            "scrollables_scanned": scan.get("scrollables", 0),
            "scroll_steps": scan.get("scroll_steps", 0),
            "target_matches": matches,
            "brazil_target_matches": brazil_matches,
            "message": (
                "Somente leitura. O seletor de fuso horário foi percorrido apenas por rolagem; "
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
