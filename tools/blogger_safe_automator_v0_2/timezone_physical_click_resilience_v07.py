#!/usr/bin/env python3
from __future__ import annotations

import configure_core_settings as cfg
import timezone_resilience_v07 as base
import timezone_offscreen_resilience_v07 as offscreen


def _physical_click_center(page, locator) -> bool:
    try:
        locator.scroll_into_view_if_needed(timeout=1800)
    except Exception:
        pass
    try:
        box = locator.bounding_box()
    except Exception:
        box = None
    if not box or box.get("width", 0) <= 0 or box.get("height", 0) <= 0:
        return False
    x = box["x"] + box["width"] * 0.5
    y = box["y"] + box["height"] * 0.5
    try:
        page.mouse.move(x, y)
        page.wait_for_timeout(60)
        page.mouse.down()
        page.wait_for_timeout(80)
        page.mouse.up()
        page.wait_for_timeout(220)
        return True
    except Exception:
        return False


def _try_physical_targets(page, target: str):
    # 1) Radio real marcado pela rotina anterior.
    control = page.locator(f'[{offscreen.CONTROL_ATTR}="1"]').first
    try:
        if control.count() and _physical_click_center(page, control):
            meta = offscreen._selection_meta(page)
            if offscreen._is_selected(meta):
                return meta
    except Exception:
        pass

    # 2) Texto exato da opção São Paulo.
    exact = page.get_by_text(target, exact=True)
    try:
        count = exact.count()
    except Exception:
        count = 0

    for i in range(count - 1, -1, -1):
        node = exact.nth(i)
        try:
            node.scroll_into_view_if_needed(timeout=1800)
        except Exception:
            pass

        # Clique físico no texto e depois, no máximo, nos 5 ancestrais imediatos
        # que ainda pertencem à mesma linha/opção.
        current = node
        for depth in range(6):
            try:
                text = current.inner_text(timeout=500).strip()
            except Exception:
                text = ""
            if depth > 0 and target not in text:
                break
            if _physical_click_center(page, current):
                meta = offscreen._selection_meta(page)
                if offscreen._is_selected(meta):
                    return meta
            try:
                current = current.locator("xpath=..").first
            except Exception:
                break

    return offscreen._selection_meta(page)


def set_timezone_physical_click_resilient(page, target: str) -> dict:
    editor = base._click_timezone_row(page)
    page.wait_for_timeout(180)
    try:
        base._open_nested_selector(page)
    except Exception:
        pass
    page.wait_for_timeout(140)

    meta = offscreen._mark_exact_target_control(page, target)
    if meta is None:
        try:
            dialog_text = page.locator('[role="dialog"]:visible').last.inner_text(timeout=1000)
        except Exception:
            dialog_text = ""
        raise cfg.SettingsError(
            f'Fuso alvo não localizado antes do clique físico: {target}. '
            f'Editor real: role={editor.get("role")} aria={editor.get("aria")} '
            f'text={editor.get("text", "")[:500]}. Texto do modal: {str(dialog_text)[:1600]}'
        )

    control = offscreen._bring_control_into_view(page)
    if control is None:
        raise cfg.SettingsError(
            f'Fuso alvo foi localizado, mas o controle não entrou na viewport antes do clique físico: {target}. Alvo={meta}'
        )

    before = offscreen._selection_meta(page)
    after = _try_physical_targets(page, target)
    if not offscreen._is_selected(after):
        raise cfg.SettingsError(
            f'GMT-03 foi localizado e ficou visível, mas o clique físico também não ativou a opção. '
            f'Alvo={meta}. Antes={before}. Depois={after}.'
        )

    cfg.click_dialog_action(page, "SALVAR")
    return {
        "target": target,
        "matched_text": str(meta.get("text") or ""),
        "selected_and_saved": True,
        "selection_meta": after,
        "navigation": "physical-mouse-radio-text-ancestor",
    }


def install() -> None:
    cfg.set_timezone = set_timezone_physical_click_resilient
