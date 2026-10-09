import json
import re
import unicodedata
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
ARQUIVO_HISTORICO = BASE_DIR / "data" / "historico.json"


PALAVRAS_FRACAS = {
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
    "esta",
    "este",
    "estes",
    "estas",
    "mais",
    "na",
    "nas",
    "no",
    "nos",
    "o",
    "os",
    "para",
    "por",
    "que",
    "se",
    "sem",
    "uma",
    "um",
    "vale",
    "pena",
    "review",
    "analise",
    "completa",
    "oferta",
}


def normalizar(texto):
    """
    Normaliza textos para comparação.
    """
    texto = str(texto or "").lower().strip()

    texto = unicodedata.normalize(
        "NFD",
        texto,
    )

    texto = "".join(
        caractere
        for caractere in texto
        if unicodedata.category(caractere) != "Mn"
    )

    texto = re.sub(
        r"[^a-z0-9\s]",
        " ",
        texto,
    )

    texto = re.sub(
        r"\s+",
        " ",
        texto,
    )

    return texto.strip()


def carregar_historico():
    """
    Carrega os conteúdos já registrados no histórico.
    """
    if not ARQUIVO_HISTORICO.exists():
        return []

    try:
        with ARQUIVO_HISTORICO.open(
            "r",
            encoding="utf-8",
        ) as arquivo:
            dados = json.load(arquivo)

        if isinstance(dados, list):
            return dados

    except (json.JSONDecodeError, OSError):
        return []

    return []


def palavras(texto, remover_fracas=False):
    """
    Transforma um texto em conjunto de palavras.

    Quando remover_fracas=True, palavras genéricas são
    descartadas para dar mais peso ao assunto real.
    """
    conjunto = set(
        normalizar(texto).split()
    )

    if remover_fracas:
        conjunto = {
            palavra
            for palavra in conjunto
            if palavra not in PALAVRAS_FRACAS
            and len(palavra) >= 3
        }

    return conjunto


def similaridade(texto_a, texto_b):
    """
    Calcula similaridade de Jaccard entre dois textos.
    """
    conjunto_a = palavras(
        texto_a,
        remover_fracas=True,
    )

    conjunto_b = palavras(
        texto_b,
        remover_fracas=True,
    )

    if not conjunto_a or not conjunto_b:
        return 0.0

    intersecao = conjunto_a.intersection(
        conjunto_b
    )

    uniao = conjunto_a.union(
        conjunto_b
    )

    return len(intersecao) / len(uniao)


def sobreposicao_assunto(texto_a, texto_b):
    """
    Mede quanto dos termos relevantes do texto menor
    aparece no outro texto.

    Isso ajuda a identificar pautas sobre o mesmo assunto
    mesmo quando os títulos são escritos de formas diferentes.
    """
    conjunto_a = palavras(
        texto_a,
        remover_fracas=True,
    )

    conjunto_b = palavras(
        texto_b,
        remover_fracas=True,
    )

    if not conjunto_a or not conjunto_b:
        return 0.0

    intersecao = conjunto_a.intersection(
        conjunto_b
    )

    menor_conjunto = min(
        len(conjunto_a),
        len(conjunto_b),
    )

    if menor_conjunto == 0:
        return 0.0

    return len(intersecao) / menor_conjunto


def palavra_chave_no_titulo(
    palavra_chave,
    titulo,
):
    """
    Verifica se os termos relevantes da palavra-chave
    aparecem de forma significativa no título histórico.
    """
    termos_chave = palavras(
        palavra_chave,
        remover_fracas=True,
    )

    termos_titulo = palavras(
        titulo,
        remover_fracas=True,
    )

    if not termos_chave or not termos_titulo:
        return False

    intersecao = termos_chave.intersection(
        termos_titulo
    )

    # Para palavras-chave com apenas um termo relevante,
    # exige correspondência direta.
    if len(termos_chave) == 1:
        return termos_chave.issubset(
            termos_titulo
        )

    proporcao = (
        len(intersecao)
        / len(termos_chave)
    )

    return proporcao >= 0.75


def comparar_com_historico(
    titulo,
    palavra_chave="",
    limite_similaridade=0.60,
    limite_assunto=0.75,
):
    """
    Compara uma pauta com todo o histórico.

    Retorna informações sobre eventual conflito.
    """
    historico = carregar_historico()

    titulo_normalizado = normalizar(titulo)
    palavra_normalizada = normalizar(
        palavra_chave
    )

    for item in historico:
        titulo_antigo = normalizar(
            item.get("titulo", "")
        )

        palavra_antiga = normalizar(
            item.get("palavra_chave", "")
        )

        # 1. Mesmo título.
        if (
            titulo_normalizado
            and titulo_normalizado
            == titulo_antigo
        ):
            return {
                "repetida": True,
                "motivo": "título idêntico",
                "item": item,
            }

        # 2. Mesma palavra-chave já registrada.
        if (
            palavra_normalizada
            and palavra_antiga
            and palavra_normalizada
            == palavra_antiga
        ):
            return {
                "repetida": True,
                "motivo": (
                    "palavra-chave idêntica"
                ),
                "item": item,
            }

        # 3. Palavra-chave atual já representada
        # pelo título de um artigo antigo.
        if (
            palavra_chave
            and palavra_chave_no_titulo(
                palavra_chave,
                titulo_antigo,
            )
        ):
            return {
                "repetida": True,
                "motivo": (
                    "assunto da palavra-chave "
                    "já coberto"
                ),
                "item": item,
            }

        # 4. Similaridade geral entre títulos.
        grau_similaridade = similaridade(
            titulo_normalizado,
            titulo_antigo,
        )

        if (
            grau_similaridade
            >= limite_similaridade
        ):
            return {
                "repetida": True,
                "motivo": (
                    "título muito semelhante"
                ),
                "item": item,
            }

        # 5. Forte sobreposição de assunto.
        grau_assunto = sobreposicao_assunto(
            titulo_normalizado,
            titulo_antigo,
        )

        if grau_assunto >= limite_assunto:
            return {
                "repetida": True,
                "motivo": (
                    "assunto muito semelhante"
                ),
                "item": item,
            }

    return {
        "repetida": False,
        "motivo": "",
        "item": None,
    }


def pauta_ja_utilizada(
    titulo,
    palavra_chave="",
    limite=0.60,
):
    """
    Mantém compatibilidade com o main.py e com
    chamadas existentes do sistema.
    """
    resultado = comparar_com_historico(
        titulo=titulo,
        palavra_chave=palavra_chave,
        limite_similaridade=limite,
    )

    return resultado["repetida"]


def filtrar_pautas(pautas):
    """
    Retorna somente pautas ainda não utilizadas.

    Também informa no log quando uma pauta é rejeitada,
    facilitando a auditoria do sistema.
    """
    aprovadas = []

    for pauta in pautas:
        titulo = pauta.get(
            "titulo",
            "",
        )

        palavra_chave = pauta.get(
            "palavra_chave",
            "",
        )

        resultado = comparar_com_historico(
            titulo=titulo,
            palavra_chave=palavra_chave,
        )

        if resultado["repetida"]:
            item = resultado.get(
                "item"
            ) or {}

            print(
                "\nPauta ignorada por repetição:"
            )
            print(
                "- Nova pauta:",
                titulo,
            )
            print(
                "- Motivo:",
                resultado["motivo"],
            )
            print(
                "- Conteúdo existente:",
                item.get(
                    "titulo",
                    "Não identificado",
                ),
            )

            continue

        aprovadas.append(pauta)

    return aprovadas


if __name__ == "__main__":
    historico = carregar_historico()

    print(
        "Motor de pautas iniciado com sucesso."
    )

    print(
        "Itens registrados no histórico:",
        len(historico),
    )
