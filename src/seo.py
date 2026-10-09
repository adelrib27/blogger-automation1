import re
import unicodedata


def limpar_espacos(texto):
    """
    Remove espaços duplicados e espaços desnecessários.
    """
    if not texto:
        return ""

    return re.sub(r"\s+", " ", str(texto)).strip()


def remover_acentos(texto):
    """
    Remove acentos para criação de slug.
    """
    texto = unicodedata.normalize("NFKD", str(texto))

    return "".join(
        caractere
        for caractere in texto
        if not unicodedata.combining(caractere)
    )


def criar_slug(texto):
    """
    Converte um título em slug amigável.

    Exemplo:
    'Como Organizar uma Cozinha Pequena'
    vira:
    'como-organizar-uma-cozinha-pequena'
    """
    texto = limpar_espacos(texto)
    texto = remover_acentos(texto).lower()

    texto = re.sub(r"[^a-z0-9\s-]", "", texto)
    texto = re.sub(r"[\s_-]+", "-", texto)

    return texto.strip("-")


def limitar_texto(texto, limite):
    """
    Limita um texto sem cortar palavras no meio.
    """
    texto = limpar_espacos(texto)

    if not texto:
        return ""

    if len(texto) <= limite:
        return texto

    trecho = texto[:limite]

    if " " in trecho:
        trecho = trecho.rsplit(" ", 1)[0]

    return trecho.rstrip(" ,.;:-")


def finalizar_frase(texto, limite):
    """
    Garante pontuação final quando houver espaço disponível.
    """
    texto = limpar_espacos(texto)

    if not texto:
        return ""

    if texto[-1] in ".!?":
        return texto

    if len(texto) < limite:
        return texto + "."

    return texto


def otimizar_titulo(titulo, palavra_chave="", limite=60):
    """
    Mantém títulos naturais e dentro do limite configurado.

    A palavra-chave não é forçada no início do título.
    """
    titulo = limpar_espacos(titulo)
    palavra_chave = limpar_espacos(palavra_chave)

    if not titulo:
        titulo = palavra_chave

    return limitar_texto(titulo, limite)


def criar_meta_description(texto, palavra_chave="", limite=155):
    """
    Cria uma meta description natural a partir da descrição da pauta.

    A palavra-chave pode ser incluída quando couber naturalmente,
    mas nunca é simplesmente adicionada com dois-pontos no início.
    """
    texto = re.sub(r"<[^>]+>", " ", str(texto))
    texto = limpar_espacos(texto)

    palavra_chave = limpar_espacos(palavra_chave)

    if not texto:
        if palavra_chave:
            texto = (
                f"Veja dicas práticas sobre {palavra_chave} "
                f"e encontre ideias úteis para o dia a dia."
            )
        else:
            return ""

    # Se a descrição já contém a palavra-chave, preserve a frase natural.
    if (
        palavra_chave
        and palavra_chave.lower() not in texto.lower()
    ):
        candidatos = [
            f"Veja dicas de {palavra_chave} e {texto[0].lower()}{texto[1:]}",
            f"Confira ideias de {palavra_chave} para {texto[0].lower()}{texto[1:]}",
        ]

        for candidato in candidatos:
            if len(candidato) <= limite:
                texto = candidato
                break

    meta = limitar_texto(texto, limite)

    return finalizar_frase(meta, limite)


def gerar_palavras_chave(palavra_principal, secundarias=None):
    """
    Organiza a palavra-chave principal e os termos secundários,
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

        chave = remover_acentos(palavra).lower()

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
    Monta o pacote SEO completo do artigo.
    """
    titulo_seo = otimizar_titulo(
        titulo=titulo,
        palavra_chave=palavra_chave,
        limite=titulo_max,
    )

    meta_description = criar_meta_description(
        texto=descricao,
        palavra_chave=palavra_chave,
        limite=meta_max,
    )

    palavras_chave = gerar_palavras_chave(
        palavra_principal=palavra_chave,
        secundarias=palavras_secundarias,
    )

    return {
        "titulo": titulo_seo,
        "slug": criar_slug(titulo_seo),
        "meta_description": meta_description,
        "palavra_chave": limpar_espacos(palavra_chave),
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
    print("Título:", teste["titulo"])
    print("Slug:", teste["slug"])
    print("Meta description:", teste["meta_description"])
    print("Palavras-chave:", teste["palavras_chave"])
