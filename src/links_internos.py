import html
import json
import re
import unicodedata
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
HISTORICO_PATH = BASE_DIR / "data" / "historico.json"

PALAVRAS_IGNORADAS = {
    "a", "ao", "aos", "as",
    "com", "como",
    "da", "das", "de", "do", "dos",
    "e", "em",
    "o", "os",
    "para", "por",
    "que",
    "um", "uma", "uns", "umas",
    "vale", "pena",
    "review", "analise", "completa",
    "completo", "oferta",
}


def normalizar(texto):
    """
    Normaliza texto para comparação de assuntos.
    """
    texto = str(texto or "").lower().strip()

    texto = unicodedata.normalize("NFD", texto)

    texto = "".join(
        caractere
        for caractere in texto
        if unicodedata.category(caractere) != "Mn"
    )

    texto = re.sub(r"[^a-z0-9\s]", " ", texto)
    texto = re.sub(r"\s+", " ", texto)

    return texto.strip()


def carregar_historico():
    """
    Carrega apenas os registros existentes no historico.json.
    """
    if not HISTORICO_PATH.exists():
        return []

    try:
        with HISTORICO_PATH.open(
            "r",
            encoding="utf-8",
        ) as arquivo:
            dados = json.load(arquivo)

        if isinstance(dados, list):
            return dados

    except (json.JSONDecodeError, OSError):
        pass

    return []


def extrair_termos(texto):
    """
    Extrai termos relevantes para comparar assuntos.
    """
    termos = set()

    for palavra in normalizar(texto).split():
        if len(palavra) < 3:
            continue

        if palavra in PALAVRAS_IGNORADAS:
            continue

        termos.add(palavra)

    return termos


def calcular_relevancia(
    item,
    titulo_atual,
    palavra_chave,
    categoria="",
):
    """
    Calcula uma pontuação simples de relevância
    entre o novo artigo e um post já publicado.
    """
    titulo_antigo = item.get("titulo", "")
    palavra_antiga = item.get("palavra_chave", "")
    categoria_antiga = item.get("categoria", "")

    termos_atual = extrair_termos(
        f"{titulo_atual} {palavra_chave} {categoria}"
    )

    termos_antigo = extrair_termos(
        f"{titulo_antigo} "
        f"{palavra_antiga} "
        f"{categoria_antiga}"
    )

    termos_comuns = termos_atual.intersection(
        termos_antigo
    )

    pontuacao = len(termos_comuns) * 3

    categoria_normalizada = normalizar(categoria)
    categoria_antiga_normalizada = normalizar(
        categoria_antiga
    )

    if (
        categoria_normalizada
        and categoria_antiga_normalizada
        and categoria_normalizada
        == categoria_antiga_normalizada
    ):
        pontuacao += 2

    palavra_normalizada = normalizar(palavra_chave)

    if palavra_normalizada:
        for termo in extrair_termos(
            palavra_normalizada
        ):
            if termo in termos_antigo:
                pontuacao += 2

    return pontuacao


def url_interna_valida(url):
    """
    Aceita somente URLs reais do blog.
    """
    url = str(url or "").strip()

    return url.startswith(
        "https://achadosparacasa2026.blogspot.com/"
    )


def selecionar_links_internos(
    titulo,
    palavra_chave,
    categoria="",
    limite=3,
):
    """
    Seleciona posts reais e relevantes do histórico.

    Nenhuma URL é criada ou inventada aqui.
    """
    historico = carregar_historico()

    candidatos = []

    for item in historico:
        titulo_antigo = str(
            item.get("titulo", "")
        ).strip()

        url = str(
            item.get("url", "")
        ).strip()

        if not titulo_antigo:
            continue

        if not url_interna_valida(url):
            continue

        # Evita apontar para o próprio artigo,
        # caso ele já esteja no histórico.
        if (
            normalizar(titulo_antigo)
            == normalizar(titulo)
        ):
            continue

        pontuacao = calcular_relevancia(
            item=item,
            titulo_atual=titulo,
            palavra_chave=palavra_chave,
            categoria=categoria,
        )

        if pontuacao <= 0:
            continue

        candidatos.append(
            {
                "titulo": titulo_antigo,
                "url": url,
                "pontuacao": pontuacao,
            }
        )

    candidatos.sort(
        key=lambda item: item["pontuacao"],
        reverse=True,
    )

    selecionados = []
    urls_usadas = set()

    for candidato in candidatos:
        url = candidato["url"]

        if url in urls_usadas:
            continue

        urls_usadas.add(url)
        selecionados.append(candidato)

        if len(selecionados) >= limite:
            break

    return selecionados


def criar_bloco_links(links):
    """
    Cria um pequeno bloco de links internos
    usando somente URLs confirmadas no histórico.
    """
    if not links:
        return ""

    itens = []

    for link in links:
        titulo = html.escape(
            link["titulo"]
        )

        url = html.escape(
            link["url"],
            quote=True,
        )

        itens.append(
            f'<li><a href="{url}">{titulo}</a></li>'
        )

    return (
        "\n<h2>Veja também</h2>\n"
        "<ul>\n"
        + "\n".join(itens)
        + "\n</ul>"
    )


def adicionar_links_internos(
    conteudo_html,
    titulo,
    palavra_chave,
    categoria="",
    limite=3,
):
    """
    Adiciona links internos reais ao final do artigo.

    Se nenhum post relevante for encontrado,
    o conteúdo original permanece intacto.
    """
    links = selecionar_links_internos(
        titulo=titulo,
        palavra_chave=palavra_chave,
        categoria=categoria,
        limite=limite,
    )

    if not links:
        return {
            "conteudo_html": conteudo_html,
            "links": [],
            "quantidade": 0,
        }

    bloco = criar_bloco_links(links)

    conteudo_final = (
        conteudo_html.rstrip()
        + "\n"
        + bloco
    )

    return {
        "conteudo_html": conteudo_final,
        "links": links,
        "quantidade": len(links),
    }


if __name__ == "__main__":
    links = selecionar_links_internos(
        titulo=(
            "Como organizar uma cozinha "
            "pequena de forma prática"
        ),
        palavra_chave=(
            "organização de cozinha pequena"
        ),
        categoria="Organização",
        limite=3,
    )

    print("=== TESTE DE LINKS INTERNOS ===")
    print(
        "Links relevantes encontrados:",
        len(links),
    )

    for numero, link in enumerate(
        links,
        start=1,
    ):
        print()
        print(f"LINK {numero}")
        print("Título:", link["titulo"])
        print("URL:", link["url"])
        print(
            "Pontuação:",
            link["pontuacao"],
        )

    print("\n=== TESTE CONCLUÍDO ===")
