import hashlib
import html
import io
import json
import math
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import cloudinary
import cloudinary.uploader
import requests
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config.json"
STATE_PATH = BASE_DIR / "data" / "state.json"

SHOPEE_ENDPOINT = os.getenv(
    "SHOPEE_AFFILIATE_ENDPOINT",
    "https://open-api.affiliate.shopee.com.br/graphql",
).strip()

BLOGGER_SCOPE = "https://www.googleapis.com/auth/blogger"
HTTP_TIMEOUT = 35
MAX_IMAGE_BYTES = 15 * 1024 * 1024


def load_json(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def save_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Variável obrigatória ausente: {name}")
    return value


def parse_float(value, default=0.0):
    if value is None:
        return default
    text = str(value).strip().replace(",", ".")
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    if not match:
        return default
    try:
        return float(match.group(0))
    except ValueError:
        return default


def parse_sales(value):
    if value is None:
        return 0
    text = str(value).strip().lower().replace(",", ".")
    multiplier = 1
    if text.endswith("k"):
        multiplier = 1000
        text = text[:-1]
    elif text.endswith("m"):
        multiplier = 1_000_000
        text = text[:-1]
    try:
        return int(float(text) * multiplier)
    except ValueError:
        digits = re.sub(r"[^\d]", "", text)
        return int(digits or 0)


def build_shopee_payload(keyword: str, limit: int) -> str:
    graphql_keyword = json.dumps(keyword, ensure_ascii=False)
    query = f"""
query ConectaAchadosShopee {{
  productOfferV2(keyword: {graphql_keyword}, sortType: 1, page: 1, limit: {limit}) {{
    nodes {{
      itemId
      productName
      commissionRate
      price
      imageUrl
      offerLink
      shopName
      sales
      ratingStar
    }}
    pageInfo {{
      page
      limit
      hasNextPage
    }}
  }}
}}
""".strip()
    return json.dumps(
        {"query": query, "operationName": "ConectaAchadosShopee"},
        ensure_ascii=False,
        separators=(",", ":"),
    )


def shopee_auth_header(app_id: str, secret: str, payload: str, timestamp: int):
    raw = f"{app_id}{timestamp}{payload}{secret}"
    signature = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return (
        f"SHA256 Credential={app_id}, "
        f"Timestamp={timestamp}, "
        f"Signature={signature}"
    )


def fetch_shopee_products(keyword: str, limit: int):
    app_id = required_env("SHOPEE_APP_ID")
    secret = required_env("SHOPEE_SECRET")
    payload = build_shopee_payload(keyword, limit)
    timestamp = int(time.time())

    response = requests.post(
        SHOPEE_ENDPOINT,
        data=payload.encode("utf-8"),
        headers={
            "Authorization": shopee_auth_header(
                app_id, secret, payload, timestamp
            ),
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "ConectaAchados-ShopeeAutomation/1.0",
        },
        timeout=HTTP_TIMEOUT,
    )

    try:
        data = response.json()
    except ValueError as exc:
        raise RuntimeError(
            f"Shopee retornou resposta não-JSON (HTTP {response.status_code})."
        ) from exc

    if data.get("errors"):
        messages = "; ".join(
            str(error.get("message", "erro sem mensagem"))
            for error in data["errors"][:5]
        )
        raise RuntimeError(
            f"Shopee API retornou erro (HTTP {response.status_code}): {messages}"
        )

    if response.status_code >= 400:
        raise RuntimeError(
            f"Shopee API respondeu HTTP {response.status_code}."
        )

    offer = ((data.get("data") or {}).get("productOfferV2") or {})
    return offer.get("nodes") or []


def product_score(product):
    rating = parse_float(product.get("ratingStar"))
    sales = parse_sales(product.get("sales"))
    commission = parse_float(product.get("commissionRate"))
    return (
        rating * 20
        + min(math.log10(max(sales, 0) + 1) * 12, 48)
        + min(commission, 20)
    )


def choose_product(config, state):
    groups = config.get("query_groups") or []
    queries = []
    for group in groups:
        label = str(group.get("label", "")).strip()
        for keyword in group.get("keywords") or []:
            keyword = str(keyword).strip()
            if keyword and label:
                queries.append({"label": label, "keyword": keyword})

    if not queries:
        raise RuntimeError("Nenhuma consulta Shopee foi configurada.")

    used = {str(item) for item in state.get("used_item_ids", [])}
    cursor = int(state.get("keyword_cursor", 0)) % len(queries)
    min_rating = float(config.get("min_rating", 4.0))
    limit = max(5, min(int(config.get("shopee_limit", 20)), 50))

    for offset in range(len(queries)):
        query_index = (cursor + offset) % len(queries)
        query = queries[query_index]
        print(
            f"Consultando Shopee: {query['keyword']} "
            f"(categoria Blogger: {query['label']})"
        )
        products = fetch_shopee_products(query["keyword"], limit)

        candidates = []
        for product in products:
            item_id = str(product.get("itemId") or "").strip()
            name = str(product.get("productName") or "").strip()
            link = str(product.get("offerLink") or "").strip()
            rating = parse_float(product.get("ratingStar"))
            if not item_id or not name or not link:
                continue
            if item_id in used:
                continue
            if rating and rating < min_rating:
                continue
            candidates.append(product)

        if candidates:
            candidates.sort(key=product_score, reverse=True)
            state["keyword_cursor"] = (query_index + 1) % len(queries)
            return candidates[0], query

    raise RuntimeError(
        "Nenhum produto novo elegível foi encontrado nas consultas configuradas."
    )


def extract_response_text(data):
    texts = []
    for item in data.get("output") or []:
        if item.get("type") != "message":
            continue
        for content in item.get("content") or []:
            if content.get("type") == "output_text":
                text = str(content.get("text") or "").strip()
                if text:
                    texts.append(text)
    return "\n".join(texts).strip()


def parse_json_object(text):
    text = str(text or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.I)
        text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.S)
        if not match:
            raise
        return json.loads(match.group(0))


def generate_chatgpt_copy(product, query, config):
    api_key = required_env("OPENAI_API_KEY")
    model = os.getenv(
        "OPENAI_MODEL",
        str(config.get("openai_model", "chat-latest")),
    ).strip() or "chat-latest"

    source = {
        "nome_original": str(product.get("productName") or "").strip(),
        "loja": str(product.get("shopName") or "").strip(),
        "avaliacao": product.get("ratingStar"),
        "vendas": product.get("sales"),
        "preco_api": product.get("price"),
        "categoria": query["label"],
        "palavra_busca": query["keyword"],
    }

    instructions = (
        "Você escreve para a loja editorial brasileira Conecta Achados. "
        "Use SOMENTE os fatos fornecidos no JSON do produto. "
        "Crie um título SEO natural em português do Brasil, idealmente entre "
        "48 e 72 caracteres. Não copie o título do vendedor literalmente: "
        "reorganize e limpe termos repetidos, mas preserve a identidade real "
        "do produto, marca, modelo, capacidade, potência, conexão ou compatibilidade "
        "somente quando esses dados estiverem explicitamente no nome original. "
        "Não invente especificações, benefícios técnicos, preço, desconto ou garantia. "
        "Crie também uma descrição curta de 2 frases, com no máximo 300 caracteres, "
        "explicando de forma útil o que o produto é e em que tipo de rotina ele pode "
        "ser considerado, sem afirmar recursos não confirmados. "
        "Retorne APENAS JSON válido com as chaves titulo e descricao."
    )

    response = requests.post(
        "https://api.openai.com/v1/responses",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "instructions": instructions,
            "input": json.dumps(source, ensure_ascii=False),
            "max_output_tokens": 500,
            "store": False,
        },
        timeout=HTTP_TIMEOUT,
    )

    if response.status_code >= 400:
        body = response.text[:800]
        raise RuntimeError(
            f"OpenAI Responses API falhou (HTTP {response.status_code}): {body}"
        )

    data = response.json()
    text = extract_response_text(data)
    parsed = parse_json_object(text)

    title = re.sub(r"\s+", " ", str(parsed.get("titulo") or "")).strip()
    description = re.sub(
        r"\s+", " ", str(parsed.get("descricao") or "")
    ).strip()

    if len(title) < 20 or len(title) > 100:
        raise RuntimeError(
            f"Título gerado pelo ChatGPT fora do limite de segurança: {title!r}"
        )
    if len(description) < 40 or len(description) > 360:
        raise RuntimeError(
            "Descrição gerada pelo ChatGPT fora do limite de segurança."
        )

    return {
        "title": title,
        "description": description,
        "model": data.get("model") or model,
        "source": "chatgpt",
    }


def download_image(url: str) -> bytes:
    response = requests.get(
        url,
        timeout=HTTP_TIMEOUT,
        headers={
            "User-Agent": "Mozilla/5.0 ConectaAchados/1.0",
            "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
        },
        stream=True,
    )
    response.raise_for_status()

    content = bytearray()
    for chunk in response.iter_content(64 * 1024):
        if not chunk:
            continue
        content.extend(chunk)
        if len(content) > MAX_IMAGE_BYTES:
            raise RuntimeError("Imagem do produto acima de 15 MB.")

    if not content:
        raise RuntimeError("Imagem do produto vazia.")

    image = Image.open(io.BytesIO(content))
    image.verify()
    return bytes(content)


def improve_image_preserving_product(image_bytes: bytes) -> bytes:
    image = Image.open(io.BytesIO(image_bytes))
    image = ImageOps.exif_transpose(image)

    if image.mode not in ("RGB", "RGBA"):
        image = image.convert("RGBA")

    if image.mode == "RGBA":
        base = Image.new("RGBA", image.size, (255, 255, 255, 255))
        base.alpha_composite(image)
        image = base.convert("RGB")
    else:
        image = image.convert("RGB")

    image = ImageEnhance.Contrast(image).enhance(1.02)
    image = ImageEnhance.Sharpness(image).enhance(1.05)
    image = image.filter(
        ImageFilter.UnsharpMask(radius=0.8, percent=105, threshold=3)
    )

    target = (1200, 1200)
    inner = (1060, 1060)
    fitted = ImageOps.contain(image, inner, Image.Resampling.LANCZOS)

    canvas = Image.new("RGB", target, (248, 250, 252))
    x = (target[0] - fitted.width) // 2
    y = (target[1] - fitted.height) // 2
    canvas.paste(fitted, (x, y))

    out = io.BytesIO()
    canvas.save(out, format="JPEG", quality=94, optimize=True)
    return out.getvalue()


def upload_cloudinary(image_bytes: bytes, item_id: str):
    if not os.getenv("CLOUDINARY_URL", "").strip():
        raise RuntimeError("CLOUDINARY_URL indisponível.")

    cloudinary.config(secure=True)
    result = cloudinary.uploader.upload(
        io.BytesIO(image_bytes),
        public_id=f"conecta-achados/produtos/{item_id}",
        overwrite=True,
        resource_type="image",
        unique_filename=False,
        use_filename=False,
        invalidate=False,
    )
    url = str(result.get("secure_url") or "").strip()
    if not url:
        raise RuntimeError("Cloudinary não retornou URL segura.")
    return url


def prepare_product_image(product):
    original = str(product.get("imageUrl") or "").strip()
    item_id = str(product.get("itemId") or "").strip()

    if not original.startswith("http"):
        return {"url": "", "source": "none"}

    try:
        raw = download_image(original)
        improved = improve_image_preserving_product(raw)
        url = upload_cloudinary(improved, item_id)
        return {
            "url": url,
            "source": "enhanced_from_shopee_original",
            "original_url": original,
        }
    except Exception as exc:
        print(
            "Aviso: não foi possível criar a versão aprimorada da imagem; "
            f"usando a imagem original da Shopee. Motivo: {exc}"
        )
        return {
            "url": original,
            "source": "shopee_original",
            "original_url": original,
        }


def blogger_service():
    missing = [
        name
        for name in (
            "BLOGGER_CLIENT_ID",
            "BLOGGER_CLIENT_SECRET",
            "BLOGGER_REFRESH_TOKEN",
        )
        if not os.getenv(name, "").strip()
    ]
    if missing:
        raise RuntimeError(
            "Credenciais Blogger ausentes: " + ", ".join(missing)
        )

    credentials = Credentials(
        token=None,
        refresh_token=os.environ["BLOGGER_REFRESH_TOKEN"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["BLOGGER_CLIENT_ID"],
        client_secret=os.environ["BLOGGER_CLIENT_SECRET"],
        scopes=[BLOGGER_SCOPE],
    )
    return build(
        "blogger",
        "v3",
        credentials=credentials,
        cache_discovery=False,
    )


def product_html(product, copy, image_info, label):
    safe_title = html.escape(copy["title"])
    safe_description = html.escape(copy["description"])
    safe_link = html.escape(
        str(product.get("offerLink") or "").strip(), quote=True
    )
    safe_shop = html.escape(str(product.get("shopName") or "").strip())
    safe_image = html.escape(str(image_info.get("url") or "").strip(), quote=True)
    safe_label = html.escape(label)
    rating = parse_float(product.get("ratingStar"))
    sales = parse_sales(product.get("sales"))

    meta = []
    if safe_shop:
        meta.append(f"<strong>Loja:</strong> {safe_shop}")
    if rating:
        meta.append(f"<strong>Avaliação informada:</strong> {rating:.1f}/5")
    if sales:
        meta.append(f"<strong>Vendas informadas:</strong> {sales}")

    image_html = ""
    if safe_image:
        image_html = (
            '<div style="margin:0 auto 24px;max-width:720px;text-align:center;">'
            f'<img src="{safe_image}" alt="{safe_title}" loading="lazy" '
            'style="display:block;width:100%;height:auto;max-height:720px;'
            'object-fit:contain;border-radius:16px;background:#f8fafc;" />'
            "</div>"
        )

    meta_html = ""
    if meta:
        meta_html = (
            '<p style="font-size:14px;color:#4b5563;line-height:1.7;">'
            + " &nbsp;•&nbsp; ".join(meta)
            + "</p>"
        )

    return f"""
<div class="conecta-achados-produto" style="max-width:820px;margin:24px auto;padding:0 4px;">
  <p style="margin:0 0 12px;font-size:12px;font-weight:700;letter-spacing:.08em;color:#007d85;text-transform:uppercase;">{safe_label}</p>
  {image_html}
  <p style="font-size:17px;line-height:1.75;color:#263746;">{safe_description}</p>
  {meta_html}
  <div style="margin:28px 0;text-align:center;">
    <a href="{safe_link}" target="_blank" rel="nofollow sponsored"
       style="display:inline-block;padding:15px 24px;background:#007d85;color:#ffffff;text-decoration:none;font-weight:700;border-radius:10px;font-size:16px;">
       Ver detalhes na Shopee →
    </a>
  </div>
  <p style="font-size:12px;line-height:1.6;color:#6b7280;">
    <strong>Transparência:</strong> este post pode conter link de afiliado.
    Preço, estoque, frete, características e condições podem mudar.
    Confira as informações atuais diretamente no anúncio antes da compra.
  </p>
</div>
""".strip()


def create_blogger_post(title, content_html, label, mode):
    blog_id = os.getenv("BLOGGER_BLOG_ID", "").strip()
    if not blog_id:
        raise RuntimeError("BLOGGER_BLOG_ID ausente.")

    is_draft = mode.lower() != "publish"
    body = {
        "kind": "blogger#post",
        "title": title,
        "content": content_html,
        "labels": [label],
    }
    result = (
        blogger_service()
        .posts()
        .insert(
            blogId=blog_id,
            body=body,
            isDraft=is_draft,
        )
        .execute()
    )
    return {
        "id": result.get("id"),
        "title": result.get("title"),
        "url": result.get("url"),
        "status": result.get("status"),
        "labels": result.get("labels") or [],
    }


def main():
    config = load_json(CONFIG_PATH, {})
    state = load_json(
        STATE_PATH,
        {"keyword_cursor": 0, "used_item_ids": [], "history": []},
    )

    expected_blog_id = str(config.get("blog_id") or "").strip()
    runtime_blog_id = os.getenv("BLOGGER_BLOG_ID", expected_blog_id).strip()
    if not expected_blog_id or runtime_blog_id != expected_blog_id:
        raise RuntimeError(
            "BLOGGER_BLOG_ID não corresponde ao Conecta Achados configurado."
        )
    os.environ["BLOGGER_BLOG_ID"] = expected_blog_id

    mode = os.getenv(
        "CONECTA_PUBLISH_MODE",
        str(config.get("publish_mode", "draft")),
    ).strip().lower()
    if mode not in {"draft", "publish"}:
        raise RuntimeError("CONECTA_PUBLISH_MODE deve ser draft ou publish.")

    product, query = choose_product(config, state)
    print(
        "Produto escolhido:",
        product.get("productName"),
        "| itemId:",
        product.get("itemId"),
    )

    copy = generate_chatgpt_copy(product, query, config)
    image_info = prepare_product_image(product)
    content = product_html(
        product,
        copy,
        image_info,
        query["label"],
    )

    result = create_blogger_post(
        copy["title"],
        content,
        query["label"],
        mode,
    )

    item_id = str(product.get("itemId") or "").strip()
    used = [str(item) for item in state.get("used_item_ids", [])]
    if item_id not in used:
        used.append(item_id)
    state["used_item_ids"] = used[-500:]

    history = list(state.get("history", []))
    history.append(
        {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "item_id": item_id,
            "source_product_name": product.get("productName"),
            "seo_title": copy["title"],
            "category": query["label"],
            "keyword": query["keyword"],
            "blogger_post_id": result.get("id"),
            "blogger_status": result.get("status"),
            "blogger_url": result.get("url"),
            "chatgpt_model": copy.get("model"),
            "image_source": image_info.get("source"),
            "mode": mode,
        }
    )
    state["history"] = history[-1000:]
    save_json(STATE_PATH, state)

    print("VALIDAÇÃO CONECTA ACHADOS: PASSOU")
    print("Modo:", mode)
    print("Título SEO:", copy["title"])
    print("Categoria:", query["label"])
    print("Imagem:", image_info.get("source"))
    print("Blogger post ID:", result.get("id"))
    print("Status Blogger:", result.get("status"))


if __name__ == "__main__":
    main()
