import html
import json
import re
import unicodedata
from pathlib import Path

from gerar_pautas import gerar_pauta_automatica
from seo import preparar_seo
from gerar_artigo import (
    MARCADOR_PRODUTO_PRINCIPAL,
    criar_estrutura_artigo,
    validar_artigo,
)
from gerar_imagem import gerar_imagem_destacada
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
    Confirma que a pauta trouxe
    um produto principal utilizável.
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
    do catálogo.
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
    Procura produtos complementares relevantes.

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


def criar_bloco_produto_principal(
    produto_principal,
):
    """
    Cria somente o bloco do produto principal.

    Este bloco será colocado exatamente no ponto
    contextual escolhido durante a geração
    editorial do artigo.
    """

    if not validar_produto_principal(
        produto_principal
    ):
        return ""

    nome = html.escape(
        str(
            produto_principal[
                "nome"
            ]
        )
    )

    link = html.escape(
        str(
            produto_principal[
                "link_afiliado"
            ]
        ),
        quote=True,
    )

    partes = [
        (
            '<div class="produto-principal-contextual">'
        ),
        (
            "<p><strong>Uma opção relacionada "
            "a esta parte do conteúdo:</strong></p>"
        ),
        (
            "<p>"
            f'<a href="{link}" '
            'target="_blank" '
            'rel="nofollow sponsored">'
            f"<strong>{nome}</strong>"
            "</a>"
            "</p>"
        ),
        (
            "<p><small>"
            "<strong>Transparência:</strong> "
            "este é um link de afiliado. "
            "Se você comprar por meio dele, "
            "podemos receber uma comissão, "
            "sem custo adicional para você."
            "</small></p>"
        ),
        "</div>",
    ]

    return "\n".join(
        partes
    )


def inserir_produto_principal_contextual(
    conteudo_html,
    produto_principal,
):
    """
    Substitui exatamente um marcador pelo bloco
    do produto principal.

    O link é inserido pelo Python e nunca
    pelo Gemini.
    """

    if not conteudo_html:
        raise RuntimeError(
            "Conteúdo do artigo vazio antes "
            "da inserção do produto principal."
        )

    quantidade = conteudo_html.count(
        MARCADOR_PRODUTO_PRINCIPAL
    )

    if quantidade != 1:
        raise RuntimeError(
            "Era esperado exatamente 1 marcador "
            "do produto principal, mas foram "
            f"encontrados {quantidade}."
        )

    bloco = criar_bloco_produto_principal(
        produto_principal
    )

    if not bloco:
        raise RuntimeError(
            "Não foi possível criar o bloco "
            "contextual do produto principal."
        )

    conteudo_final = conteudo_html.replace(
        MARCADOR_PRODUTO_PRINCIPAL,
        bloco,
        1,
    )

    if MARCADOR_PRODUTO_PRINCIPAL in (
        conteudo_final
    ):
        raise RuntimeError(
            "O marcador do produto principal "
            "permaneceu no artigo após "
            "a substituição."
        )

    return conteudo_final


def criar_bloco_complementares(
    complementares=None,
):
    """
    Cria um bloco final somente para produtos
    complementares realmente relevantes.

    Se não houver complementares, não adiciona nada.
    """

    if not complementares:
        return ""

    produtos_validos = []

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

        produtos_validos.append(
            {
                "nome": nome,
                "link_afiliado": link,
            }
        )

    if not produtos_validos:
        return ""

    partes = [
        '<div class="produtos-complementares">',
        (
            "<h2>Outras opções relacionadas</h2>"
        ),
        (
            "<p>Dependendo da sua rotina, "
            "estes itens também podem ser úteis:</p>"
        ),
        "<ul>",
    ]

    for produto in produtos_validos:
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

    partes.extend(
        [
            "</ul>",
            (
                "<p><small>"
                "<strong>Transparência:</strong> "
                "os links acima podem ser links "
                "de afiliados. Se você comprar "
                "por meio deles, podemos receber "
                "uma comissão, sem custo adicional "
                "para você."
                "</small></p>"
            ),
            "</div>",
        ]
    )

    return "\n".join(
        partes
    )


def adicionar_complementares_ao_artigo(
    conteudo_html,
    complementares=None,
):
    """
    Acrescenta complementares ao final somente
    quando existirem opções relevantes.
    """

    bloco = criar_bloco_complementares(
        complementares or []
    )

    if not bloco:
        return conteudo_html

    return (
        conteudo_html.rstrip()
        + "\n\n"
        + bloco
    )


# ============================================================
# COMPATIBILIDADE COM TESTES ANTERIORES
# ============================================================

def criar_bloco_produtos(
    produto_principal,
    complementares=None,
):
    """
    Mantido para compatibilidade com os testes.

    Retorna o bloco contextual do principal e,
    quando houver, o bloco de complementares.
    """

    principal = criar_bloco_produto_principal(
        produto_principal
    )

    complementares_html = (
        criar_bloco_complementares(
            complementares or []
        )
    )

    partes = [
        parte
        for parte in (
            principal,
            complementares_html,
        )
        if parte
    ]

    return "\n\n".join(
        partes
    )


def adicionar_produtos_ao_artigo(
    conteudo_html,
    produto_principal,
    complementares=None,
):
    """
    Mantido para compatibilidade com testes
    anteriores.

    Se houver marcador, o principal entra
    contextualmente.

    Sem marcador, o principal é acrescentado
    ao final apenas para preservar testes antigos.
    """

    if (
        MARCADOR_PRODUTO_PRINCIPAL
        in conteudo_html
    ):
        conteudo_html = (
            inserir_produto_principal_contextual(
                conteudo_html=conteudo_html,
                produto_principal=(
                    produto_principal
                ),
            )
        )

    else:
        bloco_principal = (
            criar_bloco_produto_principal(
                produto_principal
            )
        )

        if bloco_principal:
            conteudo_html = (
                conteudo_html.rstrip()
                + "\n\n"
                + bloco_principal
            )

    return adicionar_complementares_ao_artigo(
        conteudo_html=conteudo_html,
        complementares=(
            complementares or []
        ),
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

    if publicacao_automatica:
        print(
            "Modo de publicação automática habilitado."
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

    # ========================================================
    # ARTIGO
    # ========================================================

    artigo = criar_estrutura_artigo(
        titulo=seo["titulo"],
        palavra_chave=pauta[
            "palavra_chave"
        ],
        categoria=categoria,
        produto_principal=(
            produto_principal[
                "nome"
            ]
        ),
    )

    # A validação acontece antes da substituição,
    # pois ela também confirma que o Gemini colocou
    # exatamente um marcador contextual.
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

    print(
        "Marcadores contextuais validados:",
        validacao.get(
            "quantidade_marcadores_produto",
            0,
        ),
    )

    # ========================================================
    # PRODUTO PRINCIPAL CONTEXTUAL
    # ========================================================

    print(
        "\n=== PRODUTO PRINCIPAL CONTEXTUAL ==="
    )

    print(
        "Produto:"
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

    artigo["conteudo_html"] = (
        inserir_produto_principal_contextual(
            conteudo_html=artigo[
                "conteudo_html"
            ],
            produto_principal=(
                produto_principal
            ),
        )
    )

    print(
        "Marcador substituído pelo produto "
        "principal com sucesso."
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
    # COMPLEMENTARES
    # ========================================================

    print(
        "\n=== PRODUTOS COMPLEMENTARES ==="
    )

    print(
        "Procurando produtos "
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

    artigo["conteudo_html"] = (
        adicionar_complementares_ao_artigo(
            conteudo_html=artigo[
                "conteudo_html"
            ],
            complementares=(
                complementares
            ),
        )
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

    print(
        "Integração de produtos concluída."
    )

    # Segurança final:
    # o marcador nunca pode chegar ao Blogger.
    if (
        MARCADOR_PRODUTO_PRINCIPAL
        in artigo["conteudo_html"]
    ):
        raise RuntimeError(
            "Marcador interno do produto "
            "permaneceu no artigo final. "
            "Nada será enviado ao Blogger."
        )

    # ========================================================
    # IMAGEM
    # ========================================================

    imagem = gerar_imagem_destacada(
    titulo=seo["titulo"],
    palavra_chave=pauta[
        "palavra_chave"
    ],
    categoria=categoria,
)
    # ========================================================
    # INSERIR IMAGEM DESTACADA NO ARTIGO
    # ========================================================

    if (
        imagem.get("gerada")
        and imagem.get("url_publica")
    ):
        url_imagem = html.escape(
            imagem["url_publica"],
            quote=True,
        )

        alt_imagem = html.escape(
            imagem["alt_text"],
            quote=True,
        )

        bloco_imagem = (
            '<div style="text-align:center;'
            'margin:0 0 24px 0;">'
            f'<img src="{url_imagem}" '
            f'alt="{alt_imagem}" '
            'width="1280" '
            'height="720" '
            'loading="eager" '
            'style="max-width:100%;'
            'height:auto;'
            'border-radius:8px;" />'
            '</div>'
        )

        artigo["conteudo_html"] = (
            bloco_imagem
            + artigo["conteudo_html"]
        )

        print(
            "Imagem destacada inserida "
            "no HTML do artigo."
        )

    else:
        print(
            "Imagem destacada indisponível. "
            "O artigo continuará sem imagem."
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
        "Marcadores contextuais:",
        validacao.get(
            "quantidade_marcadores_produto",
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
        "Produto principal contextual: 1"
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
        if publicacao_automatica:
            print(
                "\nPublicação automática autorizada "
                "pela configuração."
            )
        else:
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
                    publicar=publicacao_automatica,
                )
            )

            pacote[
                "blogger"
            ] = resultado_blogger

            if publicacao_automatica:
                print(
                    "\n=== POST PUBLICADO "
                    "NO BLOGGER ==="
                )
            else:
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

        except Exception as erro:
            print(
                "\nERRO AO ENVIAR "
                "CONTEÚDO AO BLOGGER:"
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
            "O envio ao Blogger "
            "está desativado."
        )

        print(
            "Nenhum conteúdo foi "
            "enviado ao Blogger."
        )

    return pacote


if __name__ == "__main__":
    executar()
