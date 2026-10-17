import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROOT_SRC = ROOT / "src"
os.environ.setdefault("SHOPEE_OPPORTUNITIES_CONFIG", str(ROOT / "oficina_garagem" / "config" / "shopee_oportunidades.json"))
os.environ.setdefault("SHOPEE_INTENT_RULES", str(ROOT / "oficina_garagem" / "config" / "shopee_intent_rules.json"))
os.environ.setdefault("SHOPEE_OUTPUT_DIR", str(ROOT / "oficina_garagem" / "data" / "shopee_oportunidades"))
if str(ROOT_SRC) not in sys.path:
    sys.path.insert(0, str(ROOT_SRC))

import shopee_oportunidades_v23 as v23  # noqa: E402


def regression_checks(rules_doc):
    cases = [
        ("Parafusadeira Furadeira 21V com Maleta", "parafusadeira", True),
        ("Kit Bits Pontas para Parafusadeira 30 Peças", "parafusadeira", False),
        ("Adaptador Angular Para Parafusadeira 105 Graus PROFISSIONAL", "parafusadeira", False),
        ("Cinto Duplo Porta Parafusadeira Ferramentas", "parafusadeira", False),
        ("Furadeira de Impacto com Empunhadura", "furadeira", True),
        ("Jogo Brocas para Furadeira 12 Peças", "furadeira", False),
        ("Kit Jogo 16 Brocas Estojo Ferro Concreto Madeira Para Furadeira", "furadeira", False),
        ("Coletor de Poeira para Furadeira Drill Dust Collector", "furadeira", False),
        ("Aspirador de Pó Portátil Automotivo para Carro", "aspirador automotivo", True),
        ("Filtro Hepa para Aspirador Automotivo", "aspirador automotivo", False),
        ("Lavadora de Alta Pressão para Carro e Piso", "lavadora alta pressao", True),
        ("Lavadora de Copos Louça Automática Jato Alta Pressão para Pia Cozinha", "lavadora alta pressao", False),
        ("Engate Rapido com Espigão Para Lavadora De Alta Pressão", "lavadora alta pressao", False),
        ("Aplicador de detergente lavadora de alta pressão electrolux", "lavadora alta pressao", False),
        ("Kit Valvula Bypass Lavadora de alta pressão Wap", "lavadora alta pressao", False),
        ("Conexão Saída Água Lavadora Alta Pressão Karcher Original Engate Reposição", "lavadora alta pressao", False),
        ("Kit Pistola E Lança Para Lavadora Alta Pressão Multimarcas Reposição Universal", "lavadora alta pressao", False),
        ("Interruptor Lavadora Alta Pressão Original Capa Chave Liga Desliga", "lavadora alta pressao", False),
        ("Caixa Ferramentas Sanfonada 7 Gavetas", "caixa ferramentas", True),
        ("Kit Caixa de ferramentas Tema Dinossauro Lembrancinha", "caixa ferramentas", False),
        ("Caixa de Cílios Extensões Ferramentas de Maquiagem", "caixa ferramentas", False),
        ("Maleta de Ferramentas Infantil Didática Brinquedo", "maleta ferramentas", False),
        ("Maleta Cinto Multiuso Porta Ferramentas Reforçada", "maleta ferramentas", False),
        ("Óculos de Proteção Transparente EPI para Trabalho", "oculos de protecao", True),
        ("Óculos Infantil Moda Proteção UV De Sol", "oculos de protecao", False),
        ("Protetor Auricular EPI com Cordão para Trabalho", "protetor auricular", True),
        ("Protetor Auricular Silicone Natação Dormir", "protetor auricular", False),
        ("Luva de Proteção EPI Segurança Trabalho CA", "luva de protecao", True),
        ("Manguito Proteção Solar UV50 Luva Ciclismo Moto", "luva de protecao", False),
        ("Painel Pegboard para Ferramentas Oficina", "painel ferramentas", True),
        ("Painel Decorativo Festa Garagem", "painel ferramentas", False),
        ("Escova Automotiva para Limpeza de Rodas", "escova limpeza automotiva", True),
        ("Removedor de Filme de Óleo Escova de Vidro de Carro 120ml", "escova limpeza automotiva", False),
    ]
    failures = []
    for title, keyword, expected in cases:
        actual = bool(v23.evaluate_keyword(title, keyword, rules_doc).get("accepted"))
        if actual != expected:
            failures.append({"title": title, "keyword": keyword, "expected": expected, "actual": actual})
    if failures:
        raise SystemExit("Falha nos testes semânticos Oficina: " + repr(failures))
    print(f"Testes semânticos Oficina: {len(cases)}/{len(cases)} OK")


def main():
    v23.run_regression_checks = regression_checks
    print("=== OFICINA & GARAGEM — SHOPEE OPORTUNIDADES ===")
    print("Isolado de Radar Tech BR e Casa e Decoração.")
    ranking = v23.scan_v23()
    v23.print_v23(ranking)


if __name__ == "__main__":
    main()
