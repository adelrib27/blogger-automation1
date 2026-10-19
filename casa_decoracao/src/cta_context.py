import html
import json
import re
import time

CTA_CLASS = "cd-produto-relacionado"
CTA_PRODUCT_TITLE_CLASS = "cd-produto-titulo-original"
CTA_BUTTON_TEXT = "CONFERIR ESPECIFICAÇÕES DO MODELO NA SHOPEE"
CTA_CONSULT_TEXT = "consultar o modelo na Shopee"
CTA_FORBIDDEN = re.compile(
    r"\b(?:imperd[ií]vel|maravilhos[oa]|incr[ií]vel|perfeit[oa]|melhor|excelente|ideal|promo[cç][aã]o|oferta|corra|aproveite|n[aã]o\s+perca|[uú]ltimas?\s+unidades?)\b",
    re.I,
)


def _parse_json(raw):
    text = str(raw or "").strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.I)
    text = re.sub(r"\s*```$", "", text)
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise RuntimeError("CTA contextual não retornou JSON")
    try:
        data = json.loads(text[start : end + 1])
    except json.JSONDecodeError as exc:
        raise RuntimeError("JSON do CTA contextual inválido") from exc
    if not isinstance(data, dict):
        raise RuntimeError("JSON do CTA contextual inválido")
    return data


def _word_count(value):
    return len(re.findall(r"\b[\wÀ-ÿ'-]+\b", str(value or ""), re.UNICODE))


def cta_copy_prompt(item, plan):
    return f"""Atue estritamente como um jornalista ou criador de conteúdo informativo de nicho.

Ao apresentar o produto relacionado, use um tom neutro, de recomendação e prestação de serviço. O produto deve ser inserido de forma orgânica, funcionando apenas como uma sugestão de consulta para o leitor que deseja se aprofundar na solução prática do problema abordado.

TÍTULO DO ARTIGO: {plan['title']}
NECESSIDADE DO LEITOR: {plan['reader_need']}
CONEXÃO EDITORIAL: {plan['product_connection']}
PRODUTO REAL DA SHOPEE: {item['product']}

REGRAS OBRRIGATÓRIAS:
- Escreva EXATAMENTE 2 frases, entre 35 e 70 palavras no total.
- A primeira frase deve começar com "Para quem" e conectar o conteúdo do artigo ao produto como uma opção de consulta, sem tom publicitário.
- A segunda frase deve orientar o leitor a conferir as especificações do modelo no anúncio e terminar com a expressão exata "você também pode consultar o modelo na Shopee.".
- A expressão "consultar o modelo na Shopee" será transformada pelo código em um link de afiliado; não escreva HTML nem URL.
- Pode abreviar o nome comercial apenas de forma fiel, preservando tipo, marca e números realmente presentes no título do produto.
- Não invente material, robustez, desempenho, finalidade específica, experiência de uso, teste, popularidade, certificação ou característica que não esteja explicitamente disponível.
- Evite adjetivos exagerados e expressões como "imperdível", "maravilhoso", "incrível", "perfeito", "melhor", "excelente", "ideal", "promoção", "oferta", "corra", "aproveite" e equivalentes.
- Não mencione preço, desconto, estoque, frete, urgência ou escassez.
- Não use linguagem de venda agressiva.
- Não escreva botão, link, HTML ou aviso de afiliado; o código insere esses elementos.

Responda SOMENTE em JSON válido:
{{"lead":"..."}}
"""


def validate_cta_lead(item, value):
    lead = re.sub(r"\s+", " ", str(value or "")).strip()
    if not lead:
        raise RuntimeError("CTA contextual vazio")
    if "<" in lead or ">" in lead or "http" in lead.casefold():
        raise RuntimeError("CTA contextual contém HTML ou link")
    words = _word_count(lead)
    if not 25 <= words <= 85:
        raise RuntimeError(f"CTA contextual fora da faixa: {words}")
    sentences = [x for x in re.split(r"(?<=[.!?])\s+", lead) if x.strip()]
    if len(sentences) != 2:
        raise RuntimeError(f"CTA contextual deve ter 2 frases: {len(sentences)}")
    if not lead.casefold().startswith("para quem"):
        raise RuntimeError("CTA contextual não começa com 'Para quem'")
    if CTA_FORBIDDEN.search(lead):
        raise RuntimeError("CTA contextual com tom promocional exagerado")
    if re.search(r"\b(?:pre[cç]o|desconto|estoque|frete|urg[eê]ncia|escassez)\b", lead, re.I):
        raise RuntimeError("CTA contextual com condição comercial")
    if CTA_CONSULT_TEXT.casefold() not in lead.casefold():
        raise RuntimeError("CTA contextual sem a chamada de consulta clicável")
    product_tokens = {
        x for x in re.findall(r"[\wÀ-ÿ]+", str(item.get("product") or "").casefold()) if len(x) >= 4
    }
    lead_tokens = set(re.findall(r"[\wÀ-ÿ]+", lead.casefold()))
    if product_tokens and len(product_tokens & lead_tokens) < min(2, len(product_tokens)):
        raise RuntimeError("CTA contextual sem referência suficiente ao produto")
    if "especifica" not in lead.casefold() or "anúncio" not in lead.casefold():
        raise RuntimeError("CTA contextual não orienta consulta às especificações no anúncio")
    return lead


def make_cta_lead(item, plan, raw):
    data = _parse_json(raw)
    return validate_cta_lead(item, data.get("lead"))


def default_cta_lead(item):
    product = re.sub(r"\s+", " ", str(item.get("product") or "produto relacionado")).strip()
    return (
        "Para quem deseja colocar essas orientações em prática e quer consultar uma opção relacionada, "
        f"o modelo {product} é uma referência disponível na Shopee. "
        "Confira as especificações do modelo no anúncio para avaliar se ele atende à sua necessidade; "
        "você também pode consultar o modelo na Shopee."
    )


def generate_cta_lead(item, plan, ai_call, attempts=2):
    last = ""
    for attempt in range(max(1, min(int(attempts), 2))):
        try:
            return make_cta_lead(item, plan, ai_call(cta_copy_prompt(item, plan))), "qwen3-contextual"
        except Exception as exc:
            last = str(exc)
            if attempt + 1 < attempts:
                time.sleep(1)
    fallback = validate_cta_lead(item, default_cta_lead(item))
    return fallback, "safe-fallback:" + last[:180]


def _linked_lead(item, cta_lead, link):
    lead = html.escape(validate_cta_lead(item, cta_lead or default_cta_lead(item)))
    anchor = (
        f'<a href="{link}" target="_blank" rel="nofollow sponsored" '
        'style="color:#0F766E;text-decoration:underline;text-decoration-thickness:1.5px;'
        'text-underline-offset:3px;font-weight:800;">'
        f"{CTA_CONSULT_TEXT}</a>"
    )
    linked, count = re.subn(re.escape(CTA_CONSULT_TEXT), anchor, lead, count=1, flags=re.I)
    if count != 1:
        raise RuntimeError("CTA contextual não pôde criar o link de consulta")
    return linked


def cta_block(item, cta_lead):
    product = html.escape(str(item.get("product") or "Produto relacionado"))
    link = html.escape(str(item.get("affiliate_link") or ""), quote=True)
    lead = _linked_lead(item, cta_lead, link)
    image_url = str(item.get("image_url") or "").strip()
    image = ""
    if image_url.startswith("https://"):
        src = html.escape(image_url, quote=True)
        image = (
            '<div style="width:100%;max-width:340px;height:300px;margin:0 auto 18px;'
            'padding:10px;display:flex;align-items:center;justify-content:center;'
            'background:#ffffff;border:1px solid #e5e7eb;border-radius:12px;overflow:hidden;">'
            f'<img src="{src}" alt="{product}" loading="lazy" '
            'style="display:block;width:100%;height:100%;object-fit:contain;" />'
            "</div>"
        )

    product_title = (
        f'<p class="{CTA_PRODUCT_TITLE_CLASS}" style="margin:0 0 14px;line-height:1.4;'
        'font-size:18px;font-weight:700;color:#111827;">'
        f'{product}</p>'
    )

    return "".join(
        [
            f'<div class="{CTA_CLASS}" style="margin:28px 0;padding:22px;border:1px solid #e5e7eb;'
            'border-radius:14px;background:#f8fafc;text-align:center;box-shadow:0 4px 14px rgba(0,0,0,.08);">',
            '<p style="margin:0 0 10px;font-size:14px;font-weight:700;letter-spacing:.4px;">'
            "🛒 REFERÊNCIA RELACIONADA AO TEMA</p>",
            image,
            product_title,
            '<p style="margin:0 0 18px;line-height:1.65;font-family:\'Trebuchet MS\',\'Segoe UI\',Arial,sans-serif;'
            'font-size:21px;font-weight:700;color:#115E59;background:linear-gradient(135deg,#ECFDF5 0%,#F0FDFA 100%);'
            'border:1px solid #99F6E4;border-left:5px solid #14B8A6;border-radius:12px;padding:16px 18px;'
            f'box-shadow:0 6px 18px rgba(20,184,166,.12);letter-spacing:.1px;">{lead}</p>',
            f'<p style="margin:0 0 16px;"><a href="{link}" target="_blank" rel="nofollow sponsored" '
            'style="display:inline-block;padding:14px 22px;background:#16A34A;color:#ffffff;'
            'text-decoration:none;font-weight:700;border-radius:10px;font-size:16px;line-height:1.3;">'
            f"👉 {CTA_BUTTON_TEXT}</a></p>",
            '<p style="margin:0 0 10px;font-size:13px;line-height:1.5;"><small>'
            "Preço, disponibilidade, características e condições podem variar conforme o modelo e o anúncio do vendedor. "
            "Confira os detalhes na página do produto antes da compra.</small></p>",
            '<p style="margin:0;font-size:12px;line-height:1.5;"><small><strong>Transparência:</strong> '
            "este é um link de afiliado. Se você comprar por meio dele, podemos receber uma comissão, "
            "sem custo adicional para você.</small></p>",
            "</div>",
        ]
    )
