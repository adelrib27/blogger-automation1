import json
import re
import time
from pathlib import Path

import article_builder_v1 as builder
import evidence_engine as evidence

# V9 mantém o Gate V7, mas substitui o corpo determinístico compartilhado por
# texto editorial original. A IA NÃO recebe nome nem especificações do produto.
source_path = Path(__file__).with_name("article_builder_evergreen_v7.py")
source = source_path.read_text(encoding="utf-8")
marker = "\nbuilder.main()\n"
if marker not in source:
    raise RuntimeError("SAFE V9: ponto de entrada V7 não encontrado")
source = source.rsplit(marker, 1)[0] + "\n"
ns = {"__name__": "vida_pet_evergreen_v7_for_v9", "__file__": str(source_path)}
exec(compile(source, str(source_path), "exec"), ns, ns)

original_call = ns["original_call"]
strict_gate = ns["strict_gate"]
current_candidate = ns["current_candidate"]
current_package = ns["current_package"]
exact_evidence_ids = ns["exact_evidence_ids"]
subject_for = ns["subject_for"]
last_call = [0.0]

LAB_ROOT = Path(__file__).resolve().parents[1]
HISTORY_PATH = LAB_ROOT / "state" / "article_history.json"

SPEC_TERMS = {
    "eva", "nylon", "silicone", "poliester", "algodao", "aluminio", "aco", "metal", "plastico",
    "impermeavel", "antiderrapante", "lavavel", "resistente", "duravel", "dupla camada", "tripla camada",
    "mosquetao", "capacidade", "voltagem", "potencia", "bivolt", "tamanho unico", "peso suportado",
}
ABSOLUTE_PATTERNS = [
    r"\bgarante\b", r"\bgarantir\b", r"\b100\s*%\b", r"\bsem risco\b", r"\btotalmente seguro\b",
    r"\bcura\b", r"\bcurar\b", r"\btratamento\b", r"\bdiagnostico\b", r"\bprescricao\b",
    r"\bmedicamento\b", r"\bremedio\b", r"\belimina\s+ansiedade\b", r"\bprevine\s+doenca\b",
]
ALLOWED_TAGS = {"p", "h2", "h3", "ul", "li", "strong", "em"}


def load_history():
    try:
        return json.loads(HISTORY_PATH.read_text(encoding="utf-8")) if HISTORY_PATH.exists() else []
    except Exception:
        return []


def previous_for(item_id):
    rows = []
    for row in load_history():
        if str(row.get("itemId") or "") == str(item_id):
            rows.append({"title": row.get("title") or "", "angle": row.get("angle") or ""})
    return rows[-8:]


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

Retorne SOMENTE JSON válido:
{{
  "article_html": "..."
}}

REGRAS OBRIGATÓRIAS:
- Português do Brasil.
- 620 a 720 palavras no article_html.
- Exatamente 7 seções <h2>, cada uma com texto substantivo e diferente.
- Tags permitidas apenas: <p>, <h2>, <h3>, <ul>, <li>, <strong>, <em>.
- Siga especificamente o ÂNGULO informado; não escreva uma ficha genérica de produto.
- Não mencione marca, modelo, material, medidas, capacidade, peças, peso, resistência, impermeabilidade, aderência, durabilidade, desempenho ou qualquer característica física do produto.
- Não use números ou percentuais.
- Não faça promessa de resultado, segurança, eficácia ou comportamento do animal.
- Não faça diagnóstico, tratamento, prescrição, alegação terapêutica ou veterinária.
- Não ensine receita de limpeza nem recomende substâncias.
- Não recomende ração, petisco, suplemento ou medicamento.
- Quando um dado específico for necessário, diga para conferir a página atual do item ou as instruções do fabricante.
- Prefira perguntas práticas, organização da decisão, observação do ambiente e verificação de fontes.
- Não fale sobre SEO, automação, IA, Evidence Engine, fingerprint, plágio ou processo interno do blog.
"""


def sanitize_html(raw):
    text = str(raw or "").strip()
    text = re.sub(r"```(?:html)?|```", "", text, flags=re.I)
    # Remove qualquer tag fora da whitelist, preservando o texto interno.
    text = re.sub(
        r"</?([a-zA-Z0-9]+)(?:\s[^>]*)?>",
        lambda m: m.group(0) if m.group(1).lower() in ALLOWED_TAGS else "",
        text,
    )
    # Retira atributos das tags permitidas.
    text = re.sub(r"<(p|h2|h3|ul|li|strong|em)\s[^>]*>", r"<\1>", text, flags=re.I)
    return text.strip()


def safety_check_editorial(html):
    plain = builder.html_text(html)
    norm = evidence.normalize(plain)
    reasons = []
    if re.search(r"\d", plain):
        reasons.append("editorial_number_present")
    words = set(norm.split())
    hits = sorted(words & SPEC_TERMS)
    if hits:
        reasons.append("editorial_spec_terms:" + ",".join(hits))
    for pattern in ABSOLUTE_PATTERNS:
        if re.search(pattern, norm):
            reasons.append("editorial_absolute_or_medical")
            break
    if re.search(r"\b(?:reduz|elimina|previne|cura|melhora|acalma|estimula)\s+(?:ansiedade|estresse|dor|doenca|sintoma|comportamento)\b", norm):
        reasons.append("editorial_outcome_claim")
    if len(re.findall(r"<h2\b", html, flags=re.I)) != 7:
        reasons.append("editorial_h2_not_7")
    wc = builder.word_count(html)
    if wc < 580:
        reasons.append(f"editorial_too_short:{wc}")
    if wc > 780:
        reasons.append(f"editorial_too_long:{wc}")
    if reasons:
        raise RuntimeError("SAFE V9 editorial rejected: " + ";".join(reasons))
    return html


def fit_title(candidate):
    subject = subject_for(candidate.get("keyword") or "")
    angle = re.sub(r"\s+", " ", str(candidate.get("angle") or "")).strip()
    if angle:
        angle = angle[0].lower() + angle[1:]
    candidates = [
        f"{subject}: {angle}",
        f"{subject}: um novo guia para decidir melhor",
        f"{subject}: como analisar esta escolha",
    ]
    for title in candidates:
        if 35 <= len(title) <= 65:
            return title
    title = candidates[0]
    out = []
    for word in title.split():
        if len(" ".join(out + [word])) > 65:
            break
        out.append(word)
    title = " ".join(out).rstrip(" ,:.-")
    return title if len(title) >= 35 else f"{subject}: critérios práticos para esta escolha"


def normalize_doc(raw_doc, candidate, package):
    if not isinstance(raw_doc, dict):
        raise RuntimeError("SAFE V9: resposta editorial não é objeto JSON")
    editorial = safety_check_editorial(sanitize_html(raw_doc.get("article_html") or ""))
    product_name = re.sub(r"\s+", " ", str(candidate.get("productName") or "")).strip()
    ids = exact_evidence_ids(package)
    if len(ids) < 2:
        raise RuntimeError("SAFE V9: evidências exatas insuficientes")
    article = editorial + (
        "<h2>Identificação do item verificada nesta rodada</h2><p>"
        "As fontes autorizadas desta execução identificam o item selecionado como <strong>" + product_name + "</strong>. "
        "Essa identificação é inserida separadamente do conteúdo editorial. Para qualquer outro detalhe específico, confira a página atual do item e as informações do fabricante quando disponíveis.</p>"
    )
    keyword = str(candidate.get("keyword") or "acessório pet")
    angle = str(candidate.get("angle") or "critérios de escolha")
    meta = f"{keyword.capitalize()}: veja {angle} com critérios práticos, fontes verificáveis e sem depender de promessas do anúncio."
    if len(meta) > 155:
        meta = f"{keyword.capitalize()}: critérios práticos para {angle}, com verificação das informações atuais do item."
    return {
        "title": fit_title(candidate),
        "focus_keyword": keyword,
        "meta_description": meta[:155].rstrip(),
        "article_html": article,
        "cta_text": "Confira a página atual do item e valide os detalhes que importam para a sua decisão antes de escolher.",
        "claim_evidence": [{"claim": product_name, "evidence_ids": ids[:2]}],
    }


def editorial_call(prompt):
    for attempt in range(1, 5):
        elapsed = time.monotonic() - last_call[0]
        if last_call[0] and elapsed < 18.0:
            time.sleep(18.0 - elapsed)
        try:
            last_call[0] = time.monotonic()
            raw, usage = original_call(prompt)
            return normalize_doc(raw, current_candidate[0], current_package[0]), usage
        except builder.ProviderFatalError as exc:
            text = str(exc)
            if "HTTP 429" not in text or attempt >= 4:
                raise
            match = re.search(r"try again in\s+([0-9.]+)s", text, flags=re.I)
            time.sleep(max(6.0, (float(match.group(1)) if match else 6.0) + 2.0))
        except RuntimeError:
            if attempt >= 2:
                raise
            # Uma segunda geração pode corrigir formato/termo indevido sem trocar o produto.
            continue


builder.prompt_for = editorial_prompt
builder.groq_call = editorial_call
builder.gate = strict_gate
builder.main()
