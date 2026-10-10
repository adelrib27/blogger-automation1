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
                    "Decoração. Escreva em português do Brasil. "
                    "Sua prioridade é precisão factual. "
                    "Nunca transforme uma suposição sobre um produto "
                    "em característica, benefício ou capacidade dele. "
                    "Quando uma informação do produto não tiver sido "
                    "fornecida, simplesmente não fale sobre ela."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "max_tokens": 5000,
        "temperature": 0.45,
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
    print("TESTE 2 — ARTIGO BLINDADO COM CLOUDFLARE")
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
Escreva um artigo editorial completo para o blog
Achados para Casa.

TÍTULO:
{titulo}

PALAVRA-CHAVE PRINCIPAL:
{palavra_chave}

CATEGORIA:
{categoria}

PRODUTO:
{produto}

==============================
FATOS CONFIRMADOS DO PRODUTO
==============================

Você conhece SOMENTE estes fatos:

1. É um kit de potes para alimentos.
2. Os potes possuem capacidade informada de 800ml.
3. O nome do produto informa travas laterais.

Esses são os únicos fatos específicos do produto
que podem ser tratados como verdade.

REGRA ABSOLUTA:

Se uma característica não estiver nos três fatos
acima, NÃO atribua essa característica ao produto.

Não tente completar informações usando conhecimento
comum sobre potes semelhantes.

==============================
NÃO INFERIR SOBRE O PRODUTO
==============================

Não diga nem sugira que o produto:

- é hermético;
- veda alimentos;
- conserva alimentos por mais tempo;
- evita vazamentos;
- mantém frescor;
- possui vedação especial;
- é transparente;
- é empilhável;
- facilita empilhamento;
- possui determinado formato;
- possui diferentes tamanhos;
- possui diferentes capacidades;
- possui quantidade específica de peças;
- é livre de BPA;
- possui material específico;
- pode ir ao freezer;
- pode ir ao micro-ondas;
- pode ir à lava-louças;
- suporta determinadas temperaturas;
- é resistente;
- possui certificação;
- possui garantia.

Também NÃO deduza que as travas:

- facilitam a abertura;
- facilitam o fechamento;
- deixam a tampa mais firme;
- impedem que a tampa caia;
- criam vedação;
- evitam abertura acidental.

Você pode mencionar apenas que o nome do produto
informa a presença de travas laterais.

==============================
CONTEÚDO EDITORIAL
==============================

O tema principal do artigo é ORGANIZAÇÃO DA COZINHA.

O produto deve aparecer como exemplo contextual,
e não como assunto exclusivo do artigo.

Desenvolva dicas gerais e úteis sobre:

- planejamento da organização;
- separação dos alimentos por categorias;
- definição de espaços nos armários;
- identificação com etiquetas;
- organização por frequência de uso;
- aproveitamento de prateleiras;
- criação de uma rotina de organização;
- revisão periódica dos mantimentos;
- como escolher capacidades adequadas para
  diferentes necessidades.

Ao apresentar dicas gerais, deixe claro que são
práticas de organização e NÃO características
específicas do produto.

==============================
ESTRUTURA
==============================

Escreva entre 850 e 1000 palavras.

IMPORTANTE:
Não encerre o texto antes de atingir pelo menos
850 palavras.

Use:

- introdução com aproximadamente 100 palavras;
- pelo menos 5 subtítulos H2;
- aproximadamente 130 a 170 palavras de
  desenvolvimento em cada seção principal;
- parágrafos curtos e naturais;
- uma lista útil quando fizer sentido.

O artigo deve responder à intenção de busca
antes de apresentar o produto.

Integre o produto naturalmente em apenas uma
ou duas partes do artigo.

Não transforme o conteúdo em página de vendas.

Não inclua CTA de compra.

Não invente preço, desconto ou promoção.

Não invente links.

Não faça alegações médicas ou de saúde.

Não use um H2 chamado "Conclusão".

Use a palavra-chave principal naturalmente.

==============================
FORMATO DE SAÍDA
==============================

Retorne SOMENTE o HTML do corpo do artigo.

Tags permitidas:

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

O primeiro elemento deve ser <p>.

Antes de responder, faça silenciosamente uma
checagem factual:

"Estou atribuindo ao produto alguma característica
que não aparece nos FATOS CONFIRMADOS?"

Se a resposta for sim, remova essa afirmação.
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

    produto_integrado = (
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
        termo
        for termo in tags_proibidas
        if termo in artigo.lower()
    ]

    alegacoes_proibidas = [
        "hermético",
        "hermetico",
        "livre de bpa",
        "sem bpa",
        "micro-ondas",
        "microondas",
        "lava-louças",
        "lava louças",
        "freezer",
        "transparente",
        "empilhável",
        "empilhavel",
        "facilidade de empilhamento",
        "variedade de tamanhos",
        "diferentes tamanhos",
        "variedade de formatos",
        "diferentes formatos",
        "evita vazamentos",
        "evitar vazamentos",
        "mantém o frescor",
        "mantem o frescor",
        "conserva por mais tempo",
        "vedação especial",
        "vedacao especial",
        "tampa mais firme",
        "tampas mais firmes",
        "impede que a tampa",
        "impedem que as tampas",
        "facilita a abertura",
        "facilitam a abertura",
        "facilita o fechamento",
        "facilitam o fechamento",
    ]

    alegacoes_encontradas = [
        termo
        for termo in alegacoes_proibidas
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
        produto_integrado,
    )

    print(
        "Tags proibidas:",
        proibidas_encontradas,
    )

    print(
        "Alegações proibidas:",
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

    if total_h2 < 5:
        erros.append(
            f"Poucos H2: {total_h2}."
        )

    if not palavra_chave_presente:
        erros.append(
            "Palavra-chave principal ausente."
        )

    if not produto_integrado:
        erros.append(
            "Produto não foi integrado corretamente."
        )

    if proibidas_encontradas:
        erros.append(
            "Foram encontradas tags ou "
            "formatações proibidas."
        )

    if alegacoes_encontradas:
        erros.append(
            "Foram encontradas características "
            "não confirmadas do produto."
        )

    if erros:
        print()
        print("==========================================")
        print("TESTE 2: REPROVADO")
        print("==========================================")

        for erro in erros:
            print("-", erro)

        raise RuntimeError(
            "O artigo não passou na validação."
        )

    print()
    print("==========================================")
    print("TESTE 2 CLOUDFLARE: OK")
    print("==========================================")
    print()

    print(
        "O artigo atingiu o tamanho mínimo, "
        "manteve a estrutura e passou pela "
        "blindagem automática de produto."
    )

    print()
    print(
        "Nenhum conteúdo foi enviado ao Blogger."
    )


if __name__ == "__main__":
    executar_teste()
