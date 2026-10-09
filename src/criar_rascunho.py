import os

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


ESCOPO_BLOGGER = "https://www.googleapis.com/auth/blogger"


def criar_credenciais():
    """
    Cria as credenciais OAuth usadas para acessar a Blogger API.
    """
    variaveis_obrigatorias = (
        "BLOGGER_REFRESH_TOKEN",
        "BLOGGER_CLIENT_ID",
        "BLOGGER_CLIENT_SECRET",
    )

    ausentes = [
        nome
        for nome in variaveis_obrigatorias
        if not os.getenv(nome)
    ]

    if ausentes:
        raise RuntimeError(
            "Variáveis do Blogger ausentes: "
            + ", ".join(ausentes)
        )

    return Credentials(
        token=None,
        refresh_token=os.environ["BLOGGER_REFRESH_TOKEN"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["BLOGGER_CLIENT_ID"],
        client_secret=os.environ["BLOGGER_CLIENT_SECRET"],
        scopes=[ESCOPO_BLOGGER],
    )


def criar_servico_blogger():
    """
    Cria e retorna o serviço da Blogger API.
    """
    credentials = criar_credenciais()

    return build(
        "blogger",
        "v3",
        credentials=credentials,
        cache_discovery=False,
    )


def criar_rascunho(
    titulo,
    conteudo_html,
    categoria=None,
    publicar=False,
):
    """
    Envia um post ao Blogger.

    Por padrão, cria um RASCUNHO.
    Quando publicar=True, publica o artigo diretamente.
    """
    blog_id = os.getenv("BLOGGER_BLOG_ID")

    if not blog_id:
        raise RuntimeError(
            "BLOGGER_BLOG_ID não encontrado."
        )

    titulo = str(titulo or "").strip()
    conteudo_html = str(conteudo_html or "").strip()
    categoria = str(categoria or "").strip()

    if not titulo:
        raise ValueError(
            "Não é possível enviar um post sem título."
        )

    if not conteudo_html:
        raise ValueError(
            "Não é possível enviar um post sem conteúdo."
        )

    post = {
        "kind": "blogger#post",
        "title": titulo,
        "content": conteudo_html,
    }

    if categoria:
        post["labels"] = [categoria]

    blogger = criar_servico_blogger()

    resultado = (
        blogger.posts()
        .insert(
            blogId=blog_id,
            body=post,
            isDraft=not publicar,
        )
        .execute()
    )

    return {
        "id": resultado.get("id"),
        "titulo": resultado.get("title"),
        "url": resultado.get("url"),
        "status": resultado.get("status"),
        "labels": resultado.get("labels", []),
    }


if __name__ == "__main__":
    print(
        "Módulo Blogger carregado com sucesso. "
        "Nenhum post foi enviado."
    )
