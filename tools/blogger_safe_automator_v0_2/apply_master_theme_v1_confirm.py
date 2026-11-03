#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import browser_provision as bp
import apply_master_theme_v1 as base
from blogger_panel_route_guard import extract_panel_blog_id
from inspect_theme_restore_dialog import THEMES_ROUTE_RE, select_expected_theme_page
from playwright.sync_api import sync_playwright

CONFIRM_LABELS = (
    "ATUALIZAR",
    "ATUALIZAR TEMA",
    "CONFIRMAR",
    "APLICAR",
    "RESTAURAR",
    "SALVAR",
    "ENVIAR",
    "FAZER UPLOAD",
    "OK",
)


def _norm(value: str | None) -> str:
    return " ".join((value or "").split()).casefold()


def _visible_actions(page) -> list[dict]:
    locator = page.locator('button,[role="button"]')
    out: list[dict] = []
    for index in range(locator.count()):
        item = locator.nth(index)
        try:
            if not item.is_visible() or not item.is_enabled():
                continue
            text = " ".join((item.inner_text() or "").split())
            aria = " ".join((item.get_attribute("aria-label") or "").split())
            if text or aria:
                out.append({"index": index, "text": text, "aria": aria})
        except Exception:
            continue
    return out


def _wait_and_confirm_update(page, timeout_ms: int = 8_000) -> dict:
    targets = {_norm(value) for value in CONFIRM_LABELS}
    deadline = time.monotonic() + timeout_ms / 1000
    last_actions: list[dict] = []

    while time.monotonic() < deadline:
        actions = _visible_actions(page)
        last_actions = actions
        matches = []
        for action in actions:
            text = _norm(action.get("text"))
            aria = _norm(action.get("aria"))
            if text in targets or aria in targets:
                matches.append(action)

        if len(matches) == 1:
            match = matches[0]
            item = page.locator('button,[role="button"]').nth(match["index"])
            item.click(timeout=5_000)
            return {
                "confirmed": True,
                "button_text": match.get("text") or "",
                "button_aria": match.get("aria") or "",
            }

        if len(matches) > 1:
            raise bp.SafeAutomationError(
                f"Confirmação pós-seleção ambígua; candidatos={matches}."
            )

        page.wait_for_timeout(250)

    raise bp.SafeAutomationError(
        "O theme.xml foi selecionado, mas nenhuma ação única de confirmação da atualização apareceu. "
        f"Ações visíveis finais: {last_actions}."
    )


def execute_apply(
    expected_blog_id: str,
    theme_path: str,
    backup_path: str,
    public_url: str,
    confirm: str,
) -> dict:
    expected_blog_id = base.validate_blog_id(expected_blog_id)
    base.validate_lab_target(expected_blog_id, public_url)
    base.validate_confirmation(confirm)

    theme = base.validate_xml_file(theme_path, label="Tema Mestre")
    backup = base.validate_xml_file(backup_path, label="Backup do tema atual")
    theme_file = Path(theme["path"])
    if theme_file.name.lower() != "theme.xml":
        raise bp.SafeAutomationError("Arquivo esperado do Tema Mestre deve se chamar theme.xml.")

    safe_cdp = bp.validate_cdp_url(bp.DEFAULT_CDP_URL, allow_remote=False)

    with sync_playwright() as p:
        browser, context = bp.connect_official_chrome(p, safe_cdp)
        page = select_expected_theme_page(context, expected_blog_id)

        current_blog_id = extract_panel_blog_id(page.url)
        if current_blog_id != expected_blog_id:
            raise bp.SafeAutomationError(
                f"Blog errado bloqueado: atual={current_blog_id!r}, esperado={expected_blog_id!r}."
            )
        match = THEMES_ROUTE_RE.search(page.url or "")
        if not match or match.group(1) != expected_blog_id:
            raise bp.SafeAutomationError("A aba ativa precisa ser Tema do blog-laboratório.")

        navigation, _, stale_inputs_cleared = base._prepare_restore_dialog(page)
        selection = base._select_theme_file_via_playwright_chooser(page, theme["path"])
        base._wait_restore_dialog_close(page)

        # A seleção do arquivo foi comprovada. Agora tratamos explicitamente a
        # confirmação adicional que o Blogger apresenta depois dessa etapa.
        confirmation = _wait_and_confirm_update(page)
        page.wait_for_timeout(1_200)
        feedback = base._visible_feedback(page)

        if extract_panel_blog_id(page.url) != expected_blog_id:
            raise bp.SafeAutomationError("Blog ID mudou após confirmação da atualização.")

        try:
            public_validation = base._wait_public_markers(public_url)
        except bp.SafeAutomationError as exc:
            raise bp.SafeAutomationError(
                f"{exc} Seleção comprovada={selection}. Confirmação={confirmation}. "
                f"Feedback visível={feedback}."
            ) from exc

        return {
            "status": "MASTER_THEME_V1_APPLIED_AND_PUBLICLY_VALIDATED",
            "blog_id": expected_blog_id,
            "theme": theme,
            "backup": backup,
            "navigation": navigation,
            "stale_inputs_cleared": stale_inputs_cleared,
            "selection": selection,
            "confirmation": confirmation,
            "blogger_feedback": feedback,
            "public_validation": public_validation,
            "browser_connected": browser.is_connected(),
            "message": "Tema Mestre v1.0 selecionado, confirmado e validado no HTML público.",
        }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Aplica o Tema Mestre v1.0 tratando a confirmação pós-seleção do Blogger."
    )
    parser.add_argument("--expected-blog-id", required=True)
    parser.add_argument("--theme-path", required=True)
    parser.add_argument("--backup-path", required=True)
    parser.add_argument("--public-url", required=True)
    parser.add_argument("--confirm", required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = execute_apply(
        args.expected_blog_id,
        args.theme_path,
        args.backup_path,
        args.public_url,
        args.confirm,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
