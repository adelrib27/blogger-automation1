import html
import re


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
    Cria uma introdução base para o artigo.
    Depois este conteúdo poderá ser produzido pela IA.
    """
    titulo = limpar_texto(titulo)
    palavra_chave = limpar_texto(palavra_chave)

    return (
        f"Se você está pesquisando sobre {palavra_chave}, "
        f"este guia foi preparado para ajudar você a entender "
        f"o assunto de forma prática antes de tomar uma decisão."
    )


def criar_estrutura_artigo(
    titulo,
    palavra_chave,
    categoria="Casa e Decoração",
    introducao="",
    secoes=None,
    conclusao=""
):
    """
    Monta um artigo estruturado em HTML compatível com o Blogger.
    """

    titulo = limpar_texto(titulo)
    palavra_chave = limpar_texto(palavra_chave)
    categoria = limpar_texto(categoria)

    if not introducao:
        introducao = criar_introducao(titulo, palavra_chave)

    if secoes is None:
        secoes = [
            {
                "titulo": f"O que saber sobre {palavra_chave}",
                "conteudo": (
                    f"Antes de escolher, vale analisar as características "
                    f"mais importantes relacionadas a {palavra_chave}."
                )
            },
            {
                "titulo": "Principais vantagens",
                "conteudo": (
                    "Observe praticidade, funcionalidade, espaço disponível "
                    "e como a solução pode facilitar a rotina da casa."
                )
            },
            {
                "titulo": "Como escolher",
                "conteudo": (
                    "Compare materiais, medidas, acabamento, facilidade de uso "
                    "e as necessidades reais do ambiente."
                )
            }
        ]

    if not conclusao:
        conclusao = (
            f"A melhor escolha depende das necessidades de cada ambiente. "
            f"Avaliar com atenção os detalhes de {palavra_chave} ajuda a "
            f"encontrar uma opção mais adequada para sua casa."
        )

    partes = []

    partes.append(f"<p>{html.escape(introducao)}</p>")

    for secao in secoes:
        titulo_secao = limpar_texto(secao.get("titulo", ""))
        conteudo_secao = limpar_texto(secao.get("conteudo", ""))

        if titulo_secao:
            partes.append(f"<h2>{html.escape(titulo_secao)}</h2>")

        if conteudo_secao:
            partes.append(f"<p>{html.escape(conteudo_secao)}</p>")

    partes.append("<h2>Conclusão</h2>")
    partes.append(f"<p>{html.escape(conclusao)}</p>")

    return {
        "titulo": titulo,
        "palavra_chave": palavra_chave,
        "categoria": categoria,
        "conteudo_html": "\n".join(partes)
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

    if len(conteudo) < 300:
        erros.append("Conteúdo ainda muito curto.")

    return {
        "valido": len(erros) == 0,
        "erros": erros
    }


if __name__ == "__main__":
    teste = criar_estrutura_artigo(
        titulo="Como organizar uma cozinha pequena de forma prática",
        palavra_chave="organização de cozinha pequena"
    )

    verificacao = validar_artigo(teste)

    print("Módulo de geração de artigos iniciado com sucesso.")
    print("Título:", teste["titulo"])
    print("Palavra-chave:", teste["palavra_chave"])
    print("Validação:", verificacao)
