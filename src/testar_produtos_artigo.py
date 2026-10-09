from gerar_artigo import (
    MARCADOR_PRODUTO_PRINCIPAL,
)
from main import (
    adicionar_complementares_ao_artigo,
    inserir_produto_principal_contextual,
    preparar_produto_principal,
    selecionar_complementares,
)
from seo import preparar_seo


def verificar(
    condicao,
    mensagem,
):
    status = (
        "OK"
        if condicao
        else "FALHOU"
    )

    print(
        f"{mensagem}: {status}"
    )

    if not condicao:
        raise RuntimeError(
            f"Falha no teste: {mensagem}"
        )


def executar_teste():
    print("=" * 70)
    print(
        "TESTE — INSERÇÃO CONTEXTUAL "
        "DO PRODUTO PRINCIPAL"
    )
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

    # ========================================================
    # ARTIGO SIMULADO
    #
    # O marcador foi colocado propositalmente
    # dentro da seção mais relacionada ao produto.
    # ========================================================

    conteudo_com_marcador = f"""
<p>Organizar os alimentos corretamente ajuda a aproveitar
melhor o espaço da geladeira e facilita a rotina.</p>

<h2>Separe os alimentos por categoria</h2>

<p>Dividir os alimentos por tipo ajuda a visualizar
o que já está armazenado e o que precisa ser consumido
primeiro.</p>

<h2>Use recipientes adequados</h2>

<p>Depois de definir onde cada alimento ficará,
vale escolher recipientes que facilitem a organização
e mantenham cada porção separada.</p>

{MARCADOR_PRODUTO_PRINCIPAL}

<p>Com os recipientes organizados, fica mais simples
identificar as porções e aproveitar melhor o espaço
disponível nas prateleiras.</p>

<h2>Mantenha uma rotina de organização</h2>

<p>Uma revisão periódica ajuda a evitar acúmulos
e alimentos esquecidos no fundo da geladeira.</p>
""".strip()

    # ========================================================
    # PRODUTO PRINCIPAL
    # ========================================================

    produto_principal = (
        preparar_produto_principal(
            pauta[
                "produto_principal"
            ]
        )
    )

    nome_principal = (
        produto_principal[
            "nome"
        ]
    )

    link_principal = (
        produto_principal[
            "link_afiliado"
        ]
    )

    print(
        "\nPRODUTO PRINCIPAL"
    )

    print(
        "-" * 70
    )

    print(
        nome_principal
    )

    print(
        link_principal
    )

    # ========================================================
    # CONFIRMA O MARCADOR ANTES DA SUBSTITUIÇÃO
    # ========================================================

    print(
        "\nARTIGO ANTES DA SUBSTITUIÇÃO"
    )

    print(
        "-" * 70
    )

    print(
        conteudo_com_marcador
    )

    quantidade_antes = (
        conteudo_com_marcador.count(
            MARCADOR_PRODUTO_PRINCIPAL
        )
    )

    verificar(
        quantidade_antes == 1,
        (
            "Existe exatamente 1 marcador "
            "antes da substituição"
        ),
    )

    verificar(
        nome_principal
        not in conteudo_com_marcador,
        (
            "Produto ainda não foi inserido "
            "antes da substituição"
        ),
    )

    verificar(
        link_principal
        not in conteudo_com_marcador,
        (
            "Link afiliado ainda não está "
            "no conteúdo editorial"
        ),
    )

    # ========================================================
    # SUBSTITUIÇÃO CONTEXTUAL
    # ========================================================

    artigo_contextual = (
        inserir_produto_principal_contextual(
            conteudo_html=(
                conteudo_com_marcador
            ),
            produto_principal=(
                produto_principal
            ),
        )
    )

    print(
        "\nARTIGO APÓS INSERÇÃO "
        "DO PRODUTO PRINCIPAL"
    )

    print(
        "-" * 70
    )

    print(
        artigo_contextual
    )

    # ========================================================
    # VERIFICAÇÕES DO PRODUTO PRINCIPAL
    # ========================================================

    print(
        "\nVERIFICAÇÕES DO "
        "PRODUTO PRINCIPAL"
    )

    print(
        "-" * 70
    )

    verificar(
        MARCADOR_PRODUTO_PRINCIPAL
        not in artigo_contextual,
        (
            "Marcador foi completamente "
            "eliminado"
        ),
    )

    verificar(
        artigo_contextual.count(
            nome_principal
        ) == 1,
        (
            "Produto principal aparece "
            "exatamente uma vez"
        ),
    )

    verificar(
        artigo_contextual.count(
            link_principal
        ) == 1,
        (
            "Link afiliado exato aparece "
            "exatamente uma vez"
        ),
    )

    verificar(
        'rel="nofollow sponsored"'
        in artigo_contextual,
        (
            "Link contém nofollow sponsored"
        ),
    )

    verificar(
        'target="_blank"'
        in artigo_contextual,
        (
            "Link abre em nova aba"
        ),
    )

    verificar(
        "este é um link de afiliado"
        in artigo_contextual,
        (
            "Aviso de transparência "
            "está presente"
        ),
    )

    # ========================================================
    # POSIÇÃO CONTEXTUAL
    # ========================================================

    posicao_secao = (
        artigo_contextual.find(
            "<h2>Use recipientes adequados</h2>"
        )
    )

    posicao_produto = (
        artigo_contextual.find(
            nome_principal
        )
    )

    posicao_proxima_secao = (
        artigo_contextual.find(
            (
                "<h2>Mantenha uma rotina "
                "de organização</h2>"
            )
        )
    )

    verificar(
        posicao_secao
        < posicao_produto
        < posicao_proxima_secao,
        (
            "Produto ficou dentro da "
            "seção contextual correta"
        ),
    )

    # ========================================================
    # SEO PARA COMPLEMENTARES
    # ========================================================

    seo = preparar_seo(
        titulo=pauta[
            "titulo"
        ],
        palavra_chave=pauta[
            "palavra_chave"
        ],
        descricao=pauta[
            "descricao"
        ],
        palavras_secundarias=(
            pauta[
                "palavras_secundarias"
            ]
        ),
        titulo_max=60,
        meta_max=155,
    )

    # ========================================================
    # COMPLEMENTARES
    # ========================================================

    complementares = (
        selecionar_complementares(
            pauta=pauta,
            seo=seo,
            categoria=pauta[
                "categoria"
            ],
            palavras_secundarias=(
                pauta[
                    "palavras_secundarias"
                ]
            ),
            produto_principal=(
                produto_principal
            ),
        )
    )

    print(
        "\nPRODUTOS COMPLEMENTARES"
    )

    print(
        "-" * 70
    )

    if complementares:
        for numero, produto in enumerate(
            complementares,
            start=1,
        ):
            print(
                f"{numero}. "
                f"{produto['nome']}"
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
                produto[
                    "link_afiliado"
                ],
            )

    else:
        print(
            "Nenhum complementar selecionado."
        )

    verificar(
        len(
            complementares
        ) <= 2,
        (
            "Existem no máximo "
            "2 complementares"
        ),
    )

    verificar(
        all(
            produto[
                "nome"
            ] != nome_principal
            for produto
            in complementares
        ),
        (
            "Produto principal não foi "
            "duplicado como complementar"
        ),
    )

    # ========================================================
    # ARTIGO FINAL
    # ========================================================

    artigo_final = (
        adicionar_complementares_ao_artigo(
            conteudo_html=(
                artigo_contextual
            ),
            complementares=(
                complementares
            ),
        )
    )

    print(
        "\n" + "=" * 70
    )

    print(
        "ARTIGO FINAL SIMULADO"
    )

    print(
        "=" * 70
    )

    print()

    print(
        artigo_final
    )

    # ========================================================
    # SEGURANÇA FINAL
    # ========================================================

    print(
        "\n" + "=" * 70
    )

    print(
        "VERIFICAÇÕES FINAIS"
    )

    print(
        "=" * 70
    )

    verificar(
        MARCADOR_PRODUTO_PRINCIPAL
        not in artigo_final,
        (
            "Nenhum marcador interno "
            "chegaria ao Blogger"
        ),
    )

    verificar(
        artigo_final.count(
            link_principal
        ) == 1,
        (
            "Link principal continua "
            "exatamente uma vez"
        ),
    )

    verificar(
        artigo_final.count(
            nome_principal
        ) == 1,
        (
            "Produto principal continua "
            "exatamente uma vez"
        ),
    )

    verificar(
        (
            "<p>Organizar os alimentos "
            "corretamente"
        )
        in artigo_final,
        (
            "Conteúdo editorial original "
            "foi preservado"
        ),
    )

    print()

    print(
        "=" * 70
    )

    print(
        "TESTE CONCLUÍDO COM SUCESSO."
    )

    print(
        "INSERÇÃO CONTEXTUAL APROVADA."
    )

    print(
        "=" * 70
    )


if __name__ == "__main__":
    executar_teste()
