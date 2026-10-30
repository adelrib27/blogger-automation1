#!/usr/bin/env python3
from __future__ import annotations

import configure_core_settings as cfg
import timezone_resilience_v07 as base

ATTR = "data-blogger-tz-offscreen-target-v07"


def _mark_exact_target_in_dialog(page, target: str):
    """Localiza o fuso alvo no DOM do modal mesmo quando está recortado/offscreen."""
    try:
        meta = page.evaluate(
            """({target, attr}) => {
                document.querySelectorAll('[' + attr + ']').forEach(el => el.removeAttribute(attr));
                const norm = value => String(value || '')
                    .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
                    .replace(/[–—−]/g, '-').replace(/\s+/g, ' ').trim().toLowerCase();
                const matches = text => {
                    const n = norm(text);
                    const t = norm(target);
                    if (t && n.includes(t)) return true;
                    const compact = n.replace(/\s/g, '');
                    if (!compact.includes('gmt-03:00') && !compact.includes('gmt03:00')) return false;
                    return ['brasilia','sao paulo','horario padrao de brasilia']
                        .some(marker => n.includes(marker));
                };
                const dialogs = [...document.querySelectorAll('[role="dialog"]')];
                let best = null;
                for (const dialog of dialogs) {
                    const nodes = [dialog, ...dialog.querySelectorAll('*')];
                    for (const el of nodes) {
                        const text = String(el.innerText || el.textContent || '').trim().replace(/\s+/g, ' ');
                        if (!text || text.length > 280 || !matches(text)) continue;

                        let clickable = el;
                        for (let depth = 0; depth < 6 && clickable; depth++) {
                            const role = clickable.getAttribute && (clickable.getAttribute('role') || '');
                            const tabindex = clickable.getAttribute && (clickable.getAttribute('tabindex') || '');
                            const style = clickable.nodeType === 1 ? getComputedStyle(clickable) : null;
                            if (['option','menuitemradio','radio','button'].includes(role) ||
                                tabindex === '0' || (style && style.cursor === 'pointer') ||
                                clickable.tagName === 'LI' || clickable.tagName === 'BUTTON') {
                                break;
                            }
                            clickable = clickable.parentElement;
                        }
                        if (!clickable || !dialog.contains(clickable)) clickable = el;

                        const r = clickable.getBoundingClientRect();
                        const role = clickable.getAttribute ? (clickable.getAttribute('role') || '') : '';
                        const tabindex = clickable.getAttribute ? (clickable.getAttribute('tabindex') || '') : '';
                        const style = getComputedStyle(clickable);
                        let score = 0;
                        const n = norm(text);
                        const compact = n.replace(/\s/g, '');
                        if (compact.includes('gmt-03:00') || compact.includes('gmt03:00')) score += 200;
                        if (n.includes('brasilia')) score += 90;
                        if (n.includes('sao paulo')) score += 90;
                        if (n.includes('horario padrao de brasilia')) score += 60;
                        if (['option','menuitemradio','radio','button'].includes(role)) score += 120;
                        if (tabindex === '0') score += 70;
                        if (style.cursor === 'pointer') score += 50;
                        if (clickable.tagName === 'LI' || clickable.tagName === 'BUTTON') score += 40;
                        // Prefere o texto mais específico e o elemento menor.
                        const rank = [score, -text.length, -(Math.max(1, r.width * r.height))];
                        if (!best || rank[0] > best.rank[0] ||
                            (rank[0] === best.rank[0] && rank[1] > best.rank[1]) ||
                            (rank[0] === best.rank[0] && rank[1] === best.rank[1] && rank[2] > best.rank[2])) {
                            best = {el: clickable, text, role, rank};
                        }
                    }
                }
                if (!best) return null;
                best.el.setAttribute(attr, '1');
                const r = best.el.getBoundingClientRect();
                return {
                    text: best.text,
                    role: best.role,
                    tag: best.el.tagName,
                    x: r.x, y: r.y, w: r.width, h: r.height,
                    viewportH: innerHeight
                };
            }""",
            {"target": target, "attr": ATTR},
        )
    except Exception:
        return None
    if not meta:
        return None
    return meta


def _scroll_marked_target_into_view(page):
    item = page.locator(f'[{ATTR}="1"]').first
    try:
        if item.count() == 0:
            return None
    except Exception:
        return None

    try:
        item.evaluate("el => el.scrollIntoView({block:'center', inline:'nearest'})")
        page.wait_for_timeout(250)
    except Exception:
        pass
    try:
        item.scroll_into_view_if_needed(timeout=2500)
        page.wait_for_timeout(180)
    except Exception:
        pass
    return item


def _target_visible_meta(page):
    try:
        return page.evaluate(
            """attr => {
                const el = document.querySelector('[' + attr + '=\"1\"]');
                if (!el) return null;
                const r = el.getBoundingClientRect();
                const s = getComputedStyle(el);
                return {
                    visible: r.width > 0 && r.height > 0 && s.display !== 'none' &&
                             s.visibility !== 'hidden' && r.bottom > 0 && r.top < innerHeight,
                    x:r.x, y:r.y, w:r.width, h:r.height,
                    text:String(el.innerText || el.textContent || '').trim().replace(/\s+/g,' ').slice(0,300),
                    role:el.getAttribute('role') || '', tag:el.tagName
                };
            }""",
            ATTR,
        )
    except Exception:
        return None


def set_timezone_offscreen_resilient(page, target: str) -> dict:
    editor = base._click_timezone_row(page)
    page.wait_for_timeout(220)

    # Alguns layouts criam um seletor interno. Abra-o antes de procurar no DOM completo.
    try:
        base._open_nested_selector(page)
    except Exception:
        pass
    page.wait_for_timeout(180)

    meta = _mark_exact_target_in_dialog(page, target)
    if meta is None:
        # Se realmente não existe no DOM atual, devolva diagnóstico claro em vez de rolar às cegas.
        try:
            dialog_text = page.locator('[role="dialog"]:visible').last.inner_text(timeout=1200)
        except Exception:
            dialog_text = ""
        raise cfg.SettingsError(
            f'Fuso alvo não existe no DOM atual do modal: {target}. '
            f'Editor real: role={editor.get("role")} aria={editor.get("aria")} '
            f'text={editor.get("text", "")[:500]}. '
            f'Texto do modal: {str(dialog_text)[:1800]}'
        )

    item = _scroll_marked_target_into_view(page)
    visible_meta = _target_visible_meta(page)
    if item is None or not visible_meta or not visible_meta.get("visible"):
        raise cfg.SettingsError(
            f'Fuso alvo foi encontrado no DOM, mas não entrou na viewport: {target}. '
            f'Alvo={meta}. Após scroll={visible_meta}.'
        )

    # Clique somente no elemento previamente marcado pela correspondência exata.
    try:
        item.click(timeout=3500)
    except Exception:
        try:
            item.evaluate("el => el.click()")
        except Exception as exc:
            raise cfg.SettingsError(
                f'Fuso alvo foi localizado, mas não pôde ser selecionado: {target}. '
                f'Alvo={visible_meta}'
            ) from exc

    page.wait_for_timeout(300)
    cfg.click_dialog_action(page, "SALVAR")
    return {
        "target": target,
        "matched_text": str(meta.get("text") or ""),
        "selected_and_saved": True,
        "navigation": "exact-offscreen-dom-scroll-into-view",
    }


def install() -> None:
    cfg.set_timezone = set_timezone_offscreen_resilient
