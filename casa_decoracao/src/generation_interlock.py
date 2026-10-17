from pathlib import Path

import generate_articles as generator
from publication_gate_v2 import GENERATION_POLICY_VERSION, publication_risk_reasons

ROOT = Path(__file__).resolve().parents[2]
QUEUE_PATH = ROOT / "casa_decoracao" / "data" / "editorial_queue_100.json"
GENERATED_DIR = ROOT / "casa_decoracao" / "data" / "generated"

_original_build_article = generator.build_article


def hardened_build_article(item, raw_html):
    article = _original_build_article(item, raw_html)
    risks = publication_risk_reasons(article)
    if risks:
        raise RuntimeError("publication risk gate: " + ", ".join(risks))
    article["generation_policy_version"] = GENERATION_POLICY_VERSION
    article["quality_gate_version"] = 2
    article["last_error"] = ""
    return article


def migrate_old_automated_drafts():
    queue = generator.load_json(QUEUE_PATH, {})
    items = queue.get("items") or []
    migrated = 0

    for item in items:
        if item.get("status") != "WORDPRESS_DRAFT":
            continue
        item_id = int(item.get("id") or 0)
        if not item_id:
            continue
        article_path = GENERATED_DIR / f"{item_id:03d}.json"
        article = generator.load_json(article_path, {})
        if int(article.get("generation_policy_version") or 0) == GENERATION_POLICY_VERSION:
            continue

        item["status"] = "QUARANTINE"
        item["generation_attempts"] = 0
        item["last_error"] = "migração automática: rascunho anterior ao gate v2; regeneração obrigatória"
        migrated += 1

    if migrated:
        queue["items"] = items
        generator.save_json(QUEUE_PATH, queue)
        print(f"Migração gate v2: {migrated} rascunho(s) antigo(s) enviados para regeneração segura.")


def recover_transient_rate_limits():
    queue = generator.load_json(QUEUE_PATH, {})
    items = queue.get("items") or []
    recovered = 0

    for item in items:
        error = str(item.get("last_error") or "").casefold()
        if "429" not in error and "too many requests" not in error:
            continue
        if item.get("status") not in {"QUARANTINE", "BLOCKED"}:
            continue

        # Erro 429 é limitação transitória do provedor, não falha editorial.
        # Não deve consumir as três tentativas editoriais nem bloquear a pauta.
        item["status"] = "QUARANTINE"
        item["generation_attempts"] = 0
        item["last_error"] = "limite temporário 429 do provedor de IA; nova tentativa automática em execução posterior"
        recovered += 1

    if recovered:
        queue["items"] = items
        generator.save_json(QUEUE_PATH, queue)
        print(f"Rate limit transitório: {recovered} pauta(s) preservadas para nova tentativa futura.")


if __name__ == "__main__":
    generator.build_article = hardened_build_article
    migrate_old_automated_drafts()
    generator.main()
    recover_transient_rate_limits()
