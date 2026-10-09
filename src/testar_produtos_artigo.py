from main import (
    adicionar_produtos_ao_artigo,
    criar_bloco_produtos,
)

from selecionar_produtos import (
    selecionar_produtos,
)


def executar_teste():
    print("=" * 70)
    print("TESTE DE PRODUTOS AFILIADOS NO ARTIGO")
    print("=" * 70)

    titulo = (
        "Como deixar o banheiro mais "
        "prático e organizado"
    )

    palavra_chave = (
        "banheiro organizado"
    )

    categoria = "Banheiro"

    descricao = (
        "Dicas para melhorar a organização, "
        "o conforto e a praticidade do banheiro."
    )

    palavras_secundarias = [
        "organização do banheiro",
        "toalhas de banho",
        "limpeza do banheiro",
    ]

    conteudo_original = """
<p>Um banheiro organizado facilita a rotina e ajuda
a aproveitar melhor o espaço disponível.</p>

<h2>Organize os itens de uso diário</h2>

<p>Mantenha os objetos mais utilizados em locais
de fácil acesso e evite acumular itens
desnecessários.</p>

<h2>Facilite a limpeza do ambiente</h2>

<p>Uma rotina simples de limpeza ajuda a manter
o banheiro mais agradável e funcional.</p>

<h2>Cuide do conforto</h2>

<p>Pequenos detalhes podem tornar o uso diário
do banheiro mais prático e confortável.</p>
""".strip()

    print()
    print("PAUTA:")
    print(titulo)

    print()
    print("Selecionando produtos...")

    produtos = selecionar_produtos(
        titulo=titulo,
        palavra_chave=palavra_chave,
        categoria=categoria,
        descricao=descricao,
        palavras_secundarias=(
            palavras_secundarias
        ),
        limite=3,
    )

    print()
    print(
        "Quantidade selecionada:",
        len(produtos),
    )

    print()

    for indice, produto in enumerate(
        produtos,
        start=1,
    ):
        print(
            f"{indice}. "
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
    print("BLOCO HTML DOS PRODUTOS")
    print("=" * 70)
    print()

    bloco = criar_bloco_produtos(
        produtos
    )

    print(bloco)

    print()
    print("=" * 70)
    print("ARTIGO FINAL SIMULADO")
    print("=" * 70)
    print()

    artigo_final = (
        adicionar_produtos_ao_artigo(
            conteudo_html=conteudo_original,
            produtos=produtos,
        )
    )

    print(artigo_final)

    print()
    print("=" * 70)
    print("VERIFICAÇÕES")
    print("=" * 70)

    verificacoes = {
        "Tem produtos": (
            len(produtos) > 0
        ),
        "Tem aviso de afiliado": (
            "links de afiliados"
            in artigo_final
        ),
        "Tem sponsored": (
            'rel="nofollow sponsored"'
            in artigo_final
        ),
        "Tem abertura em nova aba": (
            'target="_blank"'
            in artigo_final
        ),
        "Preservou artigo original": (
            conteudo_original
            in artigo_final
        ),
    }

    tudo_correto = True

    for nome, resultado in (
        verificacoes.items()
    ):
        status = (
            "OK"
            if resultado
            else "ERRO"
        )

        print(
            f"{nome}: {status}"
        )

        if not resultado:
            tudo_correto = False

    print()

    if tudo_correto:
        print(
            "TESTE CONCLUÍDO COM SUCESSO."
        )
    else:
        raise RuntimeError(
            "Uma ou mais verificações "
            "do bloco de afiliados falharam."
        )


if __name__ == "__main__":
    executar_teste()
