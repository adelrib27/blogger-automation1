import os
import re
import requests


ACCOUNT_ID = os.environ.get("CLOUDFLARE_ACCOUNT_ID")
API_TOKEN = os.environ.get("CLOUDFLARE_API_TOKEN")

MODEL = "@cf/qwen/qwen3-30b-a3b-fp8"


def gerar_texto(prompt, max_tokens=2400):
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
                    "especializado em conteúdo útil para blogs "
                    "de Casa e Decoração. "
                    "Escreva em português do Brasil. "
                    "Nesta tarefa você escreve somente conteúdo "
                    "editorial geral. Não descreva, recomende ou "
                    "avalie produtos comerciais específicos."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "max_tokens": max_tokens,
        "temperature": 0.50,
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


def validar_html_basico(html):
    erros = []

    tags_proibidas = [
        "<html",
        "<head",
        "<body",
        "<h1",
        "```",
    ]

    for tag in tags_proibidas:
        if tag in html.lower():
            erros.append(
                f"Tag/formatação proibida: {tag}"
            )

    # H2 não pode estar dentro de um parágrafo.
    if re.search(
        r"<p[^>]*>.*?<h2\b",
        html,
        flags=re.IGNORECASE | re.DOTALL,
    ):
        erros.append(
            "Existe H2 dentro de um parágrafo."
        )

    # Verificação simples de abertura/fechamento.
    for tag in ["p", "h2", "ul", "li", "strong"]:
        aberturas = len(
            re.findall(
                rf"<{tag}\b[^>]*>",
                html,
                flags=re.IGNORECASE,
            )
        )

        fechamentos = len(
            re.findall(
                rf"</{tag}>",
                html,
                flags=re.IGNORECASE,
            )
        )

        if aberturas != fechamentos:
            erros.append(
                f"Tag {tag} desbalanceada: "
                f"{aberturas} abertura(s), "
                f"{fechamentos} fechamento(s)."
            )

    return erros


def executar_teste():
    print()
    print("==========================================")
    print("TESTE 4 — SEPARAÇÃO EDITORIAL TOTAL")
    print("QWEN NÃO RECEBE DADOS DO PRODUTO")
    print("PYTHON CONTROLA PRODUTO + SEO COMERCIAL")
    print("NENHUM CONTEÚDO SERÁ ENVIADO AO BLOGGER")
    print("==========================================")
    print()

    # Tema que a IA pode conhecer.
    tema_editorial = (
        "como organizar alimentos e mantimentos "
        "na cozinha de forma prática"
    )

    # Dados comerciais que ficam SOMENTE no Python.
    palavra_chave_comercial = (
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
Escreva a PRIMEIRA PARTE de um artigo editorial
sobre:

{tema_editorial}

Escreva aproximadamente 450 a 550 palavras.

Inclua:

- introdução curta;
- um H2 sobre planejamento da organização;
- um H2 sobre separação por categorias;
- um H2 sobre frequência de uso;
- exemplos cotidianos de organização.

Fale somente sobre métodos gerais de organização.

Não diga que recipientes conservam alimentos,
protegem ingredientes, evitam contaminação,
evitam desperdício ou aumentam durabilidade.

Não fale sobre propriedades de tampas,
vedação, materiais ou conservação.

Não mencione:
- marcas;
- produtos específicos;
- kits comerciais;
- capacidade em ml;
- travas laterais;
- links;
- compras;
- promoções.

FORMATO OBRIGATÓRIO:

Cada H2 deve ficar fora dos parágrafos.

CORRETO:
<h2>Título</h2>
<p>Texto...</p>

PROIBIDO:
<p><h2>Título</h2>Texto...</p>

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
Escreva a SEGUNDA PARTE do mesmo artigo editorial
sobre:

{tema_editorial}

Escreva aproximadamente 400 a 500 palavras.

Não faça uma nova introdução.

Inclua:

- H2 sobre armários e prateleiras;
- H2 sobre etiquetas e identificação;
- H2 sobre rotina de organização;
- revisão periódica dos mantimentos;
- escolha geral do tamanho dos recipientes
  conforme a necessidade e o espaço;
- fechamento natural, sem H2 chamado Conclusão.

Fale somente sobre organização doméstica geral.

Não atribua a recipientes benefícios de
conservação, higiene, segurança alimentar,
vedação ou durabilidade.

Não mencione:
- marcas;
- produtos específicos;
- kits comerciais;
- capacidade em ml;
- travas laterais;
- links;
- compras;
- promoções.

FORMATO OBRIGATÓRIO:

Cada H2 deve ficar fora dos parágrafos.

CORRETO:
<h2>Título</h2>
<p>Texto...</p>

PROIBIDO:
<p><h2>Título</h2>Texto...</p>

Use somente:
<p>
<h2>
<strong>
<ul>
<li>

Não use H1, Markdown ou bloco de código.

Retorne somente HTML.
"""

    print("ETAPA 1 — CONTEÚDO EDITORIAL 1")
    bloco_1 = limpar_saida(
        gerar_texto(prompt_bloco_1)
    )

    print()
    print("ETAPA 2 — CONTEÚDO EDITORIAL 2")
    bloco_2 = limpar_saida(
        gerar_texto(prompt_bloco_2)
    )

    print()
    print("ETAPA 3 — BLOCO CONTROLADO PELO PYTHON")

    bloco_produto = f"""
<h2>Potes para alimentos na organização da cozinha</h2>
<p>Entre as opções disponíveis para organizar
mantimentos está o
<strong>{produto_nome}</strong>.
De acordo com as informações cadastradas para
este item, os potes possuem capacidade informada
de 800ml e travas laterais.</p>
<p>Ao avaliar esse tipo de item, compare a
capacidade informada com a quantidade que você
costuma organizar e com o espaço disponível
no armário ou na prateleira.</p>
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

    print("Produto inserido sem participação da IA: OK")

    print()
    print("ETAPA 4 — SEO COMERCIAL VIA PYTHON")

    # A IA editorial não precisa conhecer a
    # palavra-chave comercial.
    # O Python garante uma ocorrência exata e
    # controlada no artigo.
    if (
        palavra_chave_comercial.lower()
        not in artigo.lower()
    ):
        raise RuntimeError(
            "A palavra-chave comercial não apareceu "
            "no bloco controlado pelo Python."
        )

    print("Palavra-chave comercial controlada: OK")

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

    conteudo_ia = (
        bloco_1.lower()
        + "\n"
        + bloco_2.lower()
    )

    # Nenhum destes dados foi fornecido à IA.
    dados_comerciais = [
        "800ml",
        "travas laterais",
        "kit de potes para alimentos",
        "tiktok.com",
        "ver o produto",
        "compre agora",
    ]

    vazamentos_comerciais = [
        termo
        for termo in dados_comerciais
        if termo in conteudo_ia
    ]

    # Expressões editoriais que preferimos bloquear
    # neste tipo de conteúdo.
    alegacoes_sensiveis = [
        "evitar contaminação",
        "evita contaminação",
        "evitando contaminação",
        "contaminação cruzada",
        "preservar a qualidade",
        "preserva a qualidade",
        "conservar por mais tempo",
        "conserva por mais tempo",
        "manter fresco por mais tempo",
        "mantém fresco por mais tempo",
        "proteger ingredientes",
        "protege ingredientes",
    ]

    alegacoes_encontradas = [
        termo
        for termo in alegacoes_sensiveis
        if termo in conteudo_ia
    ]

    erros_html = validar_html_basico(artigo)

    produto_presente = (
        produto_nome in artigo
    )

    link_presente = (
        link_afiliado in artigo
    )

    palavra_chave_presente = (
        palavra_chave_comercial.lower()
        in artigo.lower()
    )

    print()
    print("==========================================")
    print("VALIDAÇÃO AUTOMÁTICA")
    print("==========================================")
    print()

    print("Palavras:", total_palavras)
    print("H2:", total_h2)

    print(
        "Palavra-chave comercial presente:",
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
        "Dados comerciais vazados para IA:",
        vazamentos_comerciais,
    )

    print(
        "Alegações editoriais sensíveis:",
        alegacoes_encontradas,
    )

    print(
        "Erros de HTML:",
        erros_html,
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
            "Palavra-chave comercial ausente."
        )

    if not produto_presente:
        erros.append(
            "Produto não foi inserido pelo Python."
        )

    if not link_presente:
        erros.append(
            "Link afiliado exato ausente."
        )

    if vazamentos_comerciais:
        erros.append(
            "A IA produziu dados comerciais: "
            + str(vazamentos_comerciais)
        )

    if alegacoes_encontradas:
        erros.append(
            "A IA produziu alegações editoriais "
            "que preferimos bloquear: "
            + str(alegacoes_encontradas)
        )

    if erros_html:
        erros.append(
            "HTML inválido: "
            + str(erros_html)
        )

    if erros:
        print()
        print("==========================================")
        print("TESTE 4: REPROVADO")
        print("==========================================")

        for erro in erros:
            print("-", erro)

        raise RuntimeError(
            "A separação editorial total não passou."
        )

    print()
    print("==========================================")
    print("TESTE 4 CLOUDFLARE: OK")
    print("==========================================")
    print()
    print(
        "Qwen ficou isolado no conteúdo editorial."
    )
    print(
        "Python controlou palavra-chave comercial, "
        "produto e link afiliado."
    )
    print(
        "Estrutura HTML validada."
    )
    print(
        "Nenhum conteúdo foi enviado ao Blogger."
    )


if __name__ == "__main__":
    executar_teste()
