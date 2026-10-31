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


def _ancestor_viewport_step(page) -> dict:
    """Parte de uma linha GMT visível e move o primeiro ancestral realmente rolável."""
    try:
        result = page.evaluate(
            """() => {
                const anchor = document.querySelector('[data-blogger-tz-wheel-anchor-v07="1"]');
                if (!anchor) return {moved:false, reason:'no-anchor', chain:[]};
                const chain = [];
                let node = anchor.parentElement;
                let chosen = null;
                let depth = 0;
                while (node && node !== document.body && depth < 14) {
                    const s = getComputedStyle(node);
                    const r = node.getBoundingClientRect();
                    const max = Math.max(0, node.scrollHeight - node.clientHeight);
                    const meta = {
                        depth,
                        tag: node.tagName,
                        role: node.getAttribute('role') || '',
                        cls: String(node.className || '').slice(0,180),
                        overflowY: s.overflowY,
                        scrollTop: Math.round(node.scrollTop || 0),
                        scrollHeight: Math.round(node.scrollHeight || 0),
                        clientHeight: Math.round(node.clientHeight || 0),
                        maxScroll: Math.round(max),
                        h: Math.round(r.height || 0),
                    };
                    chain.push(meta);
                    if (!chosen && max > 16 && ['auto','scroll','overlay'].includes(s.overflowY)) {
                        chosen = node;
                    }
                    node = node.parentElement;
                    depth += 1;
                }
                if (!chosen) {
                    // Alguns componentes virtuais deixam overflowY=visible/hidden,
                    // mas ainda expõem scrollHeight > clientHeight. Use o ancestral mais próximo.
                    node = anchor.parentElement;
                    depth = 0;
                    while (node && node !== document.body && depth < 14) {
                        const max = Math.max(0, node.scrollHeight - node.clientHeight);
                        if (max > 16) { chosen = node; break; }
                        node = node.parentElement;
                        depth += 1;
                    }
                }
                if (!chosen) return {moved:false, reason:'no-scrollable-ancestor', chain};
                const before = chosen.scrollTop;
                const max = Math.max(0, chosen.scrollHeight - chosen.clientHeight);
                const step = Math.max(240, chosen.clientHeight * 0.78);
                chosen.scrollTop = Math.min(max, before + step);
                chosen.dispatchEvent(new Event('scroll', {bubbles:true}));
                return {
                    moved: Math.abs(chosen.scrollTop - before) > 1,
                    reason: 'ancestor-scroll',
                    before: Math.round(before),
                    after: Math.round(chosen.scrollTop),
                    maxScroll: Math.round(max),
                    chosen: {
                        tag: chosen.tagName,
                        role: chosen.getAttribute('role') || '',
                        cls: String(chosen.className || '').slice(0,180),
                        overflowY: getComputedStyle(chosen).overflowY,
                    },
                    chain,
                };
            }"""
        )
        return result or {"moved": False, "reason": "empty"}
    except Exception as exc:
        return {"moved": False, "reason": f"evaluate-error:{type(exc).__name__}"}


def _advance_timezone_list(page) -> tuple[bool, dict]:
    before = _visible_gmt_signature(page)
    if not _mark_visible_gmt_row(page):
        return False, {"reason": "no-visible-gmt-row"}

    structural = _ancestor_viewport_step(page)
    page.wait_for_timeout(180)
    after = _visible_gmt_signature(page)
    if after and after != before:
        return True, structural

    anchor = page.locator('[data-blogger-tz-wheel-anchor-v07="1"]').first
    try:
        box = anchor.bounding_box()
    except Exception:
        box = None

    if box:
        try:
            page.mouse.move(box["x"] + box["width"] * 0.5, box["y"] + box["height"] * 0.5)
            page.mouse.wheel(0, 900)
            page.wait_for_timeout(180)
            after = _visible_gmt_signature(page)
            if after and after != before:
                return True, {**structural, "fallback": "wheel"}
        except Exception:
            pass

    try:
        anchor.evaluate(
            """el => {
                if (!el.hasAttribute('tabindex')) el.setAttribute('tabindex', '-1');
                el.focus({preventScroll:true});
            }"""
        )
        for key in ("PageDown", "PageDown", "ArrowDown", "ArrowDown"):
            page.keyboard.press(key)
            page.wait_for_timeout(70)
        after = _visible_gmt_signature(page)
        if after and after != before:
            return True, {**structural, "fallback": "keyboard"}
    except Exception:
        pass

    return False, structural


def set_timezone_keyboard_resilient(page, target: str) -> dict:
    editor = base._click_timezone_row(page)
    page.wait_for_timeout(220)

    if base._find_candidate(page, target) is None:
        base._open_nested_selector(page)

    chosen = None
    chosen_text = ""
    seen_signatures: set[tuple[str, ...]] = set()
    last_diag: dict = {}

    for _ in range(30):
        match = base._find_candidate(page, target)
        if match is not None:
            _, chosen, chosen_text = match
            break

        signature = _visible_gmt_signature(page)
        if signature in seen_signatures:
            moved, last_diag = _advance_timezone_list(page)
            if not moved:
                break
        else:
            seen_signatures.add(signature)
            moved, last_diag = _advance_timezone_list(page)
            if not moved:
                break

    if chosen is None:
        visible = " | ".join(_visible_gmt_signature(page))
        editor_desc = (
            f"role={editor.get('role')} aria={editor.get('aria')} "
            f"text={editor.get('text','')[:500]}"
        )
        chain = last_diag.get("chain") or []
        chain_text = " || ".join(
            f"d={x.get('depth')} {x.get('tag')} role={x.get('role')} ov={x.get('overflowY')} "
            f"top={x.get('scrollTop')} sh={x.get('scrollHeight')} ch={x.get('clientHeight')} max={x.get('maxScroll')} cls={x.get('cls')}"
            for x in chain[:10]
        )
        raise cfg.SettingsError(
            f'Fuso alvo não localizado após navegação estrutural: {target}. '
            f'Editor real: {editor_desc}. Fusos visíveis finais: {visible[:1200]}. '
            f'Diagnóstico de viewport: reason={last_diag.get("reason")} chosen={last_diag.get("chosen")} '
            f'before={last_diag.get("before")} after={last_diag.get("after")} max={last_diag.get("maxScroll")}. '
            f'Ancestrais: {chain_text[:1800]}'
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
        "navigation": "gmt-row-ancestor-viewport",
    }


def install() -> None:
    cfg.set_timezone = set_timezone_keyboard_resilient
