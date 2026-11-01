#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "vitrine_pratica_store"
DST = ROOT / "ventiladores_em_foco_store"
WORKFLOWS = ROOT / ".github" / "workflows"

CATEGORY_MAP = {
    "Casa & Organização": "Ventiladores de Mesa",
    "Cozinha & Utilidades": "Ventiladores de Coluna",
    "Tecnologia & Acessórios": "Ventiladores de Parede",
    "Beleza & Cuidados": "Ventiladores de Teto",
    "Dia a Dia & Praticidade": "Torre & Circuladores",
}
SLUG_MAP = {
    "bls-casa-organizacao": "bls-ventiladores-mesa",
    "bls-cozinha-utilidades": "bls-ventiladores-coluna",
    "bls-tecnologia": "bls-ventiladores-parede",
    "bls-beleza": "bls-ventiladores-teto",
    "bls-dia-a-dia": "bls-torre-circuladores",
}


def replace_text_files() -> None:
    mapping = {
        "vitrine_pratica_store": "ventiladores_em_foco_store",
        "Vitrine Prática": "Ventiladores em Foco",
        "VITRINE PRÁTICA": "VENTILADORES EM FOCO",
        "9144338307944682868": "4473989735719981382",
        "115613719594316807": "1410775502611365606",
        "https://vitrine-pratica.blogspot.com": "https://ventiladores-em-foco.blogspot.com",
        "Achados práticos para casa, tecnologia, beleza e dia a dia": "Ventiladores para cada ambiente",
        "Descubra produtos úteis para facilitar a rotina": "Encontre o ventilador ideal para cada ambiente",
        "Uma vitrine afiliada com achados para casa, cozinha, tecnologia, beleza e dia a dia, selecionados automaticamente na Shopee.": "Uma vitrine afiliada dedicada a ventiladores de mesa, coluna, parede, teto, torre e circuladores selecionados automaticamente na Shopee.",
        "Vitrine de achados práticos para casa, tecnologia, beleza e dia a dia": "Vitrine especializada em ventiladores e circuladores",
    }
    mapping.update(CATEGORY_MAP)
    mapping.update(SLUG_MAP)
    for path in DST.rglob("*"):
        if not path.is_file() or path.suffix not in {".py", ".json", ".html", ".txt", ".md", ".yml", ".yaml"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for before, after in mapping.items():
            text = text.replace(before, after)
        path.write_text(text, encoding="utf-8")


def write_config() -> None:
    config = {
        "version": 1,
        "project": "Blogger Store - Ventiladores em Foco",
        "market": "BR",
        "currency": "BRL",
        "min_seller_commission_rate": 0.03,
        "min_rating_when_available": 4.0,
        "reserve_enabled": True,
        "reserve_min_rating_when_available": 4.0,
        "query_limit": 15,
        "reserve_query_limit": 15,
        "top_n": 60,
        "weights": {
            "seller_extra_commission": 0.4,
            "search_demand_proxy": 0.25,
            "sales": 0.15,
            "rating": 0.1,
            "discount": 0.05,
            "top_performance": 0.05,
        },
        "diversity": {
            "enabled": True,
            "max_per_shop": 2,
            "max_per_keyword": 2,
            "max_per_category": 8,
            "relaxed_caps": {"max_per_shop": 3, "max_per_keyword": 3, "max_per_category": 10},
            "policy": "strict_first_then_relax_then_fill_without_using_standard_commission_if_extra_candidates_still_exist",
        },
        "categories": {
            "Ventiladores de Mesa": ["ventilador de mesa", "ventilador turbo mesa", "ventilador silencioso mesa"],
            "Ventiladores de Coluna": ["ventilador de coluna", "ventilador pedestal", "ventilador coluna turbo"],
            "Ventiladores de Parede": ["ventilador de parede", "ventilador industrial parede", "ventilador oscilante parede"],
            "Ventiladores de Teto": ["ventilador de teto", "ventilador teto controle remoto", "ventilador teto com luminaria"],
            "Torre & Circuladores": ["ventilador torre", "circulador de ar", "ventilador circulador turbo"],
        },
    }
    (DST / "config" / "shopee_oportunidades.json").write_text(
        json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    blocked = [
        "helice avulsa", "hélice avulsa", "helice para ventilador", "hélice para ventilador",
        "motor para ventilador", "motor ventilador", "capacitor", "grade para ventilador",
        "grade ventilador", "peca ventilador", "peça ventilador", "pecas ventilador",
        "peças ventilador", "reposicao", "reposição", "kit reparo", "rolamento", "eixo",
        "parafuso", "carcaca", "carcaça", "suporte avulso", "base avulsa", "botao ventilador",
        "botão ventilador", "placa ventilador", "controle remoto avulso", "controle para ventilador",
        "capa para ventilador", "adaptador para ventilador",
    ]
    specs = {
        "ventilador de mesa": [["ventilador"], ["mesa"]],
        "ventilador turbo mesa": [["ventilador"], ["mesa"], ["turbo", "forte", "potente"]],
        "ventilador silencioso mesa": [["ventilador"], ["mesa"], ["silencioso", "silencio", "silêncio", "quiet"]],
        "ventilador de coluna": [["ventilador"], ["coluna", "pedestal"]],
        "ventilador pedestal": [["ventilador"], ["pedestal", "coluna"]],
        "ventilador coluna turbo": [["ventilador"], ["coluna", "pedestal"], ["turbo", "forte", "potente"]],
        "ventilador de parede": [["ventilador"], ["parede"]],
        "ventilador industrial parede": [["ventilador"], ["parede"], ["industrial", "50cm", "60cm", "70cm"]],
        "ventilador oscilante parede": [["ventilador"], ["parede"], ["oscilante", "oscilacao", "oscilação"]],
        "ventilador de teto": [["ventilador"], ["teto"]],
        "ventilador teto controle remoto": [["ventilador"], ["teto"], ["controle remoto", "controle"]],
        "ventilador teto com luminaria": [["ventilador"], ["teto"], ["luminaria", "luminária", "lampada", "lâmpada", "led"]],
        "ventilador torre": [["ventilador"], ["torre", "tower"]],
        "circulador de ar": [["circulador"], ["ar"]],
        "ventilador circulador turbo": [["ventilador", "circulador"], ["turbo", "circulador"]],
    }
    intent = {
        "version": 1,
        "description": "Regras semânticas de Ventiladores em Foco. Aceita aparelhos completos e bloqueia peças, reposições e acessórios avulsos.",
        "rules": {k: {"require_groups": groups, "block_phrases": blocked} for k, groups in specs.items()},
    }
    (DST / "config" / "shopee_intent_rules.json").write_text(
        json.dumps(intent, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def write_scanner() -> None:
    text = r'''#!/usr/bin/env python3
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE_DIR = ROOT / "ventiladores_em_foco_store"
ROOT_SRC = ROOT / "src"
os.environ.setdefault("SHOPEE_OPPORTUNITIES_CONFIG", str(MODULE_DIR / "config" / "shopee_oportunidades.json"))
os.environ.setdefault("SHOPEE_INTENT_RULES", str(MODULE_DIR / "config" / "shopee_intent_rules.json"))
os.environ.setdefault("SHOPEE_OUTPUT_DIR", str(MODULE_DIR / "data" / "shopee_oportunidades"))
if str(ROOT_SRC) not in sys.path:
    sys.path.insert(0, str(ROOT_SRC))
import shopee_oportunidades_v23 as v23


def regression_checks(rules_doc):
    cases = [
        ("Ventilador de Mesa 40cm Turbo 6 Pás", "ventilador de mesa", True),
        ("Hélice para Ventilador de Mesa 40cm Reposição", "ventilador de mesa", False),
        ("Ventilador de Coluna Pedestal 40cm 3 Velocidades", "ventilador de coluna", True),
        ("Motor para Ventilador de Coluna", "ventilador de coluna", False),
        ("Ventilador de Parede 60cm Oscilante Industrial", "ventilador de parede", True),
        ("Grade para Ventilador de Parede 60cm", "ventilador de parede", False),
        ("Ventilador de Teto 3 Pás com Controle Remoto", "ventilador teto controle remoto", True),
        ("Controle Remoto Avulso para Ventilador de Teto", "ventilador teto controle remoto", False),
        ("Ventilador de Teto com Luminária LED", "ventilador teto com luminaria", True),
        ("Ventilador Torre Silencioso 3 Velocidades", "ventilador torre", True),
        ("Circulador de Ar Turbo 50cm", "circulador de ar", True),
        ("Capacitor para Circulador de Ar", "circulador de ar", False),
    ]
    failures = []
    for title, keyword, expected in cases:
        actual = bool(v23.evaluate_keyword(title, keyword, rules_doc).get("accepted"))
        if actual != expected:
            failures.append({"title": title, "keyword": keyword, "expected": expected, "actual": actual})
    if failures:
        raise SystemExit("Falha nos testes semânticos Ventiladores em Foco: " + repr(failures))
    print(f"Testes semânticos Ventiladores em Foco: {len(cases)}/{len(cases)} OK")


def main():
    v23.run_regression_checks = regression_checks
    print("=== VENTILADORES EM FOCO — SHOPEE OPORTUNIDADES ===")
    ranking = v23.scan_v23()
    v23.print_v23(ranking)


if __name__ == "__main__":
    main()
'''
    (DST / "src" / "shopee_oportunidades_vitrine_pratica.py").write_text(text, encoding="utf-8")


def write_post_wrapper() -> None:
    text = r'''#!/usr/bin/env python3
from __future__ import annotations
import os
import re
import unicodedata
import store_auto as base
from post_target_proxy import BloggerPostTargetProxy
from store_layout_patch import patch_store_layout

POST_ID = os.getenv("BLOGGER_STORE_POST_ID", "1410775502611365606").strip()
if not POST_ID:
    raise RuntimeError("BLOGGER_STORE_POST_ID ausente.")


def _norm(value):
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch)).lower()
    return re.sub(r"\s+", " ", text).strip()


_original_valid_product = base.valid_product


def strict_valid_product(product):
    if not _original_valid_product(product):
        return False
    title = _norm(product.get("productName") or "")
    if not ("ventilador" in title or "circulador" in title):
        return False
    blocked = (
        "helice avulsa", "helice para ventilador", "motor para ventilador", "motor ventilador",
        "capacitor", "grade para ventilador", "grade ventilador", "peca ventilador",
        "pecas ventilador", "reposicao", "kit reparo", "rolamento", "eixo", "parafuso",
        "carcaca", "suporte avulso", "base avulsa", "botao ventilador", "placa ventilador",
        "controle remoto avulso", "controle para ventilador", "capa para ventilador",
        "adaptador para ventilador",
    )
    return not any(token in title for token in blocked)


base.valid_product = strict_valid_product
_real_factory = base.criar_servico_blogger
base.PAGE_ID = POST_ID
base.criar_servico_blogger = lambda: BloggerPostTargetProxy(_real_factory())

if __name__ == "__main__":
    patch_store_layout()
    base.main()
'''
    (DST / "src" / "store_auto_post.py").write_text(text, encoding="utf-8")


def patch_hero() -> None:
    path = DST / "src" / "store_hero_sync.py"
    text = path.read_text(encoding="utf-8")
    start = text.index("def hero_sets(data: dict):")
    end = text.index("\n\ndef main()", start)
    func = '''def hero_sets(data: dict):
    c = data.get("categories") or {}
    required = ["Ventiladores de Mesa", "Ventiladores de Coluna", "Ventiladores de Parede", "Ventiladores de Teto", "Torre & Circuladores"]
    for key in required:
        if len(c.get(key) or []) != 4:
            raise RuntimeError(f"Seleção inválida para hero: {key}")
    slides = [
        [("Mesa", p) for p in c[required[0]]],
        [("Coluna", p) for p in c[required[1]][:2]] + [("Parede", p) for p in c[required[2]][:2]],
        [("Teto", p) for p in c[required[3]][:2]] + [("Torre/Circulador", p) for p in c[required[4]][:2]],
    ]
    ids = [str(p.get("itemId")) for slide in slides for _, p in slide]
    if len(ids) != 12 or len(set(ids)) != 12:
        raise RuntimeError("Seleção do hero não contém 12 produtos únicos.")
    return slides
'''
    text = text[:start] + func + text[end:]
    text = text.replace('"Casa e organização em destaque"', '"Ventiladores de mesa em destaque"')
    text = text.replace('"Cozinha e tecnologia para a rotina"', '"Coluna e parede para diferentes ambientes"')
    text = text.replace('"Beleza e praticidade no dia a dia"', '"Teto, torre e circuladores em destaque"')
    path.write_text(text, encoding="utf-8")


def write_workflows() -> None:
    safe = (WORKFLOWS / "vitrine_pratica_store_safe.yml").read_text(encoding="utf-8")
    safe = safe.replace("Vitrine Prática — Loja Shopee SAFE", "Ventiladores em Foco — Loja Shopee SAFE")
    safe = safe.replace("vitrine_pratica_store", "ventiladores_em_foco_store")
    safe = safe.replace("vitrine-pratica-store-safe", "ventiladores-em-foco-store-safe")
    safe = safe.replace("9144338307944682868", "4473989735719981382")
    safe = safe.replace("115613719594316807", "1410775502611365606")
    safe = safe.replace("BLOGGER_STORE_SHOPEE_VALIDADA_V1", "BLOGGER_STORE_VENTILADORES_VALIDADA_V1")
    (WORKFLOWS / "ventiladores_em_foco_store_safe.yml").write_text(safe, encoding="utf-8")

    live = (WORKFLOWS / "vitrine_pratica_store_autonomous.yml").read_text(encoding="utf-8")
    live = live.replace("Vitrine Prática — Loja Shopee LIVE Controlada", "Ventiladores em Foco — Loja Shopee LIVE Controlada")
    live = live.replace("vitrine_pratica_store", "ventiladores_em_foco_store")
    live = live.replace("vitrine-pratica-store-live", "ventiladores-em-foco-store-live")
    live = live.replace("9144338307944682868", "4473989735719981382")
    live = live.replace("115613719594316807", "1410775502611365606")
    live = live.replace("https://vitrine-pratica.blogspot.com/2026/11/loja.html", "https://ventiladores-em-foco.blogspot.com/2026/11/loja.html")
    live = live.replace("/tmp/vitrine-pratica-loja.html", "/tmp/ventiladores-em-foco-loja.html")
    live = re.sub(r'\n  schedule:\n    - cron: "35 8 \* \* \*"\n      timezone: "America/Recife"', "", live, count=1)
    (WORKFLOWS / "ventiladores_em_foco_store_autonomous.yml").write_text(live, encoding="utf-8")


def main() -> None:
    if not SRC.exists():
        raise SystemExit("Fonte validada vitrine_pratica_store ausente.")
    if DST.exists():
        shutil.rmtree(DST)
    shutil.copytree(SRC, DST)
    replace_text_files()
    write_config()
    write_scanner()
    write_post_wrapper()
    patch_hero()
    (DST / "data" / "store_rotation.json").write_text(json.dumps({"version": 1, "runs": []}, indent=2) + "\n", encoding="utf-8")
    (DST / "data" / "store_last_selection.json").unlink(missing_ok=True)
    for cache in list(DST.rglob("__pycache__")):
        shutil.rmtree(cache, ignore_errors=True)
    for pyc in DST.rglob("*.pyc"):
        pyc.unlink(missing_ok=True)
    write_workflows()
    print("VENTILADORES_EM_FOCO_STORE_SETUP_OK")


if __name__ == "__main__":
    main()
