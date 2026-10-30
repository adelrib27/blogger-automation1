#!/usr/bin/env python3
from __future__ import annotations

import timezone_offscreen_resilience_v07 as offscreen

_ORIGINAL_MARK = offscreen._mark_exact_target_control


def _gmt_tail_signature(page) -> tuple[str, ...]:
    try:
        rows = page.evaluate(
            """() => {
                const norm = s => String(s || '').trim().replace(/\s+/g, ' ');
                const dialogs = [...document.querySelectorAll('[role="dialog"]')];
                const out = [];
                for (const dialog of dialogs) {
                    for (const el of dialog.querySelectorAll('*')) {
                        const text = norm(el.innerText || el.textContent || '');
                        if (!/^\(GMT[+-]\d\d:\d\d\)/i.test(text) || text.length > 180) continue;
                        let childSame = false;
                        for (const child of el.children || []) {
                            const ct = norm(child.innerText || child.textContent || '');
                            if (/^\(GMT[+-]\d\d:\d\d\)/i.test(ct) && ct.length <= 180) {
                                childSame = true;
                                break;
                            }
                        }
                        if (childSame) continue;
                        if (!out.includes(text)) out.push(text);
                    }
                }
                return out.slice(-8);
            }"""
        ) or []
    except Exception:
        rows = []
    return tuple(str(x) for x in rows)


def _mark_last_materialized_gmt(page) -> bool:
    try:
        return bool(page.evaluate(
            """() => {
                const ATTR = 'data-blogger-tz-virtual-tail-v07';
                document.querySelectorAll('[' + ATTR + ']').forEach(el => el.removeAttribute(ATTR));
                const norm = s => String(s || '').trim().replace(/\s+/g, ' ');
                const dialogs = [...document.querySelectorAll('[role="dialog"]')];
                let best = null;
                for (const dialog of dialogs) {
                    for (const el of dialog.querySelectorAll('*')) {
                        const text = norm(el.innerText || el.textContent || '');
                        if (!/^\(GMT[+-]\d\d:\d\d\)/i.test(text) || text.length > 180) continue;
                        let childSame = false;
                        for (const child of el.children || []) {
                            const ct = norm(child.innerText || child.textContent || '');
                            if (/^\(GMT[+-]\d\d:\d\d\)/i.test(ct) && ct.length <= 180) {
                                childSame = true;
                                break;
                            }
                        }
                        if (childSame) continue;
                        best = el;
                    }
                }
                if (!best) return false;
                best.setAttribute(ATTR, '1');
                return true;
            }"""
        ))
    except Exception:
        return False


def _advance_virtual_window(page) -> bool:
    before = _gmt_tail_signature(page)
    if not _mark_last_materialized_gmt(page):
        return False

    tail = page.locator('[data-blogger-tz-virtual-tail-v07="1"]').first
    try:
        tail.evaluate("el => el.scrollIntoView({block:'end', inline:'nearest'})")
        page.wait_for_timeout(260)
    except Exception:
        pass

    after = _gmt_tail_signature(page)
    if after and after != before:
        return True

    # Avance o ancestral scrollável real da última linha materializada.
    try:
        moved = bool(tail.evaluate(
            """el => {
                let n = el.parentElement;
                while (n && n !== document.body) {
                    const style = getComputedStyle(n);
                    const max = n.scrollHeight - n.clientHeight;
                    if (max > 24 || ['auto','scroll'].includes(style.overflowY)) {
                        const before = n.scrollTop;
                        const target = Math.min(Math.max(0, max), before + Math.max(260, n.clientHeight * 0.88));
                        n.scrollTop = target;
                        n.dispatchEvent(new Event('scroll', {bubbles:true}));
                        return Math.abs(n.scrollTop - before) > 1;
                    }
                    n = n.parentElement;
                }
                return false;
            }"""
        ))
    except Exception:
        moved = False

    page.wait_for_timeout(260)
    after = _gmt_tail_signature(page)
    if after and after != before:
        return True

    # Último fallback: gesto físico diretamente sobre a última linha já carregada.
    try:
        box = tail.bounding_box()
    except Exception:
        box = None
    if box:
        try:
            page.mouse.move(box['x'] + box['width'] * 0.5, box['y'] + box['height'] * 0.5)
            page.mouse.wheel(0, 900)
            page.wait_for_timeout(260)
        except Exception:
            pass
    final = _gmt_tail_signature(page)
    return bool(final and final != before) or moved


def _mark_with_virtual_window(page, target: str):
    meta = _ORIGINAL_MARK(page, target)
    if meta is not None:
        return meta

    seen: set[tuple[str, ...]] = set()
    for _ in range(18):
        signature = _gmt_tail_signature(page)
        if signature in seen:
            if not _advance_virtual_window(page):
                break
        else:
            seen.add(signature)
            if not _advance_virtual_window(page):
                break
        meta = _ORIGINAL_MARK(page, target)
        if meta is not None:
            return meta
    return None


def install() -> None:
    offscreen._mark_exact_target_control = _mark_with_virtual_window
