#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BLOG_ID = "8052455848487624244"
PAGE_ID = "8624646966938350648"
POST_ID = "7332800716046515902"
PAGE_URL = "https://vida-pet-pratica.blogspot.com/p/loja.html"


def fail(message: str) -> None:
    raise SystemExit("BLOGGER_NEW_BLOG_POLICY_REPO_AUDIT_FAIL: " + message)


def read(rel: str) -> str:
    path = ROOT / rel
    if not path.exists():
        fail(f"arquivo obrigatório ausente: {rel}")
    return path.read_text(encoding="utf-8", errors="ignore")


def load_json(rel: str) -> dict:
    return json.loads(read(rel))


def require(text: str, tokens: list[str], label: str) -> None:
    missing = [token for token in tokens if token not in text]
    if missing:
        fail(f"{label}: tokens ausentes: {missing}")


def main() -> None:
    safe = read(".github/workflows/vida_pet_pratica_store_safe.yml")
    live = read(".github/workflows/vida_pet_pratica_store_page_autonomous.yml")
    acceptance = read(".github/workflows/vida_pet_pratica_acceptance_audit.yml")
    engine = read("blogger_stores/src/vida_pet_pratica_store.py")
    wrapper = read("blogger_stores/src/vida_pet_pratica_store_page.py")
    public = read("blogger_stores/src/vida_pet_pratica_public_acceptance.py")
    adapter = read("blogger_stores/src/blogger_new_blog_store_page_target.py")
    rules = load_json("config/shopee_vida_pet_pratica_intent_rules.json")
    config = load_json("config/shopee_vida_pet_pratica.json")
    selection = load_json("blogger_stores/data/vida_pet_pratica_selection.json")
    rotation = load_json("blogger_stores/data/vida_pet_pratica_rotation.json")
    inventory = load_json("blogger_multi_store/data/NETWORK_STORE_INVENTORY_2026-11-02.json")

    require(safe, ["blogger_policy_guard.py", "blogger_policy_guard_self_test.py", "require_product_allowed", "20/20", "VIDA_PET_PRATICA_SAFE_READ_ONLY_PASS"], "SAFE")
    if re.search(r"(?m)^\s*schedule\s*:", safe):
        fail("SAFE não pode ter schedule")

    require(live, [
        "workflow_dispatch:", 'cron: "35 11 * * *"', 'timezone: "America/Recife"',
        "SCHEDULE_ENABLED_AFTER_VALIDATION_2026_11_02", "FINAL_WRITER_NO_PUSH_2026_11_02",
        f'BLOGGER_BLOG_ID: "{BLOG_ID}"', f'BLOGGER_STORE_PAGE_ID: "{PAGE_ID}"',
        f'BLOGGER_STORE_POST_ID: "{POST_ID}"', f'BLOGGER_STORE_PAGE_URL: "{PAGE_URL}"',
        "blogger_policy_guard.py", "require_product_allowed", "sync-dry-run", "sync-live",
        "ensure-staging-draft", "verify-page", "vida_pet_pratica_public_acceptance.py", "persist",
        "STORE_POST_TECHNICAL_STAGING_MUST_REMAIN_DRAFT",
    ], "writer final")
    if re.search(r"(?m)^\s*push\s*:", live):
        fail("writer final voltou a ter gatilho push")
    ordered = ["sync-dry-run", "sync-live", "vida_pet_pratica_public_acceptance.py", "persist"]
    positions = [live.find(x) for x in ordered]
    if any(p < 0 for p in positions) or positions != sorted(positions):
        fail(f"ordem fail-closed do writer inválida: {list(zip(ordered, positions))}")

    require(acceptance, [
        "workflow_dispatch:", 'cron: "50 11 * * *"', 'timezone: "America/Recife"',
        "permissions:\n  contents: read", f'BLOGGER_BLOG_ID: "{BLOG_ID}"',
        f'BLOGGER_STORE_PAGE_ID: "{PAGE_ID}"', f'BLOGGER_STORE_POST_ID: "{POST_ID}"',
        "READ_ONLY", "vida_pet_pratica_public_acceptance.py",
    ], "auditor permanente")
    if re.search(r"(?m)^\s*push\s*:", acceptance):
        fail("auditor permanente não deve ter push")

    require(engine, [
        f'BLOG_ID = "{BLOG_ID}"', f'POST_ID = "{POST_ID}"', PAGE_URL,
        "GLOBAL_POLICY_BLOCKS", "regulatedPetHealthExcluded", "VIDA_PET_PRATICA_SEMANTIC_REGRESSION_PASS",
    ], "motor pet")
    require(wrapper, ["get_post_any_status", "update_staging", "store_write", "hero_write", "identity_write"], "wrapper staging")
    require(public, ["require_store_html_allowed", "expected_products=20", "expected_hero=12", "BLOGGER_NEW_BLOG_V20_E2E_ACCEPTED"], "aceitação pública")
    require(adapter, ["service.pages().update", "service.posts().revert", "expected_products=20, expected_hero=12", "inject_share_card"], "adapter Page-target")

    categories = config.get("categories") or {}
    intents = [item for values in categories.values() for item in values]
    if len(categories) != 5 or len(intents) != 20 or len(set(intents)) != 20:
        fail(f"config pet precisa permanecer 5x4: categorias={len(categories)} intents={len(intents)} únicos={len(set(intents))}")
    if len(rules.get("rules") or {}) != 20:
        fail("regras semânticas pet precisam cobrir exatamente as 20 intenções")

    selected_categories = selection.get("categories") or {}
    products = [p for values in selected_categories.values() for p in values]
    ids = [str(p.get("itemId") or "") for p in products]
    semantic = selection.get("semanticValidation") or {}
    if len(selected_categories) != 5 or len(products) != 20 or len(set(ids)) != 20 or not all(ids):
        fail("seleção persistida não preserva 5 categorias / 20 produtos únicos")
    if not semantic.get("regulatedPetHealthExcluded"):
        fail("seleção persistida perdeu gate regulatedPetHealthExcluded")

    if rotation.get("blogId") != BLOG_ID:
        fail("rotação está associada a outro Blog ID")
    runs = rotation.get("runs") or []
    if not runs or len((runs[-1] or {}).get("items") or []) != 20:
        fail("rotação não possui último run público validado com 20 itens")

    summary = inventory.get("summary") or {}
    if int(summary.get("blogs_total") or 0) != 18:
        fail("inventário legado deixou de ser 18; novo blog não deve alterar o inventário legado")
    if any(str(b.get("blog_id") or "") == BLOG_ID for b in (inventory.get("blogs") or [])):
        fail("Vida Pet Prática foi indevidamente misturado ao inventário legado")

    print("BLOGGER_NEW_BLOG_POLICY_REPO_AUDIT_PASS")
    print("Vida Pet Prática: SAFE + writer Page-target + staging DRAFT + 5x4 semântico + Policy Guard + auditor permanente + schedule 11:35 protegidos; rede legada 18 preservada.")


if __name__ == "__main__":
    main()
