import json
from pathlib import Path

source_path = Path("blogger_stores/src/moda_ofertas_store.py")
rules_path = Path("config/shopee_moda_ofertas_intent_rules.json")
raw = source_path.read_text(encoding="utf-8")

old_wallet = '        "carteira feminina": ["kit bolsa", "kit 2 bolsa", "kit com bolsa", "bolsa + carteira", "carteira de trabalho", "carteira profissional", "documento", "chaveiro", "miniatura", "pet"],'
new_wallet = '        "carteira feminina": ["kit bolsa", "kit 2 bolsa", "kit com bolsa", "bolsa + carteira", "bolsa feminina kit", "kit sacola", "mini tote", "necessaire", "carteira de trabalho", "carteira profissional", "documento", "chaveiro", "miniatura", "pet"],'
old_belt = '        "cinto feminino": ["short", "shorts", "calca", "saia", "vestido", "macacao", "conjunto", "cinto de seguranca", "automotivo", "ferramenta", "academia", "lombar", "pet", "cachorro"],'
new_belt = '        "cinto feminino": ["short", "shorts", "shoth", "bermuda", "body", "blusa", "cropped", "top", "calca", "saia", "vestido", "macacao", "conjunto", "cinto de seguranca", "automotivo", "ferramenta", "academia", "lombar", "pet", "cachorro"],'
for old, new, label in [(old_wallet, new_wallet, "carteira"), (old_belt, new_belt, "cinto")]:
    if old not in raw:
        raise SystemExit(f"Bloco final de {label} não encontrado; abortando fail-closed.")
    raw = raw.replace(old, new, 1)

old_cases = '        ("Kit Bolsa + Carteira Feminina", "carteira feminina", False),\n        ("Carteira Feminina Compacta", "carteira feminina", True),\n        ("Short Feminino com Cinto", "cinto feminino", False),\n        ("Cinto Feminino Couro Ajustável", "cinto feminino", True),'
new_cases = '        ("Kit Bolsa + Carteira Feminina", "carteira feminina", False),\n        ("Bolsa Feminina Kit Sacola Bag + Mini Tote + Carteira + Necessaire 4 Peças", "carteira feminina", False),\n        ("Carteira Feminina Compacta", "carteira feminina", True),\n        ("Short Feminino com Cinto", "cinto feminino", False),\n        ("SHOTH FEMININO ALFAIATARIA CON CINTO MARRON É BOLSOS ELEGANTES", "cinto feminino", False),\n        ("Cinto Feminino Couro Ajustável", "cinto feminino", True),'
if old_cases not in raw:
    raise SystemExit("Casos de regressão de carteira/cinto não encontrados; abortando fail-closed.")
raw = raw.replace(old_cases, new_cases, 1)
source_path.write_text(raw, encoding="utf-8")

rules = json.loads(rules_path.read_text(encoding="utf-8"))
for term in ["bolsa feminina kit", "kit sacola", "mini tote", "necessaire"]:
    block = rules["rules"]["carteira feminina"]["block_phrases"]
    if term not in block:
        block.append(term)
for term in ["shoth", "bermuda", "body", "blusa", "cropped", "top"]:
    block = rules["rules"]["cinto feminino"]["block_phrases"]
    if term not in block:
        block.append(term)
rules_path.write_text(json.dumps(rules, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

print("MODA_OFERTAS_ACCESSORY_FALSE_POSITIVE_FIX_READY")
