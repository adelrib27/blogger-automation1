import json
from pathlib import Path

source_path = Path("blogger_stores/src/moda_ofertas_store.py")
rules_path = Path("config/shopee_moda_ofertas_intent_rules.json")

raw = source_path.read_text(encoding="utf-8")
old_block = '        "secador de cabelo": ["difusor", "bico para secador", "suporte para secador", "resistencia para secador", "cabo para secador", "peca para secador"],'
new_block = '        "secador de cabelo": ["difusor", "bico para secador", "suporte", "resistencia para secador", "cabo para secador", "peca para secador", "adaptador", "acessorio"],'
if old_block not in raw:
    raise SystemExit("Bloco final de secador não encontrado; abortando fail-closed.")
raw = raw.replace(old_block, new_block, 1)

old_case = '        ("Difusor Universal para Secador de Cabelo", "secador de cabelo", False),\n        ("Secador de Cabelo Profissional 2000W", "secador de cabelo", True),'
new_case = '        ("Difusor Universal para Secador de Cabelo", "secador de cabelo", False),\n        ("Suporte De Parede Multifuncional Chapinha Babyliss Secador De Cabelo Organizador", "secador de cabelo", False),\n        ("Secador de Cabelo Profissional 2000W", "secador de cabelo", True),'
if old_case not in raw:
    raise SystemExit("Casos de regressão de secador não encontrados; abortando fail-closed.")
raw = raw.replace(old_case, new_case, 1)
source_path.write_text(raw, encoding="utf-8")

rules = json.loads(rules_path.read_text(encoding="utf-8"))
block = rules["rules"]["secador de cabelo"]["block_phrases"]
for term in ["suporte", "adaptador", "acessorio", "acessório"]:
    if term not in block:
        block.append(term)
rules_path.write_text(json.dumps(rules, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

print("MODA_OFERTAS_SEMANTIC_SECador_FIX_READY")
