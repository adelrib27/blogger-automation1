#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

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


def _open_expected_settings(page, expected_blog_id: str) -> str:
    blog_id = bp.extract_current_blog_id(page)
    if blog_id != expected_blog_id:
        raise cfg.SettingsError(
            f"Blog errado bloqueado: atual={blog_id!r}, esperado={expected_blog_id!r}."
        )
    cfg.core.goto_settings(page, blog_id)
    blog_id_after = bp.extract_current_blog_id(page)
    if blog_id_after != expected_blog_id:
        raise cfg.SettingsError(
            f"Blog mudou ao abrir Configurações: atual={blog_id_after!r}, esperado={expected_blog_id!r}."
        )
    return blog_id


def _select_expected_page(context, expected_blog_id: str):
    """Seleciona o Blog ID esperado; se necessário, troca primeiro pela rota de Postagens.

    A rota de Postagens é o ponto de entrada estável do Blogger para selecionar um blog.
    O Blog ID é validado após a troca e novamente ao abrir Configurações, antes de escrita.
    """
    try:
        return cfg.core.select_expected_blog_page(context, expected_blog_id)
    except Exception:
        pass

    try:
        page = bp.select_page(context)
        bp.require_blogger_session(page)
    except Exception as exc:
        raise cfg.SettingsError(
            f"Nenhuma aba Blogger autenticada está disponível para abrir o Blog ID esperado {expected_blog_id}."
        ) from exc

    posts_url = f"https://draft.blogger.com/blog/posts/{expected_blog_id}"
    try:
        page.goto(posts_url, wait_until="domcontentloaded", timeout=15_000)
        page.wait_for_timeout(1_500)
    except Exception as exc:
        raise cfg.SettingsError(
            f"Não foi possível abrir com segurança as postagens do Blog ID esperado {expected_blog_id}."
        ) from exc

    try:
        bp.require_blogger_session(page)
        actual_blog_id = bp.extract_current_blog_id(page)
    except Exception as exc:
        raise cfg.SettingsError(
            f"A troca para o Blog ID esperado {expected_blog_id} não resultou em uma página Blogger validável."
        ) from exc

    if actual_blog_id != expected_blog_id:
        raise cfg.SettingsError(
            f"Blog errado bloqueado após troca: atual={actual_blog_id!r}, esperado={expected_blog_id!r}."
        )
    if f"/blog/posts/{expected_blog_id}" not in bp.sanitize_url(page.url):
        raise cfg.SettingsError(
            f"A tela de postagens do Blog ID esperado {expected_blog_id} não abriu como esperado."
        )
    return page


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
        bp.require_blogger_session(page)
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
        bp.require_blogger_session(page)
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
