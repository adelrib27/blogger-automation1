#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import browser_provision as bp
import validate_core_settings_profile as core
from playwright.sync_api import sync_playwright

CDP_URL = bp.DEFAULT_CDP_URL
OUT_DIR = Path("logs/browser_diagnostics")
TARGET = "(GMT-03:00) Horário Padrão de Brasília – Recife"


def find_modal_box(page):
    data = page.evaluate(
        r"""() => {
          const norm = v => String(v || '').trim().replace(/\s+/g, ' ');
          const visible = el => {
            const r = el.getBoundingClientRect();
            const s = getComputedStyle(el);
            return r.width > 300 && r.height > 250 && s.display !== 'none' && s.visibility !== 'hidden';
          };
          const candidates = [];
          for (const el of document.querySelectorAll('body *')) {
            if (!visible(el)) continue;
            const text = norm(el.innerText || el.textContent);
            if (!/Fuso hor[aá]rio/i.test(text)) continue;
            if (!/CANCELAR/i.test(text) || !/SALVAR/i.test(text)) continue;
            const r = el.getBoundingClientRect();
            candidates.push({
              tag: el.tagName,
              role: el.getAttribute('role') || '',
              text: text.slice(0, 250),
              x: r.x, y: r.y, width: r.width, height: r.height,
              area: r.width * r.height,
            });
          }
          candidates.sort((a,b) => a.area - b.area);
          return candidates[0] || null;
        }"""
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

        core.goto_settings(page, blog_id)
        opened = core.click_row_prefix(page, "Fuso horário")
        page.wait_for_timeout(600)

        modal = find_modal_box(page) if opened else None
        found = False
        found_text = None
        wheel_steps = 0

        if modal:
            # Mantém o ponteiro no miolo da lista, acima dos botões de ação.
            x = modal["x"] + modal["width"] * 0.55
            y = modal["y"] + modal["height"] * 0.45
            page.mouse.move(x, y)

            for _ in range(28):
                loc = page.get_by_text(TARGET, exact=True)
                try:
                    for i in range(loc.count()):
                        item = loc.nth(i)
                        if item.is_visible():
                            found = True
                            found_text = item.inner_text().strip()
                            break
                except Exception:
                    pass
                if found:
                    break

                page.mouse.wheel(0, 520)
                page.wait_for_timeout(90)
                wheel_steps += 1

        core.close_overlay(page)

        result = {
            "ok": bool(opened and modal and found),
            "read_only": True,
            "blog_id": blog_id,
            "target": TARGET,
            "modal_found": bool(modal),
            "modal": modal,
            "target_found": found,
            "found_text": found_text,
            "wheel_steps": wheel_steps,
            "message": (
                "Somente leitura. O modal de fuso foi apenas rolado até procurar o alvo exato; "
                "nenhuma opção foi selecionada e nada foi salvo."
            ),
        }

        (OUT_DIR / "timezone_exact.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
