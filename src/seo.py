import re
import unicodedata


def limpar_espacos(texto):
    """
    Remove espaços duplicados e espaços desnecessários.
    """

    if not texto:
        return ""

    return re.sub(
        r"\s+",
        " ",
        str(texto),
    ).strip()


def remover_acentos(texto):
    """
    Remove acentos para criação de slug
    e comparações.
    """

    texto = unicodedata.normalize(
        "NFKD",
        str(texto),
    )

    return "".join(
        caractere
        for caractere in texto
        if not unicodedata.combining(
            caractere
        )
    )


def criar_slug(texto):
    """
    Converte um título em slug amigável.
    """

    texto = limpar_espacos(
        texto
    )

    texto = remover_acentos(
        texto
    ).lower()

    texto = re.sub(
        r"[^a-z0-9\s-]",
        "",
        texto,
    )

    texto = re.sub(
        r"[\s_-]+",
        "-",
        texto,
    )

    return texto.strip(
        "-"
    )


def limitar_texto(
    texto,
    limite,
):
    """
    Limita texto sem cortar palavras no meio.

    Função genérica usada principalmente
    para títulos.
    """

    texto = limpar_espacos(
        texto
    )

    if not texto:
        return ""

    if len(
        texto
    ) <= limite:
        return texto

    trecho = texto[
        :limite
    ]

    if " " in trecho:
        trecho = trecho.rsplit(
            " ",
            1,
        )[0]

    return trecho.rstrip(
        " ,.;:-"
    )


def finalizar_frase(
    texto,
    limite,
):
    """
    Garante pontuação final quando possível.
    """

    texto = limpar_espacos(
        texto
    )

    if not texto:
        return ""

    if texto[
        -1
    ] in ".!?":
        return texto

    if len(
        texto
    ) < limite:
        return texto + "."

    return texto


# Palavras que normalmente indicam que
# uma meta description terminou no meio
# de uma ideia.
PALAVRAS_FINAIS_FRACAS = {
    "a",
    "ao",
    "aos",
    "as",
    "com",
    "como",
    "da",
    "das",
    "de",
    "do",
    "dos",
    "e",
    "em",
    "entre",
    "na",
    "nas",
    "no",
    "nos",
    "o",
    "os",
    "ou",
    "para",
    "pela",
    "pelas",
    "pelo",
    "pelos",
    "por",
    "que",
    "se",
    "sem",
    "sobre",
    "um",
    "uma",
    "usando",
    "utilizando",
}


def remover_final_fraco(
    texto,
):
    """
    Remove palavras penduradas no final
    de um texto truncado.

    Exemplo:
    '...por mais tempo usando'
    vira:
    '...por mais tempo'
    """

    texto = limpar_espacos(
        texto
    ).rstrip(
        " ,;:-"
    )

    if not texto:
        return ""

    while True:
        partes = texto.split()

        if not partes:
            return ""

        ultima = remover_acentos(
            partes[-1]
        ).lower().strip(
            ".,;:!?()[]{}"
        )

        if (
            ultima
            not in PALAVRAS_FINAIS_FRACAS
        ):
            break

        partes.pop()

        texto = " ".join(
            partes
        ).rstrip(
            " ,;:-"
        )

    return texto


def encontrar_frase_completa(
    texto,
    limite,
):
    """
    Procura a última frase completa que caiba
    naturalmente dentro do limite.

    Retorna vazio se nenhuma frase completa
    adequada for encontrada.
    """

    if not texto:
        return ""

    trecho = texto[
        :limite + 1
    ]

    posicoes = []

    for correspondencia in re.finditer(
        r"[.!?](?=\s|$)",
        trecho,
    ):
        posicoes.append(
            correspondencia.end()
        )

    if not posicoes:
        return ""

    posicao = posicoes[
        -1
    ]

    candidato = trecho[
        :posicao
    ].strip()

    # Evita escolher uma primeira frase
    # excessivamente curta quando a descrição
    # original contém muito mais informação.
    if len(
        candidato
    ) < 70:
        return ""

    return candidato


def encontrar_pausa_natural(
    texto,
    limite,
):
    """
    Quando não existe uma frase completa,
    tenta terminar em vírgula, ponto e vírgula
    ou dois-pontos antes de recorrer ao corte
    por palavra.
    """

    trecho = texto[
        :limite
    ]

    candidatos = []

    for caractere in (
        ",",
        ";",
        ":",
    ):
        posicao = trecho.rfind(
            caractere
        )

        if posicao >= 70:
            candidatos.append(
                posicao
            )

    if not candidatos:
        return ""

    posicao = max(
        candidatos
    )

    return trecho[
        :posicao
    ].strip(
        " ,;:-"
    )


def cortar_meta_com_sentido(
    texto,
    limite,
):
    """
    Limita uma meta description priorizando
    sentido completo, não apenas quantidade
    de caracteres.

    Ordem:
    1. texto completo, se couber;
    2. frase completa;
    3. pausa natural;
    4. corte por palavra;
    5. remoção de final fraco.
    """

    texto = limpar_espacos(
        texto
    )

    if not texto:
        return ""

    if len(
        texto
    ) <= limite:
        return finalizar_frase(
            texto,
            limite,
        )

    frase = encontrar_frase_completa(
        texto,
        limite,
    )

    if frase:
        return frase

    pausa = encontrar_pausa_natural(
        texto,
        limite,
    )

    if pausa:
        pausa = remover_final_fraco(
            pausa
        )

        if pausa:
            return finalizar_frase(
                pausa,
                limite,
            )

    trecho = texto[
        :limite
    ]

    if " " in trecho:
        trecho = trecho.rsplit(
            " ",
            1,
        )[0]

    trecho = remover_final_fraco(
        trecho
    )

    # Reserva espaço para pontuação.
    if len(
        trecho
    ) >= limite:
        trecho = trecho[
            :limite - 1
        ]

        if " " in trecho:
            trecho = trecho.rsplit(
                " ",
                1,
            )[0]

        trecho = remover_final_fraco(
            trecho
        )

    return finalizar_frase(
        trecho,
        limite,
    )


def otimizar_titulo(
    titulo,
    palavra_chave="",
    limite=60,
):
    """
    Mantém títulos naturais e dentro
    do limite configurado.

    A palavra-chave não é forçada
    no início do título.
    """

    titulo = limpar_espacos(
        titulo
    )

    palavra_chave = limpar_espacos(
        palavra_chave
    )

    if not titulo:
        titulo = palavra_chave

    return limitar_texto(
        titulo,
        limite,
    )


def criar_meta_description(
    texto,
    palavra_chave="",
    limite=155,
):
    """
    Cria uma meta description natural.

    A prioridade é:
    - clareza;
    - sentido completo;
    - intenção de busca;
    - limite de caracteres.

    Nunca força a palavra-chave quando isso
    deixa a descrição artificial ou truncada.
    """

    texto = re.sub(
        r"<[^>]+>",
        " ",
        str(
            texto or ""
        ),
    )

    texto = limpar_espacos(
        texto
    )

    palavra_chave = limpar_espacos(
        palavra_chave
    )

    if not texto:
        if palavra_chave:
            texto = (
                "Veja dicas práticas sobre "
                f"{palavra_chave} e encontre "
                "ideias úteis para o dia a dia."
            )
        else:
            return ""

    # Primeiro preserva a descrição original
    # sempre que ela já estiver natural.
    if len(
        texto
    ) <= limite:
        return finalizar_frase(
            texto,
            limite,
        )

    # Se a palavra-chave não estiver presente,
    # tentamos uma versão SEO somente quando
    # ela couber sem truncamento.
    if (
        palavra_chave
        and palavra_chave.lower()
        not in texto.lower()
    ):
        primeira_letra = (
            texto[
                0
            ].lower()
            if texto
            else ""
        )

        restante = (
            texto[
                1:
            ]
            if len(
                texto
            ) > 1
            else ""
        )

        texto_minusculo = (
            primeira_letra
            + restante
        )

        candidatos = [
            (
                f"Veja dicas de "
                f"{palavra_chave} e "
                f"{texto_minusculo}"
            ),
            (
                f"Confira ideias de "
                f"{palavra_chave} para "
                f"{texto_minusculo}"
            ),
        ]

        for candidato in candidatos:
            if len(
                candidato
            ) <= limite:
                return finalizar_frase(
                    candidato,
                    limite,
                )

    # Se a descrição é maior que o limite,
    # priorizamos encerramento natural.
    return cortar_meta_com_sentido(
        texto,
        limite,
    )


def gerar_palavras_chave(
    palavra_principal,
    secundarias=None,
):
    """
    Organiza a palavra-chave principal
    e os termos secundários,
    removendo duplicações.
    """

    secundarias = (
        secundarias or []
    )

    palavras = [
        palavra_principal
    ] + list(
        secundarias
    )

    resultado = []
    usadas = set()

    for palavra in palavras:
        palavra = limpar_espacos(
            palavra
        )

        if not palavra:
            continue

        chave = remover_acentos(
            palavra
        ).lower()

        if chave not in usadas:
            usadas.add(
                chave
            )

            resultado.append(
                palavra
            )

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

    meta_description = (
        criar_meta_description(
            texto=descricao,
            palavra_chave=palavra_chave,
            limite=meta_max,
        )
    )

    palavras_chave = (
        gerar_palavras_chave(
            palavra_principal=(
                palavra_chave
            ),
            secundarias=(
                palavras_secundarias
            ),
        )
    )

    return {
        "titulo": titulo_seo,
        "slug": criar_slug(
            titulo_seo
        ),
        "meta_description": (
            meta_description
        ),
        "palavra_chave": (
            limpar_espacos(
                palavra_chave
            )
        ),
        "palavras_chave": (
            palavras_chave
        ),
    }


if __name__ == "__main__":
    teste = preparar_seo(
        titulo=(
            "Como deixar a sala mais "
            "bonita gastando pouco"
        ),
        palavra_chave=(
            "decoração de sala"
        ),
        descricao=(
            "Descubra ideias práticas para "
            "transformar a sala com organização, "
            "iluminação e decoração."
        ),
        palavras_secundarias=[
            "decoração barata",
            "sala pequena",
            "organização da sala",
        ],
    )

    print(
        "Módulo SEO iniciado "
        "com sucesso."
    )

    print(
        "Título:",
        teste[
            "titulo"
        ],
    )

    print(
        "Slug:",
        teste[
            "slug"
        ],
    )

    print(
        "Meta description:",
        teste[
            "meta_description"
        ],
    )

    print(
        "Tamanho da meta:",
        len(
            teste[
                "meta_description"
            ]
        ),
    )

    print(
        "Palavras-chave:",
        teste[
            "palavras_chave"
        ],
    )
