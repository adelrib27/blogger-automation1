import json
import re
import unicodedata
from pathlib import Path


ARQUIVO_PRODUTOS = Path("data/produtos.json")


STOPWORDS = {
    "a", "o", "as", "os", "de", "da", "do", "das", "dos",
    "e", "em", "para", "com", "como", "um", "uma", "no",
    "na", "nos", "nas", "mais", "por", "que", "se", "ao",
    "aos", "sua", "seu", "suas", "seus",
}


TEMAS = {
    "organizacao": {
        "organizar", "organizacao", "organizador",
        "organizadores", "espaco", "pratico", "pratica",
    },

    "cozinha": {
        "cozinha", "pia", "bancada", "armario",
        "utensilio", "utensilios",
    },

    "armazenamento_alimentos": {
        "pote", "potes", "marmita", "marmitas",
        "alimento", "alimentos", "congelador",
        "armazenamento",
    },

    "preparo_alimentos": {
        "cortador", "legume", "legumes", "cebola",
        "tomate", "cenoura", "lamina", "laminas",
        "preparo",
    },

    "loucas": {
        "louca", "loucas", "prato", "pratos",
        "talher", "talheres", "escorredor",
    },

    "limpeza": {
        "limpeza", "limpar", "escova", "esfregao",
        "mop", "mancha", "manchas",
    },

    "lavanderia": {
        "lavanderia", "roupa", "roupas", "lavar",
        "lavagem", "secar", "secagem", "varal",
        "percarbonato",
    },

    "banheiro": {
        "banheiro", "banho", "toalha", "toalhas",
        "rosto",
    },

    "quarto": {
        "quarto", "cama", "colchao", "lencol",
        "lencois", "edredom", "cobertor",
        "coberdrom",
    },

    "conforto_sono": {
        "dormir", "sono", "travesseiro", "cervical",
        "confortavel", "conforto", "macio",
        "colchao",
    },

    "cama_mesa_banho": {
        "lencol", "lencois", "toalha", "toalhas",
        "cobertor", "edredom", "coberdrom",
    },

    "seguranca": {
        "seguranca", "camera", "monitoramento",
        "wifi", "vigilancia",
    },

    "climatizacao": {
        "climatizador", "ventilador", "umidificador",
        "calor", "refrescar", "climatizacao",
        "ventilacao",
    },
}


TEMAS_RELACIONADOS = {
    "organizacao": {
        "cozinha",
        "armazenamento_alimentos",
        "loucas",
        "lavanderia",
        "banheiro",
        "quarto",
    },

    "cozinha": {
        "organizacao",
        "armazenamento_alimentos",
        "preparo_alimentos",
        "loucas",
        "limpeza",
    },

    "armazenamento_alimentos": {
        "organizacao",
        "cozinha",
    },

    "preparo_alimentos": {
        "cozinha",
    },

    "loucas": {
        "cozinha",
        "organizacao",
    },

    "limpeza": {
        "cozinha",
        "banheiro",
        "lavanderia",
    },

    "lavanderia": {
        "organizacao",
        "limpeza",
    },

    "banheiro": {
        "organizacao",
        "limpeza",
        "cama_mesa_banho",
    },

    "quarto": {
        "organizacao",
        "conforto_sono",
        "cama_mesa_banho",
    },

    "conforto_sono": {
        "quarto",
        "cama_mesa_banho",
    },

    "cama_mesa_banho": {
        "quarto",
        "banheiro",
        "conforto_sono",
    },

    "seguranca": set(),

    "climatizacao": set(),
}


CONFLITOS_TEMATICOS = {
    ("organizacao", "limpeza"),
    ("organizacao", "preparo_alimentos"),
    ("armazenamento_alimentos", "limpeza"),
    ("loucas", "limpeza"),
    ("conforto_sono", "limpeza"),
    ("climatizacao", "limpeza"),
    ("seguranca", "limpeza"),
}


# Temas que não devem ser cruzados apenas porque existe
# alguma palavra genérica em comum.
INCOMPATIBILIDADES_FORTES = {
    "banheiro": {
        "quarto",
        "conforto_sono",
    },

    "quarto": {
        "banheiro",
        "cozinha",
        "preparo_alimentos",
        "loucas",
    },

    "cozinha": {
        "quarto",
        "conforto_sono",
        "seguranca",
        "climatizacao",
    },

    "lavanderia": {
        "quarto",
        "conforto_sono",
        "preparo_alimentos",
        "loucas",
    },

    "seguranca": {
        "cozinha",
        "banheiro",
        "quarto",
        "limpeza",
        "lavanderia",
        "climatizacao",
    },

    "climatizacao": {
        "cozinha",
        "banheiro",
        "quarto",
        "limpeza",
        "lavanderia",
        "seguranca",
    },
}


def normalizar_texto(texto):
    texto = str(texto or "").lower()

    texto = unicodedata.normalize(
        "NFKD",
        texto,
    )

    texto = "".join(
        caractere
        for caractere in texto
        if not unicodedata.combining(caractere)
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


def tokenizar(texto):
    palavras = normalizar_texto(texto).split()

    return {
        palavra
        for palavra in palavras
        if palavra not in STOPWORDS
        and len(palavra) >= 3
    }


def carregar_produtos():
    if not ARQUIVO_PRODUTOS.exists():
        return []

    with ARQUIVO_PRODUTOS.open(
        "r",
        encoding="utf-8",
    ) as arquivo:
        dados = json.load(arquivo)

    if isinstance(dados, list):
        produtos = dados
    elif isinstance(dados, dict):
        produtos = dados.get(
            "produtos",
            [],
        )
    else:
        produtos = []

    return [
        produto
        for produto in produtos
        if produto.get("ativo", True)
        and produto.get("nome")
        and produto.get("link_afiliado")
    ]


def criar_contexto_artigo(
    titulo,
    palavra_chave,
    categoria="",
    descricao="",
    palavras_secundarias=None,
):
    partes = [
        titulo,
        palavra_chave,
        categoria,
        descricao,
    ]

    if palavras_secundarias:
        partes.extend(
            palavras_secundarias
        )

    return " ".join(
        str(parte)
        for parte in partes
        if parte
    )


def detectar_temas(texto):
    tokens = tokenizar(texto)
    encontrados = {}

    for tema, palavras in TEMAS.items():
        quantidade = len(
            tokens.intersection(palavras)
        )

        if quantidade > 0:
            encontrados[tema] = quantidade

    return encontrados


def temas_sao_relacionados(
    tema_artigo,
    tema_produto,
):
    if tema_produto in TEMAS_RELACIONADOS.get(
        tema_artigo,
        set(),
    ):
        return True

    if tema_artigo in TEMAS_RELACIONADOS.get(
        tema_produto,
        set(),
    ):
        return True

    return False


def temas_entram_em_conflito(
    tema_artigo,
    tema_produto,
):
    par = (
        tema_artigo,
        tema_produto,
    )

    par_invertido = (
        tema_produto,
        tema_artigo,
    )

    return (
        par in CONFLITOS_TEMATICOS
        or par_invertido
        in CONFLITOS_TEMATICOS
    )


def possui_incompatibilidade_forte(
    temas_artigo,
    temas_produto,
):
    for tema_artigo in temas_artigo:
        incompatíveis = (
            INCOMPATIBILIDADES_FORTES.get(
                tema_artigo,
                set(),
            )
        )

        for tema_produto in temas_produto:
            if tema_produto in incompatíveis:
                return True

    return False


def calcular_relevancia(
    contexto_artigo,
    nome_produto,
):
    palavras_artigo = tokenizar(
        contexto_artigo
    )

    palavras_produto = tokenizar(
        nome_produto
    )

    palavras_comuns = (
        palavras_artigo
        & palavras_produto
    )

    temas_artigo = detectar_temas(
        contexto_artigo
    )

    temas_produto = detectar_temas(
        nome_produto
    )

    # Se artigo e produto pertencem a universos
    # claramente incompatíveis, o produto é
    # descartado antes de receber pontos genéricos.
    if possui_incompatibilidade_forte(
        temas_artigo,
        temas_produto,
    ):
        return 0

    pontuacao = (
        len(palavras_comuns) * 4
    )

    for (
        tema_artigo,
        forca_artigo,
    ) in temas_artigo.items():

        for (
            tema_produto,
            forca_produto,
        ) in temas_produto.items():

            if tema_artigo == tema_produto:
                pontuacao += (
                    7
                    + min(forca_artigo, 3)
                    + min(forca_produto, 3)
                )

            elif temas_sao_relacionados(
                tema_artigo,
                tema_produto,
            ):
                pontuacao += 3

            if temas_entram_em_conflito(
                tema_artigo,
                tema_produto,
            ):
                pontuacao -= 5

    palavras_comerciais_fortes = {
        "organizador",
        "organizadores",
        "escorredor",
        "varal",
        "travesseiro",
        "colchao",
        "camera",
        "climatizador",
        "ventilador",
        "umidificador",
        "toalha",
        "toalhas",
        "marmita",
        "marmitas",
        "pote",
        "potes",
        "cortador",
        "percarbonato",
    }

    correspondencias_fortes = (
        palavras_comuns
        & palavras_comerciais_fortes
    )

    pontuacao += (
        len(correspondencias_fortes) * 5
    )

    return max(
        0,
        pontuacao,
    )


def selecionar_produtos(
    titulo,
    palavra_chave,
    categoria="",
    descricao="",
    palavras_secundarias=None,
    limite=3,
    pontuacao_minima=6,
):
    produtos = carregar_produtos()

    contexto_artigo = criar_contexto_artigo(
        titulo=titulo,
        palavra_chave=palavra_chave,
        categoria=categoria,
        descricao=descricao,
        palavras_secundarias=(
            palavras_secundarias
        ),
    )

    avaliados = []

    nomes_usados = set()

    for produto in produtos:
        nome = produto["nome"]

        nome_normalizado = normalizar_texto(
            nome
        )

        if nome_normalizado in nomes_usados:
            continue

        nomes_usados.add(
            nome_normalizado
        )

        pontuacao = calcular_relevancia(
            contexto_artigo,
            nome,
        )

        if pontuacao < pontuacao_minima:
            continue

        item = dict(produto)

        item["pontuacao"] = pontuacao

        avaliados.append(
            item
        )

    avaliados.sort(
        key=lambda item: item["pontuacao"],
        reverse=True,
    )

    return avaliados[:limite]


def exibir_resultado(
    titulo,
    palavra_chave,
    categoria="",
    descricao="",
    palavras_secundarias=None,
):
    produtos = selecionar_produtos(
        titulo=titulo,
        palavra_chave=palavra_chave,
        categoria=categoria,
        descricao=descricao,
        palavras_secundarias=(
            palavras_secundarias
        ),
    )

    print()
    print("=== SELEÇÃO DE PRODUTOS ===")
    print(f"Título: {titulo}")
    print(
        f"Palavra-chave: "
        f"{palavra_chave}"
    )
    print(f"Categoria: {categoria}")
    print()

    if not produtos:
        print(
            "Nenhum produto relevante "
            "encontrado."
        )
        return

    print(
        f"{len(produtos)} produto(s) "
        f"relevante(s) encontrado(s):"
    )
    print()

    for indice, produto in enumerate(
        produtos,
        start=1,
    ):
        print(
            f"{indice}. "
            f"{produto['nome']}"
        )
        print(
            f"   Pontuação: "
            f"{produto['pontuacao']}"
        )
        print(
            f"   Link: "
            f"{produto['link_afiliado']}"
        )
        print()


if __name__ == "__main__":
    exibir_resultado(
        titulo=(
            "Como organizar uma cozinha "
            "pequena de forma prática"
        ),
        palavra_chave=(
            "organização de cozinha pequena"
        ),
        categoria="Cozinha",
        descricao=(
            "Ideias práticas para aproveitar "
            "melhor o espaço da cozinha, "
            "organizar utensílios, louças "
            "e alimentos."
        ),
        palavras_secundarias=[
            "organização de cozinha",
            "utensílios de cozinha",
            "armazenamento de alimentos",
        ],
    )
