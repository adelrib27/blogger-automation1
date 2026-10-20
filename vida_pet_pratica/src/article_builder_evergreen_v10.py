import json
import re
import time
from pathlib import Path

import article_builder_v1 as builder

# V10 preserva integralmente os gates e a injeção determinística de fatos do V9.
# A mudança é de confiabilidade: quando o texto editorial falha no gate V9,
# uma nova geração recebe o motivo da rejeição e deve reescrever o corpo do zero.
source_path = Path(__file__).with_name("article_builder_evergreen_v9.py")
source = source_path.read_text(encoding="utf-8")
marker = "\nbuilder.main()\n"
if marker not in source:
    raise RuntimeError("SAFE V10: ponto de entrada V9 não encontrado")
source = source.rsplit(marker, 1)[0] + "\n"
ns = {"__name__": "vida_pet_evergreen_v9_for_v10", "__file__": str(source_path)}
exec(compile(source, str(source_path), "exec"), ns, ns)

original_call = ns["original_call"]
normalize_doc = ns["normalize_doc"]
strict_gate = ns["strict_gate"]
current_candidate = ns["current_candidate"]
current_package = ns["current_package"]
previous_for = ns["previous_for"]
last_call = [0.0]

MAX_EDITORIAL_ATTEMPTS = 4
MIN_CALL_INTERVAL_SECONDS = 18.0


def editorial_prompt(candidate, package):
    current_candidate[0] = candidate
    current_package[0] = package
    category = str(candidate.get("category") or "Pets")
    keyword = str(candidate.get("keyword") or "acessório pet")
    angle = str(candidate.get("angle") or "critérios de escolha")
    prior = previous_for(candidate.get("itemId"))

    return f"""Você escreve para o blog brasileiro Vida Pet Prática.

Crie um guia editorial ORIGINAL sobre o TEMA, sem descrever nenhum produto específico.
CATEGORIA: {category}
PALAVRA-CHAVE/TEMA: {keyword}
ÂNGULO DESTA PÁGINA: {angle}
ABORDAGENS JÁ USADAS NESTE ITEM (não repetir): {json.dumps(prior, ensure_ascii=False)}

IMPORTANTE: você NÃO recebeu o nome nem as especificações do produto. Não tente adivinhá-los.
O corpo deve ser útil por si só como orientação de planejamento, comparação, organização ou verificação.

Retorne SOMENTE JSON válido no formato:
{{
  "article_html": "..."
}}

REGRAS OBRIGATÓRIAS:
- Português do Brasil.
- Mire aproximadamente setecentas e vinte a setecentas e sessenta palavras no article_html; não entregue texto curto.
- Exatamente sete seções <h2>, cada uma com texto substantivo e diferente.
- Tags permitidas apenas: <p>, <h2>, <h3>, <ul>, <li>, <strong>, <em>.
- Siga especificamente o ÂNGULO informado; não escreva uma ficha genérica de produto.
- Não mencione marca, modelo, material, medidas, peças, peso, características físicas, desempenho ou especificações do produto.
- Não use algarismos nem percentuais no article_html.
- Não faça promessa de resultado, segurança, eficácia ou comportamento do animal.
- Não faça diagnóstico, tratamento, prescrição, alegação terapêutica ou veterinária.
- Não ensine receita de limpeza nem recomende substâncias.
- Não recomende ração, petisco, suplemento ou medicamento.
- Quando um dado específico for necessário, diga apenas para conferir a página atual do item ou as instruções do fabricante.
- Prefira perguntas práticas, organização da decisão, observação do ambiente e verificação de fontes.
- Não fale sobre SEO, automação, IA, Evidence Engine, fingerprint, histórico editorial, rodízio, gate, plágio ou processo interno do blog.
- Evite completamente, inclusive em frases negativas, palavras de especificação como: impermeável, antiderrapante, lavável, resistente, durável, mosquetão, capacidade, voltagem, potência, bivolt, nylon, silicone, plástico, metal, aço, alumínio, poliéster, algodão e EVA.
- Evite completamente, inclusive para negar uma promessa, verbos ou expressões como: garante, garantir, cura, curar, tratamento, diagnóstico, prescrição, medicamento, remédio, sem risco e totalmente seguro.
- Não use palavras como reduz, elimina, previne, melhora, acalma ou estimula ligadas a ansiedade, estresse, dor, doença, sintoma ou comportamento.
"""


def correction_prompt(base_prompt, reason, attempt):
    reason_text = re.sub(r"\s+", " ", str(reason or "falha editorial")).strip()[:500]
    return base_prompt + f"""

CORREÇÃO OBRIGATÓRIA — NOVA GERAÇÃO
A tentativa editorial anterior foi rejeitada pelo validador: {reason_text}
Esta é a tentativa de correção {attempt}.
Reescreva TODO o JSON do zero. Não edite nem reaproveite frases da tentativa anterior.
Se houve editorial_too_short, aproxime-se do topo da faixa pedida e desenvolva cada seção com substância.
Se houve editorial_spec_terms, não use nenhuma palavra de especificação apontada pelo validador, nem mesmo para dizer que ela deve ser conferida.
Se houve editorial_absolute_or_medical ou editorial_outcome_claim, remova completamente esse vocabulário; não tente formular a mesma ideia de modo negativo.
Se houve editorial_number_present, escreva quantidades por extenso ou reformule sem quantidade.
Se houve editorial_h2_not_7, entregue exatamente sete <h2>.
Mantenha o foco no ângulo e retorne somente o objeto JSON válido com article_html.
"""


def wait_for_slot():
    elapsed = time.monotonic() - last_call[0]
    if last_call[0] and elapsed < MIN_CALL_INTERVAL_SECONDS:
        time.sleep(MIN_CALL_INTERVAL_SECONDS - elapsed)


def provider_call(prompt):
    for attempt in range(1, 5):
        wait_for_slot()
        try:
            last_call[0] = time.monotonic()
            return original_call(prompt)
        except builder.ProviderFatalError as exc:
            text = str(exc)
            if "HTTP 429" not in text or attempt >= 4:
                raise
            match = re.search(r"try again in\s+([0-9.]+)s", text, flags=re.I)
            time.sleep(max(6.0, (float(match.group(1)) if match else 6.0) + 2.0))


def retryable_editorial_error(exc):
    text = str(exc)
    return (
        text.startswith("SAFE V9 editorial rejected:")
        or "Groq não retornou objeto JSON" in text
        or "Expecting" in text
        or "JSON" in text
    )


def editorial_call(prompt):
    last_reason = ""
    for attempt in range(1, MAX_EDITORIAL_ATTEMPTS + 1):
        current_prompt = prompt if attempt == 1 else correction_prompt(prompt, last_reason, attempt)
        try:
            raw, usage = provider_call(current_prompt)
            doc = normalize_doc(raw, current_candidate[0], current_package[0])
            return doc, usage
        except RuntimeError as exc:
            if not retryable_editorial_error(exc) or attempt >= MAX_EDITORIAL_ATTEMPTS:
                raise
            last_reason = str(exc)
            continue
    raise RuntimeError("SAFE V10: tentativas editoriais esgotadas")


builder.prompt_for = editorial_prompt
builder.groq_call = editorial_call
builder.gate = strict_gate
builder.main()
