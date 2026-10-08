import json
import os
import re
import unicodedata


ARQUIVO_HISTORICO = "data/historico.json"


def normalizar(texto):
    """Normaliza textos para facilitar a comparação."""
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
    """Carrega o histórico de conteúdos já utilizados."""
    if not os.path.exists(ARQUIVO_HISTORICO):
        return []

    try:
        with open(ARQUIVO_HISTORICO, "r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)

        if isinstance(dados, list):
            return dados

    except (json.JSONDecodeError, OSError):
        pass

    return []


def palavras(texto):
    return set(normalizar(texto).split())


def similaridade(texto_a, texto_b):
    """Calcula semelhança simples entre dois textos."""
    conjunto_a = palavras(texto_a)
    conjunto_b = palavras(texto_b)

    if not conjunto_a or not conjunto_b:
        return 0.0

    intersecao = conjunto_a.intersection(conjunto_b)
    uniao = conjunto_a.union(conjunto_b)

    return len(intersecao) / len(uniao)


def pauta_ja_utilizada(titulo, palavra_chave="", limite=0.60):
    """
    Verifica se uma pauta é muito semelhante a algo
    que já existe no histórico.
    """
    historico = carregar_historico()

    titulo_normalizado = normalizar(titulo)
    palavra_normalizada = normalizar(palavra_chave)

    for item in historico:
        titulo_antigo = normalizar(item.get("titulo", ""))
        palavra_antiga = normalizar(item.get("palavra_chave", ""))

        # Mesmo título
        if titulo_normalizado and titulo_normalizado == titulo_antigo:
            return True

        # Mesma palavra-chave principal
        if (
            palavra_normalizada
            and palavra_antiga
            and palavra_normalizada == palavra_antiga
        ):
            return True

        # Títulos muito semelhantes
        if similaridade(titulo_normalizado, titulo_antigo) >= limite:
            return True

    return False


def filtrar_pautas(pautas):
    """Retorna somente pautas que ainda não foram utilizadas."""
    aprovadas = []

    for pauta in pautas:
        titulo = pauta.get("titulo", "")
        palavra_chave = pauta.get("palavra_chave", "")

        if not pauta_ja_utilizada(titulo, palavra_chave):
            aprovadas.append(pauta)

    return aprovadas


if __name__ == "__main__":
    historico = carregar_historico()

    print("Motor de pautas iniciado com sucesso.")
    print(f"Itens registrados no histórico: {len(historico)}")
