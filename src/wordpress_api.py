import os
import re
import unicodedata
from urllib.parse import urlparse

import requests


TIMEOUT = 45


def _normalizar(texto):
    texto = str(texto or "").lower().strip()
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(
        caractere
        for caractere in texto
        if unicodedata.category(caractere) != "Mn"
    )
    texto = re.sub(r"[^a-z0-9\s]+", " ", texto)
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()


def _configuracao():
    url = os.getenv("WORDPRESS_URL", "").strip().rstrip("/")
    usuario = os.getenv("WORDPRESS_USERNAME", "").strip()
    senha_app = os.getenv("WORDPRESS_APP_PASSWORD", "").strip()

    ausentes = []
    if not url:
        ausentes.append("WORDPRESS_URL")
    if not usuario:
        ausentes.append("WORDPRESS_USERNAME")
    if not senha_app:
        ausentes.append("WORDPRESS_APP_PASSWORD")

    if ausentes:
        raise RuntimeError(
            "Configuração WordPress ausente: "
            + ", ".join(ausentes)
        )

    return url, usuario, senha_app


def _endpoint(caminho):
    url, _, _ = _configuracao()
    return f"{url}/wp-json{caminho}"


def _request(method, caminho, **kwargs):
    _, usuario, senha_app = _configuracao()

    headers = dict(kwargs.pop("headers", {}) or {})
    headers.setdefault(
        "User-Agent",
        "RadarTechBR-Automation/1.0",
    )

    resposta = requests.request(
        method=method,
        url=_endpoint(caminho),
        auth=(usuario, senha_app),
        headers=headers,
        timeout=TIMEOUT,
        **kwargs,
    )

    if resposta.status_code >= 400:
        detalhe = resposta.text[:700]
        if senha_app:
            detalhe = detalhe.replace(senha_app, "***")
        raise RuntimeError(
            f"WordPress REST retornou HTTP {resposta.status_code} "
            f"em {caminho}: {detalhe}"
        )

    if not resposta.content:
        return {}

    try:
        return resposta.json()
    except ValueError as erro:
        raise RuntimeError(
            "WordPress REST retornou resposta não JSON."
        ) from erro


def verificar_conexao():
    dados = _request(
        "GET",
        "/wp/v2/users/me?context=edit",
    )

    return {
        "id": dados.get("id"),
        "nome": dados.get("name"),
        "slug": dados.get("slug"),
    }


def listar_posts(status):
    status = str(status or "").strip().lower()
    if status not in {"publish", "draft"}:
        raise ValueError("Status WordPress suportado: publish ou draft.")

    dados = _request(
        "GET",
        f"/wp/v2/posts?status={status}&per_page=100&orderby=date&order=desc",
    )

    if not isinstance(dados, list):
        return []

    posts = []

    for item in dados:
        if not isinstance(item, dict):
            continue

        titulo_bruto = item.get("title") or {}
        if isinstance(titulo_bruto, dict):
            titulo = str(titulo_bruto.get("rendered") or "").strip()
        else:
            titulo = str(titulo_bruto or "").strip()

        posts.append(
            {
                "post_id": item.get("id"),
                "titulo": titulo,
                "url": item.get("link"),
                "status": item.get("status") or status,
                "categorias_ids": item.get("categories") or [],
            }
        )

    return posts


def mapear_categoria_slug(categoria="", titulo="", produto=""):
    texto = _normalizar(
        f"{categoria} {titulo} {produto}"
    )

    regras = [
        (
            "tecnologia",
            (
                "camera", "headset", "fone", "bluetooth", "radio",
                "scanner", "rgb", "led", "celular", "computador",
                "gamer", "audio", "caixa de som", "wi fi", "wifi",
            ),
        ),
        (
            "moda-beleza",
            (
                "cabelo", "barbeador", "barbear", "shaver", "chapinha",
                "prancha", "beleza", "maquina de cortar cabelo",
                "acabamento profissional", "cuidados pessoais",
            ),
        ),
        (
            "cozinha-utilidades",
            (
                "cozinha", "air fryer", "mixer", "batedor", "gelo",
                "cafe", "leite", "tabua", "fatiador", "legumes",
                "petisqueira", "carnes", "potes", "loucas",
            ),
        ),
        (
            "ferramentas-automotivo",
            (
                "automotivo", "carro", "obd", "hoverboard", "skate",
                "lanterna tatica", "ferramenta", "garagem", "motor",
            ),
        ),
        (
            "casa-decoracao",
            (
                "casa", "decoracao", "quarto", "cama", "colcha",
                "lencol", "fronha", "colchao", "toalha", "varal",
                "mop", "climatizador", "ar condicionado", "ferro de passar",
                "limpeza", "mesa", "cobertor", "manta",
            ),
        ),
    ]

    for slug, termos in regras:
        if any(termo in texto for termo in termos):
            return slug

    return "guias-de-compra"


def obter_categoria_id(slug):
    dados = _request(
        "GET",
        f"/wp/v2/categories?slug={slug}&per_page=1",
    )

    if isinstance(dados, list) and dados:
        return int(dados[0]["id"])

    if slug != "guias-de-compra":
        return obter_categoria_id("guias-de-compra")

    raise RuntimeError(
        "Categoria padrão 'guias-de-compra' não encontrada no WordPress."
    )


def _nome_arquivo_imagem(url, nome_sugerido=""):
    nome = str(nome_sugerido or "").strip()

    if nome:
        nome = re.sub(r"[^a-zA-Z0-9._-]+", "-", nome)
        nome = nome.strip("-.")

    if not nome:
        caminho = urlparse(url).path
        nome = caminho.rsplit("/", 1)[-1] or "radar-tech-br.jpg"

    if "." not in nome:
        nome += ".jpg"

    return nome[:180]


def enviar_imagem_destacada(url, alt_text="", nome_arquivo=""):
    url = str(url or "").strip()
    if not url.startswith(("http://", "https://")):
        return 0

    resposta = requests.get(
        url,
        timeout=TIMEOUT,
        headers={"User-Agent": "RadarTechBR-Automation/1.0"},
    )
    resposta.raise_for_status()

    content_type = resposta.headers.get(
        "Content-Type",
        "image/jpeg",
    ).split(";", 1)[0].strip()

    if not content_type.startswith("image/"):
        raise RuntimeError(
            "A URL de imagem não retornou um arquivo de imagem válido."
        )

    nome = _nome_arquivo_imagem(
        url,
        nome_arquivo,
    )

    media = _request(
        "POST",
        "/wp/v2/media",
        data=resposta.content,
        headers={
            "Content-Type": content_type,
            "Content-Disposition": f'attachment; filename="{nome}"',
        },
    )

    media_id = int(media.get("id") or 0)

    if media_id and alt_text:
        _request(
            "POST",
            f"/wp/v2/media/{media_id}",
            json={"alt_text": str(alt_text)},
        )

    return media_id


def _remover_hero_imagem_destacada(conteudo_html, url_imagem):
    """
    No motor legado a imagem destacada também é prependida ao HTML.
    No WordPress ela já será enviada como featured_media, então removemos
    somente o primeiro bloco de imagem quando ele usa exatamente a mesma URL.
    """
    conteudo = str(conteudo_html or "")
    url = str(url_imagem or "").strip()

    if not conteudo or not url:
        return conteudo

    primeiro_bloco = re.match(
        r'^\s*(<div\b[^>]*>\s*<img\b[^>]*>\s*</div>)\s*',
        conteudo,
        flags=re.IGNORECASE | re.DOTALL,
    )

    if not primeiro_bloco:
        return conteudo

    bloco = primeiro_bloco.group(1)
    if url not in bloco:
        return conteudo

    print(
        "Hero duplicado removido do HTML: "
        "a imagem permanecerá apenas como imagem destacada do WordPress."
    )
    return conteudo[primeiro_bloco.end():].lstrip()


def criar_post_rascunho(pacote):
    seo = pacote.get("seo") or {}
    pauta = pacote.get("pauta") or {}
    artigo = pacote.get("artigo") or {}
    imagem = pacote.get("imagem") or {}

    titulo = str(seo.get("titulo") or pauta.get("titulo") or "").strip()
    conteudo = str(artigo.get("conteudo_html") or "").strip()

    if not titulo or not conteudo:
        raise RuntimeError(
            "Pacote editorial sem título ou conteúdo para o WordPress."
        )

    produto_principal = artigo.get("produto_principal") or {}
    nome_produto = str(produto_principal.get("nome") or "")

    slug_categoria = mapear_categoria_slug(
        categoria=pauta.get("categoria", ""),
        titulo=titulo,
        produto=nome_produto,
    )

    categoria_id = obter_categoria_id(slug_categoria)

    media_id = 0
    url_imagem = str(imagem.get("url_publica") or "").strip()

    conteudo = _remover_hero_imagem_destacada(
        conteudo_html=conteudo,
        url_imagem=url_imagem,
    )

    if url_imagem:
        try:
            media_id = enviar_imagem_destacada(
                url=url_imagem,
                alt_text=imagem.get("alt_text", ""),
                nome_arquivo=imagem.get("nome_arquivo", ""),
            )
        except Exception as erro:
            print(
                "Aviso: não foi possível enviar a imagem destacada "
                f"ao WordPress: {erro}"
            )
            media_id = 0

    payload = {
        "title": titulo,
        "content": conteudo,
        "status": "draft",
        "slug": str(seo.get("slug") or "").strip(),
        "excerpt": str(seo.get("meta_description") or "").strip(),
        "categories": [categoria_id],
    }

    if media_id:
        payload["featured_media"] = media_id

    post = _request(
        "POST",
        "/wp/v2/posts",
        json=payload,
    )

    return {
        "id": post.get("id"),
        "status": post.get("status"),
        "titulo": post.get("title", {}).get("rendered", titulo)
        if isinstance(post.get("title"), dict)
        else titulo,
        "url": post.get("link"),
        "categoria_slug": slug_categoria,
        "categoria_id": categoria_id,
        "featured_media": media_id,
    }
