import re
from pathlib import Path

import article_builder_v1 as builder

# V11 preserva os gates e a injeção determinística de fatos do V9/V10.
# A diferença é o retry: em vez de descartar o rascunho rejeitado e pedir outro
# texto do zero, o modelo recebe o próprio rascunho e faz uma revisão incremental.
# Isso ataca a falha dominante do V10 (texto curto) sem reduzir thresholds.
source_path = Path(__file__).with_name("article_builder_evergreen_v10.py")
source = source_path.read_text(encoding="utf-8")
marker = "\nbuilder.main()\n"
if marker not in source:
    raise RuntimeError("SAFE V11: ponto de entrada V10 não encontrado")
source = source.rsplit(marker, 1)[0] + "\n"
ns = {"__name__": "vida_pet_evergreen_v10_for_v11", "__file__": str(source_path)}
exec(compile(source, str(source_path), "exec"), ns, ns)

base_prompt = ns["editorial_prompt"]
provider_call = ns["provider_call"]
normalize_doc = ns["normalize_doc"]
strict_gate = ns["strict_gate"]
retryable_editorial_error = ns["retryable_editorial_error"]
current_candidate = ns["current_candidate"]
current_package = ns["current_package"]

MAX_REPAIR_ATTEMPTS = 4


def plain_word_count(html):
    return builder.word_count(str(html or ""))


def repair_prompt(original_prompt, draft, reason, attempt):
    html = str((draft or {}).get("article_html") or "").strip()
    wc = plain_word_count(html)
    target = 700
    per_section = max(20, min(45, round(max(0, target - wc) / 7)))
    reason_text = re.sub(r"\s+", " ", str(reason or "falha editorial")).strip()[:600]

    return f"""{original_prompt}

REVISÃO INCREMENTAL OBRIGATÓRIA
O rascunho abaixo já foi produzido para este mesmo ângulo e foi rejeitado pelo validador.
MOTIVO DA REJEIÇÃO: {reason_text}
PALAVRAS APROXIMADAS DO RASCUNHO: {wc}
TENTATIVA DE REPAIR: {attempt}

RASCUNHO ATUAL:
{html}

Sua tarefa é REVISAR ESTE RASCUNHO, não começar outro texto curto do zero.
- Preserve a intenção, as sete seções e todo conteúdo seguro que já existe.
- Se o motivo inclui editorial_too_short, acrescente conteúdo substantivo em TODAS as sete seções. Como referência interna, acrescente cerca de {per_section} palavras por seção. Não escreva esse número no artigo.
- Desenvolva exemplos de perguntas, critérios de observação, organização da decisão e formas de conferir informações sem atribuir fatos ao produto.
- Se o motivo inclui editorial_spec_terms, reescreva a frase ofensora sem a palavra de especificação e sem sinônimo que vire uma especificação do item.
- Se o motivo inclui editorial_absolute_or_medical ou editorial_outcome_claim, remova a ideia inteira; não apenas negue a promessa.
- Se o motivo inclui editorial_number_present, reformule sem algarismos.
- Se o motivo inclui editorial_h2_not_7, normalize para exatamente sete <h2>.
- Se o texto ultrapassar a faixa permitida, corte repetição em vez de remover seções.
- O resultado final deve ficar confortavelmente dentro da faixa de comprimento pedida no prompt original.
- Não acrescente produto, marca, modelo, material, medida, peça, desempenho, benefício ou especificação.
- Não acrescente SEO, automação, IA, histórico editorial, gate ou processo interno.

Retorne SOMENTE um novo objeto JSON válido no formato {{"article_html":"..."}} com o artigo completo revisado.
"""


def editorial_call(prompt):
    draft = None
    last_reason = ""
    last_usage = {}

    for attempt in range(1, MAX_REPAIR_ATTEMPTS + 1):
        current_prompt = prompt if draft is None else repair_prompt(prompt, draft, last_reason, attempt)
        try:
            raw, usage = provider_call(current_prompt)
            draft = raw
            last_usage = usage
            doc = normalize_doc(raw, current_candidate[0], current_package[0])
            return doc, usage
        except RuntimeError as exc:
            if not retryable_editorial_error(exc) or attempt >= MAX_REPAIR_ATTEMPTS:
                raise
            last_reason = str(exc)
            continue

    raise RuntimeError(f"SAFE V11: repair esgotado: {last_reason}; usage={bool(last_usage)}")


builder.prompt_for = base_prompt
builder.groq_call = editorial_call
builder.gate = strict_gate
builder.main()
