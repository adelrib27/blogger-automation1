import html
import json
import os
import re
import time
import urllib.request
from pathlib import Path

from cta_context import cta_block, default_cta_lead, generate_cta_lead, validate_cta_lead
from editorial_normalizer import normalize_editorial
from quality_gate import quality, word_count
from category_rotation import load_state, order_items

ROOT = Path(__file__).resolve().parents[2]
QUEUE = ROOT / "casa_decoracao" / "data" / "editorial_queue.json"
OUT_DIR = ROOT / "casa_decoracao" / "data" / "generated"
ROTATION = ROOT / "casa_decoracao" / "data" / "category_rotation.json"
MODEL = os.getenv("CASA_AI_MODEL", "@cf/qwen/qwen3-30b-a3b-fp8").strip()
BATCH_SIZE = max(1, min(int(os.getenv("CASA_GENERATION_BATCH_SIZE", "1")), 10))
ENABLED = os.getenv("CASA_GENERATION_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}
BODY_ATTEMPTS = max(1, min(int(os.getenv("CASA_GENERATION_BODY_ATTEMPTS", "3")), 3))
CTA_ATTEMPTS = max(1, min(int(os.getenv("CASA_CTA_ATTEMPTS", "2")), 2))


def load(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def creds():
    account = os.getenv("CASA_CLOUDFLARE_ACCOUNT_ID", "").strip()
    token = os.getenv("CASA_CLOUDFLARE_API_TOKEN", "").strip()
    if not account or not token:
        raise RuntimeError("Credenciais Cloudflare Casa e Decoração ausentes")
    return account, token


def _text_value(value):
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        for key in ("content", "text", "output_text", "response"):
            if key in value:
                text = _text_value(value.get(key))
                if text:
                    return text
        message = value.get("message")
        if message is not None:
            text = _text_value(message)
            if text:
                return text
    if isinstance(value, list):
        for part in value:
            text = _text_value(part)
            if text:
                return text
    return ""


def extract_text(payload):
    result = payload.get("result") if isinstance(payload, dict) else None
    if not isinstance(result, dict):
        return ""
    for key in ("response", "text", "output_text"):
        text = _text_value(result.get(key))
        if text:
            return text
    for choice in result.get("choices") or []:
        if not isinstance(choice, dict):
            continue
        text = _text_value(choice.get("message"))
        if text:
            return text
    return ""


def ai(prompt, retries=3):
    account, token = creds()
    prompt = str(prompt or "").strip()
    if MODEL.startswith("@cf/qwen/qwen3") and not prompt.startswith("/no_think"):
        prompt = "/no_think\n" + prompt
    req_body = json.dumps(
        {
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 8192,
            "temperature": 0.2,
        },
        ensure_ascii=False,
    ).encode()
    endpoint = f"https://api.cloudflare.com/client/v4/accounts/{account}/ai/run/{MODEL}"
    last = ""
    for attempt in range(retries):
        req = urllib.request.Request(
            endpoint,
            data=req_body,
            method="POST",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "CasaEDecoracao-Editorial/3.0",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as response:
                payload = json.loads(response.read().decode("utf-8", "replace"))
            text = extract_text(payload)
            if text:
                return text
            last = "resposta vazia ou em formato não reconhecido"
        except Exception as exc:
            last = str(exc)
        if attempt + 1 < retries:
            time.sleep(5 if attempt == 0 else 15)
    raise RuntimeError("Falha Workers AI: " + last)


def clean(raw):
    raw = re.sub(r"^```(?:html)?\s*", "", str(raw or "").strip(), flags=re.I)
    raw = re.sub(r"\s*```$", "", raw)
    raw = re.sub(r"</?(?:html|head|body)[^>]*>", "", raw, flags=re.I)
    raw = re.sub(r"<h1[^>]*>.*?</h1>", "", raw, flags=re.I | re.S)
    return raw.strip()


def parse_json(raw):
    text = str(raw or "").strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.I)
    text = re.sub(r"\s*```$", "", text)
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise RuntimeError("planejamento editorial não retornou JSON")
    try:
        data = json.loads(text[start : end + 1])
    except json.JSONDecodeError as exc:
        raise RuntimeError("JSON editorial inválido") from exc
    if not isinstance(data, dict):
        raise RuntimeError("planejamento editorial inválido")
    return data


def slug_category(name):
    return {
        "Decoração": "decoracao",
        "Organização": "organizacao",
        "Sala": "sala",
        "Quarto": "quarto",
        "Cozinha": "cozinha",
        "Banheiro": "banheiro",
        "Área Externa": "area-externa",
        "Cama, Mesa e Banho": "cama-mesa-banho",
    }.get(name, "")


def cut_text(value, limit):
    value = re.sub(r"\s+", " ", str(value or "")).strip()
    if len(value) <= limit:
        return value
    short = value[: limit + 1].rsplit(" ", 1)[0].rstrip(" -:;,. ")
    while short and short.casefold().split()[-1] in {
        "a", "ao", "aos", "as", "com", "da", "das", "de", "do", "dos", "e", "em", "na", "nas", "no", "nos", "para", "por", "sem"
    }:
        short = short.rsplit(" ", 1)[0].rstrip(" -:;,. ")
    return (short or value[:limit].rstrip(" -:;,. ")).rstrip(".") + "."


def editorial_plan_prompt(item):
    return f"""Você é editor de um blog brasileiro chamado Casa e Decoração.

Use o produto real da Shopee apenas como ponto de partida para escolher UM ÚNICO TÍTULO EDITORIAL útil ao leitor. Neste sistema, tema e título são a mesma coisa: não crie um campo de tema separado.

PRODUTO REAL: {item['product']}
INTENÇÃO DA BUSCA: {item['source_keyword']}
CATEGORIA: {item['category']}

REGRAS:
- O título editorial deve ter entre 35 e 65 caracteres.
- Deve tratar de uma necessidade, dúvida, organização, decoração, escolha ou situação doméstica coerente com o produto.
- Não copie nem faça paráfrase rasa do título comercial.
- Não inclua marca, loja, quantidade, medidas, material, voltagem, potência, desconto, preço ou promessa comercial apenas porque aparecem no anúncio.
- O conteúdo deve continuar útil mesmo que o leitor nunca clique no produto.
- Não transforme automaticamente todo produto em review, ficha técnica ou "vale a pena comprar?".
- Gere uma palavra-chave principal natural, coerente com o título.
- Explique em uma frase qual é a necessidade do leitor e em outra como o produto se conecta naturalmente ao assunto.

Responda SOMENTE em JSON válido:
{{
  "title": "...",
  "keyword": "...",
  "reader_need": "...",
  "product_connection": "..."
}}
"""


def make_plan(item, raw=None):
    data = parse_json(ai(editorial_plan_prompt(item)) if raw is None else raw)
    title = re.sub(r"\s+", " ", str(data.get("title") or "")).strip()
    keyword = re.sub(r"\s+", " ", str(data.get("keyword") or "")).strip()
    reader_need = re.sub(r"\s+", " ", str(data.get("reader_need") or "")).strip()
    product_connection = re.sub(r"\s+", " ", str(data.get("product_connection") or "")).strip()
    if not 35 <= len(title) <= 65:
        raise RuntimeError(f"título editorial fora da faixa: {len(title)}")
    if not keyword:
        raise RuntimeError("palavra-chave editorial ausente")
    if not reader_need or not product_connection:
        raise RuntimeError("contexto editorial incompleto")
    return {
        "title": title,
        "keyword": keyword,
        "reader_need": reader_need,
        "product_connection": product_connection,
    }


def meta_description(plan):
    title = str(plan.get("title") or "").strip().rstrip(".")
    keyword = str(plan.get("keyword") or "").strip()
    text = f"{title}. Veja critérios práticos sobre {keyword}, pontos de atenção e o que conferir antes de decidir para sua casa."
    if len(text) < 120:
        text = text.rstrip(".") + ", com foco em uso real, medidas do espaço e informações confirmadas no anúncio."
    return cut_text(text, 155)


def universal_article_rules(item):
    return """
- 600 a 900 palavras, pelo menos 5 H2 distintos; sem H1.
- O artigo deve entregar valor por si só, mesmo sem clique no produto.
- O produto é apenas uma referência relacionada ao tema; não escreva como página de venda, review obrigatório ou ficha técnica.
- O nome comercial do produto é contexto interno. NÃO repita no corpo a oferta específica, marca, título comercial, quantidade, medidas, material ou especificações não confirmadas.
- Fale da classe genérica do produto e dos critérios que o leitor deve verificar antes da escolha.
- Não copie nem faça paráfrase rasa do título comercial como título editorial.
- Não invente preço, desconto, estoque, entrega, dimensões, material, capacidade, potência, voltagem, compatibilidade, certificação, garantia ou desempenho.
- Quando uma medida, material ou especificação for relevante e não estiver confirmada, oriente a conferir o anúncio, ficha técnica ou manual.
- Não diga que testamos, usamos ou comprovamos o produto.
- Não faça alegações médicas, terapêuticas ou de correção postural.
- Não associe produtos a alergias, asma, rinite, ausência de pólen/esporos ou qualquer benefício de saúde sem fonte verificável.
- Não declare que um produto é seguro para crianças, bebês ou animais, não tóxico, inofensivo, sustentável, ecológico ou econômico a longo prazo sem fonte verificável.
- Não prometa que algo permanecerá intacto, durará por muito tempo ou não poderá ser arrancado, quebrado ou danificado.
- Não dê passo a passo de instalação elétrica, gás, ligação de fios ou misturas químicas.
- Não faça promessas absolutas de segurança, impermeabilidade, durabilidade, conforto ou resultado.
- Para organização e decoração, considere espaço disponível, rotina, manutenção, armazenamento e compatibilidade visual sem inventar fatos do produto.
- Evite exemplos arbitrários, frases genéricas repetitivas e conclusões vazias.
- Use naturalmente a palavra-chave principal.
- Não escreva CTA, links, imagem do produto, preço ou bloco de afiliado; o código insere isso depois.
- HTML somente com <p>, <h2>, <h3>, <ul>, <li>, <strong>, <em>. Sem estilos, markdown, H1, links ou scripts.
"""


def article_prompt(item, plan):
    return f"""Você é editor de um blog brasileiro chamado Casa e Decoração.

TÍTULO EDITORIAL ÚNICO: {plan['title']}
PALAVRA-CHAVE PRINCIPAL: {plan['keyword']}
NECESSIDADE DO LEITOR: {plan['reader_need']}
CONEXÃO NATURAL DO PRODUTO: {plan['product_connection']}
PRODUTO REAL DE REFERÊNCIA: {item['product']}
CATEGORIA: {item['category']}

Escreva um artigo informativo em português do Brasil.

REGRAS:
{universal_article_rules(item)}

Responda SOMENTE com o fragmento HTML.
"""


def repair_prompt(item, plan, raw, failure):
    return f"""Você é revisor editorial do blog Casa e Decoração.

O rascunho abaixo foi BLOQUEADO pelos gates automáticos. Reescreva o artigo inteiro corrigindo as falhas, sem discutir o diagnóstico e sem adicionar explicações fora do HTML.

TÍTULO EDITORIAL ÚNICO: {plan['title']}
PALAVRA-CHAVE PRINCIPAL: {plan['keyword']}
CATEGORIA: {item['category']}
PRODUTO REAL: {item['product']}

FALHAS DETECTADAS:
{failure}

REGRAS UNIVERSAIS QUE DEVEM SER CUMPRIDAS:
{universal_article_rules(item)}

RASCUNHO BLOQUEADO:
{clean(raw)}

Responda SOMENTE com um novo fragmento HTML completo.
"""


def insert_contextual_blocks(editorial, item, cta_lead):
    h2_matches = list(re.finditer(r"<h2\b[^>]*>.*?</h2>", editorial, flags=re.I | re.S))
    if len(h2_matches) < 4:
        raise RuntimeError("estrutura insuficiente para posicionar CTAs")
    third_h2_start = h2_matches[2].start()
    first_part = editorial[:third_h2_start].rstrip()
    second_part = editorial[third_h2_start:].rstrip()
    cta = cta_block(item, cta_lead)
    cat_slug = slug_category(item.get("category"))
    internal = (
        f'<p><a href="/category/{cat_slug}/">Veja outros guias de {html.escape(str(item.get("category") or ""))}</a>.</p>'
        if cat_slug
        else ""
    )
    pieces = [first_part, cta, second_part]
    if internal:
        pieces.append(internal)
    pieces.append(cta)
    return "\n\n".join(x for x in pieces if x)


def build(item, plan, raw, enforce=True, cta_lead=None, cta_generation_mode="test-or-fallback"):
    editorial = normalize_editorial(clean(raw))
    wc = word_count(editorial)
    if wc < 500:
        raise RuntimeError(f"artigo curto: {wc}")
    title = plan["title"]
    article_item = {**item, "topic": title, "editorial_title": title}
    lead = validate_cta_lead(article_item, cta_lead or default_cta_lead(article_item))
    content = insert_contextual_blocks(editorial, article_item, lead)
    article = {
        **article_item,
        "seo_title": title,
        "meta_description": meta_description(plan),
        "focus_keyword": plan["keyword"],
        "reader_need": plan["reader_need"],
        "product_connection": plan["product_connection"],
        "excerpt": meta_description(plan),
        "editorial_html": editorial,
        "content_html": content,
        "cta_lead": lead,
        "cta_generation_mode": cta_generation_mode,
        "word_count": wc,
        "generation_model": MODEL,
        "generation_mode": "qwen3-no-think+universal-normalizer" if MODEL.startswith("@cf/qwen/qwen3") else "standard+universal-normalizer",
        "status": "GENERATED",
    }
    article["quality"] = quality(article)
    if enforce and article["quality"]["status"] == "REJECTED":
        raise RuntimeError("quality gate: " + ", ".join(article["quality"]["reasons"]))
    return article


def generate_article(item, plan):
    raw = ai(article_prompt(item, plan))
    editorial = ""
    last_error = ""
    for attempt in range(BODY_ATTEMPTS):
        try:
            candidate = build(item, plan, raw, enforce=True)
            editorial = candidate["editorial_html"]
            break
        except RuntimeError as exc:
            last_error = str(exc)
            if attempt + 1 >= BODY_ATTEMPTS:
                raise RuntimeError("geração editorial bloqueada após revisões: " + last_error)
            raw = ai(repair_prompt(item, plan, raw, last_error))
    cta_lead, cta_mode = generate_cta_lead(item, plan, ai, attempts=CTA_ATTEMPTS)
    return build(item, plan, editorial, enforce=True, cta_lead=cta_lead, cta_generation_mode=cta_mode)


def main():
    if not ENABLED:
        print("Geração desativada por CASA_GENERATION_ENABLED=false; nenhuma chamada de IA realizada.")
        return
    doc = load(QUEUE, {})
    items = doc.get("items") or []
    rotation = load_state(ROTATION)
    candidates = order_items(
        [item for item in items if item.get("status") in {"PENDING", "QUARANTINE"}],
        rotation,
        pending_only=True,
    )
    generated = 0
    attempted = 0
    max_attempts = max(BATCH_SIZE * 6, 6)
    for item in candidates:
        if generated >= BATCH_SIZE or attempted >= max_attempts:
            break
        attempted += 1
        try:
            plan = make_plan(item)
            article = generate_article(item, plan)
            OUT_DIR.mkdir(parents=True, exist_ok=True)
            save(OUT_DIR / f"{int(item['id']):03d}.json", article)
            item["topic"] = plan["title"]
            item["editorial_title"] = plan["title"]
            item["status"] = "GENERATED" if article["quality"]["status"] == "DRAFT_READY" else "HUMAN_REVIEW"
            item["quality"] = article["quality"]
            item["last_error"] = ""
            if item["status"] == "GENERATED":
                generated += 1
        except Exception as exc:
            item["generation_attempts"] = int(item.get("generation_attempts") or 0) + 1
            item["last_error"] = str(exc)[:800]
            item["status"] = "BLOCKED" if item["generation_attempts"] >= 3 else "QUARANTINE"
    doc["items"] = items
    save(QUEUE, doc)
    print(f"Geração Casa: tentados={attempted} | gerados_aprovados={generated} | ciclo={rotation.get('cycle')} | pendentes={rotation.get('pending_categories')}")


if __name__ == "__main__":
    main()
