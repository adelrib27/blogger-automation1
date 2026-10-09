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


def calcular_relevancia(
    produto,
    contexto,
):
    """
    Calcula relevância básica entre
    o produto e a pauta do artigo.

    Quanto mais palavras importantes
    coincidirem, maior será a pontuação.
    """

    nome = produto.get(
        "nome",
        "",
    )

    tokens_produto = tokenizar(nome)
    tokens_contexto = tokenizar(contexto)

    palavras_comuns = (
        tokens_produto
        & tokens_contexto
    )

    pontuacao = len(
        palavras_comuns
    ) * 3

    contexto_normalizado = (
        normalizar_texto(contexto)
    )

    nome_normalizado = (
        normalizar_texto(nome)
    )

    # Reforço por expressões e núcleos temáticos.
    grupos = [
        {
            "cozinha",
            "louca",
            "prato",
            "talher",
            "marmita",
            "pote",
            "legume",
            "cebola",
            "tomate",
            "cenoura",
            "escorredor",
        },
        {
            "quarto",
            "cama",
            "colchao",
            "lencol",
            "travesseiro",
            "cobertor",
            "edredom",
            "queen",
        },
        {
            "banheiro",
            "toalha",
            "banho",
            "limpeza",
            "escova",
        },
        {
            "lavanderia",
            "roupa",
            "varal",
            "mancha",
            "percarbonato",
            "limpeza",
        },
        {
            "limpeza",
            "mop",
            "esfregao",
            "escova",
            "banheiro",
            "cozinha",
        },
        {
            "seguranca",
            "camera",
            "wifi",
            "lampada",
            "monitoramento",
        },
        {
            "climatizacao",
            "climatizador",
            "ventilador",
            "umidificador",
            "calor",
            "refrescar",
        },
    ]

    for grupo in grupos:
        produto_no_grupo = bool(
            tokens_produto & grupo
        )

        contexto_no_grupo = bool(
            tokens_contexto & grupo
        )

        if (
            produto_no_grupo
            and contexto_no_grupo
        ):
            pontuacao += 4

    # Pequeno reforço se alguma palavra
    # relevante do produto aparecer
    # literalmente no contexto.
    for palavra in tokens_produto:
        if (
            len(palavra) >= 5
            and palavra
            in contexto_normalizado
        ):
            pontuacao += 1

    # Evita considerar o próprio nome vazio
    # ou comparações sem conteúdo.
    if not nome_normalizado:
        return 0

    return pontuacao


def selecionar_produtos(
    titulo,
    palavra_chave="",
    categoria="",
    descricao="",
    palavras_secundarias=None,
    limite=3,
    pontuacao_minima=4,
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

        candidato = dict(produto)
        candidato["pontuacao"] = pontuacao

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

    # Evita selecionar o mesmo produto
    # duas vezes quando houver links
    # diferentes para um título igual.
    selecionados = []
    nomes_usados = set()

    for produto in candidatos:
        nome_normalizado = (
            normalizar_texto(
                produto["nome"]
            )
        )

        if nome_normalizado in nomes_usados:
            continue

        nomes_usados.add(
            nome_normalizado
        )

        selecionados.append(
            produto
        )

        if len(selecionados) >= limite:
            break

    return selecionados


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
    print("Título:", titulo)
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
            produto["link_afiliado"],
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
