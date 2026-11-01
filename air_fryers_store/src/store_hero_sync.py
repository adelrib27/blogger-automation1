#!/usr/bin/env python3
from __future__ import annotations
import importlib.util
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE_DIR = ROOT / "air_fryers_store"
DATA_DIR = MODULE_DIR / "data"
LAST_SELECTION_PATH = DATA_DIR / "store_last_selection.json"
BLOG_ID = os.getenv("BLOGGER_BLOG_ID", "9113728635217260884").strip()
PAGE_ID = os.getenv("BLOGGER_STORE_PAGE_ID", "").strip()

sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "blogger_product_store" / "src"))
_base_path = ROOT / "blogger_product_store" / "src" / "store_hero_sync.py"
_spec = importlib.util.spec_from_file_location("validated_store_hero", _base_path)
base = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
_spec.loader.exec_module(base)
base.MODULE_DIR = MODULE_DIR
base.DATA_DIR = DATA_DIR
base.LAST_SELECTION_PATH = LAST_SELECTION_PATH
base.BLOG_ID = BLOG_ID
base.PAGE_ID = PAGE_ID

HERO_MARKERS = base.HERO_MARKERS
render_card = base.render_card
render_region = base.render_region
locate = base.locate
load_selection = base.load_selection
criar_servico_blogger = base.criar_servico_blogger


def hero_sets(data: dict):
    c = data.get("categories") or {}
    required = ["Air Fryers & Fritadeiras", "Air Fryers Grandes & Família", "Formas & Revestimentos", "Grelhas & Cestos", "Utensílios & Preparo"]
    for key in required:
        if len(c.get(key) or []) != 4:
            raise RuntimeError(f"Seleção inválida para hero: {key}")
    slides = [
        [("Air Fryer", p) for p in c[required[0]]],
        [("Grande/Família", p) for p in c[required[1]][:2]] + [("Forma", p) for p in c[required[2]][:2]],
        [("Grelha/Cesto", p) for p in c[required[3]][:2]] + [("Preparo", p) for p in c[required[4]][:2]],
    ]
    ids = [str(p.get("itemId")) for slide in slides for _, p in slide]
    if len(ids) != 12 or len(set(ids)) != 12:
        raise RuntimeError("Seleção do hero não contém 12 produtos únicos.")
    return slides


def main() -> None:
    base.MODULE_DIR = MODULE_DIR
    base.DATA_DIR = DATA_DIR
    base.LAST_SELECTION_PATH = LAST_SELECTION_PATH
    base.BLOG_ID = BLOG_ID
    base.PAGE_ID = PAGE_ID
    base.criar_servico_blogger = globals()["criar_servico_blogger"]
    data = base.load_selection()
    slides = hero_sets(data)
    blocks = [
        base.render_region(*base.HERO_MARKERS[0], "Air fryers em destaque", slides[0], include_css=True),
        base.render_region(*base.HERO_MARKERS[1], "Modelos grandes, formas e revestimentos", slides[1]),
        base.render_region(*base.HERO_MARKERS[2], "Grelhas, cestos e utensílios úteis", slides[2]),
    ]
    blogger = base.criar_servico_blogger()
    page = blogger.pages().get(blogId=BLOG_ID, pageId=base.page_id()).execute()
    raw = str(page.get("content") or "")
    original_len = len(raw)
    for (start, end), block in zip(base.HERO_MARKERS, blocks):
        a, b = base.locate(raw, start, end)
        raw = raw[:a] + block + raw[b:]
    if len(raw) < max(4500, int(original_len * 0.55)):
        raise RuntimeError("Proteção de integridade do hero: conteúdo resultante ficou pequeno demais.")
    blogger.pages().update(blogId=BLOG_ID, pageId=base.page_id(), body={"title": page.get("title") or "Loja", "content": raw}).execute()
    verify = blogger.pages().get(blogId=BLOG_ID, pageId=base.page_id()).execute()
    verify_raw = str(verify.get("content") or "")
    ids = [str(p.get("itemId")) for slide in slides for _, p in slide]
    missing = [i for i in ids if f'data-hero-item-id="{i}"' not in verify_raw]
    if missing or verify_raw.count("data-hero-item-id=") != 12:
        raise RuntimeError(f"Falha na sincronização do hero; IDs ausentes={missing[:5]}")
    print("HERO OK: 12 mini-cards únicos sincronizados.")


if __name__ == "__main__":
    main()
