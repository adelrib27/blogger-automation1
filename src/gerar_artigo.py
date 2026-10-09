import html
import os
import re
import time
import unicodedata

from google import genai


# ============================================================
# MODELOS PARA GERAÇÃO DE ARTIGOS
# ============================================================

MODELOS_ARTIGO = [
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
]


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


def limpar_html_gemini(
    conteudo,
):
    """
    Faz uma limpeza básica na resposta do Gemini
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


def erro_de_cota(
    erro,
):
    """
    Detecta cota esgotada ou indisponível.
    """

    mensagem = str(
        erro
    ).upper()

    return (
        "429" in mensagem
        or "RESOURCE_EXHAUSTED" in mensagem
        or "QUOTA EXCEEDED" in mensagem
    )


def erro_temporario(
    erro,
):
    """
    Detecta indisponibilidade temporária.
    """

    mensagem = str(
        erro
    ).upper()

    return (
        "503" in mensagem
        or "UNAVAILABLE" in mensagem
        or "HIGH DEMAND" in mensagem
    )


def gerar_com_modelo(
    client,
    modelo,
    prompt,
):
    """
    Tenta produzir o artigo usando
    um modelo específico.
    """

    tentativas = 3
    esperas = [5, 15]

    for tentativa in range(
        1,
        tentativas + 1,
    ):
        try:
            print(
                f"\nModelo de artigo: "
                f"{modelo}"
            )

            print(
                f"Tentativa {tentativa}/"
                f"{tentativas} com "
                f"{modelo}..."
            )

            resposta = (
                client.models.generate_content(
                    model=modelo,
                    contents=prompt,
                )
            )

            conteudo = resposta.text

            if not conteudo:
                raise RuntimeError(
                    "Gemini retornou uma "
                    "resposta sem conteúdo."
                )

            conteudo = (
                limpar_html_gemini(
                    conteudo
                )
            )

            if not conteudo:
                raise RuntimeError(
                    "O conteúdo ficou vazio "
                    "após a limpeza."
                )

            print(
                "Artigo recebido com "
                "sucesso do modelo "
                f"{modelo}."
            )

            return conteudo

        except Exception as erro:
            print(
                f"Erro no modelo {modelo}, "
                f"tentativa {tentativa}/"
                f"{tentativas}: {erro}"
            )

            if erro_de_cota(
                erro
            ):
                print(
                    f"Cota do modelo {modelo} "
                    "indisponível ou esgotada."
                )

                print(
                    "Pulando imediatamente "
                    "para o próximo modelo..."
                )

                raise

            if erro_temporario(
                erro
            ):
                if tentativa >= tentativas:
                    print(
                        f"O modelo {modelo} "
                        "continua temporariamente "
                        "indisponível."
                    )

                    raise

                espera = esperas[
                    tentativa - 1
                ]

                print(
                    f"Aguardando {espera} "
                    "segundos antes de tentar "
                    "novamente o mesmo modelo..."
                )

                time.sleep(
                    espera
                )

                continue

            mensagem = str(
                erro
            )

            erro_resposta = (
                "sem conteúdo" in mensagem
                or (
                    "vazio após a limpeza"
                    in mensagem
                )
            )

            if erro_resposta:
                if tentativa >= tentativas:
                    raise

                espera = esperas[
                    tentativa - 1
                ]

                print(
                    f"Aguardando {espera} "
                    "segundos antes de solicitar "
                    "novamente o artigo..."
                )

                time.sleep(
                    espera
                )

                continue

            print(
                "Erro não recuperável no "
                f"modelo {modelo}."
            )

            raise

    raise RuntimeError(
        f"O modelo {modelo} não conseguiu "
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

    Quando existe produto principal, o Gemini
    recebe somente o nome do produto.

    O link afiliado nunca é enviado ao modelo.
    """

    produto_principal = limpar_texto(
        produto_principal
    )

    instrucao_produto = ""

    if produto_principal:
        instrucao_produto = f"""
PRODUTO PRINCIPAL RELACIONADO À PAUTA:

{produto_principal}

INTEGRAÇÃO EDITORIAL DO PRODUTO:

- O produto acima originou esta pauta e tem relação
  direta com o assunto.
- Desenvolva primeiro o conteúdo editorial normalmente.
- Identifique a seção em que esse produto seja mais
  útil e natural para o leitor.
- Nesse ponto, insira EXATAMENTE este marcador:

{MARCADOR_PRODUTO_PRINCIPAL}

- O marcador deve aparecer sozinho entre blocos HTML.
- Use o marcador EXATAMENTE UMA VEZ.
- Não altere o marcador.
- Não coloque o marcador dentro de <p>, <li>, <h2>
  ou <h3>.
- Não escreva URL.
- Não crie link.
- Não invente preço.
- Não invente desconto.
- Não invente características adicionais do produto.
- Não transforme o artigo em propaganda.
- Não faça review do produto.
- Não repita o nome do produto diversas vezes.
- O texto antes e depois do marcador deve continuar
  naturalmente, como parte do mesmo artigo.
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

{instrucao_produto}

OBJETIVO PRINCIPAL:

Produzir um artigo que resolva de verdade a dúvida
ou necessidade de quem fez essa pesquisa, com
informações práticas que possam ser aplicadas
no cotidiano.

O conteúdo deve ser útil primeiro para a pessoa e
otimizado para mecanismos de busca de forma natural,
sem parecer escrito para um algoritmo.

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
- Não invente capacidade.
- Não invente dimensões.
- Não invente materiais.
- Não invente composição.
- Não invente potência.
- Não invente resistência.
- Não invente certificações.
- Não invente compatibilidades.
- Não atribua ao produto características que não estejam
  explicitamente presentes no nome fornecido.
- Não deduza características apenas porque seriam comuns
  em produtos semelhantes.
- Não transforme uma característica genérica da categoria
  em característica específica do produto principal.
- Se determinada característica do produto não foi
  informada, simplesmente não a mencione.
- Não faça promessas exageradas.
- Não dê garantias de resultado.
- Não diga ou sugira que o produto resolve definitivamente
  um problema.
- Não use superlativos comerciais sem informação que os
  sustente, como "melhor", "mais eficiente", "superior",
  "premium" ou equivalentes.
- Não copie textos de outros sites.
- Não inclua preços.
- Não inclua links externos.
- Não invente marcas ou produtos.

REGRA ESPECIAL PARA O PRODUTO PRINCIPAL:

- Considere o nome do produto recebido neste prompt como
  a ÚNICA fonte de características específicas desse
  produto.
- Você pode mencionar somente características que estejam
  literalmente sustentadas por esse nome.
- Não complete mentalmente informações ausentes.
- Não suponha características com base no tipo de produto.
- Não atribua vantagens específicas ao produto sem que
  elas estejam sustentadas pelo nome fornecido.
- O artigo pode explicar benefícios gerais da categoria,
  desde que fique claro que são orientações gerais e não
  características garantidas do produto principal.
- A função do produto principal é servir como opção
  relacionada ao contexto do artigo, e não como fonte de
  alegações técnicas.
- Não escreva o link do produto.
- Não invente nem tente reconstruir URL.
- O Python fará a inserção do link afiliado posteriormente.

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

- Produza aproximadamente 900 a 1300 palavras.
- Comece diretamente com uma introdução útil em <p>.
- Depois da introdução, organize o conteúdo em
  seções com <h2>.
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

O marcador {MARCADOR_PRODUTO_PRINCIPAL}, quando
solicitado acima, é a única exceção de texto que
pode aparecer fora de uma tag HTML.

O primeiro caractere útil da resposta deve fazer
parte de uma tag <p>.

Não escreva comentários ou explicações antes ou
depois do artigo.
"""


def gerar_conteudo_gemini(
    titulo,
    palavra_chave,
    categoria,
    produto_principal="",
):
    """
    Gera o conteúdo principal usando uma fila
    automática de modelos Gemini.

    Retorna:
        (conteudo_html, modelo_utilizado)

    Se todos os modelos falharem:
        (None, None)
    """

    api_key = os.getenv(
        "GEMINI_API_KEY"
    )

    if not api_key:
        print(
            "GEMINI_API_KEY não encontrada. "
            "Usando conteúdo de segurança."
        )

        return None, None

    client = genai.Client(
        api_key=api_key
    )

    prompt = criar_prompt_artigo(
        titulo=titulo,
        palavra_chave=palavra_chave,
        categoria=categoria,
        produto_principal=(
            produto_principal
        ),
    )

    print(
        "\n=== FILA DE MODELOS PARA ARTIGO ==="
    )

    for numero, modelo in enumerate(
        MODELOS_ARTIGO,
        start=1,
    ):
        print(
            f"{numero}. {modelo}"
        )

    ultimo_erro = None

    for numero, modelo in enumerate(
        MODELOS_ARTIGO,
        start=1,
    ):
        print(
            f"\n=== MODELO DE ARTIGO "
            f"{numero}/"
            f"{len(MODELOS_ARTIGO)} ==="
        )

        try:
            conteudo = gerar_com_modelo(
                client=client,
                modelo=modelo,
                prompt=prompt,
            )

            return conteudo, modelo

        except Exception as erro:
            ultimo_erro = erro

            print(
                f"Modelo {modelo} não pôde "
                "concluir o artigo."
            )

            if numero < len(
                MODELOS_ARTIGO
            ):
                print(
                    "Tentando o próximo modelo "
                    "da fila..."
                )

    print(
        "\nTodos os modelos configurados "
        "para artigos falharam."
    )

    if ultimo_erro:
        print(
            "Último erro:",
            ultimo_erro,
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
        "\nGerando artigo com Gemini..."
    )

    (
        conteudo_html,
        modelo_utilizado,
    ) = gerar_conteudo_gemini(
        titulo=titulo,
        palavra_chave=palavra_chave,
        categoria=categoria,
        produto_principal=(
            produto_principal
        ),
    )

    fonte = "gemini"

    if conteudo_html:
        print(
            "Artigo gerado pelo Gemini "
            "com sucesso."
        )

        print(
            "Modelo utilizado:",
            modelo_utilizado,
        )

        if produto_principal:
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
            "Gemini indisponível. "
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
        "Modelo Gemini:",
        teste.get(
            "modelo_gemini"
        ),
    )

    print(
        "Validação:",
        verificacao,
    )
