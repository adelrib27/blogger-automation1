import json
import os
import random
import re
import time
from pathlib import Path

import requests

from pautas import comparar_com_historico


# ============================================================
# CAMINHOS
# ============================================================

ARQUIVO_PRODUTOS = Path("data/produtos.json")


# ============================================================
# MODELO CLOUDFLARE PARA GERAÇÃO DE PAUTAS
# ============================================================

MODELO_CLOUDFLARE = "@cf/qwen/qwen3-30b-a3b-fp8"


# ============================================================
# PRODUTOS
# ============================================================

def carregar_produtos():
    """
    Carrega os produtos ativos do catálogo.

    O catálogo é a fonte oficial para:
    - nome do produto;
    - link afiliado;
    - status ativo.

    A IA nunca cria nem modifica links afiliados.
    """

    if not ARQUIVO_PRODUTOS.exists():
        raise RuntimeError(
            f"Arquivo de produtos não encontrado: "
            f"{ARQUIVO_PRODUTOS}"
        )

    try:
        with ARQUIVO_PRODUTOS.open(
            "r",
            encoding="utf-8",
        ) as arquivo:
            dados = json.load(arquivo)

    except json.JSONDecodeError as erro:
        raise RuntimeError(
            "data/produtos.json contém JSON inválido."
        ) from erro

    if not isinstance(dados, list):
        raise RuntimeError(
            "data/produtos.json deve conter uma lista."
        )

    produtos = []

    for produto in dados:
        if not isinstance(produto, dict):
            continue

        nome = str(
            produto.get("nome", "")
        ).strip()

        link = str(
            produto.get("link_afiliado", "")
        ).strip()

        ativo = produto.get(
            "ativo",
            True,
        )

        if not nome:
            continue

        if not link:
            continue

        if ativo is not True:
            continue

        produtos.append(
            {
                "nome": nome,
                "link_afiliado": link,
                "ativo": True,
            }
        )

    if not produtos:
        raise RuntimeError(
            "Nenhum produto ativo com link afiliado "
            "foi encontrado em data/produtos.json."
        )

    return produtos


def deduplicar_produtos(produtos):
    """
    Evita escolher duas vezes o mesmo produto quando
    existem registros duplicados no catálogo.

    O primeiro registro encontrado é preservado.
    """

    unicos = []
    nomes_vistos = set()

    for produto in produtos:
        chave = re.sub(
            r"\s+",
            " ",
            produto["nome"].strip().lower(),
        )

        if chave in nomes_vistos:
            continue

        nomes_vistos.add(chave)
        unicos.append(produto)

    return unicos


def ordenar_produtos_para_tentativa(produtos):
    """
    Embaralha os produtos para que o blog não fique preso
    sempre aos primeiros itens do catálogo.

    A seleção definitiva ainda depende de uma pauta inédita.
    """

    produtos = list(produtos)
    random.shuffle(produtos)

    return produtos


# ============================================================
# LIMPEZA E VALIDAÇÃO DA RESPOSTA DA IA
# ============================================================

def limpar_json_resposta(texto):
    """
    Limpa a resposta da IA e extrai o bloco JSON.
    """

    if not texto:
        return ""

    texto = texto.strip()

    texto = re.sub(
        r"^```(?:json)?\s*",
        "",
        texto,
        flags=re.IGNORECASE,
    )

    texto = re.sub(
        r"\s*```$",
        "",
        texto,
    )

    inicio = texto.find("[")
    fim = texto.rfind("]")

    if inicio == -1 or fim == -1 or fim <= inicio:
        return ""

    return texto[inicio: fim + 1]


def validar_pauta(pauta):
    """
    Verifica se a pauta possui os campos editoriais
    necessários.

    produto_principal não é aceito da IA.
    Esse campo será anexado posteriormente pelo Python.
    """

    if not isinstance(pauta, dict):
        return False

    campos_obrigatorios = (
        "titulo",
        "palavra_chave",
        "categoria",
        "descricao",
        "palavras_secundarias",
    )

    for campo in campos_obrigatorios:
        if campo not in pauta:
            return False

    if not str(
        pauta["titulo"]
    ).strip():
        return False

    if not str(
        pauta["palavra_chave"]
    ).strip():
        return False

    if not str(
        pauta["categoria"]
    ).strip():
        return False

    if not str(
        pauta["descricao"]
    ).strip():
        return False

    if not isinstance(
        pauta["palavras_secundarias"],
        list,
    ):
        return False

    palavras_secundarias = [
        str(item).strip()
        for item in pauta["palavras_secundarias"]
        if str(item).strip()
    ]

    if not palavras_secundarias:
        return False

    pauta["titulo"] = str(
        pauta["titulo"]
    ).strip()

    pauta["palavra_chave"] = str(
        pauta["palavra_chave"]
    ).strip()

    pauta["categoria"] = str(
        pauta["categoria"]
    ).strip()

    pauta["descricao"] = str(
        pauta["descricao"]
    ).strip()

    pauta["palavras_secundarias"] = (
        palavras_secundarias
    )

    # Segurança:
    # mesmo que o modelo tente devolver esse campo,
    # ele é removido. O produto oficial vem do catálogo.
    pauta.pop(
        "produto_principal",
        None,
    )

    pauta.pop(
        "link_afiliado",
        None,
    )

    return True


# ============================================================
# CLOUDFLARE WORKERS AI
# ============================================================

def obter_config_cloudflare():
    """Obtém as credenciais do Workers AI pelas variáveis de ambiente."""
    account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID")
    api_token = os.getenv("CLOUDFLARE_API_TOKEN")
    if not account_id:
        raise RuntimeError("CLOUDFLARE_ACCOUNT_ID não encontrada.")
    if not api_token:
        raise RuntimeError("CLOUDFLARE_API_TOKEN não encontrada.")
    return account_id, api_token


def extrair_texto_cloudflare(dados):
    """Extrai texto de formatos atuais e legados do Workers AI."""
    if not isinstance(dados, dict):
        return ""

    def extrair(objeto):
        if not isinstance(objeto, dict):
            return ""

        for campo in ("response", "text", "output_text"):
            valor = objeto.get(campo)
            if isinstance(valor, str) and valor.strip():
                return valor.strip()

        choices = objeto.get("choices")
        if isinstance(choices, list) and choices:
            primeira = choices[0]
            if isinstance(primeira, dict):
                mensagem = primeira.get("message")
                if isinstance(mensagem, dict):
                    conteudo = mensagem.get("content")
                    if isinstance(conteudo, str) and conteudo.strip():
                        return conteudo.strip()
                texto = primeira.get("text")
                if isinstance(texto, str) and texto.strip():
                    return texto.strip()
        return ""

    resultado = dados.get("result")
    if isinstance(resultado, str) and resultado.strip():
        return resultado.strip()

    return extrair(resultado) or extrair(dados)


def gerar_candidatas_com_cloudflare(prompt):
    """Gera pautas com Qwen no Cloudflare Workers AI."""
    account_id, api_token = obter_config_cloudflare()
    modelo = MODELO_CLOUDFLARE
    url = (
        "https://api.cloudflare.com/client/v4/accounts/"
        f"{account_id}/ai/run/{modelo}"
    )
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "messages": [
            {
                "role": "system",
                "content": (
                    "Você é um estrategista editorial para blogs brasileiros. "
                    "Siga rigorosamente as instruções do usuário e, quando "
                    "solicitado, responda somente com JSON válido, sem Markdown."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.6,
        "max_tokens": 4096,
    }
    tentativas = 3
    esperas = [5, 15]
    for tentativa in range(1, tentativas + 1):
        try:
            print(f"\nModelo Cloudflare: {modelo}")
            print(f"Tentativa {tentativa}/{tentativas} para gerar novas pautas...")
            resposta = requests.post(
                url, headers=headers, json=payload, timeout=120
            )
            print("HTTP Cloudflare:", resposta.status_code)
            if resposta.status_code != 200:
                detalhe = resposta.text[:1000]
                if resposta.status_code in (429, 500, 502, 503, 504):
                    raise RuntimeError(
                        "ERRO_TEMPORARIO_CLOUDFLARE: "
                        f"HTTP {resposta.status_code}: {detalhe}"
                    )
                raise RuntimeError(
                    "Erro não recuperável no Cloudflare Workers AI. "
                    f"HTTP {resposta.status_code}: {detalhe}"
                )
            dados = resposta.json()
            texto = extrair_texto_cloudflare(dados)
            if not texto:
                chaves_topo = list(dados.keys()) if isinstance(dados, dict) else []
                resultado_debug = dados.get("result") if isinstance(dados, dict) else None
                chaves_resultado = (
                    list(resultado_debug.keys())
                    if isinstance(resultado_debug, dict)
                    else []
                )
                raise RuntimeError(
                    "RESPOSTA_ESTRUTURAL: HTTP 200, mas o texto não foi "
                    f"localizado. Chaves topo={chaves_topo}; "
                    f"chaves result={chaves_resultado}."
                )
            texto_json = limpar_json_resposta(texto)
            if not texto_json:
                raise RuntimeError(
                    "RESPOSTA_ESTRUTURAL: não foi possível localizar JSON "
                    "na resposta da Cloudflare."
                )
            pautas = json.loads(texto_json)
            if not isinstance(pautas, list):
                raise RuntimeError(
                    "RESPOSTA_ESTRUTURAL: a resposta não contém uma lista de pautas."
                )
            pautas_validas = [p for p in pautas if validar_pauta(p)]
            if not pautas_validas:
                raise RuntimeError(
                    "RESPOSTA_ESTRUTURAL: nenhuma pauta válida foi gerada."
                )
            print("Cloudflare/Qwen respondeu com sucesso.")
            return pautas_validas
        except Exception as erro:
            print(
                "Erro na geração Cloudflare/Qwen, "
                f"tentativa {tentativa}/{tentativas}: {erro}"
            )
            mensagem = str(erro)
            recuperavel = (
                "ERRO_TEMPORARIO_CLOUDFLARE" in mensagem
                or "RESPOSTA_ESTRUTURAL" in mensagem
                or isinstance(erro, json.JSONDecodeError)
                or isinstance(erro, requests.Timeout)
                or isinstance(erro, requests.ConnectionError)
            )
            if not recuperavel:
                raise
            if tentativa >= tentativas:
                raise
            espera = esperas[tentativa - 1]
            print(f"Aguardando {espera} segundos antes de tentar novamente...")
            time.sleep(espera)
    raise RuntimeError("Cloudflare/Qwen não conseguiu gerar pautas válidas.")


# ============================================================
# PROMPT DE PAUTA BASEADA EM PRODUTO
# ============================================================

def criar_prompt_produto(
    produto,
    quantidade,
    nicho,
):
    """
    Cria o prompt editorial a partir de um produto real.

    O produto orienta o assunto, mas o artigo não deve
    parecer um anúncio ou uma review comercial.
    """

    nome_produto = produto["nome"]

    return f"""
Você é um estrategista editorial especializado em conteúdo útil,
SEO e planejamento de pautas para blogs brasileiros.

O blog pertence ao nicho:

{nicho}

PRODUTO PRINCIPAL DISPONÍVEL NO CATÁLOGO:

{nome_produto}

OBJETIVO:

Crie {quantidade} pautas editoriais diferentes relacionadas de forma
direta e natural ao produto acima.

A pauta deve nascer de um problema, necessidade, dúvida, ambiente,
rotina ou intenção de busca em que esse produto possa ser apresentado
posteriormente como uma solução útil dentro do artigo.

IMPORTANTE:

O artigo final não será uma simples propaganda do produto.
Ele deverá responder de verdade à intenção de busca do leitor.

O produto principal será inserido posteriormente pelo nosso sistema.
Você NÃO deve criar link, URL, preço, desconto ou oferta.

REGRAS:

- Escreva em português do Brasil.
- Todas as pautas devem ter relação clara com o produto principal.
- Crie assuntos específicos e úteis.
- Priorize intenção de busca informacional com possibilidade comercial natural.
- O título deve funcionar como título editorial para Google.
- A palavra-chave principal deve representar uma busca natural.
- A descrição deve explicar claramente o que o artigo entregará.
- Gere de 3 a 5 palavras-chave secundárias por pauta.
- Evite títulos genéricos.
- Evite títulos sensacionalistas.
- Evite clickbait.
- Não use datas no título.
- Não use preços.
- Não invente pesquisas ou estatísticas.
- Não invente características que não estejam presentes no nome do produto.
- Não invente marcas.
- Não crie URLs.
- Não crie links afiliados.
- Não escreva o link do produto.
- Não crie títulos no formato "review".
- Não crie títulos no formato "vale a pena".
- Não transforme o título do vendedor no título do artigo.
- Não faça todas as pautas com o nome exato do produto.
- Não repita o mesmo ângulo dentro da lista.
- Priorize pautas evergreen.
- O produto deve poder entrar naturalmente no assunto posteriormente.

EXEMPLO DE RACIOCÍNIO:

Se o produto fosse um mop giratório, uma pauta adequada poderia tratar
de como facilitar a limpeza do piso ou como organizar uma rotina prática
de limpeza da casa.

Uma pauta inadequada seria sobre decoração de parede, pois o produto
não teria relação natural com o assunto.

CATEGORIAS PERMITIDAS:

Organização
Decoração
Cozinha
Sala
Quarto
Banheiro
Lavanderia
Iluminação
Móveis
Casa e Decoração

RETORNE SOMENTE JSON VÁLIDO.

Use exatamente esta estrutura:

[
  {{
    "titulo": "Título editorial da pauta",
    "palavra_chave": "palavra-chave principal",
    "categoria": "Categoria permitida",
    "descricao": "Descrição objetiva da pauta.",
    "palavras_secundarias": [
      "termo relacionado 1",
      "termo relacionado 2",
      "termo relacionado 3"
    ]
  }}
]

Não inclua produto_principal no JSON.
Não inclua link_afiliado no JSON.
Não escreva Markdown.
Não use ```json.
Não escreva explicações antes ou depois do JSON.
"""


# ============================================================
# GERAÇÃO DE CANDIDATAS PARA UM PRODUTO
# ============================================================

def gerar_candidatas_cloudflare(
    produto,
    quantidade=6,
    nicho="Casa e Decoração",
):
    """
    Pede ao Cloudflare/Qwen pautas relacionadas especificamente
    ao produto principal escolhido pelo código.

    A decisão final sobre repetição continua pertencendo
    ao nosso próprio motor.
    """
    prompt = criar_prompt_produto(
        produto=produto,
        quantidade=quantidade,
        nicho=nicho,
    )
    print("\n=== MODELO PARA PAUTAS ===")
    print(MODELO_CLOUDFLARE)
    return gerar_candidatas_com_cloudflare(prompt=prompt)


# ============================================================
# ANTI-REPETIÇÃO
# ============================================================

def selecionar_pauta_inedita(
    pautas,
    produto_principal,
):
    """
    Compara cada candidata com publicados e rascunhos.

    Quando encontra uma pauta inédita, anexa o produto
    principal usando exclusivamente os dados do catálogo.
    """

    print(
        "\n=== ANÁLISE ANTI-REPETIÇÃO ==="
    )

    for numero, pauta in enumerate(
        pautas,
        start=1,
    ):
        titulo = pauta["titulo"]

        palavra_chave = pauta[
            "palavra_chave"
        ]

        resultado = comparar_com_historico(
            titulo=titulo,
            palavra_chave=palavra_chave,
        )

        print(
            f"\nCandidata {numero}:"
        )

        print(
            "Título:",
            titulo,
        )

        print(
            "Palavra-chave:",
            palavra_chave,
        )

        if resultado["repetida"]:
            print(
                "Resultado: REJEITADA"
            )

            print(
                "Motivo:",
                resultado["motivo"],
            )

            existente = resultado.get(
                "item"
            ) or {}

            if existente:
                print(
                    "Conteúdo relacionado:",
                    existente.get(
                        "titulo",
                        "",
                    ),
                )

                fonte = existente.get(
                    "_fonte_antirrepeticao",
                    "",
                )

                if fonte:
                    print(
                        "Fonte:",
                        fonte,
                    )

            continue

        print(
            "Resultado: APROVADA"
        )

        print(
            "Motivo: pauta inédita"
        )

        pauta_final = dict(
            pauta
        )

        pauta_final[
            "produto_principal"
        ] = {
            "nome": produto_principal[
                "nome"
            ],
            "link_afiliado": (
                produto_principal[
                    "link_afiliado"
                ]
            ),
        }

        return pauta_final

    return None


# ============================================================
# FLUXO PRINCIPAL
# ============================================================

def gerar_pauta_automatica(
    nicho="Casa e Decoração",
):
    """
    Novo fluxo:

    catálogo de produtos
        ->
    produto principal
        ->
    pautas SEO relacionadas ao produto
        ->
    anti-repetição
        ->
    pauta inédita
        ->
    produto principal anexado pelo Python

    Se todas as pautas de um produto forem repetidas,
    o sistema tenta outro produto do catálogo.
    """

    print(
        "\n=== GERAÇÃO AUTOMÁTICA DE PAUTA ==="
    )

    produtos = carregar_produtos()

    produtos = deduplicar_produtos(
        produtos
    )

    produtos = ordenar_produtos_para_tentativa(
        produtos
    )

    print(
        "\nProdutos ativos disponíveis:",
        len(produtos),
    )

    if not produtos:
        raise RuntimeError(
            "Nenhum produto disponível para "
            "originar uma pauta."
        )

    for numero_produto, produto in enumerate(
        produtos,
        start=1,
    ):
        print(
            "\n=================================================="
        )

        print(
            f"PRODUTO {numero_produto}/"
            f"{len(produtos)}"
        )

        print(
            "=================================================="
        )

        print(
            "Produto principal:",
            produto["nome"],
        )

        try:
            candidatas = gerar_candidatas_cloudflare(
                produto=produto,
                quantidade=6,
                nicho=nicho,
            )

        except Exception as erro:
            print(
                "\nNão foi possível gerar pautas "
                "para este produto."
            )

            print(
                "Erro:",
                erro,
            )

            print(
                "Tentando outro produto do catálogo..."
            )

            continue

        print(
            f"\nPautas válidas geradas: "
            f"{len(candidatas)}"
        )

        escolhida = selecionar_pauta_inedita(
            pautas=candidatas,
            produto_principal=produto,
        )

        if escolhida is None:
            print(
                "\nTodas as pautas deste produto "
                "foram rejeitadas pelo "
                "anti-repetição."
            )

            print(
                "Tentando outro produto "
                "do catálogo..."
            )

            continue

        print(
            "\n=== PAUTA AUTOMÁTICA ESCOLHIDA ==="
        )

        print(
            "Produto principal:",
            escolhida[
                "produto_principal"
            ]["nome"],
        )

        print(
            "Título:",
            escolhida["titulo"],
        )

        print(
            "Palavra-chave:",
            escolhida[
                "palavra_chave"
            ],
        )

        print(
            "Categoria:",
            escolhida["categoria"],
        )

        print(
            "Link afiliado preservado:",
            escolhida[
                "produto_principal"
            ]["link_afiliado"],
        )

        return escolhida

    raise RuntimeError(
        "Nenhum produto do catálogo conseguiu "
        "originar uma pauta inédita."
    )


# ============================================================
# TESTE MANUAL
# ============================================================

if __name__ == "__main__":
    pauta = gerar_pauta_automatica()

    print(
        "\n=== RESULTADO FINAL DO TESTE ==="
    )

    print(
        json.dumps(
            pauta,
            ensure_ascii=False,
            indent=2,
        )
    )
