#!/usr/bin/env python3
from __future__ import annotations

import configure_core_settings as cfg
import timezone_resilience_v07 as base

ROW_ATTR = "data-blogger-tz-offscreen-row-v07"
CONTROL_ATTR = "data-blogger-tz-offscreen-control-v07"


def _mark_exact_target_control(page, target: str):
    """Localiza a linha do fuso alvo e marca o controle selecionável real dentro dela."""
    try:
        return page.evaluate(
            """({target, rowAttr, controlAttr}) => {
                document.querySelectorAll('[' + rowAttr + ']').forEach(el => el.removeAttribute(rowAttr));
                document.querySelectorAll('[' + controlAttr + ']').forEach(el => el.removeAttribute(controlAttr));

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
                const textOf = el => String(el && (el.innerText || el.textContent) || '').trim().replace(/\s+/g, ' ');
                const dialogs = [...document.querySelectorAll('[role="dialog"]')];
                let best = null;

                for (const dialog of dialogs) {
                    for (const textEl of [dialog, ...dialog.querySelectorAll('*')]) {
                        const text = textOf(textEl);
                        if (!text || text.length > 300 || !matches(text)) continue;

                        // Ache a menor "linha" ancestral que ainda contém exatamente este fuso.
                        let row = textEl;
                        for (let depth = 0; depth < 8 && row.parentElement && dialog.contains(row.parentElement); depth++) {
                            const parent = row.parentElement;
                            const parentText = textOf(parent);
                            if (!matches(parentText) || parentText.length > 420) break;
                            row = parent;
                        }

                        // Monte candidatos interativos dentro da linha e nos ancestrais imediatos.
                        const candidates = [];
                        const add = el => { if (el && el.nodeType === 1 && !candidates.includes(el)) candidates.push(el); };
                        add(textEl);
                        add(row);
                        for (const el of row.querySelectorAll(
                            'input[type="radio"], [role="radio"], [role="option"], [role="menuitemradio"], '
                            '[aria-checked], [aria-selected], button, [role="button"], [tabindex="0"]'
                        )) add(el);
                        let up = row.parentElement;
                        for (let depth = 0; depth < 4 && up && dialog.contains(up); depth++, up = up.parentElement) add(up);

                        let control = null;
                        let controlScore = -1e9;
                        for (const el of candidates) {
                            const role = el.getAttribute('role') || '';
                            const type = (el.getAttribute('type') || '').toLowerCase();
                            const ariaChecked = el.getAttribute('aria-checked');
                            const ariaSelected = el.getAttribute('aria-selected');
                            const tabindex = el.getAttribute('tabindex') || '';
                            const style = getComputedStyle(el);
                            const r = el.getBoundingClientRect();
                            let score = 0;
                            if (type === 'radio') score += 500;
                            if (role === 'radio') score += 480;
                            if (role === 'option') score += 450;
                            if (role === 'menuitemradio') score += 450;
                            if (ariaChecked !== null) score += 420;
                            if (ariaSelected !== null) score += 410;
                            if (el.tagName === 'BUTTON' || role === 'button') score += 250;
                            if (tabindex === '0') score += 180;
                            if (style.cursor === 'pointer') score += 160;
                            if (row.contains(el)) score += 120;
                            if (textOf(el) && matches(textOf(el))) score += 100;
                            // Evite containers gigantes do modal.
                            const area = Math.max(1, r.width * r.height);
                            score -= Math.min(100, area / 10000);
                            if (score > controlScore) {
                                control = el;
                                controlScore = score;
                            }
                        }
                        if (!control) control = textEl;

                        const n = norm(text);
                        const compact = n.replace(/\s/g, '');
                        let matchScore = 0;
                        if (compact.includes('gmt-03:00') || compact.includes('gmt03:00')) matchScore += 300;
                        if (n.includes('brasilia')) matchScore += 120;
                        if (n.includes('sao paulo')) matchScore += 120;
                        if (n.includes('horario padrao de brasilia')) matchScore += 80;
                        matchScore += Math.max(0, controlScore);
                        matchScore -= text.length / 10;

                        if (!best || matchScore > best.score) {
                            best = {row, control, text, score: matchScore};
                        }
                    }
                }

                if (!best) return null;
                best.row.setAttribute(rowAttr, '1');
                best.control.setAttribute(controlAttr, '1');
                const r = best.control.getBoundingClientRect();
                return {
                    text: best.text,
                    controlTag: best.control.tagName,
                    controlRole: best.control.getAttribute('role') || '',
                    controlType: best.control.getAttribute('type') || '',
                    ariaChecked: best.control.getAttribute('aria-checked'),
                    ariaSelected: best.control.getAttribute('aria-selected'),
                    tabindex: best.control.getAttribute('tabindex') || '',
                    x:r.x, y:r.y, w:r.width, h:r.height
                };
            }""",
            {"target": target, "rowAttr": ROW_ATTR, "controlAttr": CONTROL_ATTR},
        )
    except Exception:
        return None


def _bring_control_into_view(page):
    control = page.locator(f'[{CONTROL_ATTR}="1"]').first
    try:
        if control.count() == 0:
            return None
    except Exception:
        return None
    try:
        control.evaluate("el => el.scrollIntoView({block:'center', inline:'nearest'})")
        page.wait_for_timeout(180)
    except Exception:
        pass
    try:
        control.scroll_into_view_if_needed(timeout=1800)
        page.wait_for_timeout(120)
    except Exception:
        pass
    return control


def _selection_meta(page):
    try:
        return page.evaluate(
            """({rowAttr, controlAttr}) => {
                const row = document.querySelector('[' + rowAttr + '=\"1\"]');
                const control = document.querySelector('[' + controlAttr + '=\"1\"]');
                if (!control) return null;
                const r = control.getBoundingClientRect();
                const s = getComputedStyle(control);
                const checked = control.checked === true;
                const ariaChecked = control.getAttribute('aria-checked');
                const ariaSelected = control.getAttribute('aria-selected');
                const descendants = row ? [...row.querySelectorAll('[aria-checked],[aria-selected],input[type="radio"]')] : [];
                return {
                    visible: r.width > 0 && r.height > 0 && s.display !== 'none' && s.visibility !== 'hidden' &&
                             r.bottom > 0 && r.top < innerHeight,
                    checked,
                    ariaChecked,
                    ariaSelected,
                    rowStates: descendants.map(el => ({
                        tag: el.tagName,
                        role: el.getAttribute('role') || '',
                        checked: el.checked === true,
                        ariaChecked: el.getAttribute('aria-checked'),
                        ariaSelected: el.getAttribute('aria-selected')
                    })).slice(0, 12)
                };
            }""",
            {"rowAttr": ROW_ATTR, "controlAttr": CONTROL_ATTR},
        )
    except Exception:
        return None


def _is_selected(meta) -> bool:
    if not meta:
        return False
    if meta.get("checked") is True:
        return True
    if str(meta.get("ariaChecked") or "").lower() == "true":
        return True
    if str(meta.get("ariaSelected") or "").lower() == "true":
        return True
    for row in meta.get("rowStates") or []:
        if row.get("checked") is True:
            return True
        if str(row.get("ariaChecked") or "").lower() == "true":
            return True
        if str(row.get("ariaSelected") or "").lower() == "true":
            return True
    return False


def set_timezone_offscreen_resilient(page, target: str) -> dict:
    editor = base._click_timezone_row(page)
    page.wait_for_timeout(180)
    try:
        base._open_nested_selector(page)
    except Exception:
        pass
    page.wait_for_timeout(140)

    meta = _mark_exact_target_control(page, target)
    if meta is None:
        try:
            dialog_text = page.locator('[role="dialog"]:visible').last.inner_text(timeout=1000)
        except Exception:
            dialog_text = ""
        raise cfg.SettingsError(
            f'Fuso alvo não existe no DOM atual do modal: {target}. '
            f'Editor real: role={editor.get("role")} aria={editor.get("aria")} '
            f'text={editor.get("text", "")[:500]}. Texto do modal: {str(dialog_text)[:1600]}'
        )

    control = _bring_control_into_view(page)
    if control is None:
        raise cfg.SettingsError(f'Fuso alvo foi localizado, mas o controle selecionável não foi materializado: {target}. Alvo={meta}')

    before = _selection_meta(page)
    try:
        control.click(timeout=3000, force=True)
    except Exception:
        try:
            control.evaluate("el => { el.dispatchEvent(new MouseEvent('mousedown',{bubbles:true})); el.click(); el.dispatchEvent(new MouseEvent('mouseup',{bubbles:true})); }")
        except Exception as exc:
            raise cfg.SettingsError(f'Controle do fuso alvo não pôde ser acionado: {target}. Alvo={meta}') from exc
    page.wait_for_timeout(260)

    after = _selection_meta(page)
    if not _is_selected(after):
        # Segundo fallback: clique no centro da linha inteira, útil quando o controle visual é filho não interativo.
        row = page.locator(f'[{ROW_ATTR}="1"]').first
        try:
            box = row.bounding_box()
        except Exception:
            box = None
        if box:
            try:
                page.mouse.click(box["x"] + box["width"] * 0.5, box["y"] + box["height"] * 0.5)
                page.wait_for_timeout(220)
                after = _selection_meta(page)
            except Exception:
                pass

    if not _is_selected(after):
        raise cfg.SettingsError(
            f'GMT-03 foi encontrado, mas o controle não entrou em estado selecionado. '
            f'Alvo={meta}. Antes={before}. Depois={after}.'
        )

    cfg.click_dialog_action(page, "SALVAR")
    return {
        "target": target,
        "matched_text": str(meta.get("text") or ""),
        "selected_and_saved": True,
        "selection_meta": after,
        "navigation": "exact-offscreen-real-selectable-control",
    }


def install() -> None:
    cfg.set_timezone = set_timezone_offscreen_resilient
