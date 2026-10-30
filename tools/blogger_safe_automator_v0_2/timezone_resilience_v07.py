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
    current_sigs = {
        f"{r.get('role')}|{r.get('aria')}|{r.get('ariaModal')}|{r.get('x')}|{r.get('y')}|{r.get('w')}|{r.get('h')}|{r.get('text')}"
        for r in current
    }
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
    # O Blogger atual renderiza as linhas de fuso como DIV/SPAN comuns em alguns layouts,
    # sem role=option. Procuramos dentro de diálogos/listboxes visíveis e escolhemos o
    # menor elemento clicável cujo texto normalizado corresponda ao fuso desejado.
    roots = page.locator('[role="dialog"], [role="listbox"]')
    best = None
    try:
        root_count = min(roots.count(), 40)
    except Exception:
        root_count = 0

    for rix in range(root_count):
        root = roots.nth(rix)
        try:
            if not root.is_visible():
                continue
        except Exception:
            continue

        candidates = root.locator(
            '[role="option"], [role="menuitemradio"], [role="radio"], '
            '[role="button"], [tabindex="0"], li, div, span'
        )
        try:
            count = min(candidates.count(), 5000)
        except Exception:
            count = 0

        for i in range(count):
            item = candidates.nth(i)
            try:
                if not item.is_visible():
                    continue
                text = item.inner_text(timeout=180).strip()
                if not text or len(text) > 260 or not _matches(text, target):
                    continue
                meta = item.evaluate(
                    """el => {
                        const r = el.getBoundingClientRect();
                        return {
                            tag: el.tagName,
                            role: el.getAttribute('role') || '',
                            tabindex: el.getAttribute('tabindex') || '',
                            cursor: getComputedStyle(el).cursor || '',
                            area: Math.max(1, r.width * r.height)
                        };
                    }"""
                )
            except Exception:
                continue

            n = _norm(text)
            compact = n.replace(" ", "")
            score = 0
            if "gmt-03:00" in compact or "gmt03:00" in compact:
                score += 140
            if "brasilia" in n:
                score += 70
            if "sao paulo" in n:
                score += 70
            if "horario padrao de brasilia" in n:
                score += 50
            if meta.get("role") in ("option", "menuitemradio", "radio", "button"):
                score += 100
            if meta.get("tabindex") == "0":
                score += 70
            if meta.get("cursor") == "pointer":
                score += 50
            if meta.get("tag") in ("LI", "BUTTON"):
                score += 30
            # Prefere o texto mais específico e o menor elemento visual.
            rank = (score, -len(text), -float(meta.get("area") or 1))
            if best is None or rank > best[0]:
                best = (rank, item, text)

    if best is None:
        return None
    _, item, text = best
    return (best[0][0], item, text)


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
    # Move prioritariamente o maior contêiner realmente scrollável do editor de fuso.
    try:
        moved = page.evaluate(
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
                        const score = max + n.clientHeight;
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
        )
        return bool(moved)
    except Exception:
        return False


def _diagnostic_options(page) -> list[str]:
    texts: list[str] = []
    try:
        dialogs = page.locator('[role="dialog"]')
        for rix in range(min(dialogs.count(), 20)):
            root = dialogs.nth(rix)
            if not root.is_visible():
                continue
            rows = root.locator('li, [role="option"], [role="radio"], div, span')
            for i in range(min(rows.count(), 1200)):
                item = rows.nth(i)
                try:
                    if not item.is_visible():
                        continue
                    text = re.sub(r"\s+", " ", item.inner_text(timeout=100)).strip()
                except Exception:
                    continue
                if not text or len(text) > 180 or "gmt" not in _norm(text):
                    continue
                if text not in texts:
                    texts.append(text)
                if len(texts) >= 20:
                    return texts
    except Exception:
        pass
    return texts


def set_timezone_resilient(page, target: str) -> dict:
    editor = _click_timezone_row(page)
    page.wait_for_timeout(300)

    match = _find_candidate(page, target)
    if match is None:
        _open_nested_selector(page)

    chosen = None
    chosen_text = ""
    stagnant = 0
    for _ in range(90):
        match = _find_candidate(page, target)
        if match is not None:
            _, chosen, chosen_text = match
            break
        moved = _scroll_roots(page)
        page.wait_for_timeout(160)
        if moved:
            stagnant = 0
        else:
            stagnant += 1
            if stagnant >= 3:
                break

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
        chosen.scroll_into_view_if_needed(timeout=2000)
    except Exception:
        pass
    try:
        chosen.click(timeout=5000)
    except Exception:
        chosen.evaluate("el => el.click()")
    page.wait_for_timeout(350)

    cfg.click_dialog_action(page, "SALVAR")
    return {"target": target, "matched_text": chosen_text, "selected_and_saved": True}


def install() -> None:
    cfg.set_timezone = set_timezone_resilient
