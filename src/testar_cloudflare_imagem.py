import os
import base64
from pathlib import Path

import requests


MODELO = "@cf/black-forest-labs/flux-2-klein-4b"

PROMPT = """
Fotografia editorial ultra-realista de uma sala de estar brasileira
moderna, aconchegante e elegante. Sofá confortável em tons neutros,
almofadas decorativas, manta com textura natural, mesa lateral,
iluminação indireta quente e decoração contemporânea.

Ambiente realista e habitável, luz natural entrando pela janela,
composição horizontal apropriada para imagem de destaque de um artigo
de blog sobre casa e decoração.

Fotografia profissional de interiores, materiais e tecidos realistas,
sombras naturais, excelente iluminação, alto nível de detalhes.

Sem pessoas, sem texto, sem letras, sem logotipos, sem marcas,
sem marca-d'água, sem interface, sem molduras.
"""


def testar_cloudflare():
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
    print("TESTE ISOLADO — CLOUDFLARE WORKERS AI")
    print(f"MODELO: {MODELO}")
    print("Nenhum conteúdo será enviado ao Blogger.")
    print("==========================================")
    print("")

    resposta = requests.post(
        url,
        headers=headers,
        files=arquivos,
        timeout=180,
    )

    print(f"HTTP STATUS: {resposta.status_code}")
    print(
        f"CONTENT-TYPE: "
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
    extensao = ".jpg"

    # Caso a API retorne a imagem diretamente.
    if content_type.startswith("image/"):
        dados_imagem = resposta.content

        if "png" in content_type:
            extensao = ".png"
        elif "webp" in content_type:
            extensao = ".webp"
        else:
            extensao = ".jpg"

    # FLUX.2 Klein atualmente pode retornar JSON
    # com a imagem codificada em Base64.
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

        # Detecta o formato pelos primeiros bytes.
        if dados_imagem.startswith(b"\x89PNG\r\n\x1a\n"):
            extensao = ".png"
        elif dados_imagem.startswith(b"\xff\xd8\xff"):
            extensao = ".jpg"
        elif dados_imagem.startswith(b"RIFF") and (
            b"WEBP" in dados_imagem[:16]
        ):
            extensao = ".webp"
        else:
            extensao = ".jpg"

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

    caminho = pasta / (
        f"teste-cloudflare-flux{extensao}"
    )

    caminho.write_bytes(dados_imagem)

    tamanho = caminho.stat().st_size

    if tamanho < 1000:
        raise RuntimeError(
            f"Arquivo gerado parece inválido: {tamanho} bytes."
        )

    print("")
    print("==========================================")
    print("GERAÇÃO CLOUDFLARE: OK")
    print(f"ARQUIVO: {caminho}")
    print(f"TAMANHO: {tamanho} bytes")
    print("==========================================")
    print("")
    print("Nenhum conteúdo foi enviado ao Blogger.")


if __name__ == "__main__":
    testar_cloudflare()
