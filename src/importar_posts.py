import os

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


ESCOPO_BLOGGER = "https://www.googleapis.com/auth/blogger"


def criar_servico_blogger():
    """
    Cria o serviço da Blogger API usando as credenciais
    já configuradas nos Secrets do GitHub.
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


def listar_posts_publicados():
    """
    Consulta somente os posts PUBLICADOS no Blogger.

    Esta função é apenas de leitura:
    não cria, edita, publica ou exclui posts.
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
                    "id": post.get("id"),
                    "titulo": post.get("title"),
                    "url": post.get("url"),
                    "publicado_em": post.get("published"),
                    "atualizado_em": post.get("updated"),
                    "labels": post.get("labels", []),
                    "status": post.get("status"),
                }
            )

        page_token = resposta.get("nextPageToken")

        if not page_token:
            break

    return posts_encontrados


def main():
    print("=== LEITURA DOS POSTS DO BLOGGER ===")
    print("Modo somente leitura.")
    print("Nenhum post será alterado.\n")

    posts = listar_posts_publicados()

    print(
        f"Posts publicados encontrados: {len(posts)}"
    )

    for numero, post in enumerate(posts, start=1):
        print("\n------------------------------")
        print(f"POST {numero}")
        print("Título:", post.get("titulo"))
        print("Post ID:", post.get("id"))
        print("URL:", post.get("url"))
        print("Publicado em:", post.get("publicado_em"))
        print("Marcadores:", post.get("labels"))
        print("Status:", post.get("status"))

    print("\n=== LEITURA CONCLUÍDA ===")
    print(
        "Nenhum conteúdo foi criado, "
        "editado ou excluído."
    )


if __name__ == "__main__":
    main()
