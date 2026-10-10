import json
import os

from criar_rascunho import criar_servico_blogger


TITULO_PROCURADO = "TESTE — Automação Blogger funcionando"

METADADOS_TESTE = {
    "teste_automacao": (
        "Teste controlado de customMetaData. "
        "Este texto não deve publicar o post."
    )
}


def localizar_rascunho(
    blogger,
    blog_id,
):
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

    for post in posts:
        titulo = str(
            post.get("title") or ""
        ).strip()

        if titulo == TITULO_PROCURADO:
            return post

    return None


def main():
    blog_id = os.getenv("BLOGGER_BLOG_ID")

    if not blog_id:
        raise RuntimeError(
            "BLOGGER_BLOG_ID não encontrado."
        )

    blogger = criar_servico_blogger()

    print(
        "=== TESTE CONTROLADO DE customMetaData ==="
    )
    print(
        "O post continuará como RASCUNHO."
    )
    print(
        "Nenhuma publicação será solicitada."
    )
    print()

    print(
        "1. Localizando o rascunho diretamente "
        "no Blogger..."
    )

    antes = localizar_rascunho(
        blogger,
        blog_id,
    )

    if antes is None:
        raise RuntimeError(
            "Rascunho de teste não encontrado: "
            + TITULO_PROCURADO
        )

    post_id = antes.get("id")

    print("Rascunho encontrado.")
    print("ID atual:", post_id)
    print("Título:", antes.get("title"))
    print("Status antes:", antes.get("status"))
    print(
        "customMetaData antes:",
        antes.get("customMetaData"),
    )
    print()

    if antes.get("status") != "DRAFT":
        raise RuntimeError(
            "SEGURANÇA: o post não está como DRAFT. "
            "Teste cancelado."
        )

    if not post_id:
        raise RuntimeError(
            "O Blogger não retornou o ID "
            "do rascunho."
        )

    valor_json = json.dumps(
        METADADOS_TESTE,
        ensure_ascii=False,
    )

    print(
        "2. Enviando customMetaData de teste..."
    )
    print("Valor:", valor_json)

    resultado = (
        blogger.posts()
        .patch(
            blogId=blog_id,
            postId=post_id,
            body={
                "customMetaData": valor_json,
            },
            publish=False,
        )
        .execute()
    )

    print()
    print("Resposta do PATCH:")
    print(
        "Status:",
        resultado.get("status"),
    )
    print(
        "customMetaData:",
        resultado.get("customMetaData"),
    )

    if resultado.get("status") != "DRAFT":
        raise RuntimeError(
            "SEGURANÇA: status inesperado "
            "após PATCH."
        )

    print()
    print(
        "3. Localizando novamente o rascunho..."
    )

    depois = localizar_rascunho(
        blogger,
        blog_id,
    )

    if depois is None:
        raise RuntimeError(
            "O rascunho não foi encontrado "
            "após o PATCH."
        )

    print("ID depois:", depois.get("id"))
    print("Título:", depois.get("title"))
    print(
        "Status depois:",
        depois.get("status"),
    )
    print(
        "customMetaData depois:",
        depois.get("customMetaData"),
    )

    print()
    print("=== RESULTADO ===")

    if (
        depois.get("customMetaData")
        == valor_json
    ):
        print(
            "SUCESSO: customMetaData foi "
            "persistido pelo Blogger."
        )
    else:
        print(
            "O Blogger não devolveu exatamente "
            "o customMetaData enviado."
        )

    print()
    print(
        "O teste NÃO solicitou publicação "
        "do post."
    )


if __name__ == "__main__":
    main()
