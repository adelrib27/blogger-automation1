import json
import re
import unicodedata
from pathlib import Path


ARQUIVO_PRODUTOS = Path("data/produtos.json")


STOPWORDS = {
    "a", "ao", "aos", "as", "com", "como", "da", "das",
    "de", "do", "dos", "e", "em", "entre", "mais", "na",
    "nas", "no", "nos", "o", "os", "ou", "para", "por",
    "que", "sem", "um", "uma", "uns", "umas", "seu",
    "sua", "seus", "suas", "usar", "usando",
}


# ============================================================
# TEMAS
# ============================================================

TEMAS = {
    "organizacao": {
        "organizacao",
        "organizar",
        "organizador",
        "organizada",
        "organizado",
        "armazenamento",
        "armazenar",
        "guardar",
        "espaco",
        "aproveitar",
        "praticidade",
        "pratico",
        "ordem",
    },

    "cozinha": {
        "cozinha",
        "louca",
        "loucas",
        "prato",
        "pratos",
        "talher",
        "talheres",
        "utensilio",
        "utensilios",
        "pia",
        "bancada",
    },

    "armazenamento_alimentos": {
        "marmita",
        "marmitas",
        "pote",
        "potes",
        "alimento",
        "alimentos",
        "congelador",
        "geladeira",
        "armazenamento",
        "armazenar",
    },

    "preparo_alimentos": {
        "cortador",
        "legume",
        "legumes",
        "cebola",
        "tomate",
        "cenoura",
        "lamina",
        "laminas",
        "cortar",
        "preparo",
        "preparar",
    },

    "loucas": {
        "escorredor",
        "louca",
        "loucas",
        "prato",
        "pratos",
        "talher",
        "talheres",
        "pia",
    },

    "limpeza": {
        "limpeza",
        "limpar",
        "escova",
        "mop",
        "esfregao",
        "sujeira",
        "mancha",
        "manchas",
    },

    "lavanderia": {
        "lavanderia",
        "roupa",
        "roupas",
        "varal",
        "percarbonato",
        "mancha",
        "manchas",
        "lavagem",
        "lavar",
    },

    "banheiro": {
        "banheiro",
        "banho",
        "toalha",
        "toalhas",
        "rosto",
    },

    "quarto": {
        "quarto",
        "cama",
        "colchao",
        "lencol",
        "travesseiro",
        "cobertor",
        "edredom",
        "queen",
        "solteiro",
        "casal",
    },

    "conforto_sono": {
        "travesseiro",
        "cervical",
        "ortopedico",
        "colchao",
        "conforto",
        "dormir",
        "sono",
        "postura",
    },

    "cama_mesa_banho": {
        "lencol",
        "toalha",
        "toalhas",
        "cobertor",
        "edredom",
        "colchao",
        "cama",
        "queen",
        "casal",
        "solteiro",
    },

    "seguranca": {
        "seguranca",
        "camera",
        "monitoramento",
        "vigilancia",
        "wifi",
    },

    "climatizacao": {
        "climatizador",
        "ventilador",
        "umidificador",
        "calor",
        "refrescar",
        "climatizacao",
        "ar",
    },
}


# Temas que combinam naturalmente entre si.
TEMAS_RELACIONADOS = {
    "organizacao": {
        "armazenamento_alimentos",
        "loucas",
        "cozinha",
    },

    "cozinha": {
        "organizacao",
        "armazenamento_alimentos",
        "preparo_alimentos",
        "loucas",
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
        "lavanderia",
        "banheiro",
        "cozinha",
    },

    "lavanderia": {
        "limpeza",
    },

    "banheiro": {
        "limpeza",
        "cama_mesa_banho",
    },

    "quarto": {
        "cama_mesa_banho",
        "conforto_sono",
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


# Alguns temas não devem receber pontuação alta
# apenas porque compartilham o mesmo cômodo.
CONFLITOS_TEMATICOS = {
    ("organizacao", "limpeza"),
    ("organizacao", "preparo_alimentos"),
    ("armazenamento_alimentos", "limpeza"),
    ("loucas", "limpeza"),
    ("conforto_sono", "limpeza"),
    ("climatizacao", "limpeza"),
    ("seguranca", "limpeza"),
}


# ============================================================
# NORMALIZAÇÃO
# ============================================================

def normalizar_texto(texto):
    """
    Normaliza texto para comparação:
    - minúsculas
    - sem acentos
    - sem pontuação
    - espaços normalizados
    """

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
    """
    Converte um texto em conjunto de palavras úteis.
    """

    texto = normalizar_texto(texto)

    return {
        palavra
        for palavra in texto.split()
        if len(palavra) >= 3
        and palavra not in STOPWORDS
    }


# ============================================================
# CATÁLOGO
# ============================================================

def carregar_produtos():
    """
    Carrega apenas produtos ativos do catálogo.
    """

    if not ARQUIVO_PRODUTOS.exists():
        print(
            "Catálogo de produtos não encontrado:",
            ARQUIVO_PRODUTOS,
        )
        return []

    try:
        with open(
            ARQUIVO_PRODUTOS,
            "r",
            encoding="utf-8",
        ) as arquivo:
            produtos = json.load(arquivo)

    except Exception as erro:
        print(
            "Erro ao carregar produtos:",
            erro,
        )
        return []

    if not isinstance(produtos, list):
        print(
            "Formato inválido em produtos.json."
        )
        return []

    produtos_validos = []

    for produto in produtos:
        if not isinstance(produto, dict):
            continue

        nome = str(
            produto.get("nome", "")
        ).strip()

        link = str(
            produto.get(
                "link_afiliado",
                "",
            )
        ).strip()

        ativo = produto.get(
            "ativo",
            True,
        )

        if not ativo:
            continue

        if not nome or not link:
            continue

        produtos_validos.append(
            {
                "nome": nome,
                "link_afiliado": link,
                "ativo": True,
            }
        )

    return produtos_validos


# ============================================================
# CONTEXTO DO ARTIGO
# ============================================================

def criar_contexto_artigo(
    titulo,
    palavra_chave="",
    categoria="",
    descricao="",
    palavras_secundarias=None,
):
    """
    Reúne os principais sinais semânticos
    disponíveis sobre a pauta.
    """

    if palavras_secundarias is None:
        palavras_secundarias = []

    if isinstance(
        palavras_secundarias,
        str,
    ):
        palavras_secundarias = [
            palavras_secundarias
        ]

    partes = [
        titulo,
        palavra_chave,
        categoria,
        descricao,
        " ".join(
            str(item)
            for item in palavras_secundarias
        ),
    ]

    return " ".join(
        str(parte or "")
        for parte in partes
    )


# ============================================================
# IDENTIFICAÇÃO TEMÁTICA
# ============================================================

def detectar_temas(texto):
    """
    Detecta quais temas estão presentes
    em determinado texto.

    Retorna:
    {
        "tema": quantidade_de_palavras_encontradas
    }
    """

    tokens = tokenizar(texto)

    temas_encontrados = {}

    for tema, palavras in TEMAS.items():
        correspondencias = (
            tokens & palavras
        )

        if correspondencias:
            temas_encontrados[tema] = len(
                correspondencias
            )

    return temas_encontrados


def temas_sao_relacionados(
    tema_artigo,
    tema_produto,
):
    """
    Verifica se dois temas possuem
    relação comercial/editorial natural.
    """

    if tema_artigo == tema_produto:
        return True

    relacionados = TEMAS_RELACIONADOS.get(
        tema_artigo,
        set(),
    )

    if tema_produto in relacionados:
        return True

    relacionados_inversos = (
        TEMAS_RELACIONADOS.get(
            tema_produto,
            set(),
        )
    )

    return (
        tema_artigo
        in relacionados_inversos
    )


def temas_entram_em_conflito(
    tema_artigo,
    tema_produto,
):
    """
    Evita que o simples compartilhamento
    de um cômodo faça um produto pouco
    relacionado receber pontuação alta.
    """

    par = (
        tema_artigo,
        tema_produto,
    )

    par_inverso = (
        tema_produto,
        tema_artigo,
    )

    return (
        par in CONFLITOS_TEMATICOS
        or par_inverso
        in CONFLITOS_TEMATICOS
    )


# ============================================================
# RELEVÂNCIA
# ============================================================

def calcular_relevancia(
    produto,
    contexto,
):
    """
    Calcula a relevância entre produto
    e pauta usando:

    1. palavras exatas em comum;
    2. temas principais;
    3. temas relacionados;
    4. penalização de temas conflitantes.

    O objetivo é evitar recomendações
    baseadas apenas no mesmo cômodo.
    """

    nome = produto.get(
        "nome",
        "",
    )

    if not nome:
        return 0

    tokens_produto = tokenizar(
        nome
    )

    tokens_contexto = tokenizar(
        contexto
    )

    if not tokens_produto:
        return 0

    if not tokens_contexto:
        return 0

    pontuacao = 0

    # --------------------------------------------------------
    # 1. PALAVRAS EXATAS
    # --------------------------------------------------------

    palavras_comuns = (
        tokens_produto
        & tokens_contexto
    )

    # Coincidências diretas são um
    # dos sinais mais fortes.
    pontuacao += (
        len(palavras_comuns) * 4
    )

    # --------------------------------------------------------
    # 2. TEMAS
    # --------------------------------------------------------

    temas_produto = detectar_temas(
        nome
    )

    temas_contexto = detectar_temas(
        contexto
    )

    # Tema exatamente igual.
    for tema, forca_artigo in (
        temas_contexto.items()
    ):
        if tema in temas_produto:
            forca_produto = (
                temas_produto[tema]
            )

            pontuacao += (
                7
                + min(
                    forca_artigo,
                    3,
                )
                + min(
                    forca_produto,
                    3,
                )
            )

    # --------------------------------------------------------
    # 3. TEMAS RELACIONADOS
    # --------------------------------------------------------

    for tema_artigo in temas_contexto:
        for tema_produto in temas_produto:

            if tema_artigo == tema_produto:
                continue

            if temas_sao_relacionados(
                tema_artigo,
                tema_produto,
            ):
                pontuacao += 3

    # --------------------------------------------------------
    # 4. CONFLITOS TEMÁTICOS
    # --------------------------------------------------------

    penalidade = 0

    for tema_artigo in temas_contexto:
        for tema_produto in temas_produto:

            if temas_entram_em_conflito(
                tema_artigo,
                tema_produto,
            ):
                penalidade += 5

    pontuacao -= penalidade

    # --------------------------------------------------------
    # 5. REFORÇO POR PALAVRAS COMERCIAIS IMPORTANTES
    # --------------------------------------------------------

    palavras_fortes = {
        "organizador",
        "armazenamento",
        "escorredor",
        "marmita",
        "marmitas",
        "pote",
        "potes",
        "cortador",
        "toalha",
        "toalhas",
        "mop",
        "varal",
        "travesseiro",
        "colchao",
        "lencol",
        "cobertor",
        "edredom",
        "camera",
        "climatizador",
        "ventilador",
        "umidificador",
    }

    fortes_comuns = (
        palavras_fortes
        & tokens_produto
        & tokens_contexto
    )

    pontuacao += (
        len(fortes_comuns) * 5
    )

    # Nunca retorna pontuação negativa.
    return max(
        0,
        pontuacao,
    )


# ============================================================
# SELEÇÃO
# ============================================================

def selecionar_produtos(
    titulo,
    palavra_chave="",
    categoria="",
    descricao="",
    palavras_secundarias=None,
    limite=3,
    pontuacao_minima=6,
):
    """
    Seleciona somente produtos com
    relevância suficiente para a pauta.

    Se nenhum produto for realmente
    relacionado, retorna lista vazia.
    """

    produtos = carregar_produtos()

    if not produtos:
        return []

    contexto = criar_contexto_artigo(
        titulo=titulo,
        palavra_chave=palavra_chave,
        categoria=categoria,
        descricao=descricao,
        palavras_secundarias=(
            palavras_secundarias
        ),
    )

    candidatos = []

    for produto in produtos:
        pontuacao = calcular_relevancia(
            produto,
            contexto,
        )

        if pontuacao < pontuacao_minima:
            continue

        candidato = dict(
            produto
        )

        candidato[
            "pontuacao"
        ] = pontuacao

        candidatos.append(
            candidato
        )

    candidatos.sort(
        key=lambda item: (
            -item["pontuacao"],
            normalizar_texto(
                item["nome"]
            ),
        )
    )

    # Evita recomendar duas vezes
    # o mesmo produto quando existirem
    # links diferentes para títulos iguais.
    selecionados = []
    nomes_usados = set()

    for produto in candidatos:
        nome_normalizado = (
            normalizar_texto(
                produto["nome"]
            )
        )

        if (
            nome_normalizado
            in nomes_usados
        ):
            continue

        nomes_usados.add(
            nome_normalizado
        )

        selecionados.append(
            produto
        )

        if (
            len(selecionados)
            >= limite
        ):
            break

    return selecionados


# ============================================================
# TESTE MANUAL
# ============================================================

def exibir_resultado(
    titulo,
    palavra_chave="",
    categoria="",
    descricao="",
    palavras_secundarias=None,
):
    """
    Utilitário de teste manual.
    """

    print()
    print(
        "=== SELEÇÃO DE PRODUTOS ==="
    )

    print(
        "Título:",
        titulo,
    )

    print(
        "Palavra-chave:",
        palavra_chave,
    )

    print(
        "Categoria:",
        categoria,
    )

    print()

    produtos = selecionar_produtos(
        titulo=titulo,
        palavra_chave=palavra_chave,
        categoria=categoria,
        descricao=descricao,
        palavras_secundarias=(
            palavras_secundarias
        ),
    )

    if not produtos:
        print(
            "Nenhum produto relevante "
            "foi encontrado."
        )
        return

    print(
        f"{len(produtos)} produto(s) "
        "relevante(s) encontrado(s):"
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
            "   Pontuação:",
            produto["pontuacao"],
        )

        print(
            "   Link:",
            produto[
                "link_afiliado"
            ],
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
