#!/usr/bin/env python3
from __future__ import annotations

import timezone_offscreen_resilience_v07 as offscreen

_ORIGINAL_MARK = offscreen._mark_exact_target_control


def _mark_exact_via_playwright(page, target: str):
    """Localiza a opção de fuso pelo texto exato e deixa o Playwright rolar o modal.

    O Blogger exibe a lista inteira em um contêiner rolável. Em vez de tentar
    manipular scrollTop/virtualização, usamos o locator de texto exato, que sabe
    trazer o nó correspondente para a viewport antes do clique.
    """
    try:
        matches = page.get_by_text(target, exact=True)
        count = min(matches.count(), 20)
    except Exception:
        count = 0

    for i in range(count):
        text_el = matches.nth(i)
        try:
            in_dialog = bool(text_el.evaluate("el => !!el.closest('[role=\"dialog\"]')"))
        except Exception:
            in_dialog = False
        if not in_dialog:
            continue

        try:
            text_el.scroll_into_view_if_needed(timeout=3000)
            page.wait_for_timeout(180)
        except Exception:
            pass

        try:
            meta = text_el.evaluate(
                """(el) => {
                    const rowAttr = 'data-blogger-tz-offscreen-row-v07';
                    const controlAttr = 'data-blogger-tz-offscreen-control-v07';
                    document.querySelectorAll('[' + rowAttr + ']').forEach(n => n.removeAttribute(rowAttr));
                    document.querySelectorAll('[' + controlAttr + ']').forEach(n => n.removeAttribute(controlAttr));

                    const textOf = n => String(n && (n.innerText || n.textContent) || '').trim().replace(/\\s+/g, ' ');
                    const dialog = el.closest('[role=\"dialog\"]');
                    if (!dialog) return null;

                    let row = el;
                    for (let depth = 0; depth < 10 && row && row !== dialog; depth++) {
                        const radio = row.querySelector && row.querySelector(
                            'input[type=\"radio\"], [role=\"radio\"], [role=\"option\"], [role=\"menuitemradio\"], [aria-checked], [aria-selected]'
                        );
                        if (radio) break;
                        row = row.parentElement;
                    }
                    if (!row || row === dialog) row = el.parentElement || el;

                    let control = null;
                    if (row.querySelector) {
                        control = row.querySelector(
                            'input[type=\"radio\"], [role=\"radio\"], [role=\"option\"], [role=\"menuitemradio\"], [aria-checked], [aria-selected]'
                        );
                    }

                    // Material Design às vezes põe o radio como irmão da célula de texto.
                    if (!control) {
                        let parent = row.parentElement;
                        for (let depth = 0; depth < 4 && parent && dialog.contains(parent); depth++, parent = parent.parentElement) {
                            control = parent.querySelector(
                                'input[type=\"radio\"], [role=\"radio\"], [role=\"option\"], [role=\"menuitemradio\"], [aria-checked], [aria-selected]'
                            );
                            if (control) {
                                row = parent;
                                break;
                            }
                        }
                    }

                    // Se a linha inteira é o alvo clicável, use-a como fallback.
                    if (!control) {
                        let n = el;
                        for (let depth = 0; depth < 8 && n && dialog.contains(n); depth++, n = n.parentElement) {
                            const role = n.getAttribute && (n.getAttribute('role') || '');
                            const tabindex = n.getAttribute && (n.getAttribute('tabindex') || '');
                            const style = n.nodeType === 1 ? getComputedStyle(n) : null;
                            if (['radio','option','menuitemradio','button'].includes(role) ||
                                tabindex === '0' || (style && style.cursor === 'pointer') || n.tagName === 'LABEL') {
                                control = n;
                                row = n;
                                break;
                            }
                        }
                    }

                    if (!control) control = el;
                    row.setAttribute(rowAttr, '1');
                    control.setAttribute(controlAttr, '1');
                    const r = control.getBoundingClientRect();
                    return {
                        text: textOf(el),
                        controlTag: control.tagName,
                        controlRole: control.getAttribute('role') || '',
                        controlType: control.getAttribute('type') || '',
                        ariaChecked: control.getAttribute('aria-checked'),
                        ariaSelected: control.getAttribute('aria-selected'),
                        tabindex: control.getAttribute('tabindex') || '',
                        x: r.x, y: r.y, w: r.width, h: r.height,
                        exactTextLocator: true
                    };
                }"""
            )
        except Exception:
            meta = None

        if meta:
            return meta

    return None


def _mark_exact_target_control(page, target: str):
    # Primeiro, o caminho determinístico revelado pela inspeção visual: texto exato.
    meta = _mark_exact_via_playwright(page, target)
    if meta is not None:
        return meta

    # Fail-safe: preserve o detector anterior como fallback diagnóstico.
    return _ORIGINAL_MARK(page, target)


def install() -> None:
    offscreen._mark_exact_target_control = _mark_exact_target_control
