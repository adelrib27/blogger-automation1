import json

import lab_compare as lab


def pet_regression_checks(rules_doc):
    cases = [
        ("Cama Pet Lavável para Cachorro e Gato", "cama pet", True),
        ("Cama Infantil Montessoriana Solteiro", "cama pet", False),
        ("Fonte Bebedouro Automático para Gatos", "bebedouro fonte pet", True),
        ("Bebedouro para Pássaros de Gaiola", "bebedouro fonte pet", False),
        ("Tapete Higiênico para Cachorro Pet", "tapete higienico cachorro", True),
        ("Tapete Higiênico para Banheiro Antiderrapante", "tapete higienico cachorro", False),
        ("Caixa Bandeja de Areia para Gatos", "caixa areia gato", True),
        ("Caixa Organizadora com Areia Decorativa", "caixa areia gato", False),
        ("Brinquedo Interativo Pet para Cachorro", "brinquedo interativo pet", True),
        ("Brinquedo Interativo Infantil Educativo", "brinquedo interativo pet", False),
        ("Arranhador para Gatos com Base", "arranhador gato", True),
        ("Peitoral Ajustável para Cachorro Pet", "peitoral cachorro", True),
        ("Peitoral Esportivo Humano Academia", "peitoral cachorro", False),
        ("Guia Retrátil para Cachorro Pet", "guia cachorro", True),
        ("Guia Turístico de Viagem", "guia cachorro", False),
        ("Recipiente Porta Ração Pet", "porta racao pet", True)
    ]
    failures = []
    for title, keyword, expected in cases:
        actual = bool(lab.shopee.evaluate_keyword(title, keyword, rules_doc).get("accepted"))
        if actual != expected:
            failures.append({"title": title, "keyword": keyword, "expected": expected, "actual": actual})
    if failures:
        raise SystemExit("Falha nos testes semânticos Vida Pet Prática: " + json.dumps(failures, ensure_ascii=False))
    print(f"Testes semânticos Vida Pet Prática: {len(cases)}/{len(cases)} OK")


if __name__ == "__main__":
    lab.shopee.run_regression_checks = pet_regression_checks
    lab.main()
