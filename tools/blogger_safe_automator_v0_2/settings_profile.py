#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urlparse

import browser_provision as bp
import configure_core_settings as cfg
from playwright.sync_api import sync_playwright

DEFAULT_TIMEZONE = cfg.DEFAULT_TIMEZONE
CONFIRMATION = cfg.CONFIRMATION


def _validate_inputs(
    expected_blog_id: str,
    description: str,
    search_description: str,
    timezone: str,
) -> tuple[str, str, str, str]:
    blog_id = str(expected_blog_id or "").strip()
    desc = str(description or "").strip()
    search_desc = str(search_description or "").strip()
    tz = str(timezone or DEFAULT_TIMEZONE).strip() or DEFAULT_TIMEZONE

    if not re.fullmatch(r"\d+", blog_id):
        raise cfg.SettingsError("Blog ID esperado inválido.")
    if not (1 <= len(desc) <= 500):
        raise cfg.SettingsError("Descrição deve ter entre 1 e 500 caracteres.")
    if not (1 <= len(search_desc) <= 150):
        raise cfg.SettingsError("Descrição de pesquisa deve ter entre 1 e 150 caracteres.")
    if len(tz) > 180:
        raise cfg.SettingsError("Fuso horário inválido.")
    return blog_id, desc, search_desc, tz


def _planned(description: str, search_description: str, timezone: str) -> dict:
    return {
        "description": description,
        "search_visibility": True,
        "https_redirect": True,
        "lazy_images": True,
        "webp_images": True,
        "search_description_enabled": True,
        "search_description": search_description,
        "timezone": timezone,
        "custom_robots_txt": "UNCHANGED",
        "custom_robots_headers": "UNCHANGED",
    }


def _validate_current_blogger_page(page, expected_blog_id: str) -> None:
    """Valida a aba atual sem navegar para a Home do Blogger."""
    host = (urlparse(page.url).hostname or "").lower()
    if host == "accounts.google.com" or host.endswith(".accounts.google.com"):
        raise cfg.SettingsError("A sessão do Chrome CDP não está autenticada no Blogger.")
    if host != "blogger.com" and not host.endswith(".blogger.com"):
        raise cfg.SettingsError(f"A aba atual não é do Blogger: {bp.sanitize_url(page.url)}")
    actual = bp.extract_current_blog_id(page)
    if actual != expected_blog_id:
        raise cfg.SettingsError(
            f"Blog errado bloqueado: atual={actual!r}, esperado={expected_blog_id!r}."
        )


def _open_expected_settings(page, expected_blog_id: str) -> str:
    _validate_current_blogger_page(page, expected_blog_id)
    cfg.core.goto_settings(page, expected_blog_id)
    blog_id_after = bp.extract_current_blog_id(page)
    if blog_id_after != expected_blog_id:
        raise cfg.SettingsError(
            f"Blog mudou ao abrir Configurações: atual={blog_id_after!r}, esperado={expected_blog_id!r}."
        )
    return expected_blog_id


def _scroll_blog_option_container(page, mode: str) -> bool:
    """Move o contêiner virtualizado que contém as opções do seletor de blogs."""
    try:
        return bool(page.evaluate(
            """mode => {
                const visible = el => {
                    const r = el.getBoundingClientRect();
                    const s = getComputedStyle(el);
                    return r.width > 0 && r.height > 0 && s.display !== 'none' && s.visibility !== 'hidden';
                };
                const option = [...document.querySelectorAll('[role="option"]')].find(visible);
                if (!option) return false;
                let node = option.parentElement;
                while (node && node !== document.body) {
                    if (node.scrollHeight > node.clientHeight + 24) {
                        const before = node.scrollTop;
                        if (mode === 'top') {
                            node.scrollTop = 0;
                        } else {
                            node.scrollTop = Math.min(
                                node.scrollHeight,
                                node.scrollTop + Math.max(280, node.clientHeight * 0.82)
                            );
                        }
                        return Math.abs(node.scrollTop - before) > 1;
                    }
                    node = node.parentElement;
                }
                return false;
            }""",
            mode,
        ))
    except Exception:
        return False


def _visible_blog_options(page) -> list[tuple[str, object]]:
    out: list[tuple[str, object]] = []
    options = page.get_by_role("option")
    try:
        count = min(options.count(), 120)
    except Exception:
        count = 0
    for i in range(count):
        item = options.nth(i)
        try:
            if not item.is_visible():
                continue
            text = re.sub(r"\s+", " ", item.inner_text()).strip()
        except Exception:
            continue
        if not text or bp.NEW_BLOG_RE.fullmatch(text):
            continue
        out.append((text, item))
    return out


def _collect_blog_option_labels(page) -> list[str]:
    """Coleta a lista virtualizada inteira, começando pelos blogs recentes no topo."""
    bp.open_blog_switcher(page)
    labels: list[str] = []
    try:
        _scroll_blog_option_container(page, "top")
        page.wait_for_timeout(250)
        stagnant = 0
        last_signature: tuple[str, ...] = ()
        for _ in range(80):
            current = _visible_blog_options(page)
            signature = tuple(text for text, _ in current)
            for text, _ in current:
                if text not in labels:
                    labels.append(text)

            moved = _scroll_blog_option_container(page, "down")
            page.wait_for_timeout(180)
            if signature == last_signature and not moved:
                stagnant += 1
            else:
                stagnant = 0
            last_signature = signature
            if stagnant >= 2:
                break
    finally:
        try:
            page.keyboard.press("Escape")
            page.wait_for_timeout(250)
        except Exception:
            pass
    return labels


def _find_option_by_label(page, label: str):
    """Abre o seletor, rola do topo até o rótulo e retorna apenas uma opção visível."""
    bp.open_blog_switcher(page)
    _scroll_blog_option_container(page, "top")
    page.wait_for_timeout(220)
    pattern = re.compile(rf"^{re.escape(label)}$", re.I)

    for _ in range(80):
        matches = page.get_by_role("option", name=pattern)
        try:
            count = min(matches.count(), 12)
        except Exception:
            count = 0
        for i in range(count):
            item = matches.nth(i)
            try:
                if item.is_visible():
                    return item
            except Exception:
                continue
        moved = _scroll_blog_option_container(page, "down")
        page.wait_for_timeout(160)
        if not moved:
            break

    try:
        page.keyboard.press("Escape")
    except Exception:
        pass
    return None


def _switch_via_blog_selector(page, expected_blog_id: str):
    """Percorre blogs existentes no seletor oficial até achar o Blog ID esperado.

    Somente navegação: nunca abre "Novo blog..." e nunca escreve durante a busca.
    A lista virtualizada é percorrida do topo para baixo, incluindo Blogs recentes.
    """
    labels = _collect_blog_option_labels(page)
    attempted: list[str] = []

    for label in labels[:100]:
        try:
            target = _find_option_by_label(page, label)
            if target is None:
                continue
            try:
                target.click(timeout=4_000)
            except Exception:
                target.evaluate("el => el.click()")
            page.wait_for_timeout(1_400)

            try:
                actual = bp.extract_current_blog_id(page)
            except Exception:
                actual = None
            attempted.append(label)
            if actual == expected_blog_id:
                _validate_current_blogger_page(page, expected_blog_id)
                return page
        except Exception:
            try:
                page.keyboard.press("Escape")
            except Exception:
                pass
            continue

    preview = " | ".join(attempted[:20])
    collected = " | ".join(labels[:20])
    detail = f" Blogs testados: {preview}." if preview else ""
    if collected:
        detail += f" Blogs coletados: {collected}."
    raise cfg.SettingsError(
        f"O Blog ID esperado {expected_blog_id} não foi localizado pelo seletor oficial do Blogger.{detail}"
    )


def _select_expected_page(context, expected_blog_id: str):
    """Seleciona o Blog ID esperado sem permitir que a validação volte à Home."""
    try:
        page = cfg.core.select_expected_blog_page(context, expected_blog_id)
        _validate_current_blogger_page(page, expected_blog_id)
        return page
    except Exception:
        pass

    try:
        page = bp.select_page(context)
        # Home somente para confirmar autenticação antes de abrir o seletor oficial.
        bp.require_blogger_session(page)
    except Exception as exc:
        raise cfg.SettingsError(
            f"Nenhuma aba Blogger autenticada está disponível para localizar o Blog ID esperado {expected_blog_id}."
        ) from exc

    return _switch_via_blog_selector(page, expected_blog_id)


def execute_settings_preflight(
    expected_blog_id: str,
    description: str,
    search_description: str,
    *,
    timezone: str = DEFAULT_TIMEZONE,
    cdp_url: str = bp.DEFAULT_CDP_URL,
    diagnostics_dir: str = "logs/browser_diagnostics",
    allow_remote_cdp: bool = False,
) -> dict:
    blog_id, desc, search_desc, tz = _validate_inputs(
        expected_blog_id, description, search_description, timezone
    )
    safe_cdp = bp.validate_cdp_url(cdp_url, allow_remote=allow_remote_cdp)

    with sync_playwright() as p:
        _, context = bp.connect_official_chrome(p, safe_cdp)
        page = _select_expected_page(context, blog_id)
        _validate_current_blogger_page(page, blog_id)
        _open_expected_settings(page, blog_id)
        current = cfg.snapshot(page)

        result = {
            "status": "SETTINGS_PREFLIGHT_OK",
            "read_only": True,
            "blog_id": blog_id,
            "settings_url": bp.sanitize_url(page.url),
            "current": current,
            "planned": _planned(desc, search_desc, tz),
            "message": (
                f'Nenhuma configuração foi alterada. Para aplicar, confirme "{CONFIRMATION}".'
            ),
        }

    out = Path(diagnostics_dir) / "settings_profile_preflight.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def execute_configure_settings(
    expected_blog_id: str,
    description: str,
    search_description: str,
    *,
    confirm: str,
    timezone: str = DEFAULT_TIMEZONE,
    cdp_url: str = bp.DEFAULT_CDP_URL,
    diagnostics_dir: str = "logs/browser_diagnostics",
    allow_remote_cdp: bool = False,
) -> dict:
    if str(confirm or "") != CONFIRMATION:
        raise cfg.SettingsError(f'Confirmação inválida. Use "{CONFIRMATION}".')

    blog_id, desc, search_desc, tz = _validate_inputs(
        expected_blog_id, description, search_description, timezone
    )
    safe_cdp = bp.validate_cdp_url(cdp_url, allow_remote=allow_remote_cdp)

    with sync_playwright() as p:
        _, context = bp.connect_official_chrome(p, safe_cdp)
        page = _select_expected_page(context, blog_id)
        _validate_current_blogger_page(page, blog_id)
        _open_expected_settings(page, blog_id)
        before = cfg.snapshot(page)

        actions = []
        actions.append(cfg.set_dialog_text(page, "Descrição", desc, ("Descrição", "Description")))
        actions.append(cfg.set_checkbox(page, "Visível para mecanismos de pesquisa", True))
        actions.append(cfg.set_checkbox(page, "Redirecionamento para HTTPS", True))
        actions.append(cfg.set_checkbox(page, "Imagens com carregamento lento", True))
        actions.append(cfg.set_checkbox(page, "Veiculação de imagens WebP", True))
        actions.append(cfg.set_checkbox(page, "Ativar a descrição de pesquisa", True))
        page.wait_for_timeout(500)
        actions.append(
            cfg.set_dialog_text(
                page,
                "Descrição da pesquisa",
                search_desc,
                ("Descrição da pesquisa", "Descrição de pesquisa", "Search description"),
            )
        )
        actions.append(cfg.set_timezone(page, tz))

        page.wait_for_timeout(800)
        after = cfg.snapshot(page)

        for key in (
            "search_visibility",
            "https_redirect",
            "lazy_images",
            "webp_images",
            "search_description",
        ):
            if after[key].get("aria_checked") != "true":
                raise cfg.SettingsError(f"Validação final falhou para {key}.")

        if after["custom_robots_txt"].get("aria_checked") != before["custom_robots_txt"].get("aria_checked"):
            raise cfg.SettingsError("robots.txt personalizado mudou inesperadamente.")
        if after["custom_robots_headers"].get("aria_checked") != before["custom_robots_headers"].get("aria_checked"):
            raise cfg.SettingsError("Tags personalizadas de robôs mudaram inesperadamente.")

        result = {
            "status": "SETTINGS_PROFILE_VALIDATED",
            "read_only": False,
            "blog_id": blog_id,
            "settings_url": bp.sanitize_url(page.url),
            "planned": _planned(desc, search_desc, tz),
            "before": before,
            "actions": actions,
            "after": after,
            "robots_untouched": True,
        }

    out = Path(diagnostics_dir) / "settings_profile_apply.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result
