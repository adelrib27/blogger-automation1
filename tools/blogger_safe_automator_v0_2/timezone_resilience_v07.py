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

    # Prioriza um modal/listbox real; menu lateral não entra nesta coleta.
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
            # Prefere ancestrais próximos do rótulo, evitando containers grandes.
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
    candidates = page.locator('[role="option"], [role="menuitemradio"], [role="radio"], li')
    try:
        count = min(candidates.count(), 3000)
    except Exception:
        count = 0
    best = None
    for i in range(count):
        item = candidates.nth(i)
        try:
            if not item.is_visible():
                continue
            text = item.inner_text(timeout=250).strip()
        except Exception:
            continue
        if not text or not _matches(text, target):
            continue
        n = _norm(text)
        score = 0
        compact = n.replace(" ", "")
        if "gmt-03:00" in compact or "gmt03:00" in compact:
            score += 100
        if "brasilia" in n:
            score += 50
        if "sao paulo" in n:
            score += 50
        if "horario padrao de brasilia" in n:
            score += 40
        if best is None or score > best[0]:
            best = (score, item, text)
    return best


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


def _scroll_roots(page) -> None:
    roots = page.locator('[role="listbox"], [role="dialog"]')
    try:
        count = min(roots.count(), 100)
    except Exception:
        count = 0
    for i in range(count):
        root = roots.nth(i)
        try:
            if not root.is_visible():
                continue
            root.evaluate(
                """el => {
                    const nodes = [el, ...el.querySelectorAll('*')];
                    for (const n of nodes) {
                        try {
                            if (n.scrollHeight > n.clientHeight + 24) {
                                n.scrollTop = Math.min(n.scrollHeight, n.scrollTop + Math.max(300, n.clientHeight * 0.85));
                            }
                        } catch (_) {}
                    }
                }"""
            )
        except Exception:
            continue


def _diagnostic_options(page) -> list[str]:
    texts: list[str] = []
    try:
        snap = cfg.core.overlay_snapshot(page)
    except Exception:
        snap = {}
    for item in snap.get("options", []):
        text = str(item.get("text") or item.get("aria") or "").strip()
        n = _norm(text)
        # Ignora explicitamente itens do menu lateral do Blogger.
        if n in {
            "postagens", "estatisticas", "comentarios", "ganhos", "paginas",
            "layout", "tema", "configuracoes", "lista de leitura"
        }:
            continue
        if text and text not in texts:
            texts.append(text)
        if len(texts) >= 30:
            break
    if not texts:
        for overlay in _visible_editor_meta(page):
            text = str(overlay.get("text") or overlay.get("aria") or "").strip()
            if text:
                texts.append(text[:900])
            if len(texts) >= 8:
                break
    return texts


def set_timezone_resilient(page, target: str) -> dict:
    editor = _click_timezone_row(page)
    page.wait_for_timeout(300)

    match = _find_candidate(page, target)
    if match is None:
        _open_nested_selector(page)

    chosen = None
    chosen_text = ""
    for _ in range(70):
        match = _find_candidate(page, target)
        if match is not None:
            _, chosen, chosen_text = match
            break
        _scroll_roots(page)
        page.wait_for_timeout(120)

    if chosen is None:
        options = _diagnostic_options(page)
        detail = " | ".join(options)
        editor_desc = f"role={editor.get('role')} aria={editor.get('aria')} text={editor.get('text','')[:500]}"
        if detail:
            raise cfg.SettingsError(
                f'Fuso alvo não localizado: {target}. Editor real: {editor_desc}. Opções: {detail[:1800]}'
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
    page.wait_for_timeout(300)

    cfg.click_dialog_action(page, "SALVAR")
    return {"target": target, "matched_text": chosen_text, "selected_and_saved": True}


def install() -> None:
    cfg.set_timezone = set_timezone_resilient
