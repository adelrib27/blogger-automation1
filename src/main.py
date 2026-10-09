import json
from pathlib import Path

from gerar_pautas import gerar_pauta_automatica
from seo import preparar_seo
from gerar_artigo import criar_estrutura_artigo, validar_artigo
from gerar_imagem import preparar_imagem
from criar_rascunho import criar_rascunho
from links_internos import adicionar_links_internos


BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config" / "blog.json"
HISTORICO_PATH = BASE_DIR / "data" / "historico.json"


def carregar_json(caminho, padrao=None):
    if padrao is None:
        padrao = {}

    if not caminho.exists():
        return padrao

    try:
        with caminho.open("r", encoding="utf-8") as arquivo:
            return json.load(arquivo)
    except (json.JSONDecodeError, OSError):
        return padrao


def carregar_config():
    return carregar_json(CONFIG_PATH, {})


def carregar_historico():
    historico = carregar_json(HISTORICO_PATH, [])

    if isinstance(historico, list):
        return historico

    return []


def escolher_pauta(nicho):
    """
    Gera automaticamente pautas com Gemini e seleciona
    uma pauta inédita usando o histórico real do blog.
    """

    return gerar_pauta_automatica(
        nicho=nicho,
    )


def executar():
    print("=== BLOGGER AUTOMATION ===")

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

    print("Blog:", nome_blog)
    print("Nicho:", nicho)
    print(
        "Criar rascunho no Blogger:",
        criar_rascunho_ativo,
    )
    print(
        "Publicação automática:",
        publicacao_automatica,
    )

    # Proteção adicional:
    # publicação automática ainda não foi liberada.
    if publicacao_automatica:
        raise RuntimeError(
            "Publicação automática está habilitada na configuração, "
            "mas esta etapa ainda não foi liberada pelo sistema."
        )

    print(
        "\nSelecionando uma pauta inédita automaticamente..."
    )

    pauta = escolher_pauta(
        nicho=nicho,
    )

    print("\nPauta escolhida:")
    print(pauta["titulo"])
    print(
        "Palavra-chave:",
        pauta["palavra_chave"],
    )
    print(
        "Categoria:",
        pauta.get(
            "categoria",
            "Casa e Decoração",
        ),
    )

    seo_config = config.get("seo", {})

    seo = preparar_seo(
        titulo=pauta["titulo"],
        palavra_chave=pauta["palavra_chave"],
        descricao=pauta["descricao"],
        palavras_secundarias=pauta.get(
            "palavras_secundarias",
            [],
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
        palavra_chave=pauta["palavra_chave"],
        categoria=pauta.get(
            "categoria",
            "Casa e Decoração",
        ),
    )

    validacao = validar_artigo(artigo)

    if not validacao["valido"]:
        print("\nArtigo reprovado:")

        for erro in validacao["erros"]:
            print("-", erro)

        print(
            "\nNada foi enviado ao Blogger."
        )
        return

    historico = carregar_historico()

    resultado_links = adicionar_links_internos(
        conteudo_html=artigo["conteudo_html"],
        historico=historico,
        titulo_atual=seo["titulo"],
        palavra_chave=pauta["palavra_chave"],
        categoria=pauta.get(
            "categoria",
            "Casa e Decoração",
        ),
    )

    artigo["conteudo_html"] = resultado_links[
        "conteudo_html"
    ]

    artigo["links_internos"] = resultado_links[
        "links"
    ]

    print(
        "\nLinks internos adicionados:",
        len(artigo["links_internos"]),
    )

    for link in artigo["links_internos"]:
        print(
            "-",
            link.get("titulo", ""),
        )
        print(
            "  URL:",
            link.get("url", ""),
        )

    imagem = preparar_imagem(
        titulo=seo["titulo"],
        palavra_chave=pauta["palavra_chave"],
        categoria=pauta.get(
            "categoria",
            "Casa e Decoração",
        ),
    )

    pacote = {
        "pauta": pauta,
        "seo": seo,
        "artigo": artigo,
        "imagem": imagem,
    }

    print("\n=== PACOTE GERADO COM SUCESSO ===")
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
        pauta.get(
            "categoria",
        ),
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
        len(artigo["links_internos"]),
    )

    # Durante os testes, mantemos o artigo visível
    # no log para revisão editorial.
    print(
        "\n=== INÍCIO DO ARTIGO GERADO ==="
    )
    print(
        artigo["conteudo_html"]
    )
    print(
        "=== FIM DO ARTIGO GERADO ==="
    )

    if criar_rascunho_ativo:
        print(
            "\nEnvio de rascunho autorizado "
            "pela configuração."
        )

        try:
            resultado_blogger = criar_rascunho(
                titulo=seo["titulo"],
                conteudo_html=artigo[
                    "conteudo_html"
                ],
                categoria=pauta.get(
                    "categoria",
                    "Casa e Decoração",
                ),
            )

            pacote["blogger"] = resultado_blogger

            print(
                "\n=== RASCUNHO CRIADO NO BLOGGER ==="
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

            # O rascunho ainda não entra no histórico.
            # O histórico definitivo continua reservado
            # para publicações reais confirmadas.

        except Exception as erro:
            print(
                "\nERRO AO CRIAR RASCUNHO NO BLOGGER:"
            )
            print(erro)

            print(
                "\nO artigo não foi registrado "
                "no histórico."
            )

            return pacote

    else:
        print(
            "\nMODO SEGURO ATIVO."
        )
        print(
            "A criação de rascunho no Blogger "
            "está desativada."
        )
        print(
            "Nenhum conteúdo foi enviado ao Blogger."
        )

    return pacote


if __name__ == "__main__":
    executar()
