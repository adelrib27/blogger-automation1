import os

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


def main():
    client_id = os.environ["BLOGGER_CLIENT_ID"]
    client_secret = os.environ["BLOGGER_CLIENT_SECRET"]
    refresh_token = os.environ["BLOGGER_REFRESH_TOKEN"]
    blog_id = os.environ["BLOGGER_BLOG_ID"]

    credentials = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=["https://www.googleapis.com/auth/blogger"],
    )

    blogger = build("blogger", "v3", credentials=credentials)

    blog = blogger.blogs().get(blogId=blog_id).execute()

    print("CONEXÃO COM O BLOGGER: OK")
    print("Nome do blog:", blog.get("name"))
    print("URL do blog:", blog.get("url"))
    print("Blog ID confirmado:", blog.get("id"))


if __name__ == "__main__":
    main()
