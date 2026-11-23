#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import browser_provision as bp
from blogger_session_guard import is_blogger_url
from playwright.sync_api import sync_playwright

CDP_URL = bp.DEFAULT_CDP_URL
OUT_DIR = Path("logs/browser_diagnostics")
BLOG_ID_RE = re.compile(r"^[0-9]+$")


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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Diagnóstico somente leitura das configurações-base do Blogger."
    )
    parser.add_argument(
        "--expected-blog-id",
        required=True,
        help="Blog ID que deve estar aberto; o diagnóstico bloqueia qualquer outro blog.",
    )
    return parser


def validate_expected_blog_id(value: str) -> str:
    value = (value or "").strip()
    if not BLOG_ID_RE.fullmatch(value):
        raise bp.SafeAutomationError("Blog ID esperado inválido.")
    return value


def _page_visibility(page) -> bool:
    try:
        return page.evaluate("() => document.visibilityState") == "visible"
    except Exception:
        return False


def select_expected_blog_page(context, expected_blog_id: str):
    """Select only a Blogger tab whose URL resolves to the expected Blog ID.

    This deliberately does not fall back to another Blogger tab. If the requested
    blog is not present in the connected Chrome context, the diagnostic fails closed.
    """
    candidates = []
    for page in context.pages:
        try:
            if not is_blogger_url(page.url):
                continue
            if bp.extract_current_blog_id(page) == expected_blog_id:
                candidates.append(page)
        except Exception:
            continue

    if not candidates:
        raise bp.SafeAutomationError(
            f"Nenhuma aba Blogger do Blog ID esperado {expected_blog_id} foi encontrada."
        )

    settings_candidates = [
        page
        for page in candidates
        if f"/blog/settings/{expected_blog_id}" in bp.sanitize_url(page.url)
    ]
    visible_settings = [page for page in settings_candidates if _page_visibility(page)]
    visible_candidates = [page for page in candidates if _page_visibility(page)]

    if visible_settings:
        return visible_settings[-1]
    if settings_candidates:
        return settings_candidates[-1]
    if visible_candidates:
        return visible_candidates[-1]
    return candidates[-1]


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


def click_row_prefix(page, label_prefix: str) -> bool:
    pattern = re.compile(rf"^{re.escape(label_prefix)}(?:\s|$)", re.I)
    candidates = [
        page.get_by_text(pattern),
        page.locator('[tabindex="0"]').filter(has_text=pattern),
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
        page.wait_for_timeout(450)
        return True
    return False


def close_overlay(page) -> None:
    try:
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)
    except Exception:
        pass


def overlay_snapshot(page) -> dict:
    return page.evaluate(
        r"""() => {
          const norm = v => String(v || '').trim().replace(/\s+/g, ' ');
          const visible = el => {
            const r = el.getBoundingClientRect();
            const s = getComputedStyle(el);
            return r.width > 0 && r.height > 0 && s.display !== 'none' && s.visibility !== 'hidden';
          };
          const meta = el => ({
            tag: el.tagName,
            role: el.getAttribute('role') || '',
            text: norm(el.innerText || el.textContent).slice(0, 600),
            aria: norm(el.getAttribute('aria-label')).slice(0, 200),
            ariaChecked: el.getAttribute('aria-checked') || '',
            ariaSelected: el.getAttribute('aria-selected') || '',
            tabindex: el.getAttribute('tabindex') || '',
            disabled: el.matches(':disabled') || el.getAttribute('aria-disabled') === 'true',
          });

          const overlays = [];
          for (const el of document.querySelectorAll('[role="dialog"], [role="listbox"], [role="menu"]')) {
            if (!visible(el)) continue;
            overlays.push(meta(el));
          }

          const fields = [];
          for (const el of document.querySelectorAll('input,textarea,[contenteditable="true"]')) {
            if (!visible(el)) continue;
            fields.push({
              ...meta(el),
              type: el.getAttribute('type') || '',
              placeholder: norm(el.getAttribute('placeholder')),
              value: 'value' in el ? String(el.value || '') : norm(el.innerText || el.textContent),
              maxlength: el.getAttribute('maxlength') || '',
            });
          }

          const options = [];
          for (const el of document.querySelectorAll('[role="option"], [role="menuitemradio"], [role="menuitem"]')) {
            if (!visible(el)) continue;
            options.push(meta(el));
          }

          const buttons = [];
          for (const el of document.querySelectorAll('button,[role="button"]')) {
            if (!visible(el)) continue;
            const m = meta(el);
            if (m.text || m.aria) buttons.push(m);
          }

          return {overlays, fields, options, buttons};
        }"""
    )


def checkbox_state(page, aria_label: str) -> dict:
    loc = first_visible(page.locator(f'[role="checkbox"][aria-label="{aria_label}"]'))
    if loc is None:
        return {"found": False, "aria_checked": None, "aria_disabled": None}
    return {
        "found": True,
        "aria_checked": loc.get_attribute("aria-checked"),
        "aria_disabled": loc.get_attribute("aria-disabled"),
    }


def row_text(page, prefix: str) -> str | None:
    pattern = re.compile(rf"^{re.escape(prefix)}(?:\s|$)", re.I)
    item = first_visible(page.get_by_text(pattern))
    if item is None:
        return None
    try:
        return norm(item.inner_text())
    except Exception:
        return None


def main() -> int:
    args = build_parser().parse_args()
    expected_blog_id = validate_expected_blog_id(args.expected_blog_id)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        _, context = bp.connect_official_chrome(p, CDP_URL)
        page = select_expected_blog_page(context, expected_blog_id)

        # Never navigate to Blogger home here: that can silently switch to the
        # account's default blog. The selected page already proved it is Blogger.
        if not is_blogger_url(page.url):
            raise bp.SafeAutomationError("A aba selecionada deixou de ser uma página do Blogger.")

        blog_id = bp.extract_current_blog_id(page)
        if blog_id != expected_blog_id:
            raise bp.SafeAutomationError(
                f"Blog errado bloqueado: atual={blog_id!r}, esperado={expected_blog_id!r}."
            )

        goto_settings(page, expected_blog_id)
        blog_id = bp.extract_current_blog_id(page)
        if blog_id != expected_blog_id:
            raise bp.SafeAutomationError(
                f"Blog mudou durante o diagnóstico: atual={blog_id!r}, esperado={expected_blog_id!r}."
            )

        direct_state = {
            "search_visibility": checkbox_state(page, "Visível para mecanismos de pesquisa"),
            "https_redirect": checkbox_state(page, "Redirecionamento para HTTPS"),
            "lazy_images": checkbox_state(page, "Imagens com carregamento lento"),
            "webp_images": checkbox_state(page, "Veiculação de imagens WebP"),
            "search_description": checkbox_state(page, "Ativar a descrição de pesquisa"),
            "custom_robots_txt": checkbox_state(page, "Ativar robots.txt personalizado"),
            "custom_robots_headers": checkbox_state(page, "Ativar as tags personalizadas de cabeçalho de robôs"),
        }

        rows = {
            "description": row_text(page, "Descrição"),
            "timezone": row_text(page, "Fuso horário"),
            "search_description": row_text(page, "Descrição da pesquisa"),
        }

        description_opened = click_row_prefix(page, "Descrição")
        description_overlay = overlay_snapshot(page) if description_opened else {}
        close_overlay(page)

        timezone_opened = click_row_prefix(page, "Fuso horário")
        timezone_overlay = overlay_snapshot(page) if timezone_opened else {}
        close_overlay(page)

        final_blog_id = bp.extract_current_blog_id(page)
        if final_blog_id != expected_blog_id:
            raise bp.SafeAutomationError(
                f"Blog mudou durante a coleta: atual={final_blog_id!r}, esperado={expected_blog_id!r}."
            )

        result = {
            "ok": bool(description_opened and timezone_opened),
            "read_only": True,
            "expected_blog_id": expected_blog_id,
            "blog_id": final_blog_id,
            "settings_url": bp.sanitize_url(page.url),
            "direct_state": direct_state,
            "rows": rows,
            "description": {
                "opened": description_opened,
                "overlay": description_overlay,
            },
            "timezone": {
                "opened": timezone_opened,
                "overlay": timezone_overlay,
            },
            "message": (
                "Somente leitura. Descrição e Fuso horário foram apenas abertos e fechados; "
                "nenhum campo foi preenchido e nenhum controle foi alterado."
            ),
        }

        (OUT_DIR / f"core_settings_profile_{expected_blog_id}.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
