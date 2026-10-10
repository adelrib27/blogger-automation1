import html

from gerar_imagem import gerar_imagem_destacada


def executar_teste():
    print()
    print("==========================================")
    print("TESTE — IMAGEM INTEGRADA AO ARTIGO")
    print("Nenhum conteúdo será enviado ao Blogger.")
    print("==========================================")

    titulo = (
        "Como deixar a sala mais aconchegante "
        "com iluminação indireta"
    )

    palavra_chave = (
        "iluminação indireta para sala"
    )

    categoria = "Iluminação"

    artigo = {
        "conteudo_html": (
            "<p>Este é um artigo fictício usado "
            "somente para testar a integração "
            "da imagem destacada.</p>"
            "<h2>Iluminação aconchegante</h2>"
            "<p>A iluminação pode transformar "
            "a percepção visual do ambiente.</p>"
        )
    }

    print()
    print("ETAPA 1 — GERAR IMAGEM")

    imagem = gerar_imagem_destacada(
        titulo=titulo,
        palavra_chave=palavra_chave,
        categoria=categoria,
    )

    if not imagem.get("gerada"):
        raise RuntimeError(
            "A imagem não foi gerada: "
            f"{imagem.get('erro')}"
        )

    if not imagem.get("url_publica"):
        raise RuntimeError(
            "A imagem foi gerada, mas não "
            "possui URL pública."
        )

    print()
    print("ETAPA 2 — INSERIR IMAGEM NO HTML")

    url_imagem = html.escape(
        imagem["url_publica"],
        quote=True,
    )

    alt_imagem = html.escape(
        imagem["alt_text"],
        quote=True,
    )

    bloco_imagem = (
        '<div style="text-align:center;'
        'margin:0 0 24px 0;">'
        f'<img src="{url_imagem}" '
        f'alt="{alt_imagem}" '
        'width="1280" '
        'height="720" '
        'loading="eager" '
        'style="max-width:100%;'
        'height:auto;'
        'border-radius:8px;" />'
        '</div>'
    )

    artigo["conteudo_html"] = (
        bloco_imagem
        + artigo["conteudo_html"]
    )

    print("IMAGEM INSERIDA NO HTML: OK")

    print()
    print("ETAPA 3 — VALIDAR HTML")

    conteudo = artigo["conteudo_html"]

    verificacoes = {
        "tag_img": "<img " in conteudo,
        "url_cloudinary": (
            "res.cloudinary.com"
            in conteudo
        ),
        "alt_text": (
            imagem["alt_text"]
            in conteudo
        ),
        "largura": (
            'width="1280"'
            in conteudo
        ),
        "altura": (
            'height="720"'
            in conteudo
        ),
        "artigo_original": (
            "Este é um artigo fictício"
            in conteudo
        ),
    }

    for nome, resultado in verificacoes.items():
        print(
            f"{nome}: "
            f"{'OK' if resultado else 'FALHOU'}"
        )

    if not all(verificacoes.values()):
        raise RuntimeError(
            "Uma ou mais validações "
            "do HTML falharam."
        )

    if not conteudo.startswith(
        '<div style="text-align:center;'
    ):
        raise RuntimeError(
            "A imagem não ficou no início "
            "do artigo."
        )

    print()
    print("==========================================")
    print("TESTE COMPLETO: OK")
    print("IMAGEM GERADA: OK")
    print("CLOUDINARY: OK")
    print("IMAGEM NO HTML: OK")
    print("POSIÇÃO NO TOPO: OK")
    print(
        "URL:",
        imagem["url_publica"],
    )
    print("==========================================")
    print()
    print(
        "Nenhum conteúdo foi enviado "
        "ao Blogger."
    )


if __name__ == "__main__":
    executar_teste()
