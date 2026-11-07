#!/usr/bin/env python3
from __future__ import annotations

import re
import unicodedata

import configure_core_settings as cfg


def _norm(value: str) -> str:
    value = unicodedata.normalize("NFKD", str(value or ""))
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.replace("–", "-").replace("—", "-").replace("−", "-")
    return re.sub(r"\s+", " ", value).strip().lower()


def _matches(text: str, target: str) -> bool:
    n = _norm(text)
    t = _norm(target)
    if t and t in n:
        return True
    compact = n.replace(" ", "")
    if "gmt-03:00" not in compact and "gmt03:00" not in compact:
        return False
    return any(
        marker in n
        for marker in (
            "brasilia",
            "sao paulo",
            "fortaleza",
            "recife",
            "horario padrao de brasilia",
        )
    )


def _visible_editor_meta(page):
    try:
        return page.evaluate(
            """() => {
                const visible = el => {
                    const r = el.getBoundingClientRect();
                    const s = getComputedStyle(el);
                    return r.width > 0 && r.height > 0 && s.display !== 'none' && s.visibility !== 'hidden';
                };
                return [...document.querySelectorAll('[role="dialog"],[role="listbox"],[role="combobox"]')]
                    .filter(visible)
                    .map((el, index) => ({
                        index,
                        tag: el.tagName,
                        role: el.getAttribute('role') || '',
                        aria: el.getAttribute('aria-label') || '',
                        ariaModal: el.getAttribute('aria-modal') || '',
                        text: String(el.innerText || el.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 1200),
                        x: Math.round(el.getBoundingClientRect().x),
                        y: Math.round(el.getBoundingClientRect().y),
                        w: Math.round(el.getBoundingClientRect().width),
                        h: Math.round(el.getBoundingClientRect().height)
                    }));
            }"""
        )
    except Exception:
        return []


def _editor_signature(page) -> tuple[str, ...]:
    rows = _visible_editor_meta(page)
    return tuple(
        f"{r.get('role')}|{r.get('aria')}|{r.get('ariaModal')}|{r.get('x')}|{r.get('y')}|{r.get('w')}|{r.get('h')}|{r.get('text')}"
        for r in rows
    )


def _new_timezone_editor(page, baseline: tuple[str, ...]):
    current = _visible_editor_meta(page)
    baseline_sigs = set(baseline)
    fresh = [r for r in current if (
        f"{r.get('role')}|{r.get('aria')}|{r.get('ariaModal')}|{r.get('x')}|{r.get('y')}|{r.get('w')}|{r.get('h')}|{r.get('text')}"
    ) not in baseline_sigs]
    if not fresh:
        return None

    def score(r):
        n = _norm(f"{r.get('aria','')} {r.get('text','')}")
        s = 0
        if r.get("role") == "dialog":
            s += 100
        if r.get("ariaModal") == "true":
            s += 80
        if r.get("role") == "listbox":
            s += 70
        if r.get("role") == "combobox":
            s += 50
        if "fuso" in n or "horario" in n or "gmt" in n:
            s += 120
        return s

    fresh.sort(key=score, reverse=True)
    return fresh[0]


def _click_timezone_row(page) -> dict:
    pattern = re.compile(r"^Fuso horário(?:\s|$)", re.I)
    labels = page.get_by_text(pattern)
    baseline = _editor_signature(page)
    candidates = []
    try:
        count = min(labels.count(), 30)
    except Exception:
        count = 0

    for i in range(count):
        label = labels.nth(i)
        try:
            if not label.is_visible():
                continue
        except Exception:
            continue
        current = label
        for depth in range(9):
            try:
                meta = current.evaluate(
                    """el => ({
                        tag: el.tagName,
                        role: el.getAttribute('role') || '',
                        tabindex: el.getAttribute('tabindex') || '',
                        cursor: getComputedStyle(el).cursor || '',
                        text: String(el.innerText || el.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 500)
                    })"""
                )
            except Exception:
                break
            score = 0
            if meta.get("tag") == "BUTTON":
                score += 100
            if meta.get("role") in ("button", "combobox"):
                score += 95
            if meta.get("tabindex") == "0":
                score += 75
            if meta.get("cursor") == "pointer":
                score += 45
            score -= depth * 4
            if score > 0:
                candidates.append((score, depth, current))
            try:
                current = current.locator("xpath=..").first
            except Exception:
                break

    candidates.sort(key=lambda x: (-x[0], x[1]))
    seen = set()
    for _, _, item in candidates:
        try:
            key = item.evaluate("el => el.outerHTML.slice(0,800)")
        except Exception:
            key = None
        if key and key in seen:
            continue
        if key:
            seen.add(key)
        try:
            item.scroll_into_view_if_needed(timeout=1500)
        except Exception:
            pass
        try:
            item.click(timeout=2500)
        except Exception:
            try:
                item.evaluate("el => el.click()")
            except Exception:
                continue
        for _ in range(12):
            page.wait_for_timeout(120)
            editor = _new_timezone_editor(page, baseline)
            if editor is not None:
                return editor

    raise cfg.SettingsError('A linha "Fuso horário" foi encontrada, mas nenhum editor real de fuso abriu.')


def _find_candidate(page, target: str):
    """Busca o fuso em uma única passagem DOM e marca o melhor elemento clicável."""
    try:
        meta = page.evaluate(
            """target => {
                const ATTR = 'data-blogger-tz-target-v07';
                document.querySelectorAll('[' + ATTR + ']').forEach(el => el.removeAttribute(ATTR));
                const visible = el => {
                    const r = el.getBoundingClientRect();
                    const s = getComputedStyle(el);
                    return r.width > 0 && r.height > 0 && s.display !== 'none' && s.visibility !== 'hidden' &&
                           r.bottom > 0 && r.top < innerHeight && r.right > 0 && r.left < innerWidth;
                };
                const norm = value => String(value || '')
                    .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
                    .replace(/[–—−]/g, '-').replace(/\s+/g, ' ').trim().toLowerCase();
                const matches = text => {
                    const n = norm(text);
                    const t = norm(target);
                    if (t && n.includes(t)) return true;
                    const compact = n.replace(/\s/g, '');
                    if (!compact.includes('gmt-03:00') && !compact.includes('gmt03:00')) return false;
                    return ['brasilia','sao paulo','fortaleza','recife','horario padrao de brasilia']
                        .some(marker => n.includes(marker));
                };
                const roots = [...document.querySelectorAll('[role="dialog"],[role="listbox"]')].filter(visible);
                let best = null;
                for (const root of roots) {
                    const nodes = [root, ...root.querySelectorAll('[role="option"],[role="menuitemradio"],[role="radio"],[role="button"],[tabindex="0"],li,div,span')];
                    for (const el of nodes) {
                        if (!visible(el)) continue;
                        const text = String(el.innerText || el.textContent || '').trim().replace(/\s+/g, ' ');
                        if (!text || text.length > 260 || !matches(text)) continue;
                        const r = el.getBoundingClientRect();
                        const role = el.getAttribute('role') || '';
                        const tabindex = el.getAttribute('tabindex') || '';
                        const cursor = getComputedStyle(el).cursor || '';
                        const n = norm(text);
                        const compact = n.replace(/\s/g, '');
                        let score = 0;
                        if (compact.includes('gmt-03:00') || compact.includes('gmt03:00')) score += 140;
                        if (n.includes('brasilia')) score += 70;
                        if (n.includes('sao paulo')) score += 70;
                        if (n.includes('horario padrao de brasilia')) score += 50;
                        if (['option','menuitemradio','radio','button'].includes(role)) score += 100;
                        if (tabindex === '0') score += 70;
                        if (cursor === 'pointer') score += 50;
                        if (el.tagName === 'LI' || el.tagName === 'BUTTON') score += 30;
                        const rank = [score, -text.length, -(Math.max(1, r.width * r.height))];
                        if (!best || rank[0] > best.rank[0] ||
                            (rank[0] === best.rank[0] && rank[1] > best.rank[1]) ||
                            (rank[0] === best.rank[0] && rank[1] === best.rank[1] && rank[2] > best.rank[2])) {
                            best = {el, text, score, rank};
                        }
                    }
                }
                if (!best) return null;
                best.el.setAttribute(ATTR, '1');
                return {text: best.text, score: best.score};
            }""",
            target,
        )
    except Exception:
        return None
    if not meta:
        return None
    item = page.locator('[data-blogger-tz-target-v07="1"]').first
    try:
        if not item.count() or not item.is_visible():
            return None
    except Exception:
        return None
    return (int(meta.get("score") or 0), item, str(meta.get("text") or ""))


def _open_nested_selector(page) -> bool:
    locators = [
        page.locator('[role="dialog"] [role="combobox"]'),
        page.locator('[role="dialog"] [aria-haspopup="listbox"]'),
        page.locator('[role="dialog"] [aria-haspopup="menu"]'),
    ]
    for loc in locators:
        try:
            count = min(loc.count(), 20)
        except Exception:
            count = 0
        for i in range(count):
            item = loc.nth(i)
            try:
                if not item.is_visible():
                    continue
                item.click(timeout=2500)
                page.wait_for_timeout(350)
                return True
            except Exception:
                continue
    return False


def _scroll_roots(page) -> bool:
    """Avança a lista virtualizada; usa scrollTop e, se necessário, wheel/PageDown reais."""
    try:
        moved = bool(page.evaluate(
            """() => {
                const visible = el => {
                    const r = el.getBoundingClientRect();
                    const s = getComputedStyle(el);
                    return r.width > 0 && r.height > 0 && s.display !== 'none' && s.visibility !== 'hidden';
                };
                const roots = [...document.querySelectorAll('[role="dialog"],[role="listbox"]')].filter(visible);
                let best = null;
                for (const root of roots) {
                    for (const n of [root, ...root.querySelectorAll('*')]) {
                        if (!visible(n)) continue;
                        const max = n.scrollHeight - n.clientHeight;
                        if (max <= 24) continue;
                        const style = getComputedStyle(n);
                        let score = max + n.clientHeight;
                        if (['auto','scroll'].includes(style.overflowY)) score += 5000;
                        if (!best || score > best.score) best = {n, score, max};
                    }
                }
                if (!best) return false;
                const before = best.n.scrollTop;
                const step = Math.max(320, best.n.clientHeight * 0.82);
                best.n.scrollTop = Math.min(best.max, before + step);
                best.n.dispatchEvent(new Event('scroll', {bubbles:true}));
                return Math.abs(best.n.scrollTop - before) > 1;
            }"""
        ))
        if moved:
            return True
    except Exception:
        pass

    dialog = page.locator('[role="dialog"]:visible').last
    try:
        box = dialog.bounding_box()
    except Exception:
        box = None
    if box:
        try:
            page.mouse.move(box["x"] + box["width"] * 0.72, box["y"] + box["height"] * 0.72)
            page.mouse.wheel(0, 900)
            page.wait_for_timeout(90)
            return True
        except Exception:
            pass

    try:
        page.keyboard.press("PageDown")
        page.wait_for_timeout(90)
        return True
    except Exception:
        return False


def _diagnostic_options(page) -> list[str]:
    try:
        return page.evaluate(
            """() => {
                const visible = el => {
                    const r = el.getBoundingClientRect();
                    const s = getComputedStyle(el);
                    return r.width > 0 && r.height > 0 && s.display !== 'none' && s.visibility !== 'hidden' &&
                           r.bottom > 0 && r.top < innerHeight && r.right > 0 && r.left < innerWidth;
                };
                const out = [];
                for (const root of [...document.querySelectorAll('[role="dialog"]')].filter(visible)) {
                    for (const el of root.querySelectorAll('li,[role="option"],[role="radio"],div,span')) {
                        if (!visible(el)) continue;
                        const text = String(el.innerText || el.textContent || '').trim().replace(/\s+/g, ' ');
                        if (!text || text.length > 180 || !text.toLowerCase().includes('gmt')) continue;
                        if (!out.includes(text)) out.push(text);
                        if (out.length >= 20) return out;
                    }
                }
                return out;
            }"""
        ) or []
    except Exception:
        return []


def set_timezone_resilient(page, target: str) -> dict:
    editor = _click_timezone_row(page)
    page.wait_for_timeout(250)

    match = _find_candidate(page, target)
    if match is None:
        _open_nested_selector(page)

    chosen = None
    chosen_text = ""
    for _ in range(20):
        match = _find_candidate(page, target)
        if match is not None:
            _, chosen, chosen_text = match
            break
        if not _scroll_roots(page):
            break
        page.wait_for_timeout(120)

    if chosen is None:
        options = _diagnostic_options(page)
        detail = " | ".join(options)
        editor_desc = f"role={editor.get('role')} aria={editor.get('aria')} text={editor.get('text','')[:500]}"
        if detail:
            raise cfg.SettingsError(
                f'Fuso alvo não localizado: {target}. Editor real: {editor_desc}. Fusos visíveis finais: {detail[:1800]}'
            )
        raise cfg.SettingsError(
            f'Fuso alvo não localizado: {target}. Editor real: {editor_desc}. Nenhuma opção de fuso foi capturada.'
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
    return {"target": target, "matched_text": chosen_text, "selected_and_saved": True}


def install() -> None:
    cfg.set_timezone = set_timezone_resilient
