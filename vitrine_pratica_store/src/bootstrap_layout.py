#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE_DIR = ROOT / "vitrine_pratica_store"
TEMPLATE_PATH = MODULE_DIR / "templates" / "store_template.html"
sys.path.insert(0, str(ROOT / "src"))
from criar_rascunho import criar_servico_blogger  # noqa: E402

BLOG_ID = os.getenv("BLOGGER_BLOG_ID", "9144338307944682868").strip()
PAGE_ID = os.getenv("BLOGGER_STORE_PAGE_ID", "8344701886444887322").strip()
START = "<!-- VITRINE_STORE_AUTO_START -->"
END = "<!-- VITRINE_STORE_AUTO_END -->"
HERO_MARKERS = ["VP_HERO_AUTO_1_START", "VP_HERO_AUTO_2_START", "VP_HERO_AUTO_3_START"]


def region(raw: str) -> str:
    a = raw.find(START)
    b = raw.find(END)
    if a < 0 or b <= a:
        raise RuntimeError("Loja atual sem marcadores da vitrine; bootstrap abortado.")
    if raw.count(START) != 1 or raw.count(END) != 1:
        raise RuntimeError("Marcadores da vitrine inconsistentes; bootstrap abortado.")
    return raw[a:b + len(END)]


def main() -> None:
    blogger = criar_servico_blogger()
    page = blogger.pages().get(blogId=BLOG_ID, pageId=PAGE_ID).execute()
    raw = str(page.get("content") or "")
    title = str(page.get("title") or "LOJA")
    if title.strip().lower() != "loja":
        raise RuntimeError("Page ID não corresponde à Loja; bootstrap abortado.")

    Path("/tmp/vitrine-pratica-loja-before.html").write_text(raw, encoding="utf-8")

    if all(marker in raw for marker in HERO_MARKERS) and "bls-page" in raw:
        print("BOOTSTRAP_LAYOUT_ALREADY_APPLIED")
        print(f"CURRENT_STORE_CARDS={raw.count('data-item-id=')}")
        return

    current_store = region(raw)
    current_count = current_store.count("data-item-id=")
    if current_count != 20:
        raise RuntimeError(f"Loja atual não possui 20 cards: {current_count}; bootstrap abortado.")

    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    ta = template.find(START)
    tb = template.find(END)
    if ta < 0 or tb <= ta:
        raise RuntimeError("Template sem marcadores da vitrine.")
    updated = template[:ta] + current_store + template[tb + len(END):]

    required = [START, END, "bls-page", *HERO_MARKERS]
    missing = [marker for marker in required if marker not in updated]
    if missing:
        raise RuntimeError(f"Template composto inválido; ausentes={missing}")
    if updated.count("data-item-id=") != 20:
        raise RuntimeError("Proteção: bootstrap alteraria a quantidade atual de cards.")

    blogger.pages().update(
        blogId=BLOG_ID,
        pageId=PAGE_ID,
        body={"title": title, "content": updated},
    ).execute()

    verify = blogger.pages().get(blogId=BLOG_ID, pageId=PAGE_ID).execute()
    verify_raw = str(verify.get("content") or "")
    missing = [marker for marker in required if marker not in verify_raw]
    if missing or verify_raw.count("data-item-id=") != 20:
        raise RuntimeError(f"Falha pós-bootstrap; ausentes={missing}; cards={verify_raw.count('data-item-id=')}")

    Path("/tmp/vitrine-pratica-loja-after.html").write_text(verify_raw, encoding="utf-8")
    print("BOOTSTRAP_LAYOUT_OK")
    print("STORE_CARDS_PRESERVED=20")
    print("HERO_MARKERS_READY=3")


if __name__ == "__main__":
    main()
