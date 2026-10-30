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
    brazil_markers = (
        "brasilia",
        "sao paulo",
        "fortaleza",
        "recife",
        "horario padrao de brasilia",
    )
    return any(marker in n for marker in brazil_markers)


def _visible_roots(page):
    roots = []
    loc = page.locator('[role="listbox"], [role="menu"], [role="dialog"]')
    try:
        count = min(loc.count(), 100)
    except Exception:
        count = 0
    for i in range(count):
        item = loc.nth(i)
        try:
            if item.is_visible():
                roots.append(item)
        except Exception:
            continue
    return roots


def _find_candidate(page, target: str):
    selectors = '[role="option"], [role="menuitemradio"], [role="menuitem"], [role="radio"], li'
    candidates = page.locator(selectors)
    try:
        count = min(candidates.count(), 2500)
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
        score = 0
        n = _norm(text)
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


def _scroll_roots(page) -> None:
    for root in _visible_roots(page):
        try:
            root.evaluate(
                """el => {
                    const nodes = [el, ...el.querySelectorAll('*')];
                    for (const n of nodes) {
                        try {
                            if (n.scrollHeight > n.clientHeight + 24) {
                                n.scrollTop = Math.min(
                                    n.scrollHeight,
                                    n.scrollTop + Math.max(300, n.clientHeight * 0.85)
                                );
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
        return texts
    for item in snap.get("options", []):
        text = str(item.get("text") or item.get("aria") or "").strip()
        if text and text not in texts:
            texts.append(text)
        if len(texts) >= 20:
            break
    if not texts:
        for overlay in snap.get("overlays", []):
            text = str(overlay.get("text") or "").strip()
            if text:
                texts.append(text[:700])
            if len(texts) >= 5:
                break
    return texts


def set_timezone_resilient(page, target: str) -> dict:
    if not cfg.core.click_row_prefix(page, "Fuso horário"):
        raise cfg.SettingsError("Fuso horário não foi localizado.")
    page.wait_for_timeout(500)

    chosen = None
    chosen_text = ""
    for _ in range(60):
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
                f'Fuso alvo não localizado: {target}. Opções/overlays visíveis: {detail[:1800]}'
            )
        raise cfg.SettingsError(f'Fuso alvo não localizado: {target}. Nenhuma opção visível foi capturada.')

    try:
        chosen.scroll_into_view_if_needed(timeout=2_000)
    except Exception:
        pass
    try:
        chosen.click(timeout=5_000)
    except Exception:
        chosen.evaluate("el => el.click()")
    page.wait_for_timeout(300)
    cfg.click_dialog_action(page, "SALVAR")
    return {"target": target, "matched_text": chosen_text, "selected_and_saved": True}


def install() -> None:
    cfg.set_timezone = set_timezone_resilient
