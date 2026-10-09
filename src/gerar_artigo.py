import html
import os
import re
import time

from google import genai


def limpar_texto(texto):
    """
    Remove espaços desnecessários e normaliza o texto.
    """
    if not texto:
        return ""

    texto = str(texto).strip()
    texto = re.sub(r"\s+", " ", texto)

    return texto


def criar_introducao(titulo, palavra_chave):
    """
    Cria uma introdução de segurança caso a IA não esteja disponível.
    """
    titulo = limpar_texto(titulo)
    palavra_chave = limpar_texto(palavra_chave)

    return (
        f"Se você está pesquisando sobre {palavra_chave}, "
        f"este guia reúne informações práticas para ajudar você "
        f"a entender melhor o assunto e encontrar soluções adequadas "
        f"para sua casa."
    )


def limpar_html_gemini(conteudo):
    """
    Faz uma limpeza básica na resposta do Gemini sem alterar
    a estrutura útil do artigo.
    """
    if not conteudo:
        return ""

    conteudo = conteudo.strip()

    # Remove cercas Markdown caso o modelo as inclua.
    conteudo = re.sub(
        r"^```(?:html)?\s*",
        "",
        conteudo,
        flags=re.IGNORECASE,
    )
    conteudo = re.sub(r"\s*```$", "", conteudo)

    # Remove estruturas HTML completas caso apareçam por engano.
    conteudo = re.sub(
        r"</?(?:html|head|body)[^>]*>",
        "",
        conteudo,
        flags=re.IGNORECASE,
    )

    # Remove título H1 caso o modelo repita o título do post.
    conteudo = re.sub(
        r"<h1[^>]*>.*?</h1>",
        "",
        conteudo,
        flags=re.IGNORECASE | re.DOTALL,
    )

    return conteudo.strip()


def gerar_conteudo_gemini(titulo, palavra_chave, categoria):
    """
    Gera o conteúdo principal do artigo usando a API do Gemini.
    """

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        print("GEMINI_API_KEY não encontrada. Usando conteúdo de segurança.")
        return None

    client = genai.Client(api_key=api_key)

    prompt = f"""
Você é um redator editorial especializado em SEO, conteúdo útil,
Casa, Organização e Decoração.

Escreva um artigo original em português do Brasil para o blog
"Achados para Casa".

TÍTULO DO POST:
{titulo}

PALAVRA-CHAVE PRINCIPAL:
{palavra_chave}

CATEGORIA:
{categoria}

OBJETIVO PRINCIPAL:
Produzir um artigo que resolva de verdade a dúvida ou necessidade
de quem fez essa pesquisa, com informações práticas que possam
ser aplicadas no cotidiano.

O conteúdo deve ser útil primeiro para a pessoa e otimizado para
mecanismos de busca de forma natural, sem parecer escrito para
um algoritmo.

ESTILO EDITORIAL:

- Escreva em português brasileiro natural.
- Use linguagem clara, próxima, útil e confiável.
- Prefira frases diretas e específicas.
- Varie o tamanho das frases e dos parágrafos.
- Evite tom robótico, acadêmico ou excessivamente formal.
- Evite introduções genéricas que poderiam servir para qualquer tema.
- Entre no assunto rapidamente.
- Não encha o artigo apenas para atingir uma quantidade de palavras.
- Evite repetir a mesma ideia com palavras diferentes.
- Evite conclusões artificiais ou excessivamente motivacionais.
- Não use frases como "neste artigo vamos explorar",
  "no mundo de hoje", "é importante ressaltar",
  "vale ressaltar" ou outras expressões genéricas semelhantes.
- Não mencione inteligência artificial, SEO, palavra-chave,
  mecanismos de busca ou estas instruções.

QUALIDADE E CONFIABILIDADE:

- Não invente pesquisas, estudos, estatísticas, especialistas,
  certificações ou dados.
- Não apresente como fato algo que dependa de condições específicas.
- Evite afirmações absolutas quando não forem necessárias.
- Para recomendações de segurança, instalação, conservação ou uso,
  utilize linguagem responsável e contextualizada.
- Não faça promessas exageradas.
- Não dê garantias de resultado.
- Não copie textos de outros sites.
- Não inclua preços.
- Não inclua links externos.
- Não invente marcas, produtos ou características técnicas.

SEO NATURAL:

- Responda diretamente à intenção de busca representada pelo título.
- Use a palavra-chave principal naturalmente no texto.
- Tente utilizar a palavra-chave principal na parte inicial do artigo,
  desde que a frase permaneça natural.
- Utilize sinônimos, variações e termos semanticamente relacionados.
- Não repita a palavra-chave de forma forçada.
- Os subtítulos devem descrever claramente o conteúdo das seções.
- Não crie subtítulos apenas para inserir a palavra-chave.
- Não repita o título principal dentro do conteúdo.
- Não crie H1.

ESTRUTURA:

- Produza aproximadamente 900 a 1300 palavras.
- Comece diretamente com uma introdução útil em <p>.
- Depois da introdução, organize o conteúdo em seções com <h2>.
- Use <h3> somente quando houver uma subdivisão realmente útil.
- Use listas quando elas facilitarem a leitura.
- Inclua exemplos práticos quando ajudarem a entender a orientação.
- Dê preferência a recomendações que o leitor consiga aplicar.
- Quando houver diferentes opções, explique em que situação cada
  uma pode fazer mais sentido.
- Termine de maneira natural, reforçando os pontos mais úteis sem
  simplesmente repetir toda a introdução.
- O último subtítulo não precisa se chamar "Conclusão".

FORMATAÇÃO:

Retorne SOMENTE o conteúdo HTML que será inserido no corpo
de uma postagem do Blogger.

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

O primeiro caractere útil da resposta deve fazer parte de uma tag <p>.
Não escreva comentários ou explicações antes ou depois do artigo.
"""

    tentativas = 3
    esperas = [5, 15]

    for tentativa in range(1, tentativas + 1):
        try:
            print(f"Tentativa {tentativa}/{tentativas} com Gemini...")

            resposta = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt,
            )

            conteudo = resposta.text

            if not conteudo:
                raise RuntimeError(
                    "Gemini retornou uma resposta sem conteúdo."
                )

            conteudo = limpar_html_gemini(conteudo)

            if not conteudo:
                raise RuntimeError(
                    "O conteúdo ficou vazio após a limpeza."
                )

            return conteudo

        except Exception as erro:
            print(
                f"Erro na tentativa {tentativa}/{tentativas} "
                f"com Gemini: {erro}"
            )

            mensagem_erro = str(erro)

            erro_temporario = any(
                codigo in mensagem_erro
                for codigo in (
                    "429",
                    "503",
                    "RESOURCE_EXHAUSTED",
                    "UNAVAILABLE",
                )
            )

            if not erro_temporario:
                print(
                    "Erro não temporário. "
                    "As novas tentativas foram interrompidas."
                )
                break

            if tentativa < tentativas:
                espera = esperas[tentativa - 1]

                print(
                    f"Aguardando {espera} segundos "
                    "antes da próxima tentativa..."
                )

                time.sleep(espera)

    print("Gemini indisponível após as tentativas.")
    return None


def criar_conteudo_fallback(titulo, palavra_chave):
    """
    Conteúdo de segurança usado se o Gemini não responder.

    Este conteúdo não deve ser publicado automaticamente.
    A validação exige um artigo completo.
    """

    introducao = criar_introducao(titulo, palavra_chave)

    partes = [
        f"<p>{html.escape(introducao)}</p>",
        f"<h2>O que considerar sobre {html.escape(palavra_chave)}</h2>",
        (
            "<p>Antes de escolher uma solução para sua casa, analise "
            "o espaço disponível, a praticidade e as necessidades "
            "reais do ambiente.</p>"
        ),
        "<h2>Pontos que merecem atenção</h2>",
        (
            "<p>Medidas, materiais, facilidade de uso, manutenção e "
            "adequação à rotina são alguns dos aspectos que podem ser "
            "comparados antes de tomar uma decisão.</p>"
        ),
        "<h2>Como avaliar as opções</h2>",
        (
            "<p>Considere como cada alternativa se encaixa no espaço "
            "e na rotina da casa. Uma solução útil é aquela que atende "
            "à necessidade do ambiente sem criar novas dificuldades.</p>"
        ),
    ]

    return "\n".join(partes)


def criar_estrutura_artigo(
    titulo,
    palavra_chave,
    categoria="Casa e Decoração",
    introducao="",
    secoes=None,
    conclusao=""
):
    """
    Cria o artigo e mantém o mesmo formato esperado pelo main.py.

    Os parâmetros introducao, secoes e conclusao são mantidos
    por compatibilidade com a versão anterior do sistema.
    """

    titulo = limpar_texto(titulo)
    palavra_chave = limpar_texto(palavra_chave)
    categoria = limpar_texto(categoria)

    print("\nGerando artigo com Gemini...")

    conteudo_html = gerar_conteudo_gemini(
        titulo=titulo,
        palavra_chave=palavra_chave,
        categoria=categoria,
    )

    fonte = "gemini"

    if conteudo_html:
        print("Artigo gerado pelo Gemini com sucesso.")
    else:
        print("Gemini indisponível. Ativando conteúdo de segurança.")

        conteudo_html = criar_conteudo_fallback(
            titulo=titulo,
            palavra_chave=palavra_chave,
        )

        fonte = "fallback"

    return {
        "titulo": titulo,
        "palavra_chave": palavra_chave,
        "categoria": categoria,
        "conteudo_html": conteudo_html,
        "fonte": fonte,
    }


def extrair_texto_html(conteudo):
    """
    Remove as tags HTML para permitir verificações sobre
    o texto efetivamente produzido.
    """
    if not conteudo:
        return ""

    texto = re.sub(r"<[^>]+>", " ", conteudo)
    texto = html.unescape(texto)
    texto = re.sub(r"\s+", " ", texto)

    return texto.strip()


def validar_artigo(artigo):
    """
    Faz verificações antes de o artigo seguir para publicação.
    """

    erros = []

    titulo = artigo.get("titulo", "")
    palavra_chave = artigo.get("palavra_chave", "")
    conteudo = artigo.get("conteudo_html", "")
    fonte = artigo.get("fonte", "")

    if not titulo:
        erros.append("Título ausente.")

    if not palavra_chave:
        erros.append("Palavra-chave ausente.")

    if not conteudo:
        erros.append("Conteúdo do artigo ausente.")
        return {
            "valido": False,
            "erros": erros,
        }

    # O fallback existe apenas como segurança operacional.
    # Ele nunca deve ser considerado pronto para publicação.
    if fonte == "fallback":
        erros.append(
            "Conteúdo de segurança utilizado; artigo não pode ser publicado."
        )

    conteudo_minusculo = conteudo.lower()

    if "<h2" not in conteudo_minusculo:
        erros.append("Artigo sem subtítulos H2.")

    if "<p" not in conteudo_minusculo:
        erros.append("Artigo sem parágrafos HTML.")

    if "<h1" in conteudo_minusculo:
        erros.append("O conteúdo não deve conter H1.")

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
                f"HTML não permitido encontrado no artigo: {tag}"
            )

    texto_puro = extrair_texto_html(conteudo)

    palavras = re.findall(
        r"\b[\wÀ-ÿ'-]+\b",
        texto_puro,
        flags=re.UNICODE,
    )

    quantidade_palavras = len(palavras)

    if quantidade_palavras < 750:
        erros.append(
            f"Artigo muito curto: {quantidade_palavras} palavras."
        )

    if quantidade_palavras > 1600:
        erros.append(
            f"Artigo muito longo: {quantidade_palavras} palavras."
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
            f"Poucos subtítulos H2: {quantidade_h2} encontrados."
        )

    if palavra_chave:
        ocorrencias_palavra_chave = texto_puro.lower().count(
            palavra_chave.lower()
        )

        if ocorrencias_palavra_chave == 0:
            erros.append(
                "A palavra-chave principal não aparece no artigo."
            )

        # Evita repetição exagerada sem impor densidade artificial.
        if ocorrencias_palavra_chave > 12:
            erros.append(
                "A palavra-chave principal aparece em excesso."
            )

    return {
        "valido": len(erros) == 0,
        "erros": erros,
        "quantidade_palavras": quantidade_palavras,
        "quantidade_h2": quantidade_h2,
    }


if __name__ == "__main__":
    teste = criar_estrutura_artigo(
        titulo="Como organizar uma cozinha pequena de forma prática",
        palavra_chave="organização de cozinha pequena",
    )

    verificacao = validar_artigo(teste)

    print("Módulo de geração de artigos iniciado com sucesso.")
    print("Título:", teste["titulo"])
    print("Palavra-chave:", teste["palavra_chave"])
    print("Fonte:", teste["fonte"])
    print("Validação:", verificacao)
