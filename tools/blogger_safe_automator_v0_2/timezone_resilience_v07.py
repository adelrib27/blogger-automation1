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


def _visible_overlay_meta(page):
    try:
        return page.evaluate(
            """() => {
                const visible = el => {
                    const r = el.getBoundingClientRect();
                    const s = getComputedStyle(el);
                    return r.width > 0 && r.height > 0 && s.display !== 'none' && s.visibility !== 'hidden';
                };
                return [...document.querySelectorAll('[role="dialog"],[role="listbox"],[role="menu"],[role="combobox"]')]
                    .filter(visible)
                    .map(el => ({
                        tag: el.tagName,
                        role: el.getAttribute('role') || '',
                        text: String(el.innerText || el.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 1000),
                        aria: el.getAttribute('aria-label') || ''
                    }));
            }"""
        )
    except Exception:
        return []


def _overlay_signature(page) -> tuple[str, ...]:
    rows = _visible_overlay_meta(page)
    return tuple(f"{r.get('role')}|{r.get('aria')}|{r.get('text')}" for r in rows)


def _timezone_editor_open(page, baseline: tuple[str, ...]) -> bool:
    current = _overlay_signature(page)
    if current != baseline and current:
        return True
    try:
        save = cfg.first_visible(page.get_by_text(re.compile(r"^SALVAR$", re.I), exact=True))
        if save is not None:
            return True
    except Exception:
        pass
    return False


def _click_timezone_row(page) -> None:
    pattern = re.compile(r"^Fuso horário(?:\s|$)", re.I)
    labels = page.get_by_text(pattern)
    baseline = _overlay_signature(page)
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
                        text: String(el.innerText || el.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 400)
                    })"""
                )
            except Exception:
                break
            score = 0
            if meta.get("tag") == "BUTTON":
                score += 100
            if meta.get("role") in ("button", "menuitem", "combobox"):
                score += 90
            if meta.get("tabindex") == "0":
                score += 70
            if meta.get("cursor") == "pointer":
                score += 40
            if depth == 1:
                score += 15
            if score > 0:
                candidates.append((score, depth, current))
            try:
                current = current.locator("xpath=..").first
            except Exception:
                break

    # Mais provável primeiro, mas sem clicar em ancestrais muito altos antes dos próximos ao label.
    candidates.sort(key=lambda x: (-x[0], x[1]))
    seen = set()
    for _, _, item in candidates:
        try:
            key = item.evaluate("el => el.outerHTML.slice(0,500)")
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
        for _ in range(8):
            page.wait_for_timeout(120)
            if _timezone_editor_open(page, baseline):
                return
        # Clique não abriu editor; não assumir sucesso.

    raise cfg.SettingsError('A linha "Fuso horário" foi encontrada, mas o editor não abriu.')


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
    # Alguns layouts do Blogger abrem primeiro um modal e só depois um seletor interno.
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
    roots = page.locator('[role="listbox"], [role="menu"], [role="dialog"]')
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
        if text and text not in texts:
            texts.append(text)
        if len(texts) >= 30:
            break
    if not texts:
        for overlay in _visible_overlay_meta(page):
            text = str(overlay.get("text") or overlay.get("aria") or "").strip()
            if text:
                texts.append(text[:900])
            if len(texts) >= 8:
                break
    return texts


def set_timezone_resilient(page, target: str) -> dict:
    _click_timezone_row(page)
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
        if detail:
            raise cfg.SettingsError(
                f'Fuso alvo não localizado: {target}. Editor abriu; opções/overlays: {detail[:2200]}'
            )
        raise cfg.SettingsError(f'Fuso alvo não localizado: {target}. Editor abriu, mas nenhuma opção foi capturada.')

    try:
        chosen.scroll_into_view_if_needed(timeout=2000)
    except Exception:
        pass
    try:
        chosen.click(timeout=5000)
    except Exception:
        chosen.evaluate("el => el.click()")
    page.wait_for_timeout(300)

    # O dropdown pode fechar e deixar o modal principal aberto.
    cfg.click_dialog_action(page, "SALVAR")
    return {"target": target, "matched_text": chosen_text, "selected_and_saved": True}


def install() -> None:
    cfg.set_timezone = set_timezone_resilient
