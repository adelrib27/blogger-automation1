import html

from gerar_imagem import gerar_imagem_destacada
from criar_rascunho import criar_rascunho


def executar_teste():
    print()
    print("==========================================")
    print("TESTE — RASCUNHO COMPLETO COM IMAGEM")
    print("O conteúdo será enviado somente como RASCUNHO.")
    print("Nenhuma publicação automática será realizada.")
    print("==========================================")

    titulo = (
        "TESTE — Sala aconchegante com iluminação indireta"
    )

    palavra_chave = "iluminação indireta para sala"
    categoria = "Iluminação"

    artigo_html = (
        "<p>Este é um artigo de teste criado exclusivamente "
        "para validar a integração entre a geração de imagem, "
        "o Cloudinary e o Blogger.</p>"
        "<h2>Iluminação indireta na sala</h2>"
        "<p>A iluminação indireta pode contribuir para uma "
        "atmosfera visualmente mais acolhedora e confortável "
        "na sala de estar.</p>"
        "<h2>Composição do ambiente</h2>"
        "<p>Pontos de luz distribuídos pelo ambiente podem "
        "ajudar a destacar móveis, texturas e elementos "
        "decorativos.</p>"
        "<p><strong>TESTE TÉCNICO:</strong> este conteúdo "
        "não corresponde a um artigo editorial definitivo.</p>"
    )

    print()
    print("ETAPA 1 — GERAR IMAGEM DESTACADA")

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
            "A imagem foi gerada, mas não possui URL pública."
        )

    print()
    print("IMAGEM: OK")
    print("URL:", imagem["url_publica"])

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

    conteudo_final = (
        bloco_imagem
        + artigo_html
    )

    if imagem["url_publica"] not in conteudo_final:
        raise RuntimeError(
            "A URL da imagem não foi inserida no HTML."
        )

    if "<img " not in conteudo_final:
        raise RuntimeError(
            "A tag IMG não foi encontrada no HTML."
        )

    print("IMAGEM INSERIDA NO HTML: OK")

    print()
    print("ETAPA 3 — CRIAR RASCUNHO NO BLOGGER")
    print("TRAVA DE SEGURANÇA: publicar=False")

    resultado = criar_rascunho(
        titulo=titulo,
        conteudo_html=conteudo_final,
        categoria=categoria,
        publicar=False,
    )

    if not resultado:
        raise RuntimeError(
            "O Blogger não retornou dados do rascunho."
        )

    print()
    print("==========================================")
    print("TESTE COMPLETO: OK")
    print("IMAGEM GERADA: OK")
    print("CLOUDINARY: OK")
    print("IMAGEM NO HTML: OK")
    print("BLOGGER: RASCUNHO CRIADO")
    print("PUBLICAÇÃO AUTOMÁTICA: NÃO")
    print("==========================================")

    print("Título:", resultado.get("titulo"))
    print("Post ID:", resultado.get("id"))
    print("Status:", resultado.get("status"))
    print("URL:", resultado.get("url"))
    print("Imagem:", imagem["url_publica"])

    print()
    print(
        "Agora abra este rascunho no painel do Blogger "
        "para conferir visualmente a imagem e o conteúdo."
    )


if __name__ == "__main__":
    executar_teste()
