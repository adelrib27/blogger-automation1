import json
import os
from pathlib import Path

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


ESCOPO_BLOGGER = "https://www.googleapis.com/auth/blogger"

BASE_DIR = Path(__file__).resolve().parent.parent
HISTORICO_PATH = BASE_DIR / "data" / "historico.json"

TITULOS_INSTITUCIONAIS = {
    "política de privacidade",
    "politica de privacidade",
    "termos de uso",
    "sobre",
    "sobre nós",
    "sobre nos",
    "contato",
}


def criar_servico_blogger():
    """
    Cria o serviço da Blogger API usando as credenciais
    configuradas nos Secrets do GitHub.
    """
    variaveis = (
        "BLOGGER_REFRESH_TOKEN",
        "BLOGGER_CLIENT_ID",
        "BLOGGER_CLIENT_SECRET",
        "BLOGGER_BLOG_ID",
    )

    ausentes = [
        nome
        for nome in variaveis
        if not os.getenv(nome)
    ]

    if ausentes:
        raise RuntimeError(
            "Variáveis ausentes: "
            + ", ".join(ausentes)
        )

    credenciais = Credentials(
        token=None,
        refresh_token=os.environ["BLOGGER_REFRESH_TOKEN"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["BLOGGER_CLIENT_ID"],
        client_secret=os.environ["BLOGGER_CLIENT_SECRET"],
        scopes=[ESCOPO_BLOGGER],
    )

    return build(
        "blogger",
        "v3",
        credentials=credenciais,
        cache_discovery=False,
    )


def carregar_historico():
    """
    Carrega o histórico existente sem apagar registros válidos.
    """
    if not HISTORICO_PATH.exists():
        return []

    try:
        with HISTORICO_PATH.open(
            "r",
            encoding="utf-8",
        ) as arquivo:
            dados = json.load(arquivo)

        if isinstance(dados, list):
            return dados

    except (json.JSONDecodeError, OSError) as erro:
        raise RuntimeError(
            f"Não foi possível ler o histórico: {erro}"
        ) from erro

    raise RuntimeError(
        "historico.json não contém uma lista válida."
    )


def salvar_historico(historico):
    """
    Salva o histórico formatado em JSON.
    """
    HISTORICO_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with HISTORICO_PATH.open(
        "w",
        encoding="utf-8",
    ) as arquivo:
        json.dump(
            historico,
            arquivo,
            ensure_ascii=False,
            indent=2,
        )

        arquivo.write("\n")


def listar_posts_publicados():
    """
    Consulta somente posts publicados no Blogger.

    Não cria, edita, publica ou exclui conteúdo.
    """
    blogger = criar_servico_blogger()
    blog_id = os.environ["BLOGGER_BLOG_ID"]

    posts_encontrados = []
    page_token = None

    while True:
        parametros = {
            "blogId": blog_id,
            "status": ["LIVE"],
            "fetchBodies": False,
            "maxResults": 50,
        }

        if page_token:
            parametros["pageToken"] = page_token

        resposta = (
            blogger.posts()
            .list(**parametros)
            .execute()
        )

        for post in resposta.get("items", []):
            posts_encontrados.append(
                {
                    "id": str(
                        post.get("id") or ""
                    ).strip(),
                    "titulo": str(
                        post.get("title") or ""
                    ).strip(),
                    "url": str(
                        post.get("url") or ""
                    ).strip(),
                    "publicado_em": post.get(
                        "published"
                    ),
                    "atualizado_em": post.get(
                        "updated"
                    ),
                    "labels": post.get(
                        "labels",
                        [],
                    ),
                }
            )

        page_token = resposta.get(
            "nextPageToken"
        )

        if not page_token:
            break

    return posts_encontrados


def post_institucional(post):
    """
    Identifica páginas institucionais que não devem participar
    do motor editorial, anti-repetição ou links internos.
    """
    titulo = str(
        post.get("titulo") or ""
    ).strip().lower()

    return titulo in TITULOS_INSTITUCIONAIS


def registro_do_blogger(post):
    """
    Converte um post real do Blogger para o formato
    usado pelo histórico da automação.

    Campos desconhecidos não são inventados.
    """
    labels = post.get("labels") or []

    categoria = ""

    if labels:
        categoria = str(labels[0]).strip()

    return {
        "id": post.get("id", ""),
        "titulo": post.get("titulo", ""),
        "url": post.get("url", ""),
        "publicado_em": post.get(
            "publicado_em"
        ),
        "atualizado_em": post.get(
            "atualizado_em"
        ),
        "categoria": categoria,
        "palavra_chave": "",
        "origem": "blogger",
    }


def sincronizar_historico(
    historico,
    posts_publicados,
):
    """
    Acrescenta posts editoriais ainda ausentes.

    Registros existentes são preservados.
    A sincronização não remove automaticamente nada.
    """
    resultado = list(historico)

    ids_existentes = {
        str(item.get("id") or "").strip()
        for item in resultado
        if item.get("id")
    }

    urls_existentes = {
        str(item.get("url") or "").strip()
        for item in resultado
        if item.get("url")
    }

    adicionados = []
    ignorados_institucionais = []
    ja_existentes = []

    for post in posts_publicados:
        if post_institucional(post):
            ignorados_institucionais.append(
                post.get("titulo")
            )
            continue

        post_id = str(
            post.get("id") or ""
        ).strip()

        post_url = str(
            post.get("url") or ""
        ).strip()

        if (
            post_id in ids_existentes
            or post_url in urls_existentes
        ):
            ja_existentes.append(
                post.get("titulo")
            )
            continue

        registro = registro_do_blogger(
            post
        )

        resultado.append(registro)
        adicionados.append(registro)

        if post_id:
            ids_existentes.add(post_id)

        if post_url:
            urls_existentes.add(post_url)

    return {
        "historico": resultado,
        "adicionados": adicionados,
        "institucionais": ignorados_institucionais,
        "ja_existentes": ja_existentes,
    }


def main():
    print(
        "=== SINCRONIZAÇÃO DO HISTÓRICO BLOGGER ==="
    )
    print(
        "Posts existentes no Blogger não serão "
        "editados ou excluídos.\n"
    )

    historico_atual = carregar_historico()

    print(
        "Registros existentes no histórico:",
        len(historico_atual),
    )

    posts = listar_posts_publicados()

    print(
        "Posts publicados encontrados no Blogger:",
        len(posts),
    )

    sincronizacao = sincronizar_historico(
        historico=historico_atual,
        posts_publicados=posts,
    )

    adicionados = sincronizacao[
        "adicionados"
    ]

    institucionais = sincronizacao[
        "institucionais"
    ]

    ja_existentes = sincronizacao[
        "ja_existentes"
    ]

    print(
        "Posts editoriais novos:",
        len(adicionados),
    )

    print(
        "Posts institucionais ignorados:",
        len(institucionais),
    )

    print(
        "Posts que já estavam no histórico:",
        len(ja_existentes),
    )

    if institucionais:
        print(
            "\nInstitucionais ignorados:"
        )

        for titulo in institucionais:
            print("-", titulo)

    if adicionados:
        print(
            "\nNovos registros:"
        )

        for registro in adicionados:
            print(
                "-",
                registro.get("titulo"),
            )
            print(
                "  URL:",
                registro.get("url"),
            )

        salvar_historico(
            sincronizacao["historico"]
        )

        print(
            "\nhistorico.json atualizado."
        )

    else:
        print(
            "\nNenhum registro novo."
        )
        print(
            "historico.json permaneceu "
            "inalterado."
        )

    print(
        "\nTotal final no histórico:",
        len(
            sincronizacao["historico"]
        ),
    )

    print(
        "\n=== SINCRONIZAÇÃO CONCLUÍDA ==="
    )


if __name__ == "__main__":
    main()
