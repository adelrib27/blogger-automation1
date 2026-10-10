import json
import os

from criar_rascunho import criar_servico_blogger


POST_ID = "429407037007587616"

METADADOS_TESTE = {
    "teste_automacao": (
        "Teste controlado de customMetaData. "
        "Este texto não deve publicar o post."
    )
}


def main():
    blog_id = os.getenv("BLOGGER_BLOG_ID")

    if not blog_id:
        raise RuntimeError(
            "BLOGGER_BLOG_ID não encontrado."
        )

    blogger = criar_servico_blogger()

    print("=== TESTE CONTROLADO DE customMetaData ===")
    print("O post continuará como RASCUNHO.")
    print("Nenhuma publicação será solicitada.")
    print()

    print("1. Lendo o rascunho antes da alteração...")

    antes = (
        blogger.posts()
        .get(
            blogId=blog_id,
            postId=POST_ID,
            fetchBody=True,
        )
        .execute()
    )

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

    valor_json = json.dumps(
        METADADOS_TESTE,
        ensure_ascii=False,
    )

    print("2. Enviando customMetaData de teste...")
    print("Valor:", valor_json)

    resultado = (
        blogger.posts()
        .patch(
            blogId=blog_id,
            postId=POST_ID,
            body={
                "customMetaData": valor_json,
            },
            publish=False,
        )
        .execute()
    )

    print()
    print("Resposta do PATCH:")
    print("Status:", resultado.get("status"))
    print(
        "customMetaData:",
        resultado.get("customMetaData"),
    )

    if resultado.get("status") != "DRAFT":
        raise RuntimeError(
            "SEGURANÇA: status inesperado após PATCH."
        )

    print()
    print("3. Lendo novamente diretamente do Blogger...")

    depois = (
        blogger.posts()
        .get(
            blogId=blog_id,
            postId=POST_ID,
            fetchBody=True,
        )
        .execute()
    )

    print("Título:", depois.get("title"))
    print("Status depois:", depois.get("status"))
    print(
        "customMetaData depois:",
        depois.get("customMetaData"),
    )

    print()
    print("=== RESULTADO ===")

    if depois.get("customMetaData") == valor_json:
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
        "O teste NÃO solicitou publicação do post."
    )


if __name__ == "__main__":
    main()
