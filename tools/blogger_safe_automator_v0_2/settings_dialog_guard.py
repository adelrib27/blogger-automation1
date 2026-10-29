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


def _current_timezone_matches(page, target: str) -> bool:
    current = cfg.core.row_text(page, "Fuso horário") or ""
    return target in current


def _target_in_timezone_dialog(page, target: str):
    """Return (target item, ancestor dialog) anchored by the exact timezone text.

    We deliberately do not identify the modal by its title because Blogger exposes
    unrelated UI containers as role=dialog. The exact timezone option is the safe
    anchor; its closest visible role=dialog is then used for the SAVE action.
    """
    matches = page.get_by_text(target, exact=True)
    candidates = []
    for i in range(matches.count()):
        item = matches.nth(i)
        dialog = item.locator('xpath=ancestor::*[@role="dialog"][1]')
        try:
            if dialog.count() == 0 or not dialog.first.is_visible():
                continue
            # The option may start outside the viewport; scroll it before testing visibility.
            item.scroll_into_view_if_needed(timeout=4_000)
            page.wait_for_timeout(150)
            if not item.is_visible():
                continue
            candidates.append((item, dialog.first))
        except Exception:
            continue

    if len(candidates) > 1:
        raise cfg.SettingsError(
            "Mais de uma opção idêntica de fuso horário está visível em diálogos distintos; operação bloqueada."
        )
    return candidates[0] if candidates else (None, None)


def set_timezone(page, target: str) -> dict:
    # Idempotência: se a linha já mostra exatamente o fuso desejado, não abra modal nem salve.
    if _current_timezone_matches(page, target):
        return {
            "target": target,
            "selected_and_saved": True,
            "changed": False,
            "dialog_guard": "already_selected",
        }

    if not cfg.core.click_row_prefix(page, "Fuso horário"):
        raise cfg.SettingsError("Fuso horário não foi localizado.")
    page.wait_for_timeout(500)

    chosen, dialog = _target_in_timezone_dialog(page, target)
    if chosen is None or dialog is None:
        raise cfg.SettingsError(
            "Opção exata do fuso horário não foi identificada dentro de um diálogo visível."
        )

    try:
        chosen.click(timeout=5_000)
    except Exception:
        chosen.evaluate("el => el.click()")
    page.wait_for_timeout(250)
    _click_action_in_dialog(page, dialog, "SALVAR")

    if not _current_timezone_matches(page, target):
        raise cfg.SettingsError("Fuso horário não foi confirmado na linha de configurações após salvar.")

    return {
        "target": target,
        "selected_and_saved": True,
        "changed": True,
        "dialog_guard": "target_anchored",
    }
