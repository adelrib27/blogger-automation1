import os
import re
import requests


ACCOUNT_ID = os.environ.get("CLOUDFLARE_ACCOUNT_ID")
API_TOKEN = os.environ.get("CLOUDFLARE_API_TOKEN")

MODEL = "@cf/qwen/qwen3-30b-a3b-fp8"


def gerar_texto(prompt, max_tokens=2200):
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
                    "Decoração. Escreva conteúdo útil, natural, "
                    "original e em português do Brasil. "
                    "Nesta tarefa você NÃO descreve produtos "
                    "comerciais. Concentre-se somente no conteúdo "
                    "editorial solicitado."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "max_tokens": max_tokens,
        "temperature": 0.55,
    }

    print("Modelo:", MODEL)
    print("Enviando bloco à Cloudflare...")

    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=180,
    )

    print("HTTP:", response.status_code)

    if response.status_code != 200:
        raise RuntimeError(
            "Erro Cloudflare:\n" + response.text
        )

    dados = response.json()

    if not dados.get("success"):
        raise RuntimeError(
            "Cloudflare retornou success=false:\n"
            + response.text
        )

    texto = dados.get("result", {}).get("response")

    if not texto:
        raise RuntimeError(
            "Nenhum texto encontrado em result.response."
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


def limpar_saida(texto):
    texto = texto.strip()

    texto = re.sub(
        r"^```(?:html)?\s*",
        "",
        texto,
        flags=re.IGNORECASE,
    )

    texto = re.sub(
        r"\s*```$",
        "",
        texto,
    )

    return texto.strip()


def executar_teste():
    print()
    print("==========================================")
    print("TESTE 3 — ARQUITETURA HÍBRIDA")
    print("QWEN = EDITORIAL")
    print("PYTHON = PRODUTO")
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

    produto_nome = (
        "Kit de Potes para Alimentos 800ml "
        "com Travas Laterais"
    )

    link_afiliado = (
        "https://vt.tiktok.com/ZS9DVmNxuKAVr-oyWt7/"
    )

    prompt_bloco_1 = f"""
Escreva a PRIMEIRA PARTE de um artigo para o blog
Achados para Casa.

TÍTULO DO ARTIGO:
{titulo}

PALAVRA-CHAVE:
{palavra_chave}

Escreva aproximadamente 450 a 550 palavras.

Esta parte deve conter:

- uma introdução objetiva;
- um H2 sobre planejamento da organização;
- um H2 sobre separação dos alimentos por categorias;
- um H2 sobre organização por frequência de uso;
- exemplos práticos;
- linguagem natural e útil.

REGRA IMPORTANTE:

NÃO mencione marcas, produtos comerciais, kits,
capacidade de recipientes, travas, características
de potes específicos ou links de compra.

Você está escrevendo SOMENTE conteúdo editorial
sobre organização da cozinha.

Use somente:
<p>
<h2>
<strong>
<ul>
<li>

Não use H1, Markdown ou bloco de código.

Retorne somente HTML.
"""

    prompt_bloco_2 = f"""
Escreva a SEGUNDA PARTE do artigo:

"{titulo}"

PALAVRA-CHAVE:
{palavra_chave}

Escreva aproximadamente 400 a 500 palavras.

Não escreva nova introdução.

Desenvolva:

- um H2 sobre aproveitamento dos espaços
  dos armários e prateleiras;
- um H2 sobre identificação e etiquetas;
- um H2 sobre criação de uma rotina de organização;
- revisão periódica dos mantimentos;
- escolha da capacidade dos recipientes de acordo
  com a necessidade de cada pessoa ou família;
- fechamento editorial natural.

REGRA IMPORTANTE:

Fale somente de práticas gerais de organização.

NÃO mencione marcas, produtos comerciais, kits,
capacidade de produtos específicos, travas,
características de potes específicos ou links.

Não use um H2 chamado "Conclusão".

Use somente:
<p>
<h2>
<strong>
<ul>
<li>

Não use H1, Markdown ou bloco de código.

Retorne somente HTML.
"""

    print("ETAPA 1 — GERANDO PRIMEIRO BLOCO")
    bloco_1 = limpar_saida(
        gerar_texto(prompt_bloco_1)
    )

    print()
    print("ETAPA 2 — GERANDO SEGUNDO BLOCO")
    bloco_2 = limpar_saida(
        gerar_texto(prompt_bloco_2)
    )

    print()
    print("ETAPA 3 — BLOCO DO PRODUTO VIA PYTHON")

    # IMPORTANTE:
    # Este bloco NÃO é escrito pela IA.
    # Ele usa somente informações confirmadas.
    bloco_produto = f"""
<h2>Uma opção para integrar à organização</h2>
<p>Na hora de colocar a organização em prática,
uma opção disponível é o
<strong>{produto_nome}</strong>.
As informações confirmadas do item são a capacidade
informada de 800ml e a presença de travas laterais.</p>
<p>Antes de escolher qualquer recipiente, vale
comparar a capacidade informada com a quantidade
de alimento que você pretende organizar e com o
espaço disponível na sua cozinha.</p>
<p><a href="{link_afiliado}"
target="_blank"
rel="nofollow sponsored">Ver o produto</a></p>
""".strip()

    artigo = (
        bloco_1
        + "\n\n"
        + bloco_produto
        + "\n\n"
        + bloco_2
    )

    print("Bloco de produto criado pelo Python: OK")

    print()
    print("==========================================")
    print("ARTIGO FINAL")
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

    link_presente = (
        link_afiliado in artigo
    )

    produto_presente = (
        produto_nome in artigo
    )

    # A IA não deve mencionar fatos comerciais.
    conteudo_ia = (
        bloco_1.lower()
        + "\n"
        + bloco_2.lower()
    )

    termos_comerciais_proibidos_na_ia = [
        "800ml",
        "travas laterais",
        "kit de potes",
        "tiktok.com",
        "link de compra",
        "compre agora",
    ]

    comerciais_encontrados = [
        termo
        for termo in termos_comerciais_proibidos_na_ia
        if termo in conteudo_ia
    ]

    tags_proibidas = [
        "<html",
        "<head",
        "<body",
        "<h1",
        "```",
    ]

    tags_encontradas = [
        termo
        for termo in tags_proibidas
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
        "Produto inserido pelo Python:",
        produto_presente,
    )
    print(
        "Link afiliado exato presente:",
        link_presente,
    )
    print(
        "Termos comerciais escritos pela IA:",
        comerciais_encontrados,
    )
    print(
        "Tags proibidas:",
        tags_encontradas,
    )

    erros = []

    if total_palavras < 800:
        erros.append(
            f"Artigo curto: {total_palavras} palavras."
        )

    if total_palavras > 1250:
        erros.append(
            f"Artigo longo demais: {total_palavras} palavras."
        )

    if total_h2 < 6:
        erros.append(
            f"Poucos H2: {total_h2}."
        )

    if not palavra_chave_presente:
        erros.append(
            "Palavra-chave principal ausente."
        )

    if not produto_presente:
        erros.append(
            "Produto não foi inserido."
        )

    if not link_presente:
        erros.append(
            "Link afiliado exato ausente."
        )

    if comerciais_encontrados:
        erros.append(
            "A IA entrou no bloco comercial: "
            + str(comerciais_encontrados)
        )

    if tags_encontradas:
        erros.append(
            "Foram encontradas tags proibidas."
        )

    if erros:
        print()
        print("==========================================")
        print("TESTE 3: REPROVADO")
        print("==========================================")

        for erro in erros:
            print("-", erro)

        raise RuntimeError(
            "A arquitetura híbrida não passou "
            "na validação."
        )

    print()
    print("==========================================")
    print("TESTE 3 CLOUDFLARE: OK")
    print("==========================================")
    print()
    print(
        "Qwen produziu somente o conteúdo editorial."
    )
    print(
        "Python controlou o produto e o link afiliado."
    )
    print(
        "Nenhum conteúdo foi enviado ao Blogger."
    )


if __name__ == "__main__":
    executar_teste()
