import json
import re
import unicodedata
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

ARQUIVO_HISTORICO = (
    BASE_DIR / "data" / "historico.json"
)

ARQUIVO_RASCUNHOS = (
    BASE_DIR / "data" / "rascunhos.json"
)


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


def carregar_lista_json(caminho):
    """
    Carrega com segurança um arquivo JSON que contenha uma lista.
    """
    if not caminho.exists():
        return []

    try:
        with caminho.open(
            "r",
            encoding="utf-8",
        ) as arquivo:
            dados = json.load(arquivo)

        if isinstance(dados, list):
            return dados

    except (json.JSONDecodeError, OSError):
        return []

    return []


def carregar_historico():
    """
    Carrega somente conteúdos publicados.
    """
    return carregar_lista_json(
        ARQUIVO_HISTORICO
    )


def carregar_rascunhos():
    """
    Carrega os rascunhos sincronizados do Blogger.
    """
    return carregar_lista_json(
        ARQUIVO_RASCUNHOS
    )


def carregar_base_antirrepeticao():
    """
    Monta a base do motor anti-repetição:

    PUBLICADOS + RASCUNHOS.

    Os arquivos continuam separados.
    """
    publicados = carregar_historico()
    rascunhos = carregar_rascunhos()

    base = []

    for item in publicados:
        registro = dict(item)
        registro["_fonte_antirrepeticao"] = (
            "publicado"
        )
        base.append(registro)

    for item in rascunhos:
        registro = dict(item)
        registro["_fonte_antirrepeticao"] = (
            "rascunho"
        )
        base.append(registro)

    return base


def palavras(texto, remover_fracas=False):
    """
    Transforma um texto em conjunto de palavras relevantes.
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


def radical_simples(palavra):
    """
    Faz uma redução conservadora de algumas terminações
    comuns para melhorar a comparação temática.

    Não tenta substituir um algoritmo linguístico completo.
    """
    palavra = normalizar(palavra)

    if len(palavra) <= 4:
        return palavra

    terminacoes = (
        "ando",
        "endo",
        "indo",
        "ados",
        "adas",
        "idos",
        "idas",
        "ado",
        "ada",
        "ido",
        "ida",
        "ar",
        "er",
        "ir",
    )

    for terminacao in terminacoes:
        if (
            palavra.endswith(terminacao)
            and len(palavra) - len(terminacao) >= 4
        ):
            return palavra[
                : -len(terminacao)
            ]

    # Singularização conservadora.
    if (
        palavra.endswith("s")
        and len(palavra) > 5
    ):
        return palavra[:-1]

    return palavra


def nucleos(texto):
    """
    Extrai os núcleos relevantes de um título/palavra-chave.

    Exemplo:
    'Como organizar uma cozinha pequena'
    tende a produzir conceitos como:
    organizar, cozinha, pequena.
    """
    termos = palavras(
        texto,
        remover_fracas=True,
    )

    return {
        radical_simples(termo)
        for termo in termos
        if radical_simples(termo)
    }


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


def sobreposicao_nucleo(texto_a, texto_b):
    """
    Mede a sobreposição dos núcleos temáticos.

    É uma camada adicional para identificar intenções
    editoriais muito próximas mesmo quando existem
    palavras complementares diferentes.
    """
    conjunto_a = nucleos(texto_a)
    conjunto_b = nucleos(texto_b)

    if not conjunto_a or not conjunto_b:
        return {
            "grau": 0.0,
            "comuns": set(),
        }

    comuns = conjunto_a.intersection(
        conjunto_b
    )

    menor = min(
        len(conjunto_a),
        len(conjunto_b),
    )

    if menor == 0:
        return {
            "grau": 0.0,
            "comuns": set(),
        }

    return {
        "grau": len(comuns) / menor,
        "comuns": comuns,
    }


def mesmo_nucleo_tematico(texto_a, texto_b):
    """
    Detecta pautas com núcleo editorial muito próximo.

    Para bloquear, exigimos pelo menos três conceitos
    relevantes em comum. Isso reduz o risco de rejeitar
    pautas apenas porque compartilham uma palavra genérica
    como 'cozinha', 'sala' ou 'banheiro'.
    """
    resultado = sobreposicao_nucleo(
        texto_a,
        texto_b,
    )

    comuns = resultado["comuns"]
    grau = resultado["grau"]

    return (
        len(comuns) >= 3
        and grau >= 0.60
    )


def palavra_chave_no_titulo(
    palavra_chave,
    titulo,
):
    """
    Verifica se os termos relevantes da palavra-chave
    aparecem significativamente no título existente.
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
    Compara uma nova pauta com posts publicados
    e rascunhos existentes no Blogger.
    """
    base_antirrepeticao = (
        carregar_base_antirrepeticao()
    )

    titulo_normalizado = normalizar(titulo)

    palavra_normalizada = normalizar(
        palavra_chave
    )

    for item in base_antirrepeticao:
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

        # 2. Mesma palavra-chave.
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

        # 3. Palavra-chave já representada
        # pelo título existente.
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

        # 4. Similaridade geral dos títulos.
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

        # 6. Núcleo temático/intenção editorial.
        if mesmo_nucleo_tematico(
            titulo_normalizado,
            titulo_antigo,
        ):
            return {
                "repetida": True,
                "motivo": (
                    "núcleo temático muito semelhante"
                ),
                "item": item,
            }

        # 7. Também compara a palavra-chave atual
        # diretamente com o título existente.
        if (
            palavra_chave
            and mesmo_nucleo_tematico(
                palavra_chave,
                titulo_antigo,
            )
        ):
            return {
                "repetida": True,
                "motivo": (
                    "intenção da palavra-chave "
                    "muito semelhante"
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
    Mantém compatibilidade com chamadas existentes.
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

    Considera publicados e rascunhos.
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

            fonte = item.get(
                "_fonte_antirrepeticao",
                "não identificada",
            )

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

            print(
                "- Fonte:",
                fonte,
            )

            continue

        aprovadas.append(pauta)

    return aprovadas


if __name__ == "__main__":
    publicados = carregar_historico()
    rascunhos = carregar_rascunhos()

    print(
        "Motor de pautas iniciado com sucesso."
    )

    print(
        "Publicados registrados:",
        len(publicados),
    )

    print(
        "Rascunhos registrados:",
        len(rascunhos),
    )

    print(
        "Total protegido contra repetição:",
        len(publicados) + len(rascunhos),
    )
