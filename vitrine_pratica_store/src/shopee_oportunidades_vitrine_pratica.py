#!/usr/bin/env python3
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE_DIR = ROOT / "vitrine_pratica_store"
ROOT_SRC = ROOT / "src"
os.environ.setdefault("SHOPEE_OPPORTUNITIES_CONFIG", str(MODULE_DIR / "config" / "shopee_oportunidades.json"))
os.environ.setdefault("SHOPEE_INTENT_RULES", str(MODULE_DIR / "config" / "shopee_intent_rules.json"))
os.environ.setdefault("SHOPEE_OUTPUT_DIR", str(MODULE_DIR / "data" / "shopee_oportunidades"))
if str(ROOT_SRC) not in sys.path:
    sys.path.insert(0, str(ROOT_SRC))

import shopee_oportunidades_v23 as v23


def regression_checks(rules_doc):
    cases = [
        ("Smartwatch Relógio Inteligente AMOLED Bluetooth", "smartwatch", True),
        ("Pulseira para Smartwatch 20mm", "smartwatch", False),
        ("Kit Carregador para iPhone Fonte + Cabo Lightning", "carregador iphone", True),
        ("Cabo Avulso Lightning para iPhone", "carregador iphone", False),
        ("Caixa de Som Bluetooth Portátil", "caixa de som bluetooth", True),
        ("Bateria para Caixa de Som Bluetooth", "caixa de som bluetooth", False),
        ("Luminária Solar com Sensor de Movimento", "luminaria solar", True),
        ("Painel Solar Avulso para Luminária", "luminaria solar", False),
        ("Organizador Banheiro Prateleira Shampoo", "organizador banheiro", True),
        ("Adesivo Avulso para Organizador de Banheiro", "organizador banheiro", False),
        ("Tapete Decorativo para Sala e Quarto", "tapete decorativo", True),
        ("Tapete Automotivo para Carro", "tapete decorativo", False),
        ("Escorredor de Louças 13 Pratos", "escorredor de loucas", True),
        ("Escorredor de Macarrão Inox", "escorredor de loucas", False),
        ("Kit Potes Herméticos para Mantimentos", "potes hermeticos", True),
        ("Tampa Avulsa para Pote Hermético", "potes hermeticos", False),
        ("Organizador de Cozinha para Pia e Talheres", "organizador cozinha", True),
        ("Gancho Avulso Adesivo para Cozinha", "organizador cozinha", False),
        ("Parafusadeira Furadeira Sem Fio com Maleta", "parafusadeira furadeira", True),
        ("Kit Brocas para Parafusadeira Furadeira", "parafusadeira furadeira", False),
        ("Compressor de Ar Portátil Inflador para Pneus", "compressor de ar portatil", True),
        ("Mangueira Avulsa para Compressor de Ar", "compressor de ar portatil", False),
        ("Jogo Escovas para Furadeira Limpeza", "escova para furadeira", True),
        ("Escova Secadora de Cabelo", "escova para furadeira", False),
        ("Saia Midi Feminina Cintura Alta", "saia midi feminina", True),
        ("Saia para Mesa Festa", "saia midi feminina", False),
        ("Aparador de Pelos Masculino Barba Recarregável", "aparador de pelos masculino", True),
        ("Lâmina Avulsa para Aparador de Pelos", "aparador de pelos masculino", False),
        ("Conjunto Feminino Saia e Cropped", "conjunto feminino", True),
        ("Conjunto Infantil Menina", "conjunto feminino", False),
    ]
    failures=[]
    for title,keyword,expected in cases:
        actual=bool(v23.evaluate_keyword(title,keyword,rules_doc).get("accepted"))
        if actual != expected:
            failures.append({"title":title,"keyword":keyword,"expected":expected,"actual":actual})
    if failures:
        raise SystemExit("Falha nos testes semânticos Vitrine Prática: "+repr(failures))
    print(f"Testes semânticos Vitrine Prática: {len(cases)}/{len(cases)} OK")


def main():
    v23.run_regression_checks=regression_checks
    ranking=v23.scan_v23()
    v23.print_v23(ranking)


if __name__ == "__main__":
    main()
