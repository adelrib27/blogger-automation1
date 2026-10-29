from __future__ import annotations

import re
import unicodedata

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


def _wait_for_field_by_aria(page, field_labels: tuple[str, ...], timeout_ms: int = 5_000):
    """Wait for Blogger's edit field to become visible after opening a dialog.

    Some Blogger builds animate/render the modal after the settings row click. A
    fixed short sleep can race that render and incorrectly report that the field is
    missing. Poll only the exact aria-labelled field; never broaden the selector.
    """
    interval_ms = 100
    attempts = max(1, int(timeout_ms / interval_ms))
    for _ in range(attempts):
        field = _field_by_aria(page, field_labels)
        if field is not None:
            return field
        page.wait_for_timeout(interval_ms)
    return _field_by_aria(page, field_labels)


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


def _norm_setting_text(value: str | None) -> str:
    text = unicodedata.normalize("NFKC", value or "")
    text = text.replace("\u00a0", " ").replace("\u202f", " ")
    return re.sub(r"\s+", " ", text).strip()


def _field_value_matches(field, value: str) -> bool:
    try:
        current = field.input_value()
    except Exception:
        try:
            current = field.get_attribute("value") or ""
        except Exception:
            return False
    return _norm_setting_text(current) == _norm_setting_text(value)


def _item_belongs_to_setting_row(item, row_label: str) -> bool:
    """Require the displayed value to share a reasonably close ancestor with its row label."""
    try:
        return bool(
            item.evaluate(
                r"""(el, label) => {
                  const norm = v => String(v || '')
                    .normalize('NFKC')
                    .replace(/[\u00a0\u202f]/g, ' ')
                    .replace(/\s+/g, ' ')
                    .trim();
                  const wanted = norm(label);
                  let node = el;
                  for (let depth = 0; node && node !== document.body && depth < 8; depth++, node = node.parentElement) {
                    const text = norm(node.innerText || node.textContent);
                    if (text === wanted || text.startsWith(wanted + ' ')) return true;
                  }
                  return false;
                }""",
                row_label,
            )
        )
    except Exception:
        return False


def _current_text_setting_matches(page, row_label: str, value: str) -> bool:
    """Read-only idempotency check for Blogger text settings.

    Prefer the existing row reader when Blogger exposes label+value together. When
    Blogger splits them into sibling nodes, accept an exact visible value only if it
    is outside a visible dialog and belongs to an ancestor beginning with the row
    label. This avoids treating unrelated page text as the setting value.
    """
    current = cfg.core.row_text(page, row_label) or ""
    current_norm = _norm_setting_text(current)
    value_norm = _norm_setting_text(value)
    if value_norm and value_norm in current_norm:
        return True

    matches = page.get_by_text(value, exact=True)
    for i in range(matches.count()):
        item = matches.nth(i)
        try:
            if not item.is_visible() or _has_visible_dialog_ancestor(item):
                continue
            if _item_belongs_to_setting_row(item, row_label):
                return True
        except Exception:
            continue
    return False


def _text_noop_result(row_label: str, value: str, guard: str) -> dict:
    return {
        "row": row_label,
        "value": value,
        "maxlength": None,
        "changed": False,
        "dialog_guard": guard,
    }


def set_dialog_text(page, row_label: str, value: str, field_labels: tuple[str, ...]) -> dict:
    # First handle a dialog already left open by a previous fail-closed attempt.
    field = _field_by_aria(page, field_labels)
    if field is not None:
        dialog = _dialog_for_field(field)
        if _field_value_matches(field, value):
            _click_action_in_dialog(page, dialog, "CANCELAR")
            return _text_noop_result(row_label, value, "open_field_noop")
    else:
        # Normal idempotent path: if the settings page already displays the exact
        # desired value, do not open the dialog and do not create a write.
        if _current_text_setting_matches(page, row_label, value):
            return _text_noop_result(row_label, value, "already_selected")

        if not cfg.core.click_row_prefix(page, row_label):
            raise cfg.SettingsError(f'Configuração "{row_label}" não foi localizada.')
        field = _wait_for_field_by_aria(page, field_labels, timeout_ms=5_000)

    # Fallback restrito: somente um campo editável dentro de diálogo visível.
    if field is None:
        field = _single_visible_dialog_field(page)
    if field is None:
        # One final read-only check: some Blogger builds update the row but fail to
        # expose the expected textarea. If the exact desired value is already there,
        # treat the operation as a safe no-op rather than forcing a write.
        if _current_text_setting_matches(page, row_label, value):
            return _text_noop_result(row_label, value, "post_click_already_selected")
        raise cfg.SettingsError(f'Campo editável de "{row_label}" não foi localizado.')

    dialog = _dialog_for_field(field)
    maxlength = field.get_attribute("maxlength")
    if maxlength and len(value) > int(maxlength):
        raise cfg.SettingsError(f'Valor de "{row_label}" excede o limite de {maxlength} caracteres.')

    # If opening the dialog reveals that it already contains the desired value,
    # close with CANCELAR. This is still a no-op and avoids needless writes.
    if _field_value_matches(field, value):
        _click_action_in_dialog(page, dialog, "CANCELAR")
        return {
            "row": row_label,
            "value": value,
            "maxlength": maxlength,
            "changed": False,
            "dialog_guard": "opened_field_noop",
        }

    field.fill(value)
    _click_action_in_dialog(page, dialog, "SALVAR")
    return {
        "row": row_label,
        "value": value,
        "maxlength": maxlength,
        "changed": True,
        "dialog_guard": "field_anchored",
    }


def _has_visible_dialog_ancestor(item) -> bool:
    ancestors = item.locator('xpath=ancestor::*[@role="dialog"]')
    for i in range(ancestors.count()):
        try:
            if ancestors.nth(i).is_visible():
                return True
        except Exception:
            continue
    return False


def _norm_timezone_text(value: str | None) -> str:
    """Normalize display-only Unicode differences without changing timezone semantics."""
    text = unicodedata.normalize("NFKC", value or "")
    text = text.replace("\u00a0", " ").replace("\u202f", " ")
    text = re.sub(r"[\u2010\u2011\u2012\u2013\u2014\u2015\u2212]", "-", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text.casefold()


def _current_timezone_matches(page, target: str) -> bool:
    # Primary path: compare the settings row after normalizing harmless display
    # differences (NBSP, repeated whitespace and Unicode dash variants).
    current = cfg.core.row_text(page, "Fuso horário") or ""
    target_norm = _norm_timezone_text(target)
    current_norm = _norm_timezone_text(current)
    if target_norm and target_norm in current_norm:
        return True

    # Some Blogger DOM variants split the label and current value into sibling nodes.
    # Accept the exact visible target only when it is outside any open dialog.
    matches = page.get_by_text(target, exact=True)
    for i in range(matches.count()):
        item = matches.nth(i)
        try:
            if item.is_visible() and not _has_visible_dialog_ancestor(item):
                return True
        except Exception:
            continue
    return False


def _dialog_box_key(dialog):
    """Stable-enough visual key used only to collapse duplicate DOM text nodes.

    Blogger can render multiple matching descendants for one visible radio option.
    Those descendants resolve to the same modal. We deduplicate by the modal's
    visible bounding box; genuinely distinct visible modals remain distinct and
    therefore still trigger fail-closed behavior.
    """
    box = dialog.bounding_box()
    if not box:
        return None
    return tuple(round(float(box[k]), 1) for k in ("x", "y", "width", "height"))


def _dialog_looks_like_timezone(dialog, target: str) -> bool:
    try:
        title = cfg.first_visible(dialog.get_by_text("Fuso horário", exact=True))
        save = cfg.first_visible(
            dialog.get_by_role("button", name=re.compile(r"^SALVAR$", re.I))
        ) or cfg.first_visible(dialog.get_by_text(re.compile(r"^SALVAR$", re.I), exact=True))
        target_item = cfg.first_visible(dialog.get_by_text(target, exact=True))
        return title is not None and save is not None and target_item is not None
    except Exception:
        return False


def _timezone_dialog(page, target: str):
    """Find exactly one active timezone modal, deduplicating same-modal DOM copies."""
    matches = page.get_by_text(target, exact=True)
    by_box = {}

    for i in range(matches.count()):
        item = matches.nth(i)
        try:
            if not item.is_visible():
                continue
            dialog = item.locator('xpath=ancestor::*[@role="dialog"][1]')
            if dialog.count() == 0:
                continue
            dialog = dialog.first
            if not dialog.is_visible() or not _dialog_looks_like_timezone(dialog, target):
                continue
            key = _dialog_box_key(dialog)
            if key is not None:
                by_box.setdefault(key, dialog)
        except Exception:
            continue

    if len(by_box) > 1:
        raise cfg.SettingsError(
            "Mais de um diálogo de fuso horário realmente visível foi encontrado; operação bloqueada."
        )
    return next(iter(by_box.values())) if by_box else None


def _target_control_in_dialog(dialog, target: str):
    # Prefer the semantic radio control. Blogger may duplicate the text in child
    # spans, but normally exposes one role=radio for the actual selectable option.
    radio = cfg.first_visible(dialog.get_by_role("radio", name=target, exact=True))
    if radio is not None:
        return radio

    text_matches = dialog.get_by_text(target, exact=True)
    for i in range(text_matches.count()):
        item = text_matches.nth(i)
        try:
            if not item.is_visible():
                continue
            ancestor_radio = item.locator('xpath=ancestor::*[@role="radio"][1]')
            radio = cfg.first_visible(ancestor_radio)
            if radio is not None:
                return radio
            return item
        except Exception:
            continue
    return None


def _control_is_selected(control) -> bool:
    try:
        aria_checked = control.get_attribute("aria-checked")
        if aria_checked is not None:
            return aria_checked == "true"
    except Exception:
        pass
    try:
        return bool(control.is_checked())
    except Exception:
        return False


def set_timezone(page, target: str) -> dict:
    # If a previous fail-closed attempt left the correct timezone modal open,
    # reuse that modal rather than clicking the settings row again.
    dialog = _timezone_dialog(page, target)

    # Idempotência: if no modal is open and the settings page already shows the
    # requested timezone, do not create a write at all.
    if dialog is None and _current_timezone_matches(page, target):
        return {
            "target": target,
            "selected_and_saved": True,
            "changed": False,
            "dialog_guard": "already_selected",
        }

    if dialog is None:
        if not cfg.core.click_row_prefix(page, "Fuso horário"):
            raise cfg.SettingsError("Fuso horário não foi localizado.")
        page.wait_for_timeout(500)
        dialog = _timezone_dialog(page, target)

    if dialog is None:
        raise cfg.SettingsError(
            "Diálogo ativo de fuso horário não foi identificado com segurança."
        )

    chosen = _target_control_in_dialog(dialog, target)
    if chosen is None:
        raise cfg.SettingsError(f'Fuso alvo não localizado no diálogo ativo: {target}')

    # If Blogger already marks the target radio as selected, close without a write.
    if _control_is_selected(chosen):
        _click_action_in_dialog(page, dialog, "CANCELAR")
        if not _current_timezone_matches(page, target):
            raise cfg.SettingsError(
                "O fuso selecionado no diálogo não correspondeu à linha de configurações após fechar."
            )
        return {
            "target": target,
            "selected_and_saved": True,
            "changed": False,
            "dialog_guard": "selected_radio_noop",
        }

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
        "dialog_guard": "active_modal_radio_anchored",
    }
