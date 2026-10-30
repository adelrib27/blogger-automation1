#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import browser_provision as bp
import local_service_v05 as v05
import resilient_create as rc
import settings_profile as settings

CONFIRMATION = "PROVISION BLOG V20"
PALETTES = {"auto", "blue", "emerald", "plum", "terracotta", "teal", "burgundy", "indigo", "amber"}


class ProvisionError(bp.SafeAutomationError):
    pass


def _checkpoint_path() -> Path:
    root = Path(__file__).resolve().parents[2]
    out = root / "logs" / "provisioning"
    out.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return out / f"provision-v20-{stamp}.json"


def _save(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _render_pages(blog_title: str) -> list[dict]:
    repo_root = Path(__file__).resolve().parents[2]
    src = repo_root / "themes" / "blogger_modelo_v20" / "pages.json"
    if not src.exists():
        raise ProvisionError(f"Template canônico de páginas V20 não encontrado: {src}")
    data = json.loads(src.read_text(encoding="utf-8"))
    if data.get("model") != "BLOGGER_MODELO_V20" or data.get("inherit_posts") is not False:
        raise ProvisionError("Template de páginas V20 inválido.")
    pages = []
    for raw in data.get("pages", []):
        content = str(raw.get("content") or "").replace("{{BLOG_TITLE}}", blog_title)
        if "{{BLOG_TITLE}}" in content:
            raise ProvisionError(f"Token de página não resolvido: {raw.get('key')}")
        pages.append({
            "key": str(raw["key"]),
            "title": str(raw["title"]),
            "expected_slug": str(raw["expected_slug"]),
            "publish": bool(raw.get("publish", True)),
            "requires_theme_contact_runtime": bool(raw.get("requires_theme_contact_runtime", False)),
            "content": content,
        })
    if len(pages) != 5:
        raise ProvisionError(f"Modelo V20 precisa ter exatamente 5 páginas; obtido {len(pages)}.")
    return pages


def execute_provision(
    title: str,
    address: str,
    description: str,
    search_description: str,
    *,
    timezone: str = settings.DEFAULT_TIMEZONE,
    palette: str = "auto",
    confirm: str,
    cdp_url: str = bp.DEFAULT_CDP_URL,
    diagnostics_dir: str = "logs/browser_diagnostics",
) -> dict:
    if confirm != CONFIRMATION:
        raise ProvisionError(f'Use confirm="{CONFIRMATION}".')
    palette = str(palette or "auto").strip().lower()
    if palette not in PALETTES:
        raise ProvisionError("Paleta V20 inválida.")

    req = bp.CreateBlogRequest.build(title, address)
    # Valida settings antes de qualquer escrita.
    settings._validate_inputs("0", description, search_description, timezone)
    pages = _render_pages(req.title)
    cp = _checkpoint_path()
    state = {
        "status": "PROVISION_STARTED",
        "title": req.title,
        "requested_address": req.address,
        "palette": palette,
        "checkpoint": str(cp),
        "steps": [],
    }
    _save(cp, state)

    try:
        created = rc.execute_create_resilient(
            req.title,
            req.address,
            confirm=bp.CREATE_CONFIRMATION,
            cdp_url=cdp_url,
            diagnostics_dir=diagnostics_dir,
            allow_remote_cdp=False,
        )
        blog_id = str(created["blog_id"])
        blog_url = str(created["expected_url"])
        state.update({"blog_id": blog_id, "blog_url": blog_url, "created": created})
        state["steps"].append("CREATE_BLOG_VALIDATED")
        _save(cp, state)

        configured = settings.execute_configure_settings(
            blog_id,
            description,
            search_description,
            confirm=settings.CONFIRMATION,
            timezone=timezone,
            cdp_url=cdp_url,
            diagnostics_dir=diagnostics_dir,
            allow_remote_cdp=False,
        )
        state["settings"] = configured
        state["steps"].append("SETTINGS_PROFILE_VALIDATED")
        _save(cp, state)

        adopted = v05.execute_model_v20_adoption(
            blog_id,
            req.title,
            blog_url,
            palette,
            confirm=v05.MODEL_V20_CONFIRMATION,
        )
        state["theme"] = adopted
        state["steps"].append("BLOGGER_MODELO_V20_ADOPTED")
        state["pages_to_publish"] = pages
        state["status"] = "BLOGGER_NEW_BLOG_V20_CORE_PROVISIONED"
        _save(cp, state)

        return {
            "status": state["status"],
            "blog_id": blog_id,
            "blog_title": req.title,
            "blog_url": blog_url,
            "address": created.get("address", req.address),
            "settings_validated": configured.get("status") == "SETTINGS_PROFILE_VALIDATED",
            "robots_untouched": configured.get("robots_untouched") is True,
            "theme_adopted": adopted.get("status") == "BLOGGER_MODELO_V20_ADOPTED",
            "theme_marker": adopted.get("public_marker"),
            "posts_deleted": adopted.get("posts_deleted"),
            "posts_copied_from_reference": adopted.get("posts_copied_from_reference"),
            "pages_to_publish": pages,
            "expected_page_count": 5,
            "expected_new_blog_posts": 0,
            "checkpoint": str(cp),
            "next_action": "PUBLISH_AND_VALIDATE_V20_PAGES_VIA_BLOGGER_BRIDGE",
        }
    except Exception as exc:
        state["status"] = "PROVISION_PARTIAL_FAILURE"
        state["error"] = re.sub(r"\s+", " ", str(exc)).strip()[:1600]
        _save(cp, state)
        blog_id = state.get("blog_id", "not-created")
        raise ProvisionError(
            f"Provisionamento interrompido com segurança. blog_id={blog_id}; checkpoint={cp}; erro={state['error']}"
        ) from exc


def main() -> int:
    p = argparse.ArgumentParser(description="Provisiona blog novo: criação + settings + V20 + manifesto das 5 páginas.")
    p.add_argument("--title", required=True)
    p.add_argument("--address", required=True)
    p.add_argument("--description", required=True)
    p.add_argument("--search-description", required=True)
    p.add_argument("--timezone", default=settings.DEFAULT_TIMEZONE)
    p.add_argument("--palette", default="auto", choices=sorted(PALETTES))
    p.add_argument("--confirm", required=True)
    args = p.parse_args()
    result = execute_provision(
        args.title,
        args.address,
        args.description,
        args.search_description,
        timezone=args.timezone,
        palette=args.palette,
        confirm=args.confirm,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
