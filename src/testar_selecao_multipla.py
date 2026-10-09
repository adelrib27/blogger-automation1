from selecionar_produtos import selecionar_produtos


PAUTAS_TESTE = [
    {
        "titulo": "Como organizar uma cozinha pequena de forma prática",
        "palavra_chave": "organização de cozinha pequena",
        "categoria": "Cozinha",
        "descricao": (
            "Ideias práticas para aproveitar melhor o espaço "
            "da cozinha, organizar utensílios, louças e alimentos."
        ),
        "palavras_secundarias": [
            "organização de cozinha",
            "utensílios de cozinha",
            "armazenamento de alimentos",
        ],
    },
    {
        "titulo": "Como deixar o quarto mais confortável para dormir",
        "palavra_chave": "quarto confortável",
        "categoria": "Quarto",
        "descricao": (
            "Ideias para melhorar o conforto do quarto, "
            "da cama e do sono no dia a dia."
        ),
        "palavras_secundarias": [
            "conforto para dormir",
            "cama confortável",
            "travesseiro",
        ],
    },
    {
        "titulo": "Como organizar a lavanderia e facilitar a rotina",
        "palavra_chave": "organização da lavanderia",
        "categoria": "Lavanderia",
        "descricao": (
            "Soluções práticas para organizar roupas, "
            "lavagem, secagem e limpeza da lavanderia."
        ),
        "palavras_secundarias": [
            "lavar roupas",
            "secar roupas",
            "varal",
            "limpeza de roupas",
        ],
    },
    {
        "titulo": "Como deixar o banheiro mais prático e organizado",
        "palavra_chave": "banheiro organizado",
        "categoria": "Banheiro",
        "descricao": (
            "Dicas para melhorar a organização, o conforto "
            "e a praticidade do banheiro."
        ),
        "palavras_secundarias": [
            "organização do banheiro",
            "toalhas de banho",
            "limpeza do banheiro",
        ],
    },
    {
        "titulo": "Como refrescar a casa nos dias de calor",
        "palavra_chave": "como refrescar a casa",
        "categoria": "Climatização",
        "descricao": (
            "Alternativas para deixar os ambientes mais "
            "agradáveis em dias quentes e melhorar "
            "a sensação térmica."
        ),
        "palavras_secundarias": [
            "climatizador",
            "ventilador",
            "umidificador",
            "calor",
        ],
    },
    {
        "titulo": "Como aumentar a segurança da casa com tecnologia",
        "palavra_chave": "segurança residencial",
        "categoria": "Segurança",
        "descricao": (
            "Soluções tecnológicas para monitorar a casa "
            "e aumentar a segurança dos ambientes."
        ),
        "palavras_secundarias": [
            "câmera de segurança",
            "monitoramento residencial",
            "câmera wifi",
        ],
    },
]


def executar_teste():
    print()
    print("=" * 70)
    print("TESTE MÚLTIPLO DO SELETOR DE PRODUTOS")
    print("=" * 70)

    for numero, pauta in enumerate(
        PAUTAS_TESTE,
        start=1,
    ):
        print()
        print("=" * 70)
        print(f"PAUTA {numero}")
        print("=" * 70)

        print(
            "Título:",
            pauta["titulo"],
        )

        print(
            "Categoria:",
            pauta["categoria"],
        )

        print(
            "Palavra-chave:",
            pauta["palavra_chave"],
        )

        print()

        produtos = selecionar_produtos(
            titulo=pauta["titulo"],
            palavra_chave=(
                pauta["palavra_chave"]
            ),
            categoria=pauta["categoria"],
            descricao=pauta["descricao"],
            palavras_secundarias=(
                pauta["palavras_secundarias"]
            ),
            limite=3,
        )

        if not produtos:
            print(
                "Nenhum produto suficientemente "
                "relevante encontrado."
            )
            continue

        for posicao, produto in enumerate(
            produtos,
            start=1,
        ):
            print(
                f"{posicao}. "
                f"{produto['nome']}"
            )

            print(
                "   Pontuação:",
                produto["pontuacao"],
            )

            print(
                "   Link:",
                produto["link_afiliado"],
            )

            print()

    print("=" * 70)
    print("FIM DO TESTE")
    print("=" * 70)
    print()


if __name__ == "__main__":
    executar_teste()
