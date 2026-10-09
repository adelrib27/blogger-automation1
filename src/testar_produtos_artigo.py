from main import (
    adicionar_produtos_ao_artigo,
    criar_bloco_produtos,
    preparar_produto_principal,
    selecionar_complementares,
)
from seo import preparar_seo


def executar_teste():
    print("=" * 70)
    print("TESTE — PRODUTO PRINCIPAL + COMPLEMENTARES")
    print("=" * 70)

    # ========================================================
    # PAUTA SIMULADA
    # ========================================================

    pauta = {
        "titulo": (
            "Guia de armazenamento: como organizar "
            "alimentos na geladeira"
        ),
        "palavra_chave": (
            "armazenamento de alimentos na geladeira"
        ),
        "categoria": "Cozinha",
        "descricao": (
            "Dicas práticas para armazenar alimentos, "
            "organizar a geladeira e conservar melhor "
            "comidas e ingredientes."
        ),
        "palavras_secundarias": [
            "como guardar comida",
            "conservação de alimentos",
            "organização da geladeira",
            "potes para alimentos",
        ],
        "produto_principal": {
            "nome": (
                "Kit de Potes para Alimentos 800ml "
                "com Travas Laterais"
            ),
            "link_afiliado": (
                "https://vt.tiktok.com/"
                "ZS9DVmNxuKAVr-oyWt7/"
            ),
        },
    }

    conteudo_original = """
<p>Organizar corretamente os alimentos ajuda a aproveitar
melhor o espaço disponível na geladeira.</p>

<h2>Separe os alimentos por categoria</h2>

<p>Uma organização simples facilita a rotina e ajuda
a visualizar o que já está armazenado.</p>

<h2>Use recipientes adequados</h2>

<p>Recipientes apropriados ajudam a manter os alimentos
organizados e facilitam o armazenamento.</p>

<h2>Mantenha uma rotina de organização</h2>

<p>Revisar periodicamente o conteúdo da geladeira evita
acúmulos e melhora o aproveitamento do espaço.</p>
""".strip()

    # ========================================================
    # PRODUTO PRINCIPAL
    # ========================================================

    produto_principal = preparar_produto_principal(
        pauta["produto_principal"]
    )

    print("\nPRODUTO PRINCIPAL")
    print("-" * 70)
    print(
        produto_principal["nome"]
    )
    print(
        produto_principal["link_afiliado"]
    )

    # ========================================================
    # SEO SIMULADO
    # ========================================================

    seo = preparar_seo(
        titulo=pauta["titulo"],
        palavra_chave=pauta["palavra_chave"],
        descricao=pauta["descricao"],
        palavras_secundarias=(
            pauta["palavras_secundarias"]
        ),
        titulo_max=60,
        meta_max=155,
    )

    # ========================================================
    # COMPLEMENTARES
    # ========================================================

    complementares = selecionar_complementares(
        pauta=pauta,
        seo=seo,
        categoria=pauta["categoria"],
        palavras_secundarias=(
            pauta["palavras_secundarias"]
        ),
        produto_principal=produto_principal,
    )

    print("\nPRODUTOS COMPLEMENTARES")
    print("-" * 70)

    if complementares:
        for numero, produto in enumerate(
            complementares,
            start=1,
        ):
            print(
                f"{numero}. {produto['nome']}"
            )
            print(
                "   Pontuação:",
                produto.get(
                    "pontuacao",
                    "",
                ),
            )
            print(
                "   Link:",
                produto["link_afiliado"],
            )
    else:
        print(
            "Nenhum complementar selecionado."
        )

    # ========================================================
    # BLOCO HTML
    # ========================================================

    bloco = criar_bloco_produtos(
        produto_principal=produto_principal,
        complementares=complementares,
    )

    artigo_final = adicionar_produtos_ao_artigo(
        conteudo_html=conteudo_original,
        produto_principal=produto_principal,
        complementares=complementares,
    )

    print("\n" + "=" * 70)
    print("BLOCO HTML DOS PRODUTOS")
    print("=" * 70)
    print()
    print(bloco)

    print("\n" + "=" * 70)
    print("ARTIGO FINAL SIMULADO")
    print("=" * 70)
    print()
    print(artigo_final)

    # ========================================================
    # VERIFICAÇÕES
    # ========================================================

    nome_principal = (
        produto_principal["nome"]
    )

    link_principal = (
        produto_principal["link_afiliado"]
    )

    ocorrencias_nome_principal = (
        bloco.count(
            nome_principal
        )
    )

    ocorrencias_link_principal = (
        bloco.count(
            link_principal
        )
    )

    nomes_complementares = {
        produto["nome"]
        for produto in complementares
    }

    principal_duplicado = (
        nome_principal
        in nomes_complementares
    )

    verificacoes = {
        "Produto principal presente": (
            nome_principal in bloco
        ),
        "Link principal exato": (
            link_principal in bloco
        ),
        "Principal aparece uma vez": (
            ocorrencias_nome_principal == 1
            and ocorrencias_link_principal == 1
        ),
        "Principal não virou complementar": (
            not principal_duplicado
        ),
        "Máximo de 2 complementares": (
            len(complementares) <= 2
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

    print("\n" + "=" * 70)
    print("VERIFICAÇÕES")
    print("=" * 70)

    falhou = False

    for nome, resultado in (
        verificacoes.items()
    ):
        status = (
            "OK"
            if resultado
            else "FALHOU"
        )

        print(
            f"{nome}: {status}"
        )

        if not resultado:
            falhou = True

    if falhou:
        raise RuntimeError(
            "Uma ou mais verificações "
            "do teste falharam."
        )

    print()
    print(
        "TESTE CONCLUÍDO COM SUCESSO."
    )


if __name__ == "__main__":
    executar_teste()
