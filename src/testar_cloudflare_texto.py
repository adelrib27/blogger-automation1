import os
import re
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
                    "Você é um redator editorial brasileiro "
                    "especializado em SEO para blogs de Casa e "
                    "Decoração. Escreva sempre em português do Brasil. "
                    "Produza conteúdo útil, natural e original. "
                    "Não invente características, benefícios técnicos, "
                    "certificações ou resultados que não tenham sido "
                    "fornecidos. Não invente preços ou promoções."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "max_tokens": 4000,
        "temperature": 0.65,
    }

    print("Modelo:", MODEL)
    print("Enviando solicitação à Cloudflare...")

    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=180,
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
            + response.text
        )

    resultado = dados.get("result", {})
    texto = resultado.get("response")

    if not texto:
        raise RuntimeError(
            "A Cloudflare respondeu, mas nenhum texto "
            "foi encontrado em result.response."
        )

    return texto.strip()


def contar_palavras_html(texto):
    texto_sem_tags = re.sub(
        r"<[^>]+>",
        " ",
        texto,
    )

    palavras = re.findall(
        r"\b[\wÀ-ÿ'-]+\b",
        texto_sem_tags,
        flags=re.UNICODE,
    )

    return len(palavras)


def executar_teste():
    print()
    print("==========================================")
    print("TESTE — ARTIGO COMPLETO COM CLOUDFLARE")
    print("NENHUM CONTEÚDO SERÁ ENVIADO AO BLOGGER")
    print("==========================================")
    print()

    titulo = (
        "Como organizar a cozinha com potes "
        "para alimentos com travas laterais"
    )

    palavra_chave = (
        "potes para alimentos com travas laterais"
    )

    categoria = "Organização de Cozinha"

    produto = (
        "Kit de Potes para Alimentos 800ml "
        "com Travas Laterais"
    )

    prompt = f"""
Escreva um artigo editorial completo para um blog brasileiro
de Casa e Decoração.

TÍTULO:
{titulo}

PALAVRA-CHAVE PRINCIPAL:
{palavra_chave}

CATEGORIA:
{categoria}

PRODUTO DISPONÍVEL PARA INTEGRAÇÃO:
{produto}

INSTRUÇÕES EDITORIAIS:

- Escreva entre 800 e 1000 palavras.
- Responda à intenção de busca antes de tentar vender qualquer coisa.
- O artigo deve ser útil mesmo para quem não comprar o produto.
- Use introdução curta e objetiva.
- Use pelo menos 4 subtítulos H2.
- Desenvolva parágrafos naturais e fáceis de ler.
- Integre o produto de forma contextual e discreta.
- Não transforme o artigo em uma página de vendas.
- Não invente características do produto.
- As únicas características confirmadas são:
  kit de potes, capacidade de 800ml e travas laterais.
- Não afirme que o produto é hermético.
- Não afirme que é livre de BPA.
- Não afirme que pode ir ao freezer,
  micro-ondas ou lava-louças.
- Não invente material, quantidade de peças,
  resistência, garantia ou certificações.
- Não invente preço, desconto ou promoção.
- Não faça alegações médicas ou de saúde.
- Evite promessas absolutas.
- Não invente links.
- Não inclua CTA de compra.
- Não inclua conclusão genérica chamada
  "Conclusão".
- Use a palavra-chave principal naturalmente,
  sem repetição forçada.

FORMATO:

Retorne somente o HTML do corpo do artigo.

Use apenas estas tags:
<p>
<h2>
<strong>
<ul>
<li>

Não use:
<html>
<head>
<body>
<h1>
Markdown
blocos de código

O primeiro conteúdo deve ser um parágrafo <p>.
"""

    artigo = gerar_texto(prompt)

    print()
    print("==========================================")
    print("ARTIGO GERADO")
    print("==========================================")
    print()
    print(artigo)
    print()

    total_palavras = contar_palavras_html(artigo)
    total_h2 = len(
        re.findall(
            r"<h2\b",
            artigo,
            flags=re.IGNORECASE,
        )
    )

    palavra_chave_presente = (
        palavra_chave.lower()
        in artigo.lower()
    )

    produto_presente = (
        "800ml" in artigo.lower()
        and "travas laterais" in artigo.lower()
    )

    tags_proibidas = [
        "<html",
        "<head",
        "<body",
        "<h1",
        "```",
    ]

    proibidas_encontradas = [
        tag
        for tag in tags_proibidas
        if tag.lower() in artigo.lower()
    ]

    alegacoes_nao_confirmadas = [
        "livre de bpa",
        "sem bpa",
        "micro-ondas",
        "microondas",
        "lava-louças",
        "lava louças",
        "freezer",
        "hermético",
        "hermetico",
    ]

    alegacoes_encontradas = [
        termo
        for termo in alegacoes_nao_confirmadas
        if termo in artigo.lower()
    ]

    print()
    print("==========================================")
    print("VALIDAÇÃO AUTOMÁTICA")
    print("==========================================")
    print()

    print("Palavras:", total_palavras)
    print("H2:", total_h2)
    print(
        "Palavra-chave presente:",
        palavra_chave_presente,
    )
    print(
        "Produto integrado:",
        produto_presente,
    )
    print(
        "Tags proibidas:",
        proibidas_encontradas,
    )
    print(
        "Alegações não confirmadas:",
        alegacoes_encontradas,
    )

    erros = []

    if total_palavras < 800:
        erros.append(
            f"Artigo curto: {total_palavras} palavras."
        )

    if total_palavras > 1100:
        erros.append(
            f"Artigo longo demais: {total_palavras} palavras."
        )

    if total_h2 < 4:
        erros.append(
            f"Poucos H2: {total_h2}."
        )

    if not palavra_chave_presente:
        erros.append(
            "Palavra-chave principal ausente."
        )

    if not produto_presente:
        erros.append(
            "Produto não foi integrado corretamente."
        )

    if proibidas_encontradas:
        erros.append(
            "Foram encontradas tags/formatações proibidas."
        )

    if alegacoes_encontradas:
        erros.append(
            "Foram encontradas alegações de produto "
            "não confirmadas."
        )

    if erros:
        print()
        print("==========================================")
        print("TESTE: REPROVADO")
        print("==========================================")

        for erro in erros:
            print("-", erro)

        raise RuntimeError(
            "O artigo não passou na validação."
        )

    print()
    print("==========================================")
    print("TESTE ARTIGO CLOUDFLARE: OK")
    print("==========================================")
    print()
    print(
        "O Qwen gerou um artigo longo em português "
        "e passou nas validações básicas."
    )
    print()
    print(
        "Nenhum conteúdo foi enviado ao Blogger."
    )


if __name__ == "__main__":
    executar_teste()
