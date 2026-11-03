#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import time
import urllib.request

import browser_provision as bp
import validate_core_settings_profile as core
import configure_core_settings as cfg
from auto_blog_route import ensure_settings_page
from blogger_session_guard import is_blogger_url
from playwright.sync_api import sync_playwright

CONFIRMATION = "CHANGE BLOG IDENTITY"


def norm(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def _find_text_field(page, field_labels: tuple[str, ...]):
    dialogs = cfg.visible_dialog_candidates(page)

    # Prefer the exact field inside a visible Blogger dialog.
    for dialog in dialogs:
        for aria in field_labels:
            field = cfg.first_visible(
                dialog.locator(
                    f'textarea[aria-label="{aria}"],input[aria-label="{aria}"],input[type="text"][aria-label="{aria}"]'
                )
            )
            if field is not None:
                return field

    # Current Blogger can render the setting editor outside the element exposed
    # with role=dialog. Fall back only to an exact aria-label on the visible page.
    for aria in field_labels:
        field = cfg.first_visible(
            page.locator(
                f'textarea[aria-label="{aria}"],input[aria-label="{aria}"],input[type="text"][aria-label="{aria}"]'
            )
        )
        if field is not None:
            return field

    # Last resort remains scoped to visible dialogs, never to arbitrary page inputs.
    for dialog in dialogs:
        field = cfg.first_visible(dialog.locator('textarea,input[type="text"],input:not([type])'))
        if field is not None:
            return field
    return None


def set_row_text(page, row_label: str, value: str, field_labels: tuple[str, ...]) -> dict:
    # A previous fail-closed attempt may have left the requested setting editor
    # open. Reuse that exact visible field instead of blindly clicking the row again.
    field = _find_text_field(page, field_labels)
    if field is None:
        if not core.click_row_prefix(page, row_label):
            raise bp.SafeAutomationError(f'Configuração "{row_label}" não foi localizada.')
        for _ in range(16):
            page.wait_for_timeout(150)
            field = _find_text_field(page, field_labels)
            if field is not None:
                break

    if field is None:
        raise bp.SafeAutomationError(f'Campo editável de "{row_label}" não foi localizado.')

    before = field.input_value()
    maxlength = field.get_attribute("maxlength")
    if maxlength and len(value) > int(maxlength):
        raise bp.SafeAutomationError(f'Valor de "{row_label}" excede o limite de {maxlength} caracteres.')

    field.fill(value)
    cfg.click_dialog_action(page, "SALVAR")
    page.wait_for_timeout(1000)
    return {"row": row_label, "before": before, "requested": value}


def wait_public_url(url: str, expected_title: str, timeout_seconds: int = 45) -> dict:
    deadline = time.monotonic() + timeout_seconds
    last = ""
    while time.monotonic() < deadline:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 BloggerIdentityValidator/1.0"})
            with urllib.request.urlopen(req, timeout=12) as r:
                status = int(getattr(r, "status", 200))
                final_url = r.geturl()
                html = r.read().decode("utf-8", errors="replace")
            found = expected_title.casefold() in html.casefold()
            if status == 200 and found:
                return {"http_status": status, "requested_url": url, "final_url": final_url, "title_found": True}
            last = f"status={status}, final_url={final_url}, title_found={found}"
        except Exception as exc:
            last = str(exc)
        time.sleep(1.5)
    raise bp.SafeAutomationError(f"Nova URL pública não validada. Última observação: {last}")


def main() -> int:
    p = argparse.ArgumentParser(description="Altera com segurança título e endereço Blogspot de um blog existente.")
    p.add_argument("--expected-blog-id", required=True)
    p.add_argument("--title", required=True)
    p.add_argument("--address", required=True)
    p.add_argument("--confirm", required=True)
    args = p.parse_args()

    blog_id = core.validate_expected_blog_id(args.expected_blog_id)
    title = norm(args.title)
    address = (args.address or "").strip().lower()
    if args.confirm != CONFIRMATION:
        raise bp.SafeAutomationError(f'Confirmação inválida. Use exatamente: {CONFIRMATION}')
    if not title or len(title) > 100:
        raise bp.SafeAutomationError("Título inválido.")
    if not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{1,61}[a-z0-9])?", address):
        raise bp.SafeAutomationError("Endereço Blogspot inválido.")

    public_url = f"https://{address}.blogspot.com/"
    safe_cdp = bp.validate_cdp_url(bp.DEFAULT_CDP_URL, allow_remote=False)

    with sync_playwright() as pw:
        browser, context = bp.connect_official_chrome(pw, safe_cdp)
        page = ensure_settings_page(context, blog_id)
        if not is_blogger_url(page.url) or bp.extract_current_blog_id(page) != blog_id:
            raise bp.SafeAutomationError("Blog errado bloqueado antes da alteração.")

        page.wait_for_timeout(700)
        if bp.extract_current_blog_id(page) != blog_id:
            raise bp.SafeAutomationError("Blog ID mudou ao abrir Configurações.")

        before = {
            "title_row": core.row_text(page, "Título"),
            "address_row": core.row_text(page, "Endereço do blog"),
            "settings_url": bp.sanitize_url(page.url),
        }

        title_action = set_row_text(page, "Título", title, ("Título", "Title"))
        address_action = set_row_text(page, "Endereço do blog", address, ("Endereço do blog", "Endereço", "Blog address", "Address"))

        page.wait_for_timeout(1200)
        if bp.extract_current_blog_id(page) != blog_id:
            raise bp.SafeAutomationError("Blog ID mudou após a alteração.")

        after = {
            "title_row": core.row_text(page, "Título"),
            "address_row": core.row_text(page, "Endereço do blog"),
            "settings_url": bp.sanitize_url(page.url),
        }

        # These row snapshots are kept as diagnostics only. Blogger may render just
        # the row label after saving, so authoritative validation is the unchanged
        # Blog ID plus the new public URL/title check below.
        public_validation = wait_public_url(public_url, title)
        result = {
            "status": "BLOG_IDENTITY_CHANGED_AND_VALIDATED",
            "blog_id": blog_id,
            "title": title,
            "address": address,
            "public_url": public_url,
            "before": before,
            "actions": {"title": title_action, "address": address_action},
            "after": after,
            "public_validation": public_validation,
            "browser_connected": browser.is_connected(),
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
