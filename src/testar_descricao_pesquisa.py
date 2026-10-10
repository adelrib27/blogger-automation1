import os

from criar_rascunho import criar_servico_blogger


TITULO_PROCURADO = "TESTE — Automação Blogger funcionando"


def main():
    blog_id = os.getenv("BLOGGER_BLOG_ID")

    if not blog_id:
        raise RuntimeError(
            "BLOGGER_BLOG_ID não encontrado."
        )

    blogger = criar_servico_blogger()

    print("=== TESTE DE LEITURA DE METADADOS ===")
    print("Nenhum post será criado, alterado ou publicado.")
    print()

    resposta = (
        blogger.posts()
        .list(
            blogId=blog_id,
            status=["DRAFT"],
            fetchBodies=True,
            maxResults=50,
        )
        .execute()
    )

    posts = resposta.get("items", [])

    encontrado = None

    for post in posts:
        titulo = str(
            post.get("title") or ""
        ).strip()

        if titulo == TITULO_PROCURADO:
            encontrado = post
            break

    if encontrado is None:
        print(
            "Rascunho de teste não encontrado:"
        )
        print(TITULO_PROCURADO)
        return

    print("Rascunho encontrado.")
    print("ID:", encontrado.get("id"))
    print("Título:", encontrado.get("title"))
    print("Status:", encontrado.get("status"))
    print()

    custom_meta = encontrado.get(
        "customMetaData"
    )

    print("=== customMetaData ===")

    if custom_meta is None:
        print("None")
    elif custom_meta == "":
        print("(vazio)")
    else:
        print(custom_meta)

    print()
    print("=== FIM DO TESTE ===")
    print(
        "Nenhuma alteração foi enviada ao Blogger."
    )


if __name__ == "__main__":
    main()
