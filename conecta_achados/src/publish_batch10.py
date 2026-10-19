import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import automation

BASE_DIR = HERE.parent
PRODUCTS_PATH = BASE_DIR / "data" / "batch_10_products.json"
READY_PATH = BASE_DIR / "data" / "batch_10_ready.json"
RESULT_PATH = BASE_DIR / "data" / "batch_10_publish_result.json"
STATE_PATH = BASE_DIR / "data" / "state.json"
EXPECTED_BLOG_ID = "1719259388907013414"
BLOGGER_SPACING_SECONDS = 20


def publish_with_retry(title, content, category):
    waits = [35, 50, 70]

    for attempt in range(4):
        try:
            return automation.create_blogger_post(
                title,
                content,
                category,
                "publish",
            )
        except Exception as exc:
            text = str(exc)
            is_rate_limit = (
                "429" in text
                or "rateLimitExceeded" in text
                or "Resource has been exhausted" in text
            )
            if not is_rate_limit or attempt >= len(waits):
                raise

            wait = waits[attempt]
            print(
                f"Blogger API limitou a requisição; retry {attempt + 1}/3 "
                f"em {wait}s: {title}"
            )
            time.sleep(wait)

    raise RuntimeError("Retry Blogger esgotado.")


def main():
    products_payload = automation.load_json(PRODUCTS_PATH, {})
    ready_payload = automation.load_json(READY_PATH, {})
    state = automation.load_json(
        STATE_PATH,
        {"keyword_cursor": 0, "used_item_ids": [], "history": []},
    )

    if str(products_payload.get("blog_id") or "") != EXPECTED_BLOG_ID:
        raise RuntimeError("Lote Shopee não pertence ao Conecta Achados.")
    if str(ready_payload.get("blog_id") or "") != EXPECTED_BLOG_ID:
        raise RuntimeError("Lote SEO não pertence ao Conecta Achados.")

    source_by_id = {
        str(item.get("itemId") or ""): item
        for item in (products_payload.get("products") or [])
    }

    used = {str(x) for x in state.get("used_item_ids", [])}
    history = list(state.get("history", []))
    results = []
    failures = []
    published_in_this_run = 0

    for index, prepared in enumerate(ready_payload.get("posts") or [], start=1):
        item_id = str(prepared.get("itemId") or "").strip()
        source = source_by_id.get(item_id)

        if not source:
            failures.append({
                "item_id": item_id,
                "error": "Produto não encontrado no lote extraído da Shopee.",
            })
            continue

        if item_id in used:
            results.append({
                "item_id": item_id,
                "status": "skipped_already_published",
                "title": prepared.get("title"),
            })
            print(f"{index}/10 já publicado anteriormente: {item_id}")
            continue

        title = str(prepared.get("title") or "").strip()
        description = str(prepared.get("description") or "").strip()
        category = str(prepared.get("category") or source.get("category") or "Achados").strip()

        if not title or not description:
            failures.append({
                "item_id": item_id,
                "error": "Título ou descrição ausente.",
            })
            continue

        try:
            print(f"{index}/10 preparando imagem: {title}")
            image_info = automation.prepare_product_image(source)
            content = automation.product_html(
                source,
                {"title": title, "description": description},
                image_info,
                category,
            )

            if published_in_this_run > 0:
                print(
                    f"Aguardando {BLOGGER_SPACING_SECONDS}s para respeitar "
                    "o limite da Blogger API."
                )
                time.sleep(BLOGGER_SPACING_SECONDS)

            print(f"{index}/10 publicando no Blogger: {title}")
            blogger_result = publish_with_retry(
                title,
                content,
                category,
            )

            result = {
                "item_id": item_id,
                "status": "published",
                "title": title,
                "category": category,
                "source_product_name": source.get("productName"),
                "blogger_post_id": blogger_result.get("id"),
                "blogger_status": blogger_result.get("status"),
                "blogger_url": blogger_result.get("url"),
                "image_source": image_info.get("source"),
                "published_at_utc": datetime.now(timezone.utc).isoformat(),
            }
            results.append(result)
            used.add(item_id)
            published_in_this_run += 1
            history.append({
                "timestamp_utc": result["published_at_utc"],
                "item_id": item_id,
                "source_product_name": source.get("productName"),
                "seo_title": title,
                "category": category,
                "keyword": source.get("source_keyword"),
                "blogger_post_id": blogger_result.get("id"),
                "blogger_status": blogger_result.get("status"),
                "blogger_url": blogger_result.get("url"),
                "chatgpt_model": "GPT-5.6 Sol (current conversation)",
                "image_source": image_info.get("source"),
                "mode": "publish",
                "batch": "initial_10",
            })
            print(f"PUBLICADO {index}/10: {blogger_result.get('url')}")

        except Exception as exc:
            failures.append({
                "item_id": item_id,
                "title": title,
                "error": str(exc),
            })
            print(f"FALHA {index}/10: {title} -> {exc}")

    state["used_item_ids"] = list(used)[-500:]
    state["history"] = history[-1000:]
    automation.save_json(STATE_PATH, state)

    payload = {
        "blog_id": EXPECTED_BLOG_ID,
        "requested": 10,
        "published_now": len([x for x in results if x.get("status") == "published"]),
        "skipped": len([x for x in results if x.get("status") == "skipped_already_published"]),
        "failures": failures,
        "results": results,
    }
    automation.save_json(RESULT_PATH, payload)

    if failures:
        raise RuntimeError(
            f"Publicação parcial: {len(failures)} falha(s). Consulte {RESULT_PATH}."
        )

    print("PUBLICAÇÃO BATCH 10: PASSOU")
    print("Posts publicados agora:", payload["published_now"])
    print("Posts já publicados e ignorados:", payload["skipped"])


if __name__ == "__main__":
    main()
