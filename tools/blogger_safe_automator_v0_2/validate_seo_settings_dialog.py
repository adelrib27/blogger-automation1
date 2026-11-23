#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

import browser_provision as bp
from playwright.sync_api import sync_playwright

CDP_URL = bp.DEFAULT_CDP_URL
OUT_DIR = Path("logs/browser_diagnostics")


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


def goto_settings(page, blog_id: str) -> None:
    if f"/blog/settings/{blog_id}" in page.url:
        return

    candidates = [
        page.get_by_role("menuitem", name=re.compile(r"^(Configurações|Settings)$", re.I)),
        page.get_by_text(re.compile(r"^(Configurações|Settings)$", re.I), exact=True),
        page.locator(f'a[href*="/blog/settings/{blog_id}"]'),
    ]
    target = None
    for loc in candidates:
        target = first_visible(loc)
        if target is not None:
            break
    if target is None:
        raise bp.SafeAutomationError("Configurações não foi localizada com segurança.")

    try:
        target.click(timeout=5_000)
    except Exception:
        target.evaluate("el => el.click()")
    page.wait_for_timeout(1200)
    if f"/blog/settings/{blog_id}" not in page.url:
        raise bp.SafeAutomationError("A tela Configurações não abriu como esperado.")


def click_setting_row(page, label: str):
    exact = re.compile(rf"^{re.escape(label)}$", re.I)
    candidates = [
        page.get_by_text(exact, exact=True),
        page.locator('[tabindex="0"]').filter(has_text=exact),
    ]
    for loc in candidates:
        item = first_visible(loc)
        if item is None:
            continue
        try:
            item.click(timeout=4_000)
        except Exception:
            try:
                item.evaluate("el => el.click()")
            except Exception:
                continue
        page.wait_for_timeout(500)
        return True
    return False


def visible_dialog_snapshot(page) -> dict:
    dialogs = page.locator('[role="dialog"]')
    visible_dialogs = []
    for i in range(dialogs.count()):
        dialog = dialogs.nth(i)
        try:
            if not dialog.is_visible():
                continue
            fields = []
            loc = dialog.locator('input, textarea, [contenteditable="true"]')
            for j in range(loc.count()):
                field = loc.nth(j)
                try:
                    if not field.is_visible():
                        continue
                    fields.append({
                        "tag": field.evaluate("el => el.tagName"),
                        "type": field.get_attribute("type") or "",
                        "aria": norm(field.get_attribute("aria-label")),
                        "placeholder": norm(field.get_attribute("placeholder")),
                        "value": field.input_value() if field.evaluate("el => ['INPUT','TEXTAREA'].includes(el.tagName)") else norm(field.inner_text()),
                        "maxlength": field.get_attribute("maxlength") or "",
                    })
                except Exception:
                    continue

            buttons = []
            bl = dialog.locator('button, [role="button"]')
            for j in range(bl.count()):
                b = bl.nth(j)
                try:
                    if not b.is_visible():
                        continue
                    buttons.append({
                        "tag": b.evaluate("el => el.tagName"),
                        "role": b.get_attribute("role") or "",
                        "text": norm(b.inner_text())[:120],
                        "aria": norm(b.get_attribute("aria-label"))[:120],
                        "disabled": b.get_attribute("aria-disabled") or b.get_attribute("disabled") or "",
                    })
                except Exception:
                    continue

            visible_dialogs.append({
                "text": norm(dialog.inner_text())[:800],
                "fields": fields,
                "buttons": buttons,
            })
        except Exception:
            continue
    return {"dialogs": visible_dialogs}


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        _, context = bp.connect_official_chrome(p, CDP_URL)
        page = bp.select_page(context)
        bp.require_blogger_session(page)

        blog_id = bp.extract_current_blog_id(page)
        if not blog_id:
            raise bp.SafeAutomationError("Não foi possível identificar o Blog ID atual.")
        goto_settings(page, blog_id)

        search_visible = first_visible(page.locator('[role="checkbox"][aria-label="Visível para mecanismos de pesquisa"]'))
        https_redirect = first_visible(page.locator('[role="checkbox"][aria-label="Redirecionamento para HTTPS"]'))
        search_desc_toggle = first_visible(page.locator('[role="checkbox"][aria-label="Ativar a descrição de pesquisa"]'))
        robots_toggle = first_visible(page.locator('[role="checkbox"][aria-label="Ativar robots.txt personalizado"]'))
        robots_headers_toggle = first_visible(page.locator('[role="checkbox"][aria-label="Ativar as tags personalizadas de cabeçalho de robôs"]'))

        state = {
            "search_visible": search_visible.get_attribute("aria-checked") if search_visible else None,
            "https_redirect": https_redirect.get_attribute("aria-checked") if https_redirect else None,
            "search_description_enabled": search_desc_toggle.get_attribute("aria-checked") if search_desc_toggle else None,
            "custom_robots_txt": robots_toggle.get_attribute("aria-checked") if robots_toggle else None,
            "custom_robots_headers": robots_headers_toggle.get_attribute("aria-checked") if robots_headers_toggle else None,
        }

        description_opened = click_setting_row(page, "Descrição")
        description_dialog = visible_dialog_snapshot(page) if description_opened else {"dialogs": []}

        # Nenhum preenchimento e nenhum salvamento: fecha somente o diálogo aberto.
        try:
            page.keyboard.press("Escape")
            page.wait_for_timeout(350)
        except Exception:
            pass

        result = {
            "ok": description_opened and bool(description_dialog.get("dialogs")),
            "read_only": True,
            "blog_id": blog_id,
            "settings_url": bp.sanitize_url(page.url),
            "current_state": state,
            "description_dialog_opened": description_opened,
            "description_dialog": description_dialog,
            "message": "Somente leitura: o diálogo de Descrição foi aberto e fechado sem preencher nem salvar. Nenhuma configuração foi alterada.",
        }

        (OUT_DIR / "seo_settings_dialog.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
