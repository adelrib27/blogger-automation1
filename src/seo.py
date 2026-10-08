import re
import unicodedata


def limpar_espacos(texto):
    """Remove espaços duplicados e espaços desnecessários."""
    return re.sub(r"\s+", " ", str(texto)).strip()


def remover_acentos(texto):
    """Remove acentos para criação de slug."""
    texto = unicodedata.normalize("NFKD", str(texto))
    return "".join(c for c in texto if not unicodedata.combining(c))


def criar_slug(texto):
    """
    Converte um título em slug amigável para SEO.
    Exemplo:
    'Como Organizar uma Cozinha Pequena'
    vira:
    'como-organizar-uma-cozinha-pequena'
    """
    texto = remover_acentos(texto).lower()
    texto = re.sub(r"[^a-z0-9\s-]", "", texto)
    texto = re.sub(r"[\s_-]+", "-", texto)
    return texto.strip("-")


def limitar_texto(texto, limite):
    """
    Limita um texto sem cortar uma palavra no meio.
    """
    texto = limpar_espacos(texto)

    if len(texto) <= limite:
        return texto

    texto = texto[:limite].rsplit(" ", 1)[0]
    return texto.rstrip(" ,.;:-")


def otimizar_titulo(titulo, palavra_chave="", limite=60):
    """
    Prepara o título para SEO e respeita o limite configurado.
    """
    titulo = limpar_espacos(titulo)
    palavra_chave = limpar_espacos(palavra_chave)

    if palavra_chave and palavra_chave.lower() not in titulo.lower():
        candidato = f"{palavra_chave}: {titulo}"

        if len(candidato) <= limite:
            titulo = candidato

    return limitar_texto(titulo, limite)


def criar_meta_description(texto, palavra_chave="", limite=155):
    """
    Cria uma meta description curta a partir do conteúdo recebido.
    """
    texto = re.sub(r"<[^>]+>", " ", str(texto))
    texto = limpar_espacos(texto)

    palavra_chave = limpar_espacos(palavra_chave)

    if palavra_chave and palavra_chave.lower() not in texto.lower():
        texto = f"{palavra_chave}: {texto}"

    meta = limitar_texto(texto, limite)

    if meta and meta[-1] not in ".!?":
        if len(meta) < limite:
            meta += "."

    return meta


def gerar_palavras_chave(palavra_principal, secundarias=None):
    """
    Organiza a palavra-chave principal e as palavras secundárias,
    removendo duplicações.
    """
    secundarias = secundarias or []

    palavras = [palavra_principal] + list(secundarias)
    resultado = []
    usadas = set()

    for palavra in palavras:
        palavra = limpar_espacos(palavra)

        if not palavra:
            continue

        chave = palavra.lower()

        if chave not in usadas:
            usadas.add(chave)
            resultado.append(palavra)

    return resultado


def preparar_seo(
    titulo,
    palavra_chave,
    descricao,
    palavras_secundarias=None,
    titulo_max=60,
    meta_max=155,
):
    """
    Monta o pacote SEO completo de um artigo.
    """
    titulo_seo = otimizar_titulo(
        titulo,
        palavra_chave,
        titulo_max,
    )

    meta_description = criar_meta_description(
        descricao,
        palavra_chave,
        meta_max,
    )

    palavras_chave = gerar_palavras_chave(
        palavra_chave,
        palavras_secundarias,
    )

    return {
        "titulo": titulo_seo,
        "slug": criar_slug(titulo_seo),
        "meta_description": meta_description,
        "palavra_chave": palavra_chave,
        "palavras_chave": palavras_chave,
    }


if __name__ == "__main__":
    teste = preparar_seo(
        titulo="Como deixar a sala mais bonita gastando pouco",
        palavra_chave="decoração de sala",
        descricao=(
            "Descubra ideias práticas para transformar a sala "
            "com organização, iluminação e decoração."
        ),
        palavras_secundarias=[
            "decoração barata",
            "sala pequena",
            "organização da sala",
        ],
    )

    print("Módulo SEO iniciado com sucesso.")
    print(teste)
