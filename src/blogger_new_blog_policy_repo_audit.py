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
# VISUAL_CONTRACT_V20_NATIVE_STORE_AND_IDENTITY_ISOLATION_2026_11_03


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
    migration = read(".github/workflows/v20_theme_frame_page_migration.yml")
    engine = read("blogger_stores/src/vida_pet_pratica_store.py")
    wrapper = read("blogger_stores/src/vida_pet_pratica_store_page.py")
    public = read("blogger_stores/src/vida_pet_pratica_public_acceptance.py")
    lab_public = read("blogger_stores/src/casa_pratica_lab_public_acceptance.py")
    adapter = read("blogger_stores/src/blogger_new_blog_store_page_target.py")
    contract = read("NEW_BLOG_E2E_CONTRACT_2026-11-02.md")
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
    ordered_steps = [
        "- name: Preparar staging DRAFT 20+12 e validar Page em memória",
        "- name: Sincronizar Page pública somente após dry-run maduro",
        "- name: Aceitação pública Page + home + artigos",
        "- name: Persistir rotação somente após PASS público completo",
    ]
    positions = [live.find(x) for x in ordered_steps]
    if any(p < 0 for p in positions) or positions != sorted(positions):
        fail(f"ordem fail-closed das etapas do writer inválida: {list(zip(ordered_steps, positions))}")

    require(acceptance, [
        "workflow_dispatch:", "push:", 'cron: "50 11 * * *"', 'timezone: "America/Recife"',
        "permissions:\n  contents: read", f'BLOGGER_BLOG_ID: "{BLOG_ID}"',
        f'BLOGGER_STORE_PAGE_ID: "{PAGE_ID}"', f'BLOGGER_STORE_POST_ID: "{POST_ID}"',
        "READ_ONLY", "PUSH_IS_AUDIT_ONLY_NO_WRITES", "vida_pet_pratica_public_acceptance.py",
        '"blogger_stores/src/vida_pet_pratica_store.py"', '"src/blogger_policy_guard.py"',
    ], "auditor permanente")
    forbidden_write_tokens = ["git push", "service.pages().update", "service.posts().update", "service.posts().revert"]
    bad_acceptance = [x for x in forbidden_write_tokens if x in acceptance]
    if bad_acceptance:
        fail(f"auditor read-only contém capacidade de escrita: {bad_acceptance}")

    require(migration, ["workflow_dispatch:", "RECOVERY_ONLY_MANUAL", "NO_PUSH_NO_SCHEDULE", "NO_SHOPEE_SELECTION_CHANGE", "NO_ROTATION_PERSIST"], "migração/recovery visual")
    if re.search(r"(?m)^\s*(push|schedule)\s*:", migration):
        fail("migração visual de recovery voltou a ter trigger automático")

    require(engine, [
        f'BLOG_ID = "{BLOG_ID}"', f'POST_ID = "{POST_ID}"', PAGE_URL,
        "GLOBAL_POLICY_BLOCKS", "regulatedPetHealthExcluded", "VIDA_PET_PRATICA_SEMANTIC_REGRESSION_PASS",
    ], "motor pet")
    require(wrapper, ["get_post_any_status", "update_staging", "store_write", "hero_write", "identity_write"], "wrapper staging")

    require(public, [
        "require_store_html_allowed", "expected_products=20", "expected_hero=12", "BLOGGER_NEW_BLOG_V20_E2E_ACCEPTED",
        "emporio-revisao-visual-20-modelo-final", "BLOGGER_MODELO_V20_BRAND_DESCRIPTION_FEED_RUNTIME",
        "BLOGGER_MODELO_V20_BLS_STORE_NATIVE", "BLOGGER_NEW_STORE_PAGE_THEME_FRAME_PRESERVED",
        "Loja nativa Tema V20", "BLOGGER_LIQ_LAYOUT_PATCH_START",
    ], "aceitação pública Vida Pet")
    require(lab_public, [
        "BLOGGER_NEW_STORE_PAGE_THEME_FRAME_PRESERVED", "BLOGGER_MODELO_V20_BRAND_DESCRIPTION_FEED_RUNTIME",
        "BLOGGER_MODELO_V20_BLS_STORE_NATIVE", "Loja nativa Tema V20", "BLOGGER_LIQ_LAYOUT_PATCH_START",
    ], "aceitação pública Casa Lab")

    require(adapter, [
        "service.pages().update", "service.posts().revert", "expected_products=20, expected_hero=12", "inject_share_card",
        "BLOGGER_NEW_STORE_PAGE_THEME_FRAME_PRESERVED", "FORBIDDEN_THEME_STRIPPING",
        "strip_legacy_layout_patch", "LAYOUT_PATCH_START", "layout nativo Tema V20",
        "Page LOJA contém BLOGGER_LIQ_LAYOUT_PATCH",
    ], "adapter Page-target")
    forbidden_adapter = [
        "PAGE_SURFACE_FIX =",
        "fundo decorativo removido",
        "fundo limpo + carousel",
    ]
    bad_adapter = [token for token in forbidden_adapter if token in adapter]
    if bad_adapter:
        fail(f"adapter Page-target voltou a codificar clean/full-width como contrato: {bad_adapter}")
    for token in ['.bg-photo-container{display:none!important', '.bg-photo{display:none!important']:
        if token not in adapter:
            fail(f"adapter perdeu guard explícito contra remoção do Tema V20: {token}")

    require(contract, [
        "BLOGGER_NEW_STORE_PAGE_THEME_FRAME_PRESERVED",
        "bg-photo-container",
        "identidade textual",
        "descrição real do próprio blog",
        "LAB antes de produção",
    ], "contrato E2E visual/identidade")

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
    if int(summary.get("modern_blogger_auto_policy_guard") or 0) != 18:
        fail("rede legada deixou de estar 18/18 no Policy Guard")
    if int(summary.get("duplicate_writer_risks") or 0) != 0:
        fail("rede legada voltou a ter risco de writer duplicado")
    if any(str(b.get("blog_id") or "") == BLOG_ID for b in (inventory.get("blogs") or [])):
        fail("Vida Pet Prática foi indevidamente misturado ao inventário legado")

    print("BLOGGER_NEW_BLOG_POLICY_REPO_AUDIT_PASS")
    print("Vida Pet Prática: SAFE + Page-target com Loja nativa Tema V20 + identidade isolada + staging DRAFT + 5x4 semântico + Policy Guard + auditor permanente + schedule 11:35 protegidos; patch de layout em conteúdo proibido; migração recovery manual-only; rede legada 18/18 preservada.")


if __name__ == "__main__":
    main()
