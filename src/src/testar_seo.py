from seo import criar_meta_description


def verificar(condicao, mensagem):
    status = "OK" if condicao else "FALHOU"
    print(f"{mensagem}: {status}")

    if not condicao:
        raise RuntimeError(
            f"Falha no teste: {mensagem}"
        )


def executar_teste():
    print("=" * 70)
    print("TESTE — META DESCRIPTION")
    print("=" * 70)

    descricao = (
        "Aprenda como organizar a geladeira corretamente "
        "para aproveitar melhor o espaço, reduzir desperdícios "
        "e conservar os alimentos frescos por mais tempo usando "
        "recipientes adequados no dia a dia."
    )

    meta = criar_meta_description(
        texto=descricao,
        palavra_chave=(
            "como organizar a geladeira"
        ),
        limite=155,
    )

    print()
    print("DESCRIÇÃO ORIGINAL:")
    print(descricao)

    print()
    print("META GERADA:")
    print(meta)

    print()
    print(
        "Quantidade de caracteres:",
        len(meta),
    )

    print()
    print("=" * 70)
    print("VERIFICAÇÕES")
    print("=" * 70)

    verificar(
        len(meta) <= 155,
        "Meta respeita o limite de 155 caracteres",
    )

    verificar(
        not meta.lower().endswith("usando."),
        'Meta não termina em "usando."',
    )

    verificar(
        meta.endswith((".", "!", "?")),
        "Meta termina com pontuação",
    )

    verificar(
        len(meta) >= 70,
        "Meta mantém conteúdo suficiente",
    )

    print()
    print("=" * 70)
    print("TESTE CONCLUÍDO COM SUCESSO.")
    print("META DESCRIPTION APROVADA.")
    print("=" * 70)


if __name__ == "__main__":
    executar_teste()
