import html
import json
import re
import unicodedata
from pathlib import Path

from gerar_pautas import gerar_pauta_automatica
from seo import preparar_seo
from gerar_artigo import criar_estrutura_artigo, validar_artigo
from gerar_imagem import preparar_imagem
from criar_rascunho import criar_rascunho
from links_internos import adicionar_links_internos
from selecionar_produtos import selecionar_produtos


BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config" / "blog.json"
HISTORICO_PATH = BASE_DIR / "data" / "historico.json"


def carregar_json(caminho, padrao=None):
    if padrao is None:
        padrao = {}

    if not caminho.exists():
        return padrao

    try:
        with caminho.open(
            "r",
            encoding="utf-8",
        ) as arquivo:
            return json.load(arquivo)

    except (
        json.JSONDecodeError,
        OSError,
    ):
        return padrao


def carregar_config():
    return carregar_json(
        CONFIG_PATH,
        {},
    )


def carregar_historico():
    historico = carregar_json(
        HISTORICO_PATH,
        [],
    )

    if isinstance(
        historico,
        list,
    ):
        return historico

    return []


def escolher_pauta(nicho):
    """
    Gera automaticamente uma pauta baseada
    em um produto real do catálogo.

    A pauta já retorna o produto principal
    com o link afiliado preservado.
    """

    return gerar_pauta_automatica(
        nicho=nicho,
    )


def normalizar_nome_produto(texto):
    """
    Normaliza nomes somente para comparação.

    Isso impede que o produto principal seja
    adicionado novamente como complementar.
    """

    texto = str(
        texto or ""
    ).strip().lower()

    texto = unicodedata.normalize(
        "NFKD",
        texto,
    )

    texto = "".join(
        caractere
        for caractere in texto
        if not unicodedata.combining(
            caractere
        )
    )

    texto = re.sub(
        r"[^a-z0-9]+",
        " ",
        texto,
    )

    texto = re.sub(
        r"\s+",
        " ",
        texto,
    ).strip()

    return texto


def validar_produto_principal(
    produto,
):
    """
    Confirma que a pauta realmente trouxe
    um produto principal utilizável.

    O produto principal é obrigatório
    na nova arquitetura.
    """

    if not isinstance(
        produto,
        dict,
    ):
        return False

    nome = str(
        produto.get(
            "nome",
            "",
        )
    ).strip()

    link = str(
        produto.get(
            "link_afiliado",
            "",
        )
    ).strip()

    if not nome:
        return False

    if not link:
        return False

    return True


def preparar_produto_principal(
    produto,
):
    """
    Cria uma cópia limpa do produto principal.

    O link permanece exatamente como veio
    do catálogo através da pauta.
    """

    return {
        "nome": str(
            produto["nome"]
        ).strip(),
        "link_afiliado": str(
            produto["link_afiliado"]
        ).strip(),
        "tipo": "principal",
    }


def selecionar_complementares(
    pauta,
    seo,
    categoria,
    palavras_secundarias,
    produto_principal,
):
    """
    Procura produtos complementares usando
    o seletor temático já aprovado.

    O principal nunca pode aparecer novamente
    como complementar.

    No máximo dois complementares são aceitos.
    """

    candidatos = selecionar_produtos(
        titulo=seo["titulo"],
        palavra_chave=pauta[
            "palavra_chave"
        ],
        categoria=categoria,
        descricao=pauta.get(
            "descricao",
            "",
        ),
        palavras_secundarias=(
            palavras_secundarias
        ),
        limite=3,
    )

    nome_principal = normalizar_nome_produto(
        produto_principal[
            "nome"
        ]
    )

    complementares = []
    nomes_vistos = {
        nome_principal
    }

    for produto in candidatos:
        if not isinstance(
            produto,
            dict,
        ):
            continue

        nome = str(
            produto.get(
                "nome",
                "",
            )
        ).strip()

        link = str(
            produto.get(
                "link_afiliado",
                "",
            )
        ).strip()

        if not nome or not link:
            continue

        nome_normalizado = (
            normalizar_nome_produto(
                nome
            )
        )

        if not nome_normalizado:
            continue

        if nome_normalizado in nomes_vistos:
            continue

        nomes_vistos.add(
            nome_normalizado
        )

        complementar = dict(
            produto
        )

        complementar[
            "tipo"
        ] = "complementar"

        complementares.append(
            complementar
        )

        if len(
            complementares
        ) >= 2:
            break

    return complementares


def criar_bloco_produtos(
    produto_principal,
    complementares=None,
):
    """
    Cria o bloco comercial do artigo.

    O produto principal aparece sempre.

    Produtos complementares aparecem somente
    quando o seletor encontrar opções relevantes.

    Todos os links já foram definidos pelo
    catálogo. O Gemini não cria links.
    """

    if complementares is None:
        complementares = []

    if not validar_produto_principal(
        produto_principal
    ):
        return ""

    nome_principal = html.escape(
        str(
            produto_principal[
                "nome"
            ]
        )
    )

    link_principal = html.escape(
        str(
            produto_principal[
                "link_afiliado"
            ]
        ),
        quote=True,
    )

    partes = [
        '<div class="produtos-recomendados">',
        (
            "<h2>Produto relacionado "
            "ao tema</h2>"
        ),
        (
            "<p>Se você quiser colocar "
            "as dicas deste conteúdo em prática, "
            "esta é uma opção diretamente "
            "relacionada ao assunto:</p>"
        ),
        "<ul>",
        (
            "<li>"
            f'<a href="{link_principal}" '
            'target="_blank" '
            'rel="nofollow sponsored">'
            f"<strong>{nome_principal}</strong>"
            "</a>"
            "</li>"
        ),
        "</ul>",
    ]

    complementares_validos = []

    for produto in complementares:
        if not isinstance(
            produto,
            dict,
        ):
            continue

        nome = str(
            produto.get(
                "nome",
                "",
            )
        ).strip()

        link = str(
            produto.get(
                "link_afiliado",
                "",
            )
        ).strip()

        if not nome or not link:
            continue

        complementares_validos.append(
            {
                "nome": nome,
                "link_afiliado": link,
            }
        )

    if complementares_validos:
        partes.extend(
            [
                (
                    "<h3>Outras opções "
                    "relacionadas</h3>"
                ),
                (
                    "<p>Dependendo da sua rotina, "
                    "estes itens também podem "
                    "ser úteis:</p>"
                ),
                "<ul>",
            ]
        )

        for produto in (
            complementares_validos
        ):
            nome = html.escape(
                produto["nome"]
            )

            link = html.escape(
                produto[
                    "link_afiliado"
                ],
                quote=True,
            )

            partes.append(
                "<li>"
                f'<a href="{link}" '
                'target="_blank" '
                'rel="nofollow sponsored">'
                f"<strong>{nome}</strong>"
                "</a>"
                "</li>"
            )

        partes.append(
            "</ul>"
        )

    partes.extend(
        [
            (
                "<p><small>"
                "<strong>Transparência:</strong> "
                "este conteúdo pode conter links "
                "de afiliados. Se você comprar "
                "por meio deles, podemos receber "
                "uma comissão, sem custo adicional "
                "para você.</small></p>"
            ),
            "</div>",
        ]
    )

    return "\n".join(
        partes
    )


def adicionar_produtos_ao_artigo(
    conteudo_html,
    produto_principal,
    complementares=None,
):
    """
    Acrescenta ao artigo o produto principal
    e, quando existirem, os complementares.
    """

    bloco = criar_bloco_produtos(
        produto_principal=(
            produto_principal
        ),
        complementares=(
            complementares or []
        ),
    )

    if not bloco:
        return conteudo_html

    return (
        conteudo_html.rstrip()
        + "\n\n"
        + bloco
    )


def executar():
    print(
        "=== BLOGGER AUTOMATION ==="
    )

    config = carregar_config()

    nome_blog = config.get(
        "nome_blog",
        "Não definido",
    )

    nicho = config.get(
        "nicho",
        "Casa e Decoração",
    )

    criar_rascunho_ativo = config.get(
        "criar_rascunho_blogger",
        False,
    )

    publicacao_automatica = config.get(
        "publicacao_automatica",
        False,
    )

    print(
        "Blog:",
        nome_blog,
    )

    print(
        "Nicho:",
        nicho,
    )

    print(
        "Criar rascunho no Blogger:",
        criar_rascunho_ativo,
    )

    print(
        "Publicação automática:",
        publicacao_automatica,
    )

    # Proteção adicional:
    # publicação automática ainda não
    # foi liberada.
    if publicacao_automatica:
        raise RuntimeError(
            "Publicação automática está "
            "habilitada na configuração, "
            "mas esta etapa ainda não foi "
            "liberada pelo sistema."
        )

    print(
        "\nSelecionando uma pauta "
        "inédita automaticamente..."
    )

    pauta = escolher_pauta(
        nicho=nicho,
    )

    categoria = pauta.get(
        "categoria",
        "Casa e Decoração",
    )

    palavras_secundarias = pauta.get(
        "palavras_secundarias",
        [],
    )

    produto_pauta = pauta.get(
        "produto_principal"
    )

    if not validar_produto_principal(
        produto_pauta
    ):
        raise RuntimeError(
            "A pauta foi gerada sem um "
            "produto principal válido. "
            "Nada será enviado ao Blogger."
        )

    produto_principal = (
        preparar_produto_principal(
            produto_pauta
        )
    )

    print(
        "\nPauta escolhida:"
    )

    print(
        pauta["titulo"]
    )

    print(
        "Palavra-chave:",
        pauta["palavra_chave"],
    )

    print(
        "Categoria:",
        categoria,
    )

    print(
        "Produto principal:",
        produto_principal[
            "nome"
        ],
    )

    print(
        "Link afiliado principal:",
        produto_principal[
            "link_afiliado"
        ],
    )

    seo_config = config.get(
        "seo",
        {},
    )

    seo = preparar_seo(
        titulo=pauta["titulo"],
        palavra_chave=pauta[
            "palavra_chave"
        ],
        descricao=pauta[
            "descricao"
        ],
        palavras_secundarias=(
            palavras_secundarias
        ),
        titulo_max=seo_config.get(
            "titulo_max",
            60,
        ),
        meta_max=seo_config.get(
            "meta_description_max",
            155,
        ),
    )

    artigo = criar_estrutura_artigo(
        titulo=seo["titulo"],
        palavra_chave=pauta[
            "palavra_chave"
        ],
        categoria=categoria,
    )

    # Primeiro validamos somente o conteúdo
    # editorial produzido pelo Gemini.
    validacao = validar_artigo(
        artigo
    )

    if not validacao["valido"]:
        print(
            "\nArtigo reprovado:"
        )

        for erro in validacao[
            "erros"
        ]:
            print(
                "-",
                erro,
            )

        print(
            "\nNada foi enviado ao Blogger."
        )

        return

    print(
        "\nArtigo editorial aprovado."
    )

    # ========================================================
    # LINKS INTERNOS
    # ========================================================

    resultado_links = (
        adicionar_links_internos(
            conteudo_html=artigo[
                "conteudo_html"
            ],
            titulo=seo["titulo"],
            palavra_chave=pauta[
                "palavra_chave"
            ],
            categoria=categoria,
            limite=3,
        )
    )

    artigo["conteudo_html"] = (
        resultado_links[
            "conteudo_html"
        ]
    )

    artigo["links_internos"] = (
        resultado_links[
            "links"
        ]
    )

    print(
        "\nLinks internos adicionados:",
        len(
            artigo[
                "links_internos"
            ]
        ),
    )

    for link in artigo[
        "links_internos"
    ]:
        print(
            "-",
            link.get(
                "titulo",
                "",
            ),
        )

        print(
            "  URL:",
            link.get(
                "url",
                "",
            ),
        )

    # ========================================================
    # PRODUTO PRINCIPAL + COMPLEMENTARES
    # ========================================================

    print(
        "\n=== PRODUTOS AFILIADOS ==="
    )

    print(
        "Produto principal obrigatório:"
    )

    print(
        "-",
        produto_principal[
            "nome"
        ],
    )

    print(
        "  Link:",
        produto_principal[
            "link_afiliado"
        ],
    )

    print(
        "\nProcurando produtos "
        "complementares relevantes..."
    )

    complementares = (
        selecionar_complementares(
            pauta=pauta,
            seo=seo,
            categoria=categoria,
            palavras_secundarias=(
                palavras_secundarias
            ),
            produto_principal=(
                produto_principal
            ),
        )
    )

    if complementares:
        print(
            "Produtos complementares "
            "selecionados:",
            len(complementares),
        )

        for produto in complementares:
            print(
                "-",
                produto.get(
                    "nome",
                    "",
                ),
            )

            print(
                "  Pontuação:",
                produto.get(
                    "pontuacao",
                    "",
                ),
            )

            print(
                "  Link:",
                produto.get(
                    "link_afiliado",
                    "",
                ),
            )

    else:
        print(
            "Nenhum produto complementar "
            "atingiu relevância suficiente."
        )

    produtos_afiliados = [
        produto_principal,
        *complementares,
    ]

    artigo[
        "produto_principal"
    ] = produto_principal

    artigo[
        "produtos_complementares"
    ] = complementares

    artigo[
        "produtos_afiliados"
    ] = produtos_afiliados

    artigo["conteudo_html"] = (
        adicionar_produtos_ao_artigo(
            conteudo_html=artigo[
                "conteudo_html"
            ],
            produto_principal=(
                produto_principal
            ),
            complementares=(
                complementares
            ),
        )
    )

    print(
        "Bloco de produtos afiliados "
        "adicionado ao artigo."
    )

    # ========================================================
    # IMAGEM
    # ========================================================

    imagem = preparar_imagem(
        titulo=seo["titulo"],
        palavra_chave=pauta[
            "palavra_chave"
        ],
        categoria=categoria,
    )

    pacote = {
        "pauta": pauta,
        "seo": seo,
        "artigo": artigo,
        "imagem": imagem,
    }

    print(
        "\n=== PACOTE GERADO "
        "COM SUCESSO ==="
    )

    print(
        "Título:",
        seo["titulo"],
    )

    print(
        "Slug:",
        seo["slug"],
    )

    print(
        "Meta description:",
        seo["meta_description"],
    )

    print(
        "Palavra-chave:",
        pauta["palavra_chave"],
    )

    print(
        "Categoria:",
        categoria,
    )

    print(
        "Imagem:",
        imagem["nome_arquivo"],
    )

    print(
        "ALT:",
        imagem["alt_text"],
    )

    print(
        "Artigo validado:",
        validacao["valido"],
    )

    print(
        "Quantidade de palavras:",
        validacao.get(
            "quantidade_palavras",
            "Não informado",
        ),
    )

    print(
        "Quantidade de H2:",
        validacao.get(
            "quantidade_h2",
            "Não informado",
        ),
    )

    print(
        "Links internos:",
        len(
            artigo[
                "links_internos"
            ]
        ),
    )

    print(
        "Produto principal: 1"
    )

    print(
        "Produtos complementares:",
        len(
            artigo[
                "produtos_complementares"
            ]
        ),
    )

    print(
        "Total de produtos afiliados:",
        len(
            artigo[
                "produtos_afiliados"
            ]
        ),
    )

    # Durante os testes, mantemos o
    # artigo visível no log para
    # revisão editorial.
    print(
        "\n=== INÍCIO DO "
        "ARTIGO GERADO ==="
    )

    print(
        artigo["conteudo_html"]
    )

    print(
        "=== FIM DO "
        "ARTIGO GERADO ==="
    )

    # ========================================================
    # BLOGGER
    # ========================================================

    if criar_rascunho_ativo:
        print(
            "\nEnvio de rascunho "
            "autorizado pela configuração."
        )

        try:
            resultado_blogger = (
                criar_rascunho(
                    titulo=seo["titulo"],
                    conteudo_html=artigo[
                        "conteudo_html"
                    ],
                    categoria=categoria,
                )
            )

            pacote[
                "blogger"
            ] = resultado_blogger

            print(
                "\n=== RASCUNHO CRIADO "
                "NO BLOGGER ==="
            )

            print(
                "Título:",
                resultado_blogger.get(
                    "titulo"
                ),
            )

            print(
                "Post ID:",
                resultado_blogger.get(
                    "id"
                ),
            )

            print(
                "Status:",
                resultado_blogger.get(
                    "status"
                ),
            )

            print(
                "URL:",
                resultado_blogger.get(
                    "url"
                ),
            )

            # O rascunho ainda não entra
            # no histórico.
            # O histórico definitivo
            # continua reservado para
            # publicações reais confirmadas.

        except Exception as erro:
            print(
                "\nERRO AO CRIAR "
                "RASCUNHO NO BLOGGER:"
            )

            print(
                erro
            )

            print(
                "\nO artigo não foi "
                "registrado no histórico."
            )

            return pacote

    else:
        print(
            "\nMODO SEGURO ATIVO."
        )

        print(
            "A criação de rascunho "
            "no Blogger está desativada."
        )

        print(
            "Nenhum conteúdo foi "
            "enviado ao Blogger."
        )

    return pacote


if __name__ == "__main__":
    executar()
