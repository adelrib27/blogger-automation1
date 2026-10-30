#!/usr/bin/env python3
from __future__ import annotations

import re

import configure_core_settings as cfg
import timezone_resilience_v07 as base


def _visible_gmt_signature(page) -> tuple[str, ...]:
    try:
        rows = page.evaluate(
            """() => {
                const visible = el => {
                    const r = el.getBoundingClientRect();
                    const s = getComputedStyle(el);
                    return r.width > 0 && r.height > 0 && s.display !== 'none' &&
                           s.visibility !== 'hidden' && r.bottom > 0 && r.top < innerHeight &&
                           r.right > 0 && r.left < innerWidth;
                };
                const out = [];
                for (const root of [...document.querySelectorAll('[role="dialog"]')].filter(visible)) {
                    for (const el of root.querySelectorAll('li,[role="option"],[role="radio"],div,span')) {
                        if (!visible(el)) continue;
                        const text = String(el.innerText || el.textContent || '').trim().replace(/\s+/g, ' ');
                        if (!/^\(GMT[+-]\d\d:\d\d\)/i.test(text) || text.length > 180) continue;
                        if (!out.includes(text)) out.push(text);
                        if (out.length >= 20) return out;
                    }
                }
                return out;
            }"""
        ) or []
    except Exception:
        rows = []
    return tuple(str(x) for x in rows)


def _mark_visible_gmt_row(page) -> bool:
    try:
        return bool(page.evaluate(
            """() => {
                const ATTR = 'data-blogger-tz-wheel-anchor-v07';
                document.querySelectorAll('[' + ATTR + ']').forEach(el => el.removeAttribute(ATTR));
                const visible = el => {
                    const r = el.getBoundingClientRect();
                    const s = getComputedStyle(el);
                    return r.width > 0 && r.height > 0 && s.display !== 'none' &&
                           s.visibility !== 'hidden' && r.bottom > 0 && r.top < innerHeight &&
                           r.right > 0 && r.left < innerWidth;
                };
                let best = null;
                for (const root of [...document.querySelectorAll('[role="dialog"]')].filter(visible)) {
                    for (const el of root.querySelectorAll('li,[role="option"],[role="radio"],[role="button"],[tabindex="0"],div,span')) {
                        if (!visible(el)) continue;
                        const text = String(el.innerText || el.textContent || '').trim().replace(/\s+/g, ' ');
                        if (!/^\(GMT[+-]\d\d:\d\d\)/i.test(text) || text.length > 180) continue;
                        const r = el.getBoundingClientRect();
                        const area = Math.max(1, r.width * r.height);
                        if (!best || area < best.area) best = {el, area};
                    }
                }
                if (!best) return false;
                best.el.setAttribute(ATTR, '1');
                return true;
            }"""
        ))
    except Exception:
        return False


def _advance_timezone_list(page) -> bool:
    before = _visible_gmt_signature(page)
    if not _mark_visible_gmt_row(page):
        return False

    anchor = page.locator('[data-blogger-tz-wheel-anchor-v07="1"]').first
    try:
        box = anchor.bounding_box()
    except Exception:
        box = None

    if box:
        try:
            page.mouse.move(box["x"] + box["width"] * 0.5, box["y"] + box["height"] * 0.5)
            page.mouse.wheel(0, 1100)
            page.wait_for_timeout(220)
            after = _visible_gmt_signature(page)
            if after and after != before:
                return True
        except Exception:
            pass

    # Se a lista não reagiu ao wheel, dê foco sem clicar/selecionar a linha e use teclado.
    try:
        anchor.evaluate(
            """el => {
                if (!el.hasAttribute('tabindex')) el.setAttribute('tabindex', '-1');
                el.focus({preventScroll:true});
            }"""
        )
        for key in ("PageDown", "PageDown", "ArrowDown", "ArrowDown", "ArrowDown"):
            page.keyboard.press(key)
            page.wait_for_timeout(90)
        after = _visible_gmt_signature(page)
        if after and after != before:
            return True
    except Exception:
        pass

    # Último fallback: foco no diálogo e PageDown, ainda sem selecionar opção alguma.
    try:
        dialog = page.locator('[role="dialog"]:visible').last
        dialog.evaluate(
            """el => {
                if (!el.hasAttribute('tabindex')) el.setAttribute('tabindex', '-1');
                el.focus({preventScroll:true});
            }"""
        )
        page.keyboard.press("PageDown")
        page.wait_for_timeout(120)
        after = _visible_gmt_signature(page)
        return bool(after and after != before)
    except Exception:
        return False


def set_timezone_keyboard_resilient(page, target: str) -> dict:
    editor = base._click_timezone_row(page)
    page.wait_for_timeout(220)

    # Alguns layouts expõem um seletor interno; abra-o antes de navegar.
    if base._find_candidate(page, target) is None:
        base._open_nested_selector(page)

    chosen = None
    chosen_text = ""
    seen_signatures: set[tuple[str, ...]] = set()

    for _ in range(30):
        match = base._find_candidate(page, target)
        if match is not None:
            _, chosen, chosen_text = match
            break

        signature = _visible_gmt_signature(page)
        if signature in seen_signatures:
            # Tente mais um avanço físico; se não mudar, encerre fail-closed.
            if not _advance_timezone_list(page):
                break
        else:
            seen_signatures.add(signature)
            if not _advance_timezone_list(page):
                break

    if chosen is None:
        visible = " | ".join(_visible_gmt_signature(page))
        editor_desc = (
            f"role={editor.get('role')} aria={editor.get('aria')} "
            f"text={editor.get('text','')[:500]}"
        )
        raise cfg.SettingsError(
            f'Fuso alvo não localizado após navegação física: {target}. '
            f'Editor real: {editor_desc}. Fusos visíveis finais: {visible[:1800]}'
        )

    try:
        chosen.scroll_into_view_if_needed(timeout=1500)
    except Exception:
        pass
    try:
        chosen.click(timeout=3500)
    except Exception:
        chosen.evaluate("el => el.click()")
    page.wait_for_timeout(300)

    cfg.click_dialog_action(page, "SALVAR")
    return {
        "target": target,
        "matched_text": chosen_text,
        "selected_and_saved": True,
        "navigation": "wheel-keyboard-visible-gmt-anchor",
    }


def install() -> None:
    cfg.set_timezone = set_timezone_keyboard_resilient
