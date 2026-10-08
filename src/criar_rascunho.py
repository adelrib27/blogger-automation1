import os

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


def main():
    credentials = Credentials(
        token=None,
        refresh_token=os.environ["BLOGGER_REFRESH_TOKEN"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["BLOGGER_CLIENT_ID"],
        client_secret=os.environ["BLOGGER_CLIENT_SECRET"],
        scopes=["https://www.googleapis.com/auth/blogger"],
    )

    blogger = build("blogger", "v3", credentials=credentials)

    blog_id = os.environ["BLOGGER_BLOG_ID"]

    post = {
        "kind": "blogger#post",
        "title": "TESTE — Automação Blogger funcionando",
        "content": """
        <h2>Teste de automação</h2>
        <p>Este artigo foi criado automaticamente pelo GitHub Actions através da Blogger API.</p>
        <p>Se você está vendo este conteúdo nos rascunhos, a integração está funcionando corretamente.</p>
        """
    }

    resultado = (
        blogger.posts()
        .insert(
            blogId=blog_id,
            body=post,
            isDraft=True
        )
        .execute()
    )

    print("RASCUNHO CRIADO COM SUCESSO!")
    print("Título:", resultado.get("title"))
    print("Post ID:", resultado.get("id"))
    print("Status:", resultado.get("status"))


if __name__ == "__main__":
    main()
