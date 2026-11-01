#!/usr/bin/env python3
from __future__ import annotations
import importlib.util
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE_DIR = ROOT / "cabelos_store"
DATA_DIR = MODULE_DIR / "data"
HISTORY_PATH = DATA_DIR / "store_rotation.json"
LAST_SELECTION_PATH = DATA_DIR / "store_last_selection.json"
SCAN_DIR = DATA_DIR / "store_shopee_scan"
BLOG_ID = os.getenv("BLOGGER_BLOG_ID", "6319734511998091378").strip()
PAGE_ID = os.getenv("BLOGGER_STORE_PAGE_ID", "").strip()
ITEMS_PER_CATEGORY = max(1, min(int(os.getenv("BLOGGER_STORE_ITEMS_PER_CATEGORY", "4")), 8))
RECENT_DAYS = max(1, min(int(os.getenv("BLOGGER_STORE_RECENT_DAYS", "1")), 30))
DRY_RUN = os.getenv("BLOGGER_STORE_DRY_RUN", "false").strip().lower() in {"1", "true", "yes", "on"}
CATEGORY_SPECS = [
    ("Máscaras & Tratamentos Cosméticos", "Máscaras & Tratamentos Cosméticos", "bls-mascaras-tratamentos"),
    ("Shampoo & Condicionamento", "Shampoo & Condicionamento", "bls-shampoo-condicionamento"),
    ("Finalização", "Finalização", "bls-finalizacao"),
    ("Secadores & Escovas", "Secadores & Escovas", "bls-secadores-escovas"),
    ("Pentes & Acessórios", "Pentes & Acessórios", "bls-pentes-acessorios"),
]

os.environ.setdefault("SHOPEE_OPPORTUNITIES_CONFIG", str(MODULE_DIR / "config" / "shopee_oportunidades.json"))
os.environ.setdefault("SHOPEE_INTENT_RULES", str(MODULE_DIR / "config" / "shopee_intent_rules.json"))
os.environ.setdefault("SHOPEE_OUTPUT_DIR", str(SCAN_DIR))
os.environ.setdefault("SHOPEE_CATEGORY", "all")
os.environ.setdefault("SHOPEE_TOP_N", "70")

sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "blogger_product_store" / "src"))
sys.path.insert(0, str(MODULE_DIR / "src"))
from shopee_oportunidades_cabelos import regression_checks

_base_path = ROOT / "blogger_product_store" / "src" / "store_auto.py"
_spec = importlib.util.spec_from_file_location("validated_store_auto", _base_path)
base = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
_spec.loader.exec_module(base)

for name, value in {
    "MODULE_DIR": MODULE_DIR, "DATA_DIR": DATA_DIR, "HISTORY_PATH": HISTORY_PATH,
    "LAST_SELECTION_PATH": LAST_SELECTION_PATH, "SCAN_DIR": SCAN_DIR, "BLOG_ID": BLOG_ID,
    "PAGE_ID": PAGE_ID, "ITEMS_PER_CATEGORY": ITEMS_PER_CATEGORY, "RECENT_DAYS": RECENT_DAYS,
    "DRY_RUN": DRY_RUN, "CATEGORY_SPECS": CATEGORY_SPECS,
}.items():
    setattr(base, name, value)
base.shopee_v23.run_regression_checks = regression_checks

START_MARKER=base.START_MARKER; END_MARKER=base.END_MARKER
now_local=base.now_local; choose_products=base.choose_products; render_store_block=base.render_store_block
validate_shape=base.validate_shape; brl=base.brl; price_label=base.price_label
valid_product=base.valid_product; criar_servico_blogger=base.criar_servico_blogger


def apply_runtime_patches():
    base.MODULE_DIR=MODULE_DIR; base.DATA_DIR=DATA_DIR; base.HISTORY_PATH=HISTORY_PATH
    base.LAST_SELECTION_PATH=LAST_SELECTION_PATH; base.SCAN_DIR=SCAN_DIR; base.BLOG_ID=BLOG_ID
    base.PAGE_ID=PAGE_ID; base.ITEMS_PER_CATEGORY=ITEMS_PER_CATEGORY; base.RECENT_DAYS=RECENT_DAYS
    base.DRY_RUN=DRY_RUN; base.CATEGORY_SPECS=CATEGORY_SPECS
    base.valid_product=globals()["valid_product"]; base.criar_servico_blogger=globals()["criar_servico_blogger"]
    base.shopee_v23.run_regression_checks=regression_checks


def enhance_store_block(block: str) -> str:
    old_css = ".bls-product{display:block;min-width:0;text-decoration:none;color:#17212b}"
    new_css = ".bls-product{display:block;min-width:0;text-decoration:none;color:#17212b;position:relative;z-index:2;pointer-events:auto!important;cursor:pointer!important}\n.bls-product>*{pointer-events:none!important}\n.bls-product-cta{display:flex;align-items:center;justify-content:center;margin-top:9px;padding:9px 10px;border-radius:8px;background:#ee4d2d;color:#fff;font-size:11px;font-weight:900;line-height:1.15;text-align:center}"
    if old_css in block:
        block=block.replace(old_css,new_css,1)
    def add_cta(m):
        card=m.group(0)
        return card if "bls-product-cta" in card else card[:-4]+'\n  <span class="bls-product-cta">Ver oferta na Shopee</span>\n</a>'
    block,count=re.subn(r'<a class="bls-product"[^>]*>.*?</a>',add_cta,block,flags=re.S)
    expected=len(CATEGORY_SPECS)*ITEMS_PER_CATEGORY
    if count != expected: raise RuntimeError(f"Cards renderizados={count}, esperado={expected}")
    return block


def main():
    apply_runtime_patches(); DATA_DIR.mkdir(parents=True,exist_ok=True)
    print("Blogger — Loja automática Cabelos em Foco")
    print("Modo:", "DRY-RUN" if DRY_RUN else "PUBLICAÇÃO")
    ranking=base.shopee_v23.scan_v23(); print("Ranking Shopee recebido:",len(ranking))
    chosen=base.choose_products(ranking,base.load_history())
    block=enhance_store_block(base.render_store_block(chosen)); base.validate_shape(chosen,block)
    if DRY_RUN:
        base.validate_blogger_target(); data=base.snapshot(chosen,"DRY_RUN_OK")
        print(f"DRY-RUN OK: {data['totalItems']} produtos únicos em {data['categoryCount']} categorias; Blogger não alterado."); return
    blogger_info=base.update_blogger(block,chosen); data=base.snapshot(chosen,"PUBLISHED",blogger_info); base.append_history(data)
    print(f"PUBLICAÇÃO OK: {data['totalItems']} produtos únicos; alvo Blogger {blogger_info.get('pageId')} verificado.")

if __name__ == "__main__": main()
