#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import browser_provision as bp
import validate_core_settings_profile as core
from playwright.sync_api import sync_playwright

CDP_URL = bp.DEFAULT_CDP_URL
OUT_DIR = Path("logs/browser_diagnostics")
CONFIRMATION = "APPLY SETTINGS"
DEFAULT_TIMEZONE = "(GMT-03:00) Horário Padrão de Brasília – São Paulo"


class SettingsError(bp.SafeAutomationError):
    pass


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


def visible_dialog_candidates(page):
    dialogs = page.locator('[role="dialog"]')
    candidates = []
    for i in range(dialogs.count()):
        d = dialogs.nth(i)
        try:
            if not d.is_visible():
                continue
            box = d.bounding_box()
            if not box:
                continue
            candidates.append((box["width"] * box["height"], d))
        except Exception:
            continue
    # Maior primeiro: overlays/toasts menores não devem roubar o foco do modal real.
    candidates.sort(key=lambda x: x[0], reverse=True)
    return [d for _, d in candidates]


def visible_dialog(page):
    candidates = visible_dialog_candidates(page)
    if not candidates:
        raise SettingsError("Nenhum diálogo visível foi encontrado.")
    return candidates[0]


def click_dialog_action(page, label: str, dialog=None) -> None:
    dialogs = [dialog] if dialog is not None else visible_dialog_candidates(page)
    if not dialogs:
        raise SettingsError("Nenhum diálogo visível foi encontrado.")
    pattern = re.compile(rf"^{re.escape(label)}$", re.I)
    for active_dialog in dialogs:
        for loc in (
            active_dialog.get_by_role("button", name=pattern),
            active_dialog.get_by_text(pattern, exact=True),
        ):
            item = first_visible(loc)
            if item is None:
                continue
            try:
                item.click(timeout=5_000)
            except Exception:
                try:
                    item.evaluate("el => el.click()")
                except Exception:
                    continue
            page.wait_for_timeout(700)
            return
    raise SettingsError(f'Botão "{label}" não foi localizado no diálogo ativo.')


def _find_dialog_text_field(page, field_labels: tuple[str, ...]):
    dialogs = visible_dialog_candidates(page)
    for dialog in dialogs:
        for aria in field_labels:
            field = first_visible(dialog.locator(f'textarea[aria-label="{aria}"], input[aria-label="{aria}"]'))
            if field is not None:
                return dialog, field
    for dialog in dialogs:
        field = first_visible(dialog.locator("textarea, input[type=text]"))
        if field is not None:
            return dialog, field
    return None, None


def set_dialog_text(page, row_label: str, value: str, field_labels: tuple[str, ...]) -> dict:
    if not core.click_row_prefix(page, row_label):
        raise SettingsError(f'Configuração "{row_label}" não foi localizada.')

    dialog = None
    field = None
    # O Blogger anima alguns modais e pode manter overlays/toasts visíveis.
    # Retry curto, somente para localizar o editor; nenhuma escrita ocorre até encontrá-lo.
    for _ in range(12):
        page.wait_for_timeout(150)
        dialog, field = _find_dialog_text_field(page, field_labels)
        if field is not None:
            break
    if field is None or dialog is None:
        raise SettingsError(f'Campo editável de "{row_label}" não foi localizado.')

    maxlength = field.get_attribute("maxlength")
    if maxlength and len(value) > int(maxlength):
        raise SettingsError(f'Valor de "{row_label}" excede o limite de {maxlength} caracteres.')

    field.fill(value)
    click_dialog_action(page, "SALVAR", dialog=dialog)
    return {"row": row_label, "value": value, "maxlength": maxlength}


def checkbox(page, aria_label: str):
    return first_visible(page.locator(f'[role="checkbox"][aria-label="{aria_label}"]'))


def set_checkbox(page, aria_label: str, desired: bool) -> dict:
    loc = checkbox(page, aria_label)
    if loc is None:
        raise SettingsError(f'Controle "{aria_label}" não foi localizado.')
    before = loc.get_attribute("aria-checked") == "true"
    changed = False
    if before != desired:
        try:
            loc.click(timeout=5_000)
        except Exception:
            loc.evaluate("el => el.click()")
        page.wait_for_timeout(650)
        changed = True
        loc = checkbox(page, aria_label)
        if loc is None:
            raise SettingsError(f'Controle "{aria_label}" desapareceu após a alteração.')
    after = loc.get_attribute("aria-checked") == "true"
    if after != desired:
        raise SettingsError(f'Controle "{aria_label}" não assumiu o estado esperado.')
    return {"label": aria_label, "before": before, "after": after, "changed": changed}


def set_timezone(page, target: str) -> dict:
    if not core.click_row_prefix(page, "Fuso horário"):
        raise SettingsError("Fuso horário não foi localizado.")
    page.wait_for_timeout(500)
    dialog = visible_dialog(page)
    target_loc = dialog.get_by_text(target, exact=True)
    chosen = None
    for i in range(target_loc.count()):
        item = target_loc.nth(i)
        try:
            item.scroll_into_view_if_needed(timeout=4_000)
            page.wait_for_timeout(150)
            if item.is_visible():
                chosen = item
                break
        except Exception:
            continue
    if chosen is None:
        raise SettingsError(f'Fuso alvo não localizado: {target}')
    try:
        chosen.click(timeout=5_000)
    except Exception:
        chosen.evaluate("el => el.click()")
    page.wait_for_timeout(250)
    click_dialog_action(page, "SALVAR", dialog=dialog)
    return {"target": target, "selected_and_saved": True}


def snapshot(page) -> dict:
    return {
        "search_visibility": core.checkbox_state(page, "Visível para mecanismos de pesquisa"),
        "https_redirect": core.checkbox_state(page, "Redirecionamento para HTTPS"),
        "lazy_images": core.checkbox_state(page, "Imagens com carregamento lento"),
        "webp_images": core.checkbox_state(page, "Veiculação de imagens WebP"),
        "search_description": core.checkbox_state(page, "Ativar a descrição de pesquisa"),
        "custom_robots_txt": core.checkbox_state(page, "Ativar robots.txt personalizado"),
        "custom_robots_headers": core.checkbox_state(page, "Ativar as tags personalizadas de cabeçalho de robôs"),
        "timezone_row": core.row_text(page, "Fuso horário"),
        "description_row": core.row_text(page, "Descrição"),
        "search_description_row": core.row_text(page, "Descrição da pesquisa"),
    }


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Configura perfil-base seguro do Blogger.")
    p.add_argument("--expected-blog-id", required=True)
    p.add_argument("--description", required=True)
    p.add_argument("--search-description", required=True)
    p.add_argument("--timezone", default=DEFAULT_TIMEZONE)
    p.add_argument("--apply", action="store_true")
    p.add_argument("--confirm", default="")
    return p


def validate_args(args) -> None:
    if not re.fullmatch(r"\d+", args.expected_blog_id):
        raise SettingsError("Blog ID esperado inválido.")
    if not (1 <= len(args.description) <= 500):
        raise SettingsError("Descrição deve ter entre 1 e 500 caracteres.")
    if not (1 <= len(args.search_description) <= 500):
        raise SettingsError("Descrição de pesquisa deve ter entre 1 e 500 caracteres.")
    if args.apply and args.confirm != CONFIRMATION:
        raise SettingsError(f'Para aplicar, use --confirm "{CONFIRMATION}".')
    if not args.apply and args.confirm:
        raise SettingsError("--confirm só pode ser usado junto com --apply.")


def main() -> int:
    args = build_parser().parse_args()
    validate_args(args)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        _, context = bp.connect_official_chrome(p, CDP_URL)
        page = bp.select_page(context)
        bp.require_blogger_session(page)

        blog_id = bp.extract_current_blog_id(page)
        if blog_id != args.expected_blog_id:
            raise SettingsError(
                f"Blog errado bloqueado: atual={blog_id!r}, esperado={args.expected_blog_id!r}."
            )
        core.goto_settings(page, blog_id)
        before = snapshot(page)

        plan = {
            "description": args.description,
            "search_visibility": True,
            "https_redirect": True,
            "lazy_images": True,
            "webp_images": True,
            "search_description_enabled": True,
            "search_description": args.search_description,
            "timezone": args.timezone,
            "custom_robots_txt": "UNCHANGED",
            "custom_robots_headers": "UNCHANGED",
        }

        if not args.apply:
            result = {
                "status": "SETTINGS_PREFLIGHT_OK",
                "read_only": True,
                "blog_id": blog_id,
                "settings_url": bp.sanitize_url(page.url),
                "current": before,
                "planned": plan,
                "message": (
                    f'Nenhuma configuração foi alterada. Para aplicar após revisar, use '
                    f'--apply --confirm "{CONFIRMATION}".'
                ),
            }
            (OUT_DIR / "settings_profile_preflight.json").write_text(
                json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0

        actions = []
        actions.append(set_dialog_text(page, "Descrição", args.description, ("Descrição", "Description")))
        actions.append(set_checkbox(page, "Visível para mecanismos de pesquisa", True))
        actions.append(set_checkbox(page, "Redirecionamento para HTTPS", True))
        actions.append(set_checkbox(page, "Imagens com carregamento lento", True))
        actions.append(set_checkbox(page, "Veiculação de imagens WebP", True))
        actions.append(set_checkbox(page, "Ativar a descrição de pesquisa", True))
        page.wait_for_timeout(500)
        actions.append(set_dialog_text(
            page,
            "Descrição da pesquisa",
            args.search_description,
            ("Descrição da pesquisa", "Descrição de pesquisa", "Search description"),
        ))
        actions.append(set_timezone(page, args.timezone))

        page.wait_for_timeout(800)
        after = snapshot(page)

        for key in (
            "search_visibility",
            "https_redirect",
            "lazy_images",
            "webp_images",
            "search_description",
        ):
            if after[key].get("aria_checked") != "true":
                raise SettingsError(f"Validação final falhou para {key}.")

        if after["custom_robots_txt"].get("aria_checked") != before["custom_robots_txt"].get("aria_checked"):
            raise SettingsError("robots.txt personalizado mudou inesperadamente.")
        if after["custom_robots_headers"].get("aria_checked") != before["custom_robots_headers"].get("aria_checked"):
            raise SettingsError("Tags personalizadas de robôs mudaram inesperadamente.")

        result = {
            "status": "SETTINGS_PROFILE_VALIDATED",
            "read_only": False,
            "blog_id": blog_id,
            "settings_url": bp.sanitize_url(page.url),
            "planned": plan,
            "before": before,
            "actions": actions,
            "after": after,
            "robots_untouched": True,
        }
        (OUT_DIR / "settings_profile_apply.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
