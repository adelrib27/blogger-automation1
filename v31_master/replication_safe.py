#!/usr/bin/env python3
"""V31 reusable SAFE gate: never writes to Blogger or starts a Runner.

Reads an exact per-blog profile, validates SEO/page/store contracts, and can
verify a separately retrieved Blogger inventory. Fail-closed by default.
"""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlsplit

PAGE_SLUGS = {
    "Sobre": "/p/sobre.html",
    "Contato": "/p/contato.html",
    "Política de Privacidade": "/p/politica-de-privacidade.html",
    "Termos de Uso": "/p/termos-de-uso.html",
    "Aviso de Afiliados": "/p/aviso-de-afiliados.html",
}

class GateError(ValueError):
    pass

def load_profile(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    validate_profile(data)
    return data

def validate_profile(d: dict) -> None:
    if d.get("schema") != "blogger-v31-replication-profile/v1" or d.get("mode") != "LAB_SAFE_ONLY":
        raise GateError("schema/mode não permitidos")
    target = d.get("target") or {}
    bid, url = str(target.get("blog_id", "")), str(target.get("url", ""))
    p = urlsplit(url)
    if not re.fullmatch(r"[0-9]{10,22}", bid):
        raise GateError("Blog ID inválido")
    if (p.scheme != "https" or not re.fullmatch(r"[a-z0-9-]+\.blogspot\.com", p.netloc)
            or p.path != "/" or p.query or p.fragment or not url.endswith("/")):
        raise GateError("URL Blogger não canônica")
    theme = d.get("theme") or {}
    if theme.get("variant") != "V31_R52_MOBILE" or theme.get("install_permission") is not False:
        raise GateError("tema V31 não autorizado para reinstalação")
    if not re.fullmatch(r"[a-f0-9]{64}", str(theme.get("reference_xml_sha256", ""))):
        raise GateError("hash de referência XML ausente")
    seo = d.get("seo") or {}
    if (len(seo.get("description", "")) not in range(1, 501)
            or len(seo.get("search_description", "")) not in range(1, 151)
            or seo.get("timezone") != "(GMT-03:00) Horário Padrão de Brasília – São Paulo"
            or seo.get("custom_robots") != "UNCHANGED"):
        raise GateError("perfil SEO fora do contrato")
    for flag in ("https_redirect", "search_visibility", "lazy_images", "webp_images"):
        if seo.get(flag) is not True:
            raise GateError(f"SEO {flag} não validado")
    pages = d.get("pages") or []
    if len(pages) != 5 or {p.get("title"): p.get("path") for p in pages} != PAGE_SLUGS:
        raise GateError("as cinco rotas institucionais precisam ser exatas")
    if len({str(x.get("id")) for x in pages}) != 5 or not all(str(x.get("id", "")).isdigit() for x in pages):
        raise GateError("Page IDs ausentes/duplicados")
    store = d.get("store") or {}
    if (store.get("page_path") != "/p/loja.html" or not str(store.get("page_id", "")).isdigit()
            or store.get("first_publish") is not False or store.get("auto_update") is not False
            or store.get("mode") != "placeholder_until_shopee_safe_pass"
            or store.get("expected_products") != 16
            or store.get("write_target") != "existing_page_only"
            or len(store.get("categories") or []) != 4):
        raise GateError("LOJA sem gate SAFE ou quantidade incorreta")
    guards = d.get("guards") or {}
    if not all(guards.get(k) is True for k in (
            "allowlisted_blog_only", "disable_existing_writers",
            "runner_r49_no_restart", "never_modify_other_blogs",
            "never_modify_theme", "never_expose_shopee_secret",
            "required_readback")):
        raise GateError("proteções R49 incompletas")

def verify_snapshot(d: dict, snapshot: dict) -> dict:
    """Optional extra gate using user-provided API readback, not inferred from file."""
    t, store = d["target"], d["store"]
    if str(snapshot.get("blog_id")) != t["blog_id"]:
        raise GateError("snapshot de outro blog")
    pages = {str(x["id"]): x for x in snapshot.get("pages", [])}
    expected = d["pages"] + [{"title": "LOJA", "id": store["page_id"], "path": store["page_path"]}]
    for item in expected:
        page = pages.get(item["id"])
        if not page or page.get("status") != "live":
            raise GateError("Page ausente ou não-live")
        if not str(page.get("url", "")).startswith(t["url"][:-1] + item["path"]):
            raise GateError("rota Page divergente")
    return {"status": "V31_SAFE_PROFILE_SNAPSHOT_VALIDATED", "blog_id": t["blog_id"],
            "page_count": len(expected), "writes": False}

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", required=True, type=Path)
    ap.add_argument("--snapshot", type=Path)
    args = ap.parse_args()
    d = load_profile(args.profile)
    result = {"status": "V31_SAFE_PROFILE_OK_NO_WRITES",
              "blog_id": d["target"]["blog_id"], "pages": 5,
              "store_page_id": d["store"]["page_id"],
              "planned_products": 16,
              "theme_install": False, "runner_restart": False, "writes": False}
    if args.snapshot:
        result["inventory"] = verify_snapshot(d, json.loads(args.snapshot.read_text(encoding="utf-8")))
    print(json.dumps(result, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"status": "V31_SAFE_PROFILE_FAIL_CLOSED",
                          "reason_type": type(exc).__name__, "writes": False}, ensure_ascii=False))
        raise SystemExit(2)
