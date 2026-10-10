import os
import base64
from pathlib import Path
from io import BytesIO

import requests
import cloudinary
import cloudinary.uploader
from PIL import Image


MODELO = "@cf/black-forest-labs/flux-2-klein-4b"

# Formato final desejado para a imagem de destaque do Blogger.
LARGURA_FINAL = 1280
ALTURA_FINAL = 720

PROMPT = """
Fotografia editorial ultra-realista de uma sala de estar brasileira
moderna, aconchegante e elegante. Sofá confortável em tons neutros,
almofadas decorativas, manta com textura natural, mesa lateral,
iluminação indireta quente e decoração contemporânea.

IMPORTANTE: criar a cena pensando em composição horizontal ampla,
com o assunto principal concentrado na região central da imagem.
Manter espaço visual suficiente nas laterais e evitar elementos
importantes muito próximos das bordas.

Ambiente realista e habitável, luz natural entrando pela janela,
composição apropriada para imagem de destaque de um artigo de blog
sobre casa e decoração.

Fotografia profissional de interiores, materiais e tecidos realistas,
sombras naturais, excelente iluminação, alto nível de detalhes.

Sem pessoas, sem texto, sem letras, sem logotipos, sem marcas,
sem marca-d'água, sem interface, sem molduras.
"""


def gerar_imagem_cloudflare():
    account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID")
    api_token = os.getenv("CLOUDFLARE_API_TOKEN")

    if not account_id:
        raise RuntimeError(
            "CLOUDFLARE_ACCOUNT_ID não encontrado nos Secrets."
        )

    if not api_token:
        raise RuntimeError(
            "CLOUDFLARE_API_TOKEN não encontrado nos Secrets."
        )

    url = (
        f"https://api.cloudflare.com/client/v4/accounts/"
        f"{account_id}/ai/run/{MODELO}"
    )

    headers = {
        "Authorization": f"Bearer {api_token}",
    }

    arquivos = {
        "prompt": (None, PROMPT.strip()),
    }

    print("")
    print("==========================================")
    print("ETAPA 1 — GERAR IMAGEM NO CLOUDFLARE")
    print(f"MODELO: {MODELO}")
    print("==========================================")

    resposta = requests.post(
        url,
        headers=headers,
        files=arquivos,
        timeout=180,
    )

    print(f"HTTP STATUS: {resposta.status_code}")
    print(
        "CONTENT-TYPE: "
        f"{resposta.headers.get('content-type', '')}"
    )

    if resposta.status_code != 200:
        print("")
        print("RESPOSTA DA CLOUDFLARE:")
        print(resposta.text[:4000])

        raise RuntimeError(
            f"Cloudflare retornou HTTP {resposta.status_code}."
        )

    content_type = resposta.headers.get(
        "content-type", ""
    ).lower()

    dados_imagem = None

    if content_type.startswith("image/"):
        dados_imagem = resposta.content

    elif "application/json" in content_type:
        dados = resposta.json()

        if not dados.get("success", False):
            raise RuntimeError(
                f"Cloudflare informou falha: {dados}"
            )

        resultado = dados.get("result") or {}
        imagem_base64 = resultado.get("image")

        if not imagem_base64:
            raise RuntimeError(
                "Cloudflare retornou JSON, mas não encontrou "
                "result.image."
            )

        try:
            dados_imagem = base64.b64decode(
                imagem_base64,
                validate=True,
            )
        except Exception as erro:
            raise RuntimeError(
                "Não foi possível decodificar a imagem Base64."
            ) from erro

    else:
        raise RuntimeError(
            "Formato inesperado retornado pela Cloudflare: "
            f"{content_type}"
        )

    if not dados_imagem:
        raise RuntimeError(
            "A Cloudflare não retornou dados de imagem."
        )

    pasta = Path("data/imagens")
    pasta.mkdir(parents=True, exist_ok=True)

    caminho_original = pasta / "teste-cloudflare-original.jpg"

    with Image.open(BytesIO(dados_imagem)) as imagem:
        imagem = imagem.convert("RGB")

        print("")
        print("GERAÇÃO CLOUDFLARE: OK")
        print(
            f"TAMANHO ORIGINAL: "
            f"{imagem.width}x{imagem.height}"
        )

        imagem.save(
            caminho_original,
            format="JPEG",
            quality=92,
            optimize=True,
        )

    return caminho_original


def converter_para_16_9(caminho_original):
    print("")
    print("==========================================")
    print("ETAPA 2 — CONVERTER PARA 16:9")
    print("==========================================")

    caminho_final = Path(
        "data/imagens/teste-cloudflare-flux-16x9.jpg"
    )

    with Image.open(caminho_original) as imagem:
        imagem = imagem.convert("RGB")

        largura = imagem.width
        altura = imagem.height

        proporcao_atual = largura / altura
        proporcao_desejada = LARGURA_FINAL / ALTURA_FINAL

        if proporcao_atual > proporcao_desejada:
            nova_largura = int(
                altura * proporcao_desejada
            )

            esquerda = (largura - nova_largura) // 2

            caixa = (
                esquerda,
                0,
                esquerda + nova_largura,
                altura,
            )

        else:
            nova_altura = int(
                largura / proporcao_desejada
            )

            topo = (altura - nova_altura) // 2

            caixa = (
                0,
                topo,
                largura,
                topo + nova_altura,
            )

        imagem = imagem.crop(caixa)

        imagem = imagem.resize(
            (LARGURA_FINAL, ALTURA_FINAL),
            Image.Resampling.LANCZOS,
        )

        imagem.save(
            caminho_final,
            format="JPEG",
            quality=92,
            optimize=True,
        )

    tamanho = caminho_final.stat().st_size

    if tamanho < 1000:
        raise RuntimeError(
            f"Arquivo final parece inválido: {tamanho} bytes."
        )

    print("")
    print("CONVERSÃO 16:9: OK")
    print(
        f"DIMENSÕES FINAIS: "
        f"{LARGURA_FINAL}x{ALTURA_FINAL}"
    )
    print(f"ARQUIVO FINAL: {caminho_final}")
    print(f"TAMANHO: {tamanho} bytes")

    return caminho_final


def enviar_para_cloudinary(caminho):
    cloudinary_url = os.getenv("CLOUDINARY_URL")

    if not cloudinary_url:
        raise RuntimeError(
            "CLOUDINARY_URL não encontrado nos Secrets."
        )

    cloudinary.config(secure=True)

    print("")
    print("==========================================")
    print("ETAPA 3 — ENVIAR IMAGEM AO CLOUDINARY")
    print("==========================================")

    resultado = cloudinary.uploader.upload(
        str(caminho),
        public_id=(
            "blogger-automation/"
            "teste-cloudflare-flux-16x9"
        ),
        overwrite=True,
        resource_type="image",
    )

    url_publica = resultado.get("secure_url")

    if not url_publica:
        raise RuntimeError(
            "Cloudinary não retornou secure_url."
        )

    print("")
    print("UPLOAD CLOUDINARY: OK")
    print(f"URL PÚBLICA: {url_publica}")

    return url_publica


def executar_teste():
    print("")
    print("==========================================")
    print("TESTE ISOLADO — IMAGEM 16:9")
    print("Cloudflare FLUX -> 16:9 -> Cloudinary")
    print("Nenhum conteúdo será enviado ao Blogger.")
    print("==========================================")

    caminho_original = gerar_imagem_cloudflare()

    caminho_final = converter_para_16_9(
        caminho_original
    )

    url_publica = enviar_para_cloudinary(
        caminho_final
    )

    print("")
    print("==========================================")
    print("TESTE COMPLETO: OK")
    print("FLUX GEROU A IMAGEM: OK")
    print("CONVERSÃO PARA 16:9: OK")
    print("CLOUDINARY RECEBEU A IMAGEM: OK")
    print(
        f"DIMENSÕES FINAIS: "
        f"{LARGURA_FINAL}x{ALTURA_FINAL}"
    )
    print(f"URL FINAL: {url_publica}")
    print("==========================================")
    print("")
    print("Nenhum conteúdo foi enviado ao Blogger.")


if __name__ == "__main__":
    executar_teste()
