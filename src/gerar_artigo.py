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
        f"a entender melhor o assunto e tomar boas decisões para sua casa."
    )


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
Você é um redator especializado em SEO, conteúdo útil e Casa e Decoração.

Escreva um artigo original em português do Brasil para o blog
"Achados para Casa".

TÍTULO:
{titulo}

PALAVRA-CHAVE PRINCIPAL:
{palavra_chave}

CATEGORIA:
{categoria}

OBJETIVO:
Criar um conteúdo realmente útil para pessoas que pesquisam soluções,
ideias e orientações para casa, decoração e organização.

REQUISITOS:

- Escreva entre 900 e 1300 palavras.
- Use linguagem natural, clara e agradável.
- Responda diretamente à intenção de busca.
- Inclua a palavra-chave principal naturalmente.
- Use termos semanticamente relacionados.
- Evite repetição excessiva de palavras-chave.
- Evite frases genéricas e conteúdo superficial.
- Não invente estatísticas, pesquisas ou especialistas.
- Não mencione que o texto foi criado por inteligência artificial.
- Não inclua preço.
- Não inclua links externos.
- Não faça promessas exageradas.
- Não copie textos de outros sites.
- Crie uma introdução envolvente.
- Divida o conteúdo em seções úteis.
- Utilize subtítulos H2.
- Use H3 somente quando realmente necessário.
- Inclua dicas práticas e exemplos quando forem úteis.
- Termine com uma conclusão natural.
- Não coloque o título principal dentro do conteúdo.
- Não use Markdown.
- Retorne somente HTML compatível com o Blogger.

HTML PERMITIDO:
<p>
<h2>
<h3>
<ul>
<ol>
<li>
<strong>

Não use:
<html>
<head>
<body>
<script>
<style>

O artigo deve começar diretamente com um parágrafo <p>.
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
                raise RuntimeError("Gemini retornou uma resposta sem conteúdo.")

            conteudo = conteudo.strip()

            # Remove cercas Markdown caso o modelo as inclua.
            conteudo = re.sub(
                r"^```(?:html)?\s*",
                "",
                conteudo,
                flags=re.IGNORECASE,
            )
            conteudo = re.sub(r"\s*```$", "", conteudo)

            return conteudo.strip()

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
                print("Erro não temporário. As novas tentativas foram interrompidas.")
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
    """

    introducao = criar_introducao(titulo, palavra_chave)

    partes = [
        f"<p>{html.escape(introducao)}</p>",
        f"<h2>O que saber sobre {html.escape(palavra_chave)}</h2>",
        (
            "<p>Antes de escolher uma solução para sua casa, vale analisar "
            "o espaço disponível, a praticidade e as necessidades reais "
            "do ambiente.</p>"
        ),
        "<h2>Principais pontos para avaliar</h2>",
        (
            "<p>Observe materiais, medidas, acabamento, facilidade de uso "
            "e manutenção. Esses detalhes ajudam a encontrar alternativas "
            "mais adequadas para a rotina.</p>"
        ),
        "<h2>Como fazer uma boa escolha</h2>",
        (
            "<p>Compare as opções com calma e considere como cada solução "
            "pode contribuir para organização, conforto e funcionalidade "
            "no dia a dia.</p>"
        ),
        "<h2>Conclusão</h2>",
        (
            f"<p>Avaliar cuidadosamente os detalhes relacionados a "
            f"{html.escape(palavra_chave)} ajuda a escolher soluções "
            "mais adequadas para cada ambiente da casa.</p>"
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

    if conteudo_html:
        print("Artigo gerado pelo Gemini com sucesso.")
    else:
        print("Gemini indisponível. Ativando conteúdo de segurança.")

        conteudo_html = criar_conteudo_fallback(
            titulo=titulo,
            palavra_chave=palavra_chave,
        )

    return {
        "titulo": titulo,
        "palavra_chave": palavra_chave,
        "categoria": categoria,
        "conteudo_html": conteudo_html,
    }


def validar_artigo(artigo):
    """
    Faz verificações básicas antes do artigo seguir
    para publicação.
    """

    erros = []

    if not artigo.get("titulo"):
        erros.append("Título ausente.")

    if not artigo.get("palavra_chave"):
        erros.append("Palavra-chave ausente.")

    conteudo = artigo.get("conteudo_html", "")

    if not conteudo:
        erros.append("Conteúdo do artigo ausente.")

    if len(conteudo) < 1000:
        erros.append("Conteúdo do artigo está muito curto.")

    if "<h2" not in conteudo.lower():
        erros.append("Artigo sem subtítulos H2.")

    return {
        "valido": len(erros) == 0,
        "erros": erros,
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
    print("Validação:", verificacao)
