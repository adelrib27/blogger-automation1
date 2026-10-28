#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import browser_provision as bp
import validate_core_settings_profile as core
from playwright.sync_api import sync_playwright

CDP_URL = bp.DEFAULT_CDP_URL
OUT_DIR = Path("logs/browser_diagnostics")


def scan_timezone_ui(page) -> dict:
    """Procura GMT-03/Brasil sem selecionar ou salvar nada.

    O Blogger pode virtualizar a lista e variar o contêiner/role do seletor.
    Por isso a descoberta não depende de role="dialog": primeiro procura em todo
    o DOM (inclusive nós não visíveis) e, se necessário, percorre contêineres
    realmente roláveis encontrados na página.
    """
    return page.evaluate(
        r"""async () => {
          const norm = v => String(v || '').trim().replace(/\s+/g, ' ');
          const target = /(GMT-03(?::00)?|Bras[ií]lia|S[aã]o Paulo|Sao Paulo)/i;
          const brazil = /(Bras[ií]lia|S[aã]o Paulo|Sao Paulo)/i;
          const timezoneMarker = /(Fuso hor[aá]rio|GMT-11:00|Hor[aá]rio Padr[aã]o de Samoa|Midway)/i;

          const meta = el => {
            const r = el.getBoundingClientRect();
            return {
              tag: el.tagName,
              role: el.getAttribute('role') || '',
              text: norm(el.innerText || el.textContent).slice(0, 700),
              aria: norm(el.getAttribute('aria-label')).slice(0, 300),
              aria_selected: el.getAttribute('aria-selected') || '',
              tabindex: el.getAttribute('tabindex') || '',
              disabled: el.matches(':disabled') || el.getAttribute('aria-disabled') === 'true',
              width: Math.round(r.width),
              height: Math.round(r.height),
            };
          };

          const seen = new Set();
          const matches = [];
          const collect = root => {
            const nodes = root === document ? document.querySelectorAll('body *') : root.querySelectorAll('*');
            for (const el of nodes) {
              const text = norm(el.innerText || el.textContent);
              const aria = norm(el.getAttribute('aria-label'));
              if (!target.test(`${text} ${aria}`) || (!text && !aria)) continue;
              const key = `${el.tagName}|${el.getAttribute('role') || ''}|${text}|${aria}`;
              if (seen.has(key)) continue;
              seen.add(key);
              matches.push(meta(el));
            }
          };

          // 1) Procura no DOM inteiro, inclusive itens virtualizados/não visíveis.
          collect(document);
          if (matches.some(x => brazil.test(`${x.text} ${x.aria}`))) {
            return {
              ui_found: true,
              discovery: 'whole-dom',
              matches,
              scroll_steps: 0,
              scrollables: 0,
            };
          }

          // 2) Identifica regiões pertencentes ao seletor de fuso por conteúdo,
          // sem depender de role="dialog".
          const all = [...document.querySelectorAll('body *')];
          const markerNodes = all.filter(el => timezoneMarker.test(norm(el.innerText || el.textContent)));

          // Inclui os próprios marcadores, descendentes e até 4 ancestrais.
          const candidates = new Set();
          for (const node of markerNodes) {
            candidates.add(node);
            let cur = node.parentElement;
            for (let i = 0; cur && i < 4; i++, cur = cur.parentElement) candidates.add(cur);
          }

          const scrollables = [...candidates].filter(el => {
            try {
              return el.scrollHeight > el.clientHeight + 4;
            } catch (_) {
              return false;
            }
          });

          let steps = 0;
          for (const scroller of scrollables) {
            const original = scroller.scrollTop;
            const max = Math.max(0, scroller.scrollHeight - scroller.clientHeight);
            const step = Math.max(120, Math.floor(Math.max(scroller.clientHeight, 160) * 0.75));

            for (let pos = 0; pos <= max; pos += step) {
              scroller.scrollTop = Math.min(pos, max);
              scroller.dispatchEvent(new Event('scroll', {bubbles:true}));
              await new Promise(r => setTimeout(r, 70));
              collect(document);
              steps += 1;
              if (matches.some(x => brazil.test(`${x.text} ${x.aria}`))) break;
            }

            // Garante uma leitura no fim da lista.
            scroller.scrollTop = max;
            scroller.dispatchEvent(new Event('scroll', {bubbles:true}));
            await new Promise(r => setTimeout(r, 90));
            collect(document);

            scroller.scrollTop = original;
            scroller.dispatchEvent(new Event('scroll', {bubbles:true}));
            await new Promise(r => setTimeout(r, 30));

            if (matches.some(x => brazil.test(`${x.text} ${x.aria}`))) break;
          }

          return {
            ui_found: markerNodes.length > 0,
            discovery: 'scroll-fallback',
            matches,
            scroll_steps: steps,
            scrollables: scrollables.length,
            marker_nodes: markerNodes.length,
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
        current_timezone = core.row_text(page, "Fuso horário")
        opened = core.click_row_prefix(page, "Fuso horário")
        page.wait_for_timeout(700)

        scan = scan_timezone_ui(page) if opened else {
            "ui_found": False,
            "discovery": "not-opened",
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
            "ok": bool(opened and scan.get("ui_found") and brazil_matches),
            "read_only": True,
            "blog_id": blog_id,
            "current_timezone": current_timezone,
            "dialog_opened": opened,
            "timezone_ui_found": scan.get("ui_found"),
            "discovery": scan.get("discovery"),
            "scrollables_scanned": scan.get("scrollables", 0),
            "scroll_steps": scan.get("scroll_steps", 0),
            "target_matches": matches,
            "brazil_target_matches": brazil_matches,
            "message": (
                "Somente leitura. O seletor de fuso horário foi apenas inspecionado; "
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
