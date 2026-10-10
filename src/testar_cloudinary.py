import os
import base64
import tempfile

import cloudinary
import cloudinary.uploader


IMAGEM_TESTE_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk"
    "YAAAAAYAAjCB0C8AAAAASUVORK5CYII="
)


def testar_cloudinary():
    cloudinary_url = os.getenv("CLOUDINARY_URL")

    if not cloudinary_url:
        raise RuntimeError("CLOUDINARY_URL não encontrado nos Secrets.")

    cloudinary.config(secure=True)

    dados_imagem = base64.b64decode(IMAGEM_TESTE_BASE64)

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as arquivo:
        arquivo.write(dados_imagem)
        caminho = arquivo.name

    try:
        resultado = cloudinary.uploader.upload(
            caminho,
            public_id="blogger-automation/teste-conexao-cloudinary",
            overwrite=True,
            resource_type="image",
        )

        url = resultado.get("secure_url")

        if not url:
            raise RuntimeError("Cloudinary não retornou secure_url.")

        print("")
        print("==========================================")
        print("UPLOAD CLOUDINARY: OK")
        print(f"URL PÚBLICA: {url}")
        print("==========================================")
        print("")
        print("Nenhum conteúdo foi enviado ao Blogger.")

    finally:
        if os.path.exists(caminho):
            os.remove(caminho)


if __name__ == "__main__":
    testar_cloudinary()
