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

    A lista de fusos do Blogger é virtualizada. O detector identifica o painel
    visível pelo título/botões e percorre qualquer descendente cujo scrollHeight
    seja maior que clientHeight, sem depender de role ou overflow CSS.
    """
    return page.evaluate(
        r"""async () => {
          const norm = v => String(v || '').trim().replace(/\s+/g, ' ');
          const target = /(GMT-03(?::00)?|Bras[ií]lia|S[aã]o Paulo|Sao Paulo)/i;
          const brazil = /(Bras[ií]lia|S[aã]o Paulo|Sao Paulo)/i;
          const visible = el => {
            if (!el) return false;
            const r = el.getBoundingClientRect();
            const s = getComputedStyle(el);
            return r.width > 0 && r.height > 0 && s.display !== 'none' && s.visibility !== 'hidden';
          };

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
            const nodes = root.querySelectorAll ? root.querySelectorAll('*') : [];
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

          // Tenta achar o painel/modal pelo próprio título e pelos botões de ação.
          const all = [...document.querySelectorAll('body *')];
          const titleNodes = all.filter(el => visible(el) && /^Fuso hor[aá]rio$/i.test(norm(el.innerText || el.textContent)));

          let panel = null;
          for (const title of titleNodes) {
            let cur = title;
            for (let depth = 0; cur && depth < 8; depth++, cur = cur.parentElement) {
              if (!visible(cur)) continue;
              const text = norm(cur.innerText || cur.textContent);
              if (/Fuso hor[aá]rio/i.test(text) && /CANCELAR/i.test(text) && /SALVAR/i.test(text)) {
                panel = cur;
                break;
              }
            }
            if (panel) break;
          }

          // Fallback: maior região visível contendo o título e os botões.
          if (!panel) {
            const candidates = all.filter(el => {
              if (!visible(el)) return false;
              const text = norm(el.innerText || el.textContent);
              return /Fuso hor[aá]rio/i.test(text) && /CANCELAR/i.test(text) && /SALVAR/i.test(text);
            });
            candidates.sort((a, b) => {
              const ra = a.getBoundingClientRect();
              const rb = b.getBoundingClientRect();
              return (ra.width * ra.height) - (rb.width * rb.height);
            });
            panel = candidates[0] || null;
          }

          const root = panel || document.body;
          collect(root);
          if (matches.some(x => brazil.test(`${x.text} ${x.aria}`))) {
            return {
              ui_found: true,
              discovery: 'panel-dom',
              panel_found: Boolean(panel),
              matches,
              scroll_steps: 0,
              scrollables: 0,
            };
          }

          // A imagem do Blogger confirma uma lista com scrollbar própria. Não
          // exigimos overflow:auto/scroll: basta haver conteúdo vertical oculto.
          const nodes = [root, ...root.querySelectorAll('*')];
          const scrollables = nodes.filter(el => {
            try {
              return visible(el) && el.clientHeight > 40 && el.scrollHeight > el.clientHeight + 8;
            } catch (_) {
              return false;
            }
          });

          // Prioriza áreas estreitas/altas de lista, depois maior amplitude de rolagem.
          scrollables.sort((a, b) => {
            const ar = a.getBoundingClientRect();
            const br = b.getBoundingClientRect();
            const aRange = a.scrollHeight - a.clientHeight;
            const bRange = b.scrollHeight - b.clientHeight;
            const aScore = aRange + Math.min(ar.height, 900);
            const bScore = bRange + Math.min(br.height, 900);
            return bScore - aScore;
          });

          let steps = 0;
          for (const scroller of scrollables.slice(0, 12)) {
            const original = scroller.scrollTop;
            const max = Math.max(0, scroller.scrollHeight - scroller.clientHeight);
            const step = Math.max(160, Math.floor(Math.max(scroller.clientHeight, 180) * 0.70));

            for (let pos = 0; pos <= max; pos += step) {
              scroller.scrollTop = Math.min(pos, max);
              scroller.dispatchEvent(new Event('scroll', {bubbles:true}));
              await new Promise(r => setTimeout(r, 90));
              collect(root);
              steps += 1;
              if (matches.some(x => brazil.test(`${x.text} ${x.aria}`))) break;
            }

            if (!matches.some(x => brazil.test(`${x.text} ${x.aria}`))) {
              scroller.scrollTop = max;
              scroller.dispatchEvent(new Event('scroll', {bubbles:true}));
              await new Promise(r => setTimeout(r, 140));
              collect(root);
              steps += 1;
            }

            scroller.scrollTop = original;
            scroller.dispatchEvent(new Event('scroll', {bubbles:true}));
            await new Promise(r => setTimeout(r, 40));

            if (matches.some(x => brazil.test(`${x.text} ${x.aria}`))) break;
          }

          return {
            ui_found: Boolean(panel || titleNodes.length),
            discovery: 'panel-scroll',
            panel_found: Boolean(panel),
            matches,
            scroll_steps: steps,
            scrollables: scrollables.length,
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
            "panel_found": False,
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
            "panel_found": scan.get("panel_found"),
            "discovery": scan.get("discovery"),
            "scrollables_scanned": scan.get("scrollables", 0),
            "scroll_steps": scan.get("scroll_steps", 0),
            "target_matches": matches,
            "brazil_target_matches": brazil_matches,
            "message": (
                "Somente leitura. O seletor de fuso horário foi apenas inspecionado e rolado; "
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
