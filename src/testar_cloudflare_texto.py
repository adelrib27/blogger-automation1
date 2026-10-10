import json
import os
import requests


ACCOUNT_ID = os.environ.get("CLOUDFLARE_ACCOUNT_ID")
API_TOKEN = os.environ.get("CLOUDFLARE_API_TOKEN")

MODEL = "@cf/qwen/qwen3-30b-a3b-fp8"


def gerar_texto(prompt):
    if not ACCOUNT_ID:
        raise RuntimeError(
            "CLOUDFLARE_ACCOUNT_ID não configurado."
        )

    if not API_TOKEN:
        raise RuntimeError(
            "CLOUDFLARE_API_TOKEN não configurado."
        )

    url = (
        "https://api.cloudflare.com/client/v4/accounts/"
        f"{ACCOUNT_ID}/ai/run/{MODEL}"
    )

    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "messages": [
            {
                "role": "system",
                "content": (
                    "Você é um especialista brasileiro em SEO, "
                    "conteúdo editorial e blogs sobre Casa e Decoração. "
                    "Responda sempre em português do Brasil. "
                    "Não invente características de produtos."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "max_tokens": 1200,
        "temperature": 0.7,
    }

    print("Modelo:", MODEL)
    print("Enviando solicitação à Cloudflare...")

    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=120,
    )

    print("HTTP:", response.status_code)

    if response.status_code != 200:
        raise RuntimeError(
            "Erro Cloudflare:\n"
            + response.text
        )

    dados = response.json()

    if not dados.get("success"):
        raise RuntimeError(
            "Cloudflare retornou success=false:\n"
            + json.dumps(
                dados,
                ensure_ascii=False,
                indent=2,
            )
        )

    resultado = dados.get("result", {})

    texto = resultado.get("response")

    if not texto:
        raise RuntimeError(
            "A Cloudflare respondeu, mas nenhum texto "
            "foi encontrado em result.response.\n"
            + json.dumps(
                dados,
                ensure_ascii=False,
                indent=2,
            )
        )

    return texto.strip()


def executar_teste():
    print()
    print("==========================================")
    print("TESTE — CLOUDFLARE WORKERS AI TEXTO")
    print("==========================================")
    print()

    produto = (
        "Kit de Potes para Alimentos 800ml "
        "com Travas Laterais"
    )

    prompt = f"""
Crie uma pauta SEO inédita para um artigo de blog.

NICHO:
Casa e Decoração

PRODUTO QUE DEVE SER INTEGRADO NATURALMENTE:
{produto}

A pauta deve resolver uma dúvida ou problema real do leitor.

Não faça uma pauta puramente comercial.
Não invente características além das presentes no nome do produto.
Não mencione preço, desconto ou promoção.

Retorne EXATAMENTE neste formato:

TITULO: título SEO
PALAVRA_CHAVE: palavra-chave principal
CATEGORIA: categoria
INTENCAO: intenção de busca
ANGULO: resumo do ângulo editorial
"""

    texto = gerar_texto(prompt)

    print()
    print("==========================================")
    print("RESPOSTA DO MODELO")
    print("==========================================")
    print()
    print(texto)
    print()

    campos_esperados = [
        "TITULO:",
        "PALAVRA_CHAVE:",
        "CATEGORIA:",
        "INTENCAO:",
        "ANGULO:",
    ]

    faltando = [
        campo
        for campo in campos_esperados
        if campo not in texto
    ]

    if faltando:
        raise RuntimeError(
            "A resposta não seguiu a estrutura esperada. "
            f"Campos ausentes: {faltando}"
        )

    print()
    print("==========================================")
    print("TESTE CLOUDFLARE TEXTO: OK")
    print("==========================================")
    print()
    print("Produto usado:")
    print(produto)
    print()
    print(
        "A Cloudflare conseguiu gerar uma pauta "
        "estruturada em português."
    )


if __name__ == "__main__":
    executar_teste()
