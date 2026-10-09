import json
import os
import re
import time

from google import genai

from pautas import comparar_com_historico


# ============================================================
# MODELOS PARA GERAÇÃO DE PAUTAS
# ============================================================
#
# A ordem importa.
# Os modelos com maior cota ficam primeiro.
# Se um modelo esgotar a cota ou ficar indisponível,
# o sistema tenta automaticamente o próximo.
#
MODELOS_GEMINI = [
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-3.5-flash",
    "gemini-3.6-flash",
    "gemini-3.7-flash",
]


def limpar_json_resposta(texto):
    """
    Limpa a resposta do Gemini e extrai o bloco JSON.
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
    Verifica se a pauta possui os campos necessários.
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

    if not str(pauta["titulo"]).strip():
        return False

    if not str(pauta["palavra_chave"]).strip():
        return False

    if not str(pauta["categoria"]).strip():
        return False

    if not str(pauta["descricao"]).strip():
        return False

    if not isinstance(
        pauta["palavras_secundarias"],
        list,
    ):
        return False

    return True


def erro_de_cota(erro):
    """
    Detecta quando a cota do modelo foi esgotada.

    Nesse caso não adianta esperar alguns segundos:
    o sistema deve passar imediatamente ao próximo modelo.
    """
    mensagem = str(erro).upper()

    return (
        "429" in mensagem
        or "RESOURCE_EXHAUSTED" in mensagem
        or "QUOTA EXCEEDED" in mensagem
    )


def erro_temporario(erro):
    """
    Detecta indisponibilidade temporária do serviço.

    Para esses erros vale a pena tentar novamente
    no mesmo modelo antes de usar o próximo.
    """
    mensagem = str(erro).upper()

    return (
        "503" in mensagem
        or "UNAVAILABLE" in mensagem
        or "HIGH DEMAND" in mensagem
    )


def gerar_candidatas_com_modelo(
    client,
    modelo,
    prompt,
):
    """
    Tenta gerar as pautas usando um modelo específico.

    Retorna:
        lista de pautas válidas, se funcionar.

    Pode lançar exceção para que a camada superior
    decida se deve tentar outro modelo.
    """

    tentativas = 3
    esperas = [5, 15]

    for tentativa in range(1, tentativas + 1):
        try:
            print(
                f"\nModelo: {modelo}"
            )
            print(
                f"Tentativa {tentativa}/{tentativas} "
                "para gerar novas pautas..."
            )

            resposta = client.models.generate_content(
                model=modelo,
                contents=prompt,
            )

            texto = resposta.text

            if not texto:
                raise RuntimeError(
                    "Gemini retornou resposta vazia."
                )

            texto_json = limpar_json_resposta(
                texto
            )

            if not texto_json:
                raise RuntimeError(
                    "Não foi possível localizar JSON "
                    "na resposta do Gemini."
                )

            pautas = json.loads(
                texto_json
            )

            if not isinstance(
                pautas,
                list,
            ):
                raise RuntimeError(
                    "A resposta não contém "
                    "uma lista de pautas."
                )

            pautas_validas = [
                pauta
                for pauta in pautas
                if validar_pauta(pauta)
            ]

            if not pautas_validas:
                raise RuntimeError(
                    "Nenhuma pauta válida foi gerada."
                )

            print(
                f"Modelo {modelo} respondeu "
                "com sucesso."
            )

            return pautas_validas

        except Exception as erro:
            print(
                f"Erro no modelo {modelo}, "
                f"tentativa {tentativa}/{tentativas}: "
                f"{erro}"
            )

            # Cota esgotada:
            # não desperdiça novas tentativas.
            if erro_de_cota(erro):
                print(
                    f"Cota do modelo {modelo} "
                    "indisponível ou esgotada."
                )
                print(
                    "Pulando imediatamente "
                    "para o próximo modelo..."
                )
                raise

            # Erro temporário:
            # vale a pena tentar novamente.
            if erro_temporario(erro):
                if tentativa >= tentativas:
                    print(
                        f"O modelo {modelo} continua "
                        "temporariamente indisponível."
                    )
                    raise

                espera = esperas[
                    tentativa - 1
                ]

                print(
                    f"Aguardando {espera} segundos "
                    "antes de tentar novamente "
                    "o mesmo modelo..."
                )

                time.sleep(
                    espera
                )

                continue

            mensagem = str(erro)

            erro_json = isinstance(
                erro,
                json.JSONDecodeError,
            )

            erro_estrutural = (
                erro_json
                or "JSON" in mensagem
                or "pauta válida" in mensagem
                or "lista de pautas" in mensagem
                or "resposta vazia" in mensagem
            )

            # Resposta malformada:
            # damos nova chance ao mesmo modelo.
            if erro_estrutural:
                if tentativa >= tentativas:
                    print(
                        f"O modelo {modelo} não "
                        "conseguiu produzir uma "
                        "resposta válida."
                    )
                    raise

                espera = esperas[
                    tentativa - 1
                ]

                print(
                    f"Aguardando {espera} segundos "
                    "antes de solicitar uma "
                    "nova resposta..."
                )

                time.sleep(
                    espera
                )

                continue

            # Erro desconhecido:
            # não insistimos no modelo.
            print(
                f"Erro não recuperável no modelo "
                f"{modelo}."
            )

            raise

    raise RuntimeError(
        f"O modelo {modelo} não conseguiu "
        "gerar pautas válidas."
    )


def gerar_candidatas_gemini(
    quantidade=8,
    nicho="Casa e Decoração",
):
    """
    Pede ao Gemini uma lista de pautas candidatas.

    A decisão final sobre repetição NÃO fica com o Gemini.
    As pautas serão comparadas posteriormente com
    publicados e rascunhos pelo nosso próprio motor.

    Se um modelo não estiver disponível, o sistema
    tenta automaticamente o próximo da fila.
    """

    api_key = os.getenv(
        "GEMINI_API_KEY"
    )

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY não encontrada."
        )

    client = genai.Client(
        api_key=api_key
    )

    prompt = f"""
Você é um estrategista editorial especializado em conteúdo útil,
SEO e planejamento de pautas para blogs brasileiros.

Crie {quantidade} pautas diferentes para um blog do nicho:

{nicho}

O blog publica conteúdos úteis sobre casa, decoração,
organização, ambientes, móveis, iluminação, cozinha,
quarto, banheiro, sala, lavanderia e assuntos relacionados.

OBJETIVO:

Criar pautas com intenção de busca clara e potencial para
responder dúvidas reais de pessoas pesquisando no Google.

REGRAS:

- Escreva em português do Brasil.
- Crie assuntos específicos e úteis.
- Evite títulos genéricos.
- Evite títulos sensacionalistas.
- Evite clickbait.
- Não use datas no título.
- Não use preços.
- Não invente pesquisas ou estatísticas.
- Não use nomes de marcas.
- Não crie títulos de review de produtos específicos.
- Não repita o mesmo assunto dentro da lista.
- Varie os ambientes e problemas abordados.
- Priorize pautas evergreen.
- A palavra-chave principal deve representar uma busca natural.
- O título deve responder ou desenvolver essa intenção de busca.
- A descrição deve explicar claramente o que o artigo entregará.
- Gere de 3 a 5 palavras-chave secundárias por pauta.

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
    "titulo": "Título da pauta",
    "palavra_chave": "palavra-chave principal",
    "categoria": "Organização",
    "descricao": "Descrição objetiva da pauta.",
    "palavras_secundarias": [
      "termo relacionado 1",
      "termo relacionado 2",
      "termo relacionado 3"
    ]
  }}
]

Não escreva Markdown.
Não use ```json.
Não escreva explicações antes ou depois do JSON.
"""

    print(
        "\n=== FILA DE MODELOS PARA PAUTAS ==="
    )

    for numero, modelo in enumerate(
        MODELOS_GEMINI,
        start=1,
    ):
        print(
            f"{numero}. {modelo}"
        )

    ultimo_erro = None

    for numero, modelo in enumerate(
        MODELOS_GEMINI,
        start=1,
    ):
        print(
            f"\n=== MODELO {numero}/"
            f"{len(MODELOS_GEMINI)} ==="
        )

        try:
            return gerar_candidatas_com_modelo(
                client=client,
                modelo=modelo,
                prompt=prompt,
            )

        except Exception as erro:
            ultimo_erro = erro

            print(
                f"Modelo {modelo} não pôde "
                "concluir a geração."
            )

            if numero < len(
                MODELOS_GEMINI
            ):
                print(
                    "Tentando o próximo modelo "
                    "da fila..."
                )

    raise RuntimeError(
        "Todos os modelos configurados para "
        "geração de pautas falharam. "
        f"Último erro: {ultimo_erro}"
    )


def selecionar_pauta_inedita(pautas):
    """
    Compara cada candidata com o histórico real do blog.

    Retorna a primeira pauta considerada inédita.
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

        return pauta

    return None


def gerar_pauta_automatica(
    nicho="Casa e Decoração",
):
    """
    Executa o fluxo completo:

    modelos Gemini
        ->
    validação
        ->
    anti-repetição
        ->
    pauta inédita
    """

    print(
        "\n=== GERAÇÃO AUTOMÁTICA DE PAUTA ==="
    )

    candidatas = gerar_candidatas_gemini(
        quantidade=8,
        nicho=nicho,
    )

    print(
        f"\nPautas válidas geradas: "
        f"{len(candidatas)}"
    )

    escolhida = selecionar_pauta_inedita(
        candidatas
    )

    if escolhida is None:
        print(
            "\nNenhuma das pautas geradas "
            "passou pelo anti-repetição."
        )

        print(
            "Gerando um segundo lote..."
        )

        candidatas = gerar_candidatas_gemini(
            quantidade=8,
            nicho=nicho,
        )

        escolhida = selecionar_pauta_inedita(
            candidatas
        )

    if escolhida is None:
        raise RuntimeError(
            "Não foi possível encontrar "
            "uma pauta inédita."
        )

    print(
        "\n=== PAUTA AUTOMÁTICA ESCOLHIDA ==="
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

    return escolhida


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
