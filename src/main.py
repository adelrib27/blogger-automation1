import json
from pathlib import Path

from pautas import filtrar_pautas
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


def escolher_pauta():
    """
    Pautas temporárias usadas durante a construção do sistema.

    Depois esta etapa será substituída pelo motor automático
    de geração e seleção de pautas.
    """
    pautas = [
        {
            "titulo": "Como organizar uma cozinha pequena de forma prática",
            "palavra_chave": "organização de cozinha pequena",
            "categoria": "Organização",
            "descricao": (
                "Ideias práticas para aproveitar melhor o espaço "
                "e manter uma cozinha pequena organizada."
            ),
            "palavras_secundarias": [
                "cozinha pequena",
                "organização da cozinha",
                "otimização de espaço",
            ],
        },
        {
            "titulo": "Como deixar a sala mais bonita gastando pouco",
            "palavra_chave": "decoração de sala barata",
            "categoria": "Decoração",
            "descricao": (
                "Dicas simples para transformar a decoração da sala "
                "sem gastar muito."
            ),
            "palavras_secundarias": [
                "decoração barata",
                "sala pequena",
                "decoração de sala",
            ],
        },
        {
            "titulo": "Ideias para organizar banheiro pequeno",
            "palavra_chave": "organização de banheiro pequeno",
            "categoria": "Organização",
            "descricao": (
                "Soluções práticas para organizar produtos e aproveitar "
                "melhor o espaço de banheiros pequenos."
            ),
            "palavras_secundarias": [
                "banheiro pequeno",
                "organizador de banheiro",
                "organização da casa",
            ],
        },
    ]

    disponiveis = filtrar_pautas(pautas)

    if not disponiveis:
        raise RuntimeError(
            "Nenhuma pauta inédita disponível."
        )

    return disponiveis[0]


def executar():
    print("=== BLOGGER AUTOMATION ===")

    config = carregar_config()

    nome_blog = config.get(
        "nome_blog",
        "Não definido",
    )

    nicho = config.get(
        "nicho",
        "Não definido",
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
    # publicação automática ainda não foi implementada.
    if publicacao_automatica:
        raise RuntimeError(
            "Publicação automática está habilitada na configuração, "
            "mas esta etapa ainda não foi liberada pelo sistema."
        )

    pauta = escolher_pauta()

    print("\nPauta escolhida:")
    print(pauta["titulo"])

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

    # Primeiro validamos o conteúdo produzido pela IA.
    validacao = validar_artigo(artigo)

    if not validacao["valido"]:
        print("\nArtigo reprovado:")

        for erro in validacao["erros"]:
            print("-", erro)

        print(
            "\nNada foi enviado ao Blogger."
        )
        return

    print(
        "\nArtigo aprovado antes dos links internos."
    )

    # Os links internos são adicionados somente depois
    # da geração e validação do artigo.
    #
    # As URLs vêm exclusivamente do historico.json.
    resultado_links = adicionar_links_internos(
        conteudo_html=artigo["conteudo_html"],
        titulo=seo["titulo"],
        palavra_chave=pauta["palavra_chave"],
        categoria=pauta.get(
            "categoria",
            "Casa e Decoração",
        ),
        limite=3,
    )

    artigo["conteudo_html"] = resultado_links[
        "conteudo_html"
    ]

    print("\n=== LINKS INTERNOS ===")
    print(
        "Quantidade inserida:",
        resultado_links["quantidade"],
    )

    if resultado_links["links"]:
        for numero, link in enumerate(
            resultado_links["links"],
            start=1,
        ):
            print()
            print(f"Link {numero}:")
            print(
                "Título:",
                link["titulo"],
            )
            print(
                "URL:",
                link["url"],
            )
            print(
                "Pontuação:",
                link["pontuacao"],
            )
    else:
        print(
            "Nenhum post suficientemente relacionado "
            "foi encontrado."
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
        "links_internos": resultado_links,
    }

    print("\n=== PACOTE GERADO COM SUCESSO ===")
    print("Título:", seo["titulo"])
    print("Slug:", seo["slug"])
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
        pauta.get("categoria"),
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
        resultado_links["quantidade"],
    )

    # Durante os testes, mantemos o artigo completo
    # visível no log para revisão editorial.
    print(
        "\n=== INÍCIO DO ARTIGO GERADO ==="
    )
    print(artigo["conteudo_html"])
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
            # para posts realmente publicados.
            print(
                "\nRascunho não registrado no histórico."
            )

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
