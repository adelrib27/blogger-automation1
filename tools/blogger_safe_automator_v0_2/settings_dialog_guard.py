from __future__ import annotations

import re

import configure_core_settings as cfg


def _dialog_for_field(field):
    dialog = field.locator('xpath=ancestor::*[@role="dialog"][1]')
    item = cfg.first_visible(dialog)
    if item is None:
        raise cfg.SettingsError("O campo editável foi encontrado, mas seu diálogo ativo não foi identificado.")
    return item


def _field_by_aria(page, field_labels: tuple[str, ...]):
    for aria in field_labels:
        item = cfg.first_visible(
            page.locator(f'textarea[aria-label="{aria}"], input[aria-label="{aria}"]')
        )
        if item is not None:
            return item
    return None


def _single_visible_dialog_field(page):
    fields = []
    dialogs = page.locator('[role="dialog"]')
    for i in range(dialogs.count()):
        dialog = dialogs.nth(i)
        try:
            if not dialog.is_visible():
                continue
        except Exception:
            continue
        item = cfg.first_visible(dialog.locator('textarea, input[type="text"]'))
        if item is not None:
            fields.append(item)
    if len(fields) == 1:
        return fields[0]
    if len(fields) > 1:
        raise cfg.SettingsError(
            "Mais de um campo editável está visível; operação bloqueada para evitar editar o diálogo errado."
        )
    return None


def _click_action_in_dialog(page, dialog, label: str) -> None:
    pattern = re.compile(rf"^{re.escape(label)}$", re.I)
    for loc in (
        dialog.get_by_role("button", name=pattern),
        dialog.get_by_text(pattern, exact=True),
    ):
        item = cfg.first_visible(loc)
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
    raise cfg.SettingsError(f'Botão "{label}" não foi localizado no diálogo correto.')


def set_dialog_text(page, row_label: str, value: str, field_labels: tuple[str, ...]) -> dict:
    # Reaproveita um diálogo já aberto pela própria automação, se existir.
    field = _field_by_aria(page, field_labels)
    if field is None:
        if not cfg.core.click_row_prefix(page, row_label):
            raise cfg.SettingsError(f'Configuração "{row_label}" não foi localizada.')
        page.wait_for_timeout(350)
        field = _field_by_aria(page, field_labels)

    # Fallback restrito: somente um campo editável dentro de diálogo visível.
    if field is None:
        field = _single_visible_dialog_field(page)
    if field is None:
        raise cfg.SettingsError(f'Campo editável de "{row_label}" não foi localizado.')

    dialog = _dialog_for_field(field)
    maxlength = field.get_attribute("maxlength")
    if maxlength and len(value) > int(maxlength):
        raise cfg.SettingsError(f'Valor de "{row_label}" excede o limite de {maxlength} caracteres.')

    field.fill(value)
    _click_action_in_dialog(page, dialog, "SALVAR")
    return {
        "row": row_label,
        "value": value,
        "maxlength": maxlength,
        "dialog_guard": "field_anchored",
    }


def _timezone_dialog(page):
    pattern = re.compile(r"^Fuso horário(?:\s|$)", re.I)
    dialogs = page.locator('[role="dialog"]').filter(has_text=pattern)
    candidates = []
    for i in range(dialogs.count()):
        item = dialogs.nth(i)
        try:
            if item.is_visible():
                candidates.append(item)
        except Exception:
            continue
    if len(candidates) > 1:
        raise cfg.SettingsError("Mais de um diálogo de fuso horário está visível; operação bloqueada.")
    return candidates[0] if candidates else None


def set_timezone(page, target: str) -> dict:
    dialog = _timezone_dialog(page)
    if dialog is None:
        if not cfg.core.click_row_prefix(page, "Fuso horário"):
            raise cfg.SettingsError("Fuso horário não foi localizado.")
        page.wait_for_timeout(500)
        dialog = _timezone_dialog(page)
    if dialog is None:
        raise cfg.SettingsError("Diálogo de fuso horário não foi identificado com segurança.")

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
        raise cfg.SettingsError(f'Fuso alvo não localizado: {target}')

    try:
        chosen.click(timeout=5_000)
    except Exception:
        chosen.evaluate("el => el.click()")
    page.wait_for_timeout(250)
    _click_action_in_dialog(page, dialog, "SALVAR")
    return {
        "target": target,
        "selected_and_saved": True,
        "dialog_guard": "timezone_anchored",
    }
