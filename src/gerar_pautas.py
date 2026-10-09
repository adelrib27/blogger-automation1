import json
import os
import re
import time

from google import genai

from pautas import comparar_com_historico


MODELO_GEMINI = "gemini-3.8-flash"


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


def gerar_candidatas_gemini(
    quantidade=8,
    nicho="Casa e Decoração",
):
    """
    Pede ao Gemini uma lista de pautas candidatas.

    A decisão final sobre repetição NÃO fica com o Gemini.
    As pautas serão comparadas posteriormente com o
    historico.json pelo nosso próprio motor.
    """

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY não encontrada."
        )

    client = genai.Client(api_key=api_key)

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

    tentativas = 3
    esperas = [5, 15]

    for tentativa in range(1, tentativas + 1):
        try:
            print(
                f"Tentativa {tentativa}/{tentativas} "
                "para gerar novas pautas..."
            )

            resposta = client.models.generate_content(
                model=MODELO_GEMINI,
                contents=prompt,
            )

            texto = resposta.text

            if not texto:
                raise RuntimeError(
                    "Gemini retornou resposta vazia."
                )

            texto_json = limpar_json_resposta(texto)

            if not texto_json:
                raise RuntimeError(
                    "Não foi possível localizar JSON "
                    "na resposta do Gemini."
                )

            pautas = json.loads(texto_json)

            if not isinstance(pautas, list):
                raise RuntimeError(
                    "A resposta não contém uma lista de pautas."
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

            return pautas_validas

        except Exception as erro:
            print(
                f"Erro na tentativa "
                f"{tentativa}/{tentativas}: {erro}"
            )

            mensagem = str(erro)

            temporario = any(
                codigo in mensagem
                for codigo in (
                    "429",
                    "503",
                    "RESOURCE_EXHAUSTED",
                    "UNAVAILABLE",
                )
            )

            # Erros de JSON também podem ser resolvidos
            # solicitando uma nova geração.
            erro_json = isinstance(
                erro,
                json.JSONDecodeError,
            )

            if tentativa >= tentativas:
                break

            if not temporario and not erro_json:
                # Para respostas estruturalmente ruins,
                # também permitimos uma nova tentativa.
                if (
                    "JSON" not in mensagem
                    and "pauta válida" not in mensagem
                    and "lista de pautas" not in mensagem
                ):
                    break

            espera = esperas[tentativa - 1]

            print(
                f"Aguardando {espera} segundos "
                "antes da próxima tentativa..."
            )

            time.sleep(espera)

    raise RuntimeError(
        "Não foi possível gerar pautas válidas "
        "com o Gemini."
    )


def selecionar_pauta_inedita(pautas):
    """
    Compara cada candidata com o histórico real do blog.

    Retorna a primeira pauta considerada inédita.
    """

    print("\n=== ANÁLISE ANTI-REPETIÇÃO ===")

    for numero, pauta in enumerate(
        pautas,
        start=1,
    ):
        titulo = pauta["titulo"]
        palavra_chave = pauta["palavra_chave"]

        resultado = comparar_com_historico(
            titulo=titulo,
            palavra_chave=palavra_chave,
        )

        print(f"\nCandidata {numero}:")
        print("Título:", titulo)
        print(
            "Palavra-chave:",
            palavra_chave,
        )

        if resultado["repetida"]:
            print("Resultado: REJEITADA")
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

            continue

        print("Resultado: APROVADA")
        print("Motivo: pauta inédita")

        return pauta

    return None


def gerar_pauta_automatica(
    nicho="Casa e Decoração",
):
    """
    Executa o fluxo completo:
    Gemini -> validação -> histórico -> pauta inédita.
    """

    print(
        "\n=== GERAÇÃO AUTOMÁTICA DE PAUTA ==="
    )

    candidatas = gerar_candidatas_gemini(
        quantidade=8,
        nicho=nicho,
    )

    print(
        f"Pautas válidas geradas: "
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
        escolhida["palavra_chave"],
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
