import os
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
        raise RuntimeError("CLOUDFLARE_ACCOUNT_ID não encontrado nos Secrets.")

    if not api_token:
        raise RuntimeError("CLOUDFLARE_API_TOKEN não encontrado nos Secrets.")

    url = (
        f"https://api.cloudflare.com/client/v4/accounts/"
        f"{account_id}/ai/run/{MODELO}"
    )

    headers = {
        "Authorization": f"Bearer {api_token}",
    }

    # O FLUX.2 Klein recebe os dados como multipart/form-data.
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
    print(f"CONTENT-TYPE: {resposta.headers.get('content-type', '')}")

    if resposta.status_code != 200:
        print("")
        print("RESPOSTA DA CLOUDFLARE:")
        print(resposta.text[:4000])
        raise RuntimeError(
            f"Cloudflare retornou HTTP {resposta.status_code}."
        )

    content_type = resposta.headers.get("content-type", "").lower()

    if not content_type.startswith("image/"):
        print("")
        print("A resposta não veio diretamente como imagem.")
        print("Primeiros bytes/texto da resposta:")
        print(resposta.text[:4000])
        raise RuntimeError(
            f"Formato inesperado retornado pela Cloudflare: {content_type}"
        )

    extensao = ".png"

    if "jpeg" in content_type or "jpg" in content_type:
        extensao = ".jpg"
    elif "webp" in content_type:
        extensao = ".webp"

    pasta = Path("data/imagens")
    pasta.mkdir(parents=True, exist_ok=True)

    caminho = pasta / f"teste-cloudflare-flux{extensao}"
    caminho.write_bytes(resposta.content)

    tamanho = caminho.stat().st_size

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
