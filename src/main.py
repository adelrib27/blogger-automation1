import json
from pathlib import Path

from pautas import filtrar_pautas
from seo import preparar_seo
from gerar_artigo import criar_estrutura_artigo, validar_artigo
from gerar_imagem import preparar_imagem


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
    Pautas iniciais para testar o motor.
    Depois esta etapa será alimentada automaticamente pela IA.
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
        raise RuntimeError("Nenhuma pauta inédita disponível.")

    return disponiveis[0]


def executar():
    print("=== BLOGGER AUTOMATION ===")

    config = carregar_config()

    print("Blog:", config.get("nome_blog", "Não definido"))
    print("Nicho:", config.get("nicho", "Não definido"))
    print("Publicação automática:", config.get("publicacao_automatica", False))

    pauta = escolher_pauta()

    print("\nPauta escolhida:")
    print(pauta["titulo"])

    seo_config = config.get("seo", {})

    seo = preparar_seo(
        titulo=pauta["titulo"],
        palavra_chave=pauta["palavra_chave"],
        descricao=pauta["descricao"],
        palavras_secundarias=pauta.get("palavras_secundarias", []),
        titulo_max=seo_config.get("titulo_max", 60),
        meta_max=seo_config.get("meta_description_max", 155),
    )

    artigo = criar_estrutura_artigo(
        titulo=seo["titulo"],
        palavra_chave=pauta["palavra_chave"],
        categoria=pauta.get("categoria", "Casa e Decoração"),
    )

    validacao = validar_artigo(artigo)

    if not validacao["valido"]:
        print("\nArtigo reprovado:")
        for erro in validacao["erros"]:
            print("-", erro)
        return

    imagem = preparar_imagem(
        titulo=seo["titulo"],
        palavra_chave=pauta["palavra_chave"],
        categoria=pauta.get("categoria", "Casa e Decoração"),
    )

    pacote = {
        "pauta": pauta,
        "seo": seo,
        "artigo": artigo,
        "imagem": imagem,
    }

    print("\n=== PACOTE GERADO COM SUCESSO ===")
    print("Título:", seo["titulo"])
    print("Slug:", seo["slug"])
    print("Meta description:", seo["meta_description"])
    print("Palavra-chave:", pauta["palavra_chave"])
    print("Categoria:", pauta.get("categoria"))
    print("Imagem:", imagem["nome_arquivo"])
    print("ALT:", imagem["alt_text"])
    print("Artigo validado:", validacao["valido"])

    # Exibe o artigo completo apenas para revisão durante os testes.
    print("\n=== INÍCIO DO ARTIGO GERADO ===")
    print(artigo["conteudo_html"])
    print("=== FIM DO ARTIGO GERADO ===")

    if config.get("publicacao_automatica", False):
        print("\nPublicação automática habilitada.")
        print("A conexão final com o Blogger será executada nesta etapa.")
    else:
        print("\nMODO SEGURO ATIVO.")
        print("Nenhum artigo será publicado automaticamente.")

    return pacote


if __name__ == "__main__":
    executar()
