import html
import io
import json
import os
import re
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

import requests
import cloudinary
import cloudinary.uploader
from PIL import Image

BASE_DIR = Path(__file__).resolve().parent.parent
CACHE_PATH = BASE_DIR / "data" / "imagens_produtos_cache.json"

TIMEOUT = 25
LIMIAR_APROVACAO = 0.58
MAX_IMAGEM_BYTES = 15 * 1024 * 1024
PASTA_CLOUDINARY = "blogger-automation/produtos-reais"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
}


def _normalizar(texto):
    texto = html.unescape(str(texto or "")).lower()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(
        c for c in texto
        if not unicodedata.combining(c)
    )
    texto = re.sub(r"[^a-z0-9]+", " ", texto)
    return re.sub(r"\s+", " ", texto).strip()


def _tokens(texto):
    ignorar = {
        "de", "da", "do", "das", "dos", "com",
        "para", "e", "em", "um", "uma", "o",
        "a", "as", "os", "por",
    }
    return {
        t for t in _normalizar(texto).split()
        if len(t) >= 3 and t not in ignorar
    }


def _pontuar(nome, titulo):
    a = _normalizar(nome)
    b = _normalizar(titulo)

    if not a or not b:
        return 0.0

    seq = SequenceMatcher(None, a, b).ratio()
    ta = _tokens(a)
    tb = _tokens(b)
    cobertura = len(ta & tb) / max(1, len(ta))

    return round(
        (0.35 * seq) + (0.65 * cobertura),
        4,
    )


def _product_id(url):
    for padrao in (
        r"/pdp/[^/?#]*-(\d{10,})",
        r"/product/[^/?#]*-(\d{10,})",
        r"/(\d{10,})(?:[/?#]|$)",
    ):
        encontrado = re.search(
            padrao,
            url or "",
        )
        if encontrado:
            return encontrado.group(1)

    return ""


def _og_info(url):
    try:
        valores = parse_qs(
            urlparse(url).query
        ).get(
            "og_info",
            [],
        )
    except Exception:
        return {}

    for valor in valores:
        for candidato in (
            valor,
            unquote(valor),
        ):
            try:
                dado = json.loads(
                    candidato
                )
                if isinstance(
                    dado,
                    dict,
                ):
                    return dado
            except Exception:
                pass

    return {}


def _meta(texto, propriedade):
    padroes = (
        rf'<meta[^>]+property=["\']{re.escape(propriedade)}'
        rf'["\'][^>]+content=["\']([^"\']+)["\']',
        rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]+'
        rf'property=["\']{re.escape(propriedade)}["\']',
    )

    for padrao in padroes:
        encontrado = re.search(
            padrao,
            texto or "",
            re.I,
        )
        if encontrado:
            return html.unescape(
                encontrado.group(1)
            ).strip()

    return ""


def _carregar_cache():
    if not CACHE_PATH.exists():
        return {}

    try:
        dado = json.loads(
            CACHE_PATH.read_text(
                encoding="utf-8",
            )
        )
        return (
            dado
            if isinstance(dado, dict)
            else {}
        )
    except Exception:
        return {}


def _salvar_cache(cache):
    CACHE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    CACHE_PATH.write_text(
        json.dumps(
            cache,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def _descobrir(link):
    sessao = requests.Session()
    sessao.headers.update(
        HEADERS
    )

    resposta = sessao.get(
        link,
        allow_redirects=True,
        timeout=TIMEOUT,
    )
    resposta.raise_for_status()

    urls = [
        item.url
        for item in resposta.history
    ] + [
        resposta.url
    ]

    info = {}
    for url in reversed(urls):
        info = _og_info(url)
        if info:
            break

    titulo = str(
        info.get("title")
        or info.get("og_title")
        or ""
    ).strip()

    imagem = str(
        info.get("image")
        or info.get("image_url")
        or info.get("og_image")
        or ""
    ).strip()

    if not titulo:
        titulo = _meta(
            resposta.text,
            "og:title",
        )

    if not imagem:
        imagem = _meta(
            resposta.text,
            "og:image",
        )

    pid = ""
    for url in reversed(urls):
        pid = _product_id(url)
        if pid:
            break

    return {
        "product_id": pid,
        "titulo": titulo,
        "imagem_origem": (
            imagem
            if imagem.startswith(
                ("http://", "https://")
            )
            else ""
        ),
    }


def _baixar_imagem(url):
    resposta = requests.get(
        url,
        headers=HEADERS,
        timeout=TIMEOUT,
        stream=True,
    )
    resposta.raise_for_status()

    tipo = (
        resposta.headers.get(
            "Content-Type"
        )
        or ""
    ).lower()

    if (
        tipo
        and not tipo.startswith(
            "image/"
        )
    ):
        raise ValueError(
            "URL encontrada não retornou imagem."
        )

    conteudo = bytearray()

    for bloco in resposta.iter_content(
        64 * 1024
    ):
        if not bloco:
            continue

        conteudo.extend(
            bloco
        )

        if (
            len(conteudo)
            > MAX_IMAGEM_BYTES
        ):
            raise ValueError(
                "Imagem acima do limite permitido."
            )

    if not conteudo:
        raise ValueError(
            "Imagem vazia."
        )

    imagem = Image.open(
        io.BytesIO(conteudo)
    )
    imagem.verify()

    imagem = Image.open(
        io.BytesIO(conteudo)
    )
    largura, altura = imagem.size

    if (
        largura < 200
        or altura < 200
    ):
        raise ValueError(
            "Imagem pequena demais."
        )

    return bytes(conteudo)


def _enviar_cloudinary(
    conteudo,
    product_id,
):
    if not os.environ.get(
        "CLOUDINARY_URL"
    ):
        raise RuntimeError(
            "CLOUDINARY_URL indisponível."
        )

    cloudinary.config(
        secure=True
    )

    resultado = (
        cloudinary.uploader.upload(
            io.BytesIO(conteudo),
            public_id=(
                f"{PASTA_CLOUDINARY}/"
                f"{product_id}"
            ),
            overwrite=True,
            resource_type="image",
            unique_filename=False,
            use_filename=False,
            invalidate=False,
        )
    )

    url = str(
        resultado.get(
            "secure_url",
            "",
        )
    ).strip()

    if not url:
        raise RuntimeError(
            "Cloudinary não retornou URL."
        )

    return url


def enriquecer_produto_com_imagem(
    produto,
):
    """
    Tenta adicionar uma imagem REAL e verificada ao produto.

    Segurança:
    - nunca substitui nome/link afiliado;
    - nunca usa imagem gerada por IA;
    - exige correspondência mínima entre catálogo e anúncio;
    - qualquer falha mantém o produto original sem foto.
    """

    if not isinstance(
        produto,
        dict,
    ):
        return produto

    resultado = dict(
        produto
    )

    nome = str(
        resultado.get(
            "nome",
            "",
        )
    ).strip()

    link = str(
        resultado.get(
            "link_afiliado",
            "",
        )
    ).strip()

    if not nome or not link:
        return resultado

    cache = _carregar_cache()

    try:
        dados = _descobrir(
            link
        )

        pid = dados[
            "product_id"
        ]
        titulo = dados[
            "titulo"
        ]

        score = _pontuar(
            nome,
            titulo,
        )

        if (
            not pid
            or not titulo
            or score
            < LIMIAR_APROVACAO
        ):
            print(
                "Imagem real não aprovada para:",
                nome,
            )
            return resultado

        cache_item = cache.get(
            pid,
            {},
        )

        url_cache = str(
            cache_item.get(
                "imagem_produto",
                "",
            )
        ).strip()

        if url_cache.startswith(
            "https://"
        ):
            resultado.update({
                "tiktok_product_id": pid,
                "titulo_tiktok": titulo,
                "imagem_produto": url_cache,
                "imagem_verificada": True,
                "correspondencia_imagem": score,
            })

            print(
                "Imagem real reutilizada do cache:",
                nome,
            )
            return resultado

        origem = dados[
            "imagem_origem"
        ]

        if not origem:
            return resultado

        conteudo = _baixar_imagem(
            origem
        )

        url_cloudinary = (
            _enviar_cloudinary(
                conteudo,
                pid,
            )
        )

        cache[pid] = {
            "nome_catalogo": nome,
            "titulo_tiktok": titulo,
            "imagem_produto": url_cloudinary,
            "correspondencia": score,
        }

        _salvar_cache(
            cache
        )

        resultado.update({
            "tiktok_product_id": pid,
            "titulo_tiktok": titulo,
            "imagem_produto": url_cloudinary,
            "imagem_verificada": True,
            "correspondencia_imagem": score,
        })

        print(
            "Imagem real validada e salva:",
            nome,
        )

    except Exception as erro:
        print(
            "Imagem real indisponível; "
            "usando card sem foto:",
            nome,
            "-",
            erro,
        )

    return resultado
