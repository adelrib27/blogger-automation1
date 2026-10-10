import html
import os
import re
import time
import unicodedata

import requests


# ============================================================
# MODELO CLOUDFLARE PARA GERAÇÃO DE ARTIGOS
# ============================================================

MODELO_ARTIGO = "@cf/qwen/qwen3-30b-a3b-fp8"


MARCADOR_PRODUTO_PRINCIPAL = (
    "[[PRODUTO_PRINCIPAL]]"
)


def limpar_texto(texto):
    """
    Remove espaços desnecessários e normaliza o texto.
    """

    if not texto:
        return ""

    texto = str(texto).strip()

    texto = re.sub(
        r"\s+",
        " ",
        texto,
    )

    return texto


def criar_introducao(
    titulo,
    palavra_chave,
):
    """
    Cria uma introdução de segurança caso
    a IA não esteja disponível.
    """

    titulo = limpar_texto(
        titulo
    )

    palavra_chave = limpar_texto(
        palavra_chave
    )

    return (
        f"Se você está pesquisando sobre "
        f"{palavra_chave}, este guia reúne "
        "informações práticas para ajudar você "
        "a entender melhor o assunto e encontrar "
        "soluções adequadas para sua casa."
    )


def limpar_html_ia(
    conteudo,
):
    """
    Faz uma limpeza básica na resposta da IA
    sem alterar a estrutura útil do artigo.

    O marcador do produto principal é preservado.
    """

    if not conteudo:
        return ""

    conteudo = conteudo.strip()

    conteudo = re.sub(
        r"^```(?:html)?\s*",
        "",
        conteudo,
        flags=re.IGNORECASE,
    )

    conteudo = re.sub(
        r"\s*```$",
        "",
        conteudo,
    )

    conteudo = re.sub(
        r"</?(?:html|head|body)[^>]*>",
        "",
        conteudo,
        flags=re.IGNORECASE,
    )

    conteudo = re.sub(
        r"<h1[^>]*>.*?</h1>",
        "",
        conteudo,
        flags=(
            re.IGNORECASE
            | re.DOTALL
        ),
    )

    return conteudo.strip()


def obter_config_cloudflare():
    """
    Obtém as credenciais do Cloudflare Workers AI.
    """

    account_id = os.getenv(
        "CLOUDFLARE_ACCOUNT_ID"
    )

    api_token = os.getenv(
        "CLOUDFLARE_API_TOKEN"
    )

    if not account_id:
        raise RuntimeError(
            "CLOUDFLARE_ACCOUNT_ID não encontrada."
        )

    if not api_token:
        raise RuntimeError(
            "CLOUDFLARE_API_TOKEN não encontrada."
        )

    return account_id, api_token


def extrair_texto_cloudflare(dados):
    """
    Aceita os formatos de resposta já observados
    no Workers AI, incluindo result.response e
    respostas no formato choices.
    """

    if not isinstance(dados, dict):
        return ""

    resultado = dados.get("result")

    if isinstance(resultado, dict):
        for campo in (
            "response",
            "text",
            "output_text",
        ):
            valor = resultado.get(campo)

            if (
                isinstance(valor, str)
                and valor.strip()
            ):
                return valor.strip()

        choices = resultado.get("choices")

        if isinstance(choices, list):
            for escolha in choices:
                if not isinstance(
                    escolha,
                    dict,
                ):
                    continue

                mensagem = escolha.get(
                    "message"
                )

                if isinstance(
                    mensagem,
                    dict,
                ):
                    conteudo = mensagem.get(
                        "content"
                    )

                    if (
                        isinstance(conteudo, str)
                        and conteudo.strip()
                    ):
                        return conteudo.strip()

                texto = escolha.get("text")

                if (
                    isinstance(texto, str)
                    and texto.strip()
                ):
                    return texto.strip()

    if (
        isinstance(resultado, str)
        and resultado.strip()
    ):
        return resultado.strip()

    choices = dados.get("choices")

    if isinstance(choices, list):
        for escolha in choices:
            if not isinstance(escolha, dict):
                continue

            mensagem = escolha.get("message")

            if isinstance(mensagem, dict):
                conteudo = mensagem.get(
                    "content"
                )

                if (
                    isinstance(conteudo, str)
                    and conteudo.strip()
                ):
                    return conteudo.strip()

            texto = escolha.get("text")

            if (
                isinstance(texto, str)
                and texto.strip()
            ):
                return texto.strip()

    return ""


def gerar_com_cloudflare(prompt):
    """
    Produz o conteúdo editorial usando Qwen
    no Cloudflare Workers AI.
    """

    account_id, api_token = (
        obter_config_cloudflare()
    )

    modelo = MODELO_ARTIGO

    url = (
        "https://api.cloudflare.com/client/v4/accounts/"
        f"{account_id}/ai/run/{modelo}"
    )

    headers = {
        "Authorization": (
            f"Bearer {api_token}"
        ),
        "Content-Type": "application/json",
    }

    payload = {
        "messages": [
            {
                "role": "system",
                "content": (
                    "Você é um redator editorial "
                    "brasileiro especializado em "
                    "conteúdo útil para blogs de Casa "
                    "e Decoração. Escreva somente o "
                    "conteúdo editorial solicitado, "
                    "em HTML permitido, sem Markdown."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "max_tokens": 5000,
        "temperature": 0.50,
    }

    tentativas = 3
    esperas = [5, 15]

    for tentativa in range(
        1,
        tentativas + 1,
    ):
        try:
            print(
                f"\nModelo de artigo: {modelo}"
            )

            print(
                f"Tentativa {tentativa}/"
                f"{tentativas}..."
            )

            resposta = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=180,
            )

            print(
                "HTTP Cloudflare:",
                resposta.status_code,
            )

            if resposta.status_code != 200:
                detalhe = resposta.text[:1000]

                if resposta.status_code in (
                    429,
                    500,
                    502,
                    503,
                    504,
                ):
                    raise RuntimeError(
                        "ERRO_TEMPORARIO_CLOUDFLARE: "
                        f"HTTP {resposta.status_code}: "
                        f"{detalhe}"
                    )

                raise RuntimeError(
                    "Erro não recuperável no "
                    "Cloudflare Workers AI. "
                    f"HTTP {resposta.status_code}: "
                    f"{detalhe}"
                )

            dados = resposta.json()

            conteudo = (
                extrair_texto_cloudflare(
                    dados
                )
            )

            if not conteudo:
                raise RuntimeError(
                    "RESPOSTA_ESTRUTURAL: "
                    "Cloudflare retornou uma "
                    "resposta sem conteúdo."
                )

            conteudo = limpar_html_ia(
                conteudo
            )

            if not conteudo:
                raise RuntimeError(
                    "RESPOSTA_ESTRUTURAL: "
                    "o conteúdo ficou vazio "
                    "após a limpeza."
                )

            print(
                "Artigo editorial recebido "
                "com sucesso da Cloudflare/Qwen."
            )

            return conteudo

        except Exception as erro:
            print(
                "Erro na geração Cloudflare/Qwen, "
                f"tentativa {tentativa}/"
                f"{tentativas}: {erro}"
            )

            mensagem = str(erro)

            recuperavel = (
                "ERRO_TEMPORARIO_CLOUDFLARE"
                in mensagem
                or "RESPOSTA_ESTRUTURAL"
                in mensagem
                or isinstance(
                    erro,
                    requests.Timeout,
                )
                or isinstance(
                    erro,
                    requests.ConnectionError,
                )
            )

            if not recuperavel:
                raise

            if tentativa >= tentativas:
                raise

            espera = esperas[
                tentativa - 1
            ]

            print(
                f"Aguardando {espera} segundos "
                "antes de tentar novamente..."
            )

            time.sleep(espera)

    raise RuntimeError(
        "Cloudflare/Qwen não conseguiu "
        "gerar o artigo."
    )


def criar_prompt_artigo(
    titulo,
    palavra_chave,
    categoria,
    produto_principal="",
):
    """
    Monta o prompt editorial.

    O parâmetro produto_principal é mantido apenas
    por compatibilidade com o restante do sistema.

    A IA NÃO recebe o nome do produto, link afiliado,
    preço ou qualquer dado comercial. O Python faz
    a integração do produto posteriormente.
    """

    return f"""
Você é um redator editorial especializado em SEO,
conteúdo útil, Casa, Organização e Decoração.

Escreva um artigo original em português do Brasil
para o blog "Achados para Casa".

TÍTULO DO POST:
{titulo}

PALAVRA-CHAVE PRINCIPAL:
{palavra_chave}

CATEGORIA:
{categoria}

OBJETIVO PRINCIPAL:

Produzir um artigo que resolva de verdade a dúvida
ou necessidade de quem fez essa pesquisa, com
informações práticas que possam ser aplicadas
no cotidiano.

O conteúdo deve ser útil primeiro para a pessoa e
otimizado para mecanismos de busca de forma natural,
sem parecer escrito para um algoritmo.

SEPARAÇÃO EDITORIAL OBRIGATÓRIA:

- Escreva SOMENTE conteúdo editorial geral.
- Não mencione produto comercial específico.
- Não mencione marca.
- Não mencione preço, desconto, promoção ou compra.
- Não crie URL ou link externo.
- Não recomende um modelo específico.
- Não invente características de produtos.
- Não tente adivinhar qual produto originou a pauta.
- O Python fará a integração comercial posteriormente.

ESTILO EDITORIAL:

- Escreva em português brasileiro natural.
- Use linguagem clara, próxima, útil e confiável.
- Prefira frases diretas e específicas.
- Varie o tamanho das frases e dos parágrafos.
- Evite tom robótico, acadêmico ou excessivamente formal.
- Evite introduções genéricas que poderiam servir
  para qualquer tema.
- Entre no assunto rapidamente.
- Não encha o artigo apenas para atingir uma quantidade
  de palavras.
- Evite repetir a mesma ideia com palavras diferentes.
- Evite conclusões artificiais ou excessivamente
  motivacionais.
- Não use frases como "neste artigo vamos explorar",
  "no mundo de hoje", "é importante ressaltar",
  "vale ressaltar" ou expressões genéricas semelhantes.
- Não mencione inteligência artificial, SEO,
  palavra-chave, mecanismos de busca ou estas instruções.

QUALIDADE E CONFIABILIDADE:

- Não invente pesquisas, estudos, estatísticas,
  especialistas, certificações ou dados.
- Não apresente como fato algo que dependa de
  condições específicas.
- Não faça afirmações categóricas sem base nas
  informações fornecidas.
- Quando uma orientação puder variar conforme ambiente,
  material, fabricante, instalação, condição de uso ou
  preferência pessoal, deixe essa condição clara.
- Para recomendações de segurança, instalação,
  conservação, armazenamento, limpeza, saúde ou uso,
  utilize linguagem prudente, responsável e
  contextualizada.
- Não apresente recomendações de saúde, higiene ou
  segurança como regras universais.
- Quando uma recomendação depender das instruções do
  fabricante, indique que o leitor deve consultar as
  orientações específicas do produto.
- Não invente benefícios funcionais.
- Não invente desempenho.
- Não invente durabilidade.
- Não dê instruções universais de lavagem, secagem, conservação
  ou manutenção quando elas puderem variar conforme material,
  etiqueta ou fabricante.
- Em cuidados com tecidos e produtos, prefira orientar o leitor
  a verificar a etiqueta e as instruções específicas do fabricante.
- Não atribua a materiais específicos propriedades de absorção,
  secagem, maciez, resistência, durabilidade, conforto ou desempenho
  como regra geral sem base fornecida.
- Não invente medidas, quantidades ou frequências recomendadas.
- Não invente capacidade.
- Não invente dimensões.
- Não invente materiais.
- Não invente composição.
- Não invente potência.
- Não invente resistência.
- Não invente certificações.
- Não invente compatibilidades.
- Não faça promessas exageradas.
- Não dê garantias de resultado.
- Não use superlativos comerciais sem informação que os
  sustente, como "melhor", "mais eficiente", "superior",
  "premium" ou equivalentes.
- Evite construções categóricas com palavras como
  "evita", "impede", "garante", "elimina", "previne",
  "protege", "resolve", "nunca" e "sempre", especialmente
  ao falar de limpeza, higiene, conservação, segurança,
  saúde, alimentos, instalação ou armazenamento.
- Prefira formulações prudentes e descritivas, como
  "pode ajudar a organizar", "pode facilitar a rotina",
  "pode contribuir para manter os itens acessíveis" ou
  "pode ser útil conforme a necessidade do ambiente".
- Não diga que uma solução torna algo "mais eficiente"
  sem uma base objetiva fornecida.
- Não copie textos de outros sites.

SEO NATURAL:

- Responda diretamente à intenção de busca
  representada pelo título.
- Use a palavra-chave principal naturalmente no texto.
- Tente utilizar a palavra-chave principal na parte
  inicial do artigo, desde que a frase permaneça natural.
- Utilize sinônimos, variações e termos semanticamente
  relacionados.
- Não repita a palavra-chave de forma forçada.
- Os subtítulos devem descrever claramente o conteúdo
  das seções.
- Não crie subtítulos apenas para inserir
  a palavra-chave.
- Não repita o título principal dentro do conteúdo.
- Não crie H1.

ESTRUTURA:

- Produza aproximadamente 900 a 1200 palavras.
- Comece diretamente com uma introdução útil em <p>.
- Depois da introdução, organize o conteúdo em
  pelo menos 5 seções com <h2>.
- Use <h3> somente quando houver uma subdivisão
  realmente útil.
- Use listas quando elas facilitarem a leitura.
- Inclua exemplos práticos quando ajudarem a entender
  a orientação.
- Dê preferência a recomendações que o leitor
  consiga aplicar.
- Quando houver diferentes opções, explique em que
  situação cada uma pode fazer mais sentido.
- Termine de maneira natural, reforçando os pontos
  mais úteis sem simplesmente repetir toda a introdução.
- O último subtítulo não precisa se chamar "Conclusão".

FORMATAÇÃO:

Retorne SOMENTE o conteúdo HTML que será inserido
no corpo de uma postagem do Blogger.

HTML PERMITIDO:
<p>
<h2>
<h3>
<ul>
<ol>
<li>
<strong>

NÃO USE:
<h1>
<html>
<head>
<body>
<script>
<style>
Markdown
blocos ```html
links inventados

O primeiro caractere útil da resposta deve fazer
parte de uma tag <p>.

Não escreva comentários ou explicações antes ou
depois do artigo.
"""


def gerar_conteudo_cloudflare(
    titulo,
    palavra_chave,
    categoria,
    produto_principal="",
):
    """
    Gera o conteúdo editorial em dois blocos com
    Cloudflare/Qwen.

    A divisão em dois blocos melhora a estabilidade
    do tamanho final. O produto continua totalmente
    fora dos prompts da IA.

    Retorna:
        (conteudo_html, modelo_utilizado)

    Se a geração falhar:
        (None, None)
    """

    prompt_base = criar_prompt_artigo(
        titulo=titulo,
        palavra_chave=palavra_chave,
        categoria=categoria,
        produto_principal="",
    )

    prompt_bloco_1 = f"""
{prompt_base}

INSTRUÇÃO DESTA ETAPA:

Esta é a PRIMEIRA PARTE do artigo.

Produza aproximadamente 600 a 700 palavras.

Inclua:
- a introdução;
- de 3 a 4 seções H2;
- orientações práticas;
- exemplos úteis quando fizer sentido.

REGRA OBRIGATÓRIA DE SEO:
Use a expressão exata abaixo pelo menos UMA VEZ,
de forma natural, preferencialmente na introdução:

{palavra_chave}

Não encerre o assunto como se o artigo tivesse
terminado. A segunda parte continuará o conteúdo.
"""

    prompt_bloco_2 = f"""
{prompt_base}

INSTRUÇÃO DESTA ETAPA:

Esta é a SEGUNDA PARTE do mesmo artigo.

Produza aproximadamente 550 a 650 palavras.

NÃO faça uma nova introdução.

Continue o assunto de forma complementar, sem repetir
as ideias, exemplos ou subtítulos da primeira parte.

Inclua:
- de 3 a 4 novas seções H2;
- aspectos práticos ainda não abordados;
- situações em que escolhas diferentes podem fazer
  sentido;
- um fechamento natural no final.

Não use H2 chamado "Introdução".
Não repita o título principal.
"""

    try:
        print(
            "\n=== BLOCO EDITORIAL 1/2 ==="
        )

        bloco_1 = gerar_com_cloudflare(
            prompt=prompt_bloco_1
        )

        print(
            "\n=== BLOCO EDITORIAL 2/2 ==="
        )

        bloco_2 = gerar_com_cloudflare(
            prompt=prompt_bloco_2
        )

        conteudo = (
            bloco_1.rstrip()
            + "\n\n"
            + bloco_2.lstrip()
        )

        return conteudo, MODELO_ARTIGO

    except Exception as erro:
        print(
            "\nCloudflare/Qwen não conseguiu "
            "concluir o artigo."
        )

        print(
            "Erro:",
            erro,
        )

        return None, None


def criar_conteudo_fallback(
    titulo,
    palavra_chave,
):
    """
    Conteúdo de segurança usado se nenhum
    modelo responder.

    Este conteúdo nunca deve ser publicado
    automaticamente.
    """

    introducao = criar_introducao(
        titulo,
        palavra_chave,
    )

    partes = [
        (
            f"<p>{html.escape(introducao)}</p>"
        ),
        (
            f"<h2>O que considerar sobre "
            f"{html.escape(palavra_chave)}</h2>"
        ),
        (
            "<p>Antes de escolher uma solução "
            "para sua casa, analise o espaço "
            "disponível, a praticidade e as "
            "necessidades reais do ambiente.</p>"
        ),
        (
            "<h2>Pontos que merecem "
            "atenção</h2>"
        ),
        (
            "<p>Medidas, materiais, facilidade "
            "de uso, manutenção e adequação à "
            "rotina são alguns dos aspectos que "
            "podem ser comparados antes de tomar "
            "uma decisão.</p>"
        ),
        (
            "<h2>Como avaliar as opções</h2>"
        ),
        (
            "<p>Considere como cada alternativa "
            "se encaixa no espaço e na rotina da "
            "casa. Uma solução útil é aquela que "
            "atende à necessidade do ambiente sem "
            "criar novas dificuldades.</p>"
        ),
    ]

    return "\n".join(
        partes
    )


def contar_marcadores_produto(
    conteudo,
):
    """
    Conta quantas vezes o marcador reservado
    ao produto principal aparece no artigo.
    """

    if not conteudo:
        return 0

    return conteudo.count(
        MARCADOR_PRODUTO_PRINCIPAL
    )


def inserir_marcador_produto_python(
    conteudo,
):
    """
    Insere o marcador do produto por decisão
    determinística do Python.

    A IA não conhece o produto nem decide a posição.
    O marcador é colocado aproximadamente no meio
    do artigo, antes de um H2, preservando HTML válido.
    """

    if not conteudo:
        return conteudo

    conteudo = conteudo.replace(
        MARCADOR_PRODUTO_PRINCIPAL,
        "",
    )

    posicoes_h2 = [
        correspondencia.start()
        for correspondencia in re.finditer(
            r"<h2\b",
            conteudo,
            flags=re.IGNORECASE,
        )
    ]

    if posicoes_h2:
        indice = max(
            1,
            len(posicoes_h2) // 2,
        )

        indice = min(
            indice,
            len(posicoes_h2) - 1,
        )

        posicao = posicoes_h2[indice]

        return (
            conteudo[:posicao].rstrip()
            + "\n\n"
            + MARCADOR_PRODUTO_PRINCIPAL
            + "\n\n"
            + conteudo[posicao:].lstrip()
        )

    return (
        conteudo.rstrip()
        + "\n\n"
        + MARCADOR_PRODUTO_PRINCIPAL
    )


def criar_estrutura_artigo(
    titulo,
    palavra_chave,
    categoria="Casa e Decoração",
    introducao="",
    secoes=None,
    conclusao="",
    produto_principal="",
):
    """
    Cria o artigo e mantém o mesmo formato
    esperado pelo main.py.

    Quando produto_principal é informado,
    o artigo deve reservar exatamente um ponto
    contextual para a inserção posterior.
    """

    titulo = limpar_texto(
        titulo
    )

    palavra_chave = limpar_texto(
        palavra_chave
    )

    categoria = limpar_texto(
        categoria
    )

    produto_principal = limpar_texto(
        produto_principal
    )

    print(
        "\nGerando artigo editorial com Cloudflare/Qwen..."
    )

    (
        conteudo_html,
        modelo_utilizado,
    ) = gerar_conteudo_cloudflare(
        titulo=titulo,
        palavra_chave=palavra_chave,
        categoria=categoria,
        produto_principal=(
            produto_principal
        ),
    )

    fonte = "cloudflare_qwen"

    if conteudo_html:
        print(
            "Artigo editorial gerado pela "
            "Cloudflare/Qwen com sucesso."
        )

        print(
            "Modelo utilizado:",
            modelo_utilizado,
        )

        if produto_principal:
            conteudo_html = (
                inserir_marcador_produto_python(
                    conteudo_html
                )
            )

            quantidade_marcadores = (
                contar_marcadores_produto(
                    conteudo_html
                )
            )

            print(
                "Marcadores de produto "
                "principal encontrados:",
                quantidade_marcadores,
            )

    else:
        print(
            "Cloudflare/Qwen indisponível. "
            "Ativando conteúdo de segurança."
        )

        conteudo_html = (
            criar_conteudo_fallback(
                titulo=titulo,
                palavra_chave=palavra_chave,
            )
        )

        fonte = "fallback"
        modelo_utilizado = None

    return {
        "titulo": titulo,
        "palavra_chave": palavra_chave,
        "categoria": categoria,
        "conteudo_html": conteudo_html,
        "fonte": fonte,
        "modelo_ia": modelo_utilizado,
        "modelo_gemini": modelo_utilizado,
        "produto_principal": (
            produto_principal
        ),
    }


def extrair_texto_html(
    conteudo,
):
    """
    Remove as tags HTML para permitir
    verificações sobre o texto produzido.
    """

    if not conteudo:
        return ""

    # O marcador é controle interno,
    # não é conteúdo editorial.
    conteudo = conteudo.replace(
        MARCADOR_PRODUTO_PRINCIPAL,
        " ",
    )

    texto = re.sub(
        r"<[^>]+>",
        " ",
        conteudo,
    )

    texto = html.unescape(
        texto
    )

    texto = re.sub(
        r"\s+",
        " ",
        texto,
    )

    return texto.strip()


def normalizar_para_comparacao(
    texto,
):
    """
    Normaliza texto para comparações
    sem diferenciar acentos.
    """

    texto = str(
        texto or ""
    ).lower()

    texto = unicodedata.normalize(
        "NFD",
        texto,
    )

    texto = "".join(
        caractere
        for caractere in texto
        if unicodedata.category(
            caractere
        ) != "Mn"
    )

    texto = re.sub(
        r"\s+",
        " ",
        texto,
    )

    return texto.strip()


# ============================================================
# TRAVA EDITORIAL DE RISCO
# ============================================================


def _sentencas_texto(texto):
    """Divide o texto em trechos curtos para análise conservadora."""
    return [
        trecho.strip()
        for trecho in re.split(r"(?<=[.!?])\s+", texto or "")
        if trecho.strip()
    ]


def _contem_contexto_prudente(texto_normalizado):
    """Reconhece linguagem que deixa claro que a orientação pode variar."""
    expressoes = (
        "pode variar",
        "podem variar",
        "pode depender",
        "podem depender",
        "dependendo",
        "conforme",
        "de acordo com",
        "consulte o fabricante",
        "consulte as instrucoes",
        "siga as instrucoes",
        "orientacoes do fabricante",
        "instrucoes do fabricante",
        "quando aplicavel",
        "em geral",
        "como referencia",
        "aproximadamente",
        "cerca de",
    )
    return any(expressao in texto_normalizado for expressao in expressoes)



def suavizar_comparativos_editoriais(conteudo):
    """
    Corrige comparativos/superlativos editoriais simples
    que o modelo pode produzir apesar do prompt.

    A função NÃO aprova o artigo: depois dela, a trava editorial
    completa continua sendo executada normalmente.
    """

    if not conteudo:
        return conteudo

    substituicoes = (
        # Formas específicas primeiro.
        (
            r"\bpode ser mais eficiente\b",
            "pode ser mais adequada nessa situação",
        ),
        (
            r"\bpodem ser mais eficientes\b",
            "podem ser mais adequadas nessa situação",
        ),
        (
            r"\bé mais eficiente\b",
            "pode ser adequada nessa situação",
        ),
        (
            r"\bsão mais eficientes\b",
            "podem ser adequadas nessa situação",
        ),
        (
            r"\ba melhor estratégia\b",
            "uma estratégia útil",
        ),
        (
            r"\bo melhor caminho\b",
            "um caminho útil",
        ),
        (
            r"\ba melhor opção\b",
            "uma opção adequada",
        ),
        (
            r"\bo melhor método\b",
            "um método adequado",
        ),

        # Rede de segurança editorial:
        # captura "mais eficiente" em outras construções,
        # como "de forma mais eficiente" ou
        # "manter a organização mais eficiente".
        (
            r"\bmais eficiente\b",
            "de maneira adequada",
        ),
        (
            r"\bmais eficientes\b",
            "mais adequadas",
        ),
    )

    resultado = conteudo

    for padrao, substituto in substituicoes:
        resultado = re.sub(
            padrao,
            substituto,
            resultado,
            flags=re.IGNORECASE,
        )

    return resultado

def validar_alegacoes_risco(artigo):
    """
    Trava editorial determinística para publicação automática.

    Ela não tenta provar que uma afirmação é verdadeira. Em vez disso,
    bloqueia padrões que merecem revisão humana antes de publicar:
    alegações numéricas/temporais sensíveis, saúde/segurança com promessa,
    superlativos/garantias e características específicas do produto que
    não estejam sustentadas pelo nome fornecido.
    """
    conteudo = artigo.get("conteudo_html", "") or ""

    conteudo_suavizado = suavizar_comparativos_editoriais(
        conteudo
    )

    if conteudo_suavizado != conteudo:
        artigo["conteudo_html"] = conteudo_suavizado
        conteudo = conteudo_suavizado
        print(
            "Ajuste editorial automático aplicado antes "
            "da trava de risco."
        )

    produto = limpar_texto(artigo.get("produto_principal", ""))
    texto = extrair_texto_html(conteudo)

    problemas = []
    vistos = set()

    def registrar(tipo, trecho):
        trecho = limpar_texto(trecho)
        chave = (tipo, normalizar_para_comparacao(trecho))
        if trecho and chave not in vistos:
            vistos.add(chave)
            problemas.append({"tipo": tipo, "trecho": trecho[:320]})

    # Termos de alto risco: usados para detectar promessas
    # categóricas em contextos que realmente merecem revisão.
    # Palavras amplas como "limpeza" e "segurança" não entram
    # sozinhas aqui, pois geravam falsos positivos em orientações
    # domésticas comuns.
    termos_alto_risco = (
        "conservacao", "validade", "saude", "higiene",
        "bacteria", "bacterias", "mofo", "fungo", "fungos",
        "contaminacao", "desinfetar", "desinfeccao",
        "esterilizar", "seguranca alimentar",
        "risco eletrico", "choque eletrico",
    )

    # Verbos/promessas fortes. Só são bloqueados automaticamente
    # quando aparecem junto de um contexto de alto risco.
    termos_promessa_forte = (
        "garante", "garantem", "elimina", "eliminam",
        "impede", "impedem", "previne", "previnem",
        "protege", "protegem", "resolve", "resolvem", "cura",
        "remove completamente", "100%", "totalmente seguro",
        "sem risco",
    )

    # "evita/evitam" é comum em português cotidiano. Mantemos
    # bloqueio apenas quando ligado a consequências sensíveis.
    termos_evitar = (
        "evita", "evitam",
    )

    padrao_numero = re.compile(
        r"(?:\b\d+(?:[.,]\d+)?\b|\b\d+\s*(?:a|ate)\s*\d+\b)"
    )
    unidades_tempo = (
        "minuto", "minutos", "hora", "horas", "dia", "dias",
        "semana", "semanas", "mes", "meses", "ano", "anos",
    )

    for sentenca in _sentencas_texto(texto):
        normalizada = normalizar_para_comparacao(sentenca)

        # "produto(s) de higiene" descreve uma categoria de objeto,
        # não uma alegação sanitária por si só. Criamos uma cópia
        # apenas para a detecção de alto risco; o artigo não é alterado.
        normalizada_alto_risco = re.sub(
            r"\\bprodutos?\\s+de\\s+higiene\\b",
            "produto_de_uso_pessoal",
            normalizada,
        )

        tem_alto_risco = any(
            t in normalizada_alto_risco
            for t in termos_alto_risco
        )

        tem_contexto_amplo = any(
            t in normalizada
            for t in (
                "geladeira", "refrigerador", "refrigeracao",
                "congelador", "freezer", "armazenamento",
                "conservacao", "validade", "seguranca",
                "saude", "higiene", "bacteria", "bacterias",
                "mofo", "fungo", "fungos", "contaminacao",
                "alimento", "alimentos", "comida", "limpeza",
                "desinfetar", "desinfeccao", "esterilizar",
                "instalacao", "eletrico", "eletrica", "voltagem",
            )
        )

        tem_numero = bool(
            padrao_numero.search(normalizada)
        )

        tem_tempo = any(
            u in normalizada
            for u in unidades_tempo
        )

        prudente = _contem_contexto_prudente(
            normalizada
        )

        if (
            tem_contexto_amplo
            and tem_numero
            and tem_tempo
            and not prudente
        ):
            registrar(
                "Prazo ou número sensível sem fonte/condição explícita",
                sentenca,
            )

        tem_promessa_forte = any(
            t in normalizada
            for t in termos_promessa_forte
        )

        tem_evitar_sensivel = (
            any(
                t in normalizada
                for t in termos_evitar
            )
            and tem_alto_risco
        )

        if (
            tem_alto_risco
            and tem_promessa_forte
        ) or tem_evitar_sensivel:
            registrar(
                "Alegação categórica de saúde, higiene, segurança ou conservação",
                sentenca,
            )

        # "superior" isolado pode significar posição física
        # ("parte superior do armário"). Por isso, somente usos
        # inequivocamente comparativos/comerciais são bloqueados.
        # Instruções técnicas de cuidado/manutenção podem variar
        # conforme material e fabricante. A regra só atua quando
        # coexistem: uma ação de cuidado, um contexto de material/produto
        # e um efeito funcional alegado. Assim, hábitos domésticos comuns
        # como "lavar os pratos" ou "limpar a pia" não são bloqueados.
        termos_cuidado = (
            "lavar", "lave", "lavagem", "secar", "secagem",
            "amaciante", "cloro", "sabao", "detergente",
            "temperatura", "agua quente", "agua morna",
        )
        contextos_cuidado_produto = (
            "tecido", "tecidos", "toalha", "toalhas",
            "roupa", "roupas", "algodao", "microfibra",
            "material", "materiais", "produto", "produtos",
            "peca", "pecas", "fibra", "fibras",
        )
        efeitos_cuidado = (
            "preserva", "preservar", "mantem", "manter",
            "reduz", "reduzir", "aumenta", "aumentar",
            "melhora", "melhorar", "durabilidade", "vida util",
            "maciez", "absorcao", "textura", "cor",
        )

        if (
            any(t in normalizada for t in termos_cuidado)
            and any(t in normalizada for t in contextos_cuidado_produto)
            and any(t in normalizada for t in efeitos_cuidado)
            and not prudente
        ):
            registrar(
                "Instrução de cuidado/manutenção sem condição do fabricante",
                sentenca,
            )

        if re.search(
            r"\b(?:o melhor|a melhor|mais eficiente|"
            r"qualidade superior|desempenho superior|"
            r"resultado superior|premium|garantido|garantida|"
            r"resultado garantido)\b",
            normalizada,
        ):
            registrar(
                "Superlativo ou garantia não sustentada",
                sentenca,
            )

    # Verificação conservadora de alegações específicas próximas ao produto.
    # O nome do catálogo é a única fonte permitida de características.
    if produto:
        produto_norm = normalizar_para_comparacao(produto)
        caracteristicas = (
            "algodao", "poliester", "microfibra", "inox", "aco",
            "aluminio", "plastico", "madeira", "impermeavel",
            "antiderrapante", "lavavel", "dobravel", "ajustavel",
            "recarregavel", "sem fio", "bivolt", "wifi", "led",
            "silencioso", "ortopedico", "ergonomico", "termico",
            "resistente", "felpudo", "macio", "confortavel",
            "litro", "litros", "ml", "w", "kw", "cm", "mm",
        )

        for sentenca in _sentencas_texto(texto):
            normalizada = normalizar_para_comparacao(sentenca)

            # Só considera referência ao produto quando as palavras
            # "produto", "item" ou "modelo" aparecem como palavras
            # completas. Isso evita falsos positivos como "permitem",
            # que contém as letras "item" no meio da palavra.
            menciona_produto = bool(
                re.search(
                    r"\\b(?:produto|item|modelo)\\b",
                    normalizada,
                )
            )

            if not menciona_produto:
                continue

            for termo in caracteristicas:
                if termo in normalizada and termo not in produto_norm:
                    registrar(
                        "Característica específica do produto não sustentada pelo nome",
                        sentenca,
                    )
                    break

    return {
        "aprovado": len(problemas) == 0,
        "problemas": problemas,
        "quantidade_problemas": len(problemas),
    }


def validar_artigo(
    artigo,
):
    """
    Faz verificações antes de o artigo
    seguir para publicação.

    Se existe produto principal associado,
    exige exatamente um marcador contextual.
    """

    erros = []

    titulo = artigo.get(
        "titulo",
        "",
    )

    palavra_chave = artigo.get(
        "palavra_chave",
        "",
    )

    conteudo = artigo.get(
        "conteudo_html",
        "",
    )

    fonte = artigo.get(
        "fonte",
        "",
    )

    produto_principal = artigo.get(
        "produto_principal",
        "",
    )

    if not titulo:
        erros.append(
            "Título ausente."
        )

    if not palavra_chave:
        erros.append(
            "Palavra-chave ausente."
        )

    if not conteudo:
        erros.append(
            "Conteúdo do artigo ausente."
        )

        return {
            "valido": False,
            "erros": erros,
        }

    if fonte == "fallback":
        erros.append(
            "Conteúdo de segurança utilizado; "
            "artigo não pode ser publicado."
        )

    conteudo_minusculo = (
        conteudo.lower()
    )

    if "<h2" not in conteudo_minusculo:
        erros.append(
            "Artigo sem subtítulos H2."
        )

    if "<p" not in conteudo_minusculo:
        erros.append(
            "Artigo sem parágrafos HTML."
        )

    if "<h1" in conteudo_minusculo:
        erros.append(
            "O conteúdo não deve conter H1."
        )

    tags_proibidas = (
        "<script",
        "<style",
        "<html",
        "<head",
        "<body",
    )

    for tag in tags_proibidas:
        if tag in conteudo_minusculo:
            erros.append(
                "HTML não permitido encontrado "
                f"no artigo: {tag}"
            )

    if produto_principal:
        quantidade_marcadores = (
            contar_marcadores_produto(
                conteudo
            )
        )

        if quantidade_marcadores == 0:
            erros.append(
                "Produto principal informado, "
                "mas o marcador contextual "
                "não foi inserido no artigo."
            )

        elif quantidade_marcadores > 1:
            erros.append(
                "O marcador do produto principal "
                "aparece mais de uma vez."
            )

    texto_puro = extrair_texto_html(
        conteudo
    )

    palavras = re.findall(
        r"\b[\wÀ-ÿ'-]+\b",
        texto_puro,
        flags=re.UNICODE,
    )

    quantidade_palavras = len(
        palavras
    )

    if quantidade_palavras < 750:
        erros.append(
            f"Artigo muito curto: "
            f"{quantidade_palavras} palavras."
        )

    if quantidade_palavras > 1600:
        erros.append(
            f"Artigo muito longo: "
            f"{quantidade_palavras} palavras."
        )

    quantidade_h2 = len(
        re.findall(
            r"<h2(?:\s[^>]*)?>",
            conteudo,
            flags=re.IGNORECASE,
        )
    )

    if quantidade_h2 < 3:
        erros.append(
            f"Poucos subtítulos H2: "
            f"{quantidade_h2} encontrados."
        )

    if palavra_chave:
        texto_normalizado = (
            normalizar_para_comparacao(
                texto_puro
            )
        )

        palavra_chave_normalizada = (
            normalizar_para_comparacao(
                palavra_chave
            )
        )

        ocorrencias_palavra_chave = (
            texto_normalizado.count(
                palavra_chave_normalizada
            )
        )

        if ocorrencias_palavra_chave == 0:
            erros.append(
                "A palavra-chave principal "
                "não aparece no artigo."
            )

        if ocorrencias_palavra_chave > 12:
            erros.append(
                "A palavra-chave principal "
                "aparece em excesso."
            )

    validacao_risco = validar_alegacoes_risco(artigo)

    if not validacao_risco["aprovado"]:
        erros.append(
            "Trava editorial de risco reprovou o artigo."
        )

        for problema in validacao_risco["problemas"]:
            erros.append(
                f"Risco editorial: {problema['tipo']} | "
                f"{problema['trecho']}"
            )

    return {
        "valido": len(
            erros
        ) == 0,
        "erros": erros,
        "quantidade_palavras": (
            quantidade_palavras
        ),
        "quantidade_h2": (
            quantidade_h2
        ),
        "quantidade_marcadores_produto": (
            contar_marcadores_produto(
                conteudo
            )
        ),
        "validacao_risco": validacao_risco,
    }


if __name__ == "__main__":
    teste = criar_estrutura_artigo(
        titulo=(
            "Como organizar uma cozinha "
            "pequena de forma prática"
        ),
        palavra_chave=(
            "organização de cozinha pequena"
        ),
    )

    verificacao = validar_artigo(
        teste
    )

    print(
        "Módulo de geração de artigos "
        "iniciado com sucesso."
    )

    print(
        "Título:",
        teste["titulo"],
    )

    print(
        "Palavra-chave:",
        teste["palavra_chave"],
    )

    print(
        "Fonte:",
        teste["fonte"],
    )

    print(
        "Modelo IA:",
        teste.get(
            "modelo_ia"
        ),
    )

    print(
        "Validação:",
        verificacao,
    )

    if not verificacao["valido"]:
        print()
        print(
            "TESTE DE ARTIGO: REPROVADO"
        )

        for erro in verificacao["erros"]:
            print(
                "-",
                erro,
            )

        raise SystemExit(1)

    print()
    print(
        "TESTE DE ARTIGO: APROVADO"
    )
