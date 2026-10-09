import html
import json
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
    Gera automaticamente pautas com Gemini
    e seleciona uma pauta inédita usando
    o histórico real do blog.
    """

    return gerar_pauta_automatica(
        nicho=nicho,
    )


def criar_bloco_produtos(produtos):
    """
    Cria um bloco editorial com produtos
    afiliados previamente selecionados.

    Os nomes e links vêm exclusivamente
    do catálogo data/produtos.json.

    O Gemini não participa da criação
    dos links de afiliado.
    """

    if not produtos:
        return ""

    partes = [
        '<div class="produtos-recomendados">',
        (
            "<h2>Produtos que podem ajudar "
            "na prática</h2>"
        ),
        (
            "<p>Algumas soluções relacionadas "
            "ao tema podem facilitar a aplicação "
            "das ideias apresentadas acima.</p>"
        ),
        (
            "<p><small><strong>Transparência:</strong> "
            "este conteúdo pode conter links de "
            "afiliados. Se você comprar por meio "
            "deles, podemos receber uma comissão, "
            "sem custo adicional para você."
            "</small></p>"
        ),
        "<ul>",
    ]

    for produto in produtos:
        nome = html.escape(
            str(
                produto.get(
                    "nome",
                    "",
                )
            )
        )

        link = html.escape(
            str(
                produto.get(
                    "link_afiliado",
                    "",
                )
            ),
            quote=True,
        )

        if not nome or not link:
            continue

        partes.append(
            "<li>"
            f'<a href="{link}" '
            'target="_blank" '
            'rel="nofollow sponsored">'
            f"<strong>{nome}</strong>"
            "</a>"
            "</li>"
        )

    partes.extend(
        [
            "</ul>",
            "</div>",
        ]
    )

    return "\n".join(
        partes
    )


def adicionar_produtos_ao_artigo(
    conteudo_html,
    produtos,
):
    """
    Acrescenta o bloco de produtos somente
    quando o seletor encontrou opções
    suficientemente relevantes.
    """

    if not produtos:
        return conteudo_html

    bloco = criar_bloco_produtos(
        produtos
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

    # Primeiro validamos somente o artigo
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
    # PRODUTOS AFILIADOS
    # ========================================================

    print(
        "\nSelecionando produtos "
        "relevantes para o artigo..."
    )

    produtos = selecionar_produtos(
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

    artigo[
        "produtos_afiliados"
    ] = produtos

    if produtos:
        print(
            "Produtos relevantes "
            "selecionados:",
            len(produtos),
        )

        for produto in produtos:
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

        artigo["conteudo_html"] = (
            adicionar_produtos_ao_artigo(
                conteudo_html=artigo[
                    "conteudo_html"
                ],
                produtos=produtos,
            )
        )

        print(
            "Bloco de produtos afiliados "
            "adicionado ao artigo."
        )

    else:
        print(
            "Nenhum produto atingiu "
            "relevância suficiente."
        )

        print(
            "O artigo seguirá sem "
            "links de afiliado."
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
        "Produtos afiliados:",
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
