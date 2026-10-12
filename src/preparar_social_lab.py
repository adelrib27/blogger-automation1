import html
import json
import os
import re
from pathlib import Path

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

ESCOPO_BLOGGER = "https://www.googleapis.com/auth/blogger"

BASE_DIR = Path(__file__).resolve().parent.parent
SAIDA_DIR = BASE_DIR / "artifacts"
SAIDA_PATH = SAIDA_DIR / "social_payload.json"
ESTADO_PATH = BASE_DIR / "data" / "social_publicados.json"

TITULOS_INSTITUCIONAIS = {
    "política de privacidade",
    "politica de privacidade",
    "termos de uso",
    "sobre",
    "sobre nós",
    "sobre nos",
    "contato",
}


def criar_servico_blogger():
    variaveis = (
        "BLOGGER_REFRESH_TOKEN",
        "BLOGGER_CLIENT_ID",
        "BLOGGER_CLIENT_SECRET",
        "BLOGGER_BLOG_ID",
    )

    ausentes = [nome for nome in variaveis if not os.getenv(nome)]
    if ausentes:
        raise RuntimeError("Variáveis ausentes: " + ", ".join(ausentes))

    credenciais = Credentials(
        token=None,
        refresh_token=os.environ["BLOGGER_REFRESH_TOKEN"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["BLOGGER_CLIENT_ID"],
        client_secret=os.environ["BLOGGER_CLIENT_SECRET"],
        scopes=[ESCOPO_BLOGGER],
    )

    return build(
        "blogger",
        "v3",
        credentials=credenciais,
        cache_discovery=False,
    )


def carregar_estado():
    if not ESTADO_PATH.exists():
        return []

    try:
        dados = json.loads(ESTADO_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []

    return dados if isinstance(dados, list) else []


def limpar_html(conteudo):
    conteudo = re.sub(r"<script\b[^>]*>.*?</script>", " ", conteudo, flags=re.I | re.S)
    conteudo = re.sub(r"<style\b[^>]*>.*?</style>", " ", conteudo, flags=re.I | re.S)
    conteudo = re.sub(r"<[^>]+>", " ", conteudo)
    conteudo = html.unescape(conteudo)
    return re.sub(r"\s+", " ", conteudo).strip()


def primeira_imagem(conteudo):
    padrao = re.compile(
        r"<img\b[^>]*?\bsrc=[\"']([^\"']+)[\"']",
        flags=re.I,
    )
    match = padrao.search(conteudo or "")
    return match.group(1).strip() if match else ""


def limitar_texto(texto, limite):
    texto = re.sub(r"[ \t]+", " ", str(texto or "")).strip()
    if len(texto) <= limite:
        return texto

    if limite <= 1:
        return texto[:limite]

    trecho = texto[: limite - 1]
    if " " in trecho:
        trecho = trecho.rsplit(" ", 1)[0]
    return trecho.rstrip(".,;:!?") + "…"


def resumo_do_post(conteudo, limite=220):
    texto = limpar_html(conteudo or "")
    return limitar_texto(texto, limite)


def hashtags_padrao(labels):
    tags = ["#AchadosParaCasa", "#CasaEDecoracao"]

    for label in labels or []:
        normalizada = re.sub(r"[^A-Za-zÀ-ÿ0-9]+", "", str(label))
        if normalizada:
            tag = "#" + normalizada
            if tag.lower() not in {item.lower() for item in tags}:
                tags.append(tag)
        if len(tags) >= 4:
            break

    return tags


def montar_payload(post):
    titulo = str(post.get("title") or "").strip()
    url = str(post.get("url") or "").strip()
    conteudo = str(post.get("content") or "")
    labels = post.get("labels") or []
    imagem = primeira_imagem(conteudo)
    resumo = resumo_do_post(conteudo)
    hashtags = hashtags_padrao(labels)
    tags_texto = " ".join(hashtags)

    facebook = (
        f"{titulo}\n\n"
        f"{resumo}\n\n"
        f"Leia no Achados para Casa: {url}\n\n"
        f"{tags_texto}"
    ).strip()

    pinterest_descricao = (
        f"{resumo} Veja o conteúdo completo no Achados para Casa. "
        f"{tags_texto}"
    ).strip()

    instagram = (
        f"{titulo}\n\n"
        f"{resumo}\n\n"
        f"Novo conteúdo no Achados para Casa.\n"
        f"{url}\n\n"
        f"{tags_texto}"
    ).strip()

    threads = limitar_texto(
        f"{titulo}\n\n{resumo}\n\n{url}",
        480,
    )

    linkedin = limitar_texto(
        f"{titulo}\n\n{resumo}\n\nLeia o conteúdo completo: {url}\n\n{tags_texto}",
        2500,
    )

    x_texto = limitar_texto(
        f"{titulo}\n\n{url}\n#AchadosParaCasa",
        280,
    )

    telegram = limitar_texto(
        f"🏠 {titulo}\n\n{resumo}\n\nLeia no Achados para Casa:\n{url}\n\n{tags_texto}",
        950,
    )

    bluesky = limitar_texto(
        f"{titulo}\n\n{url}\n#AchadosParaCasa",
        300,
    )

    return {
        "post": {
            "id": str(post.get("id") or ""),
            "title": titulo,
            "url": url,
            "published": post.get("published"),
            "updated": post.get("updated"),
            "labels": labels,
            "featured_image_url": imagem,
            "summary": resumo,
        },
        "facebook": {
            "enabled": False,
            "text": facebook,
            "link": url,
            "image_url": imagem,
        },
        "pinterest": {
            "enabled": False,
            "title": titulo[:100],
            "description": pinterest_descricao[:450],
            "link": url,
            "image_url": imagem,
            "board_id": None,
        },
        "instagram": {
            "enabled": False,
            "caption": instagram[:2000],
            "image_url": imagem,
        },
        "threads": {
            "enabled": False,
            "text": threads,
            "link": url,
            "image_url": imagem,
            "preferred_media_type": "TEXT",
        },
        "linkedin": {
            "enabled": False,
            "commentary": linkedin,
            "article": {
                "source": url,
                "title": titulo,
                "description": resumo,
                "thumbnail_url": imagem,
            },
        },
        "x": {
            "enabled": False,
            "text": x_texto,
            "link": url,
            "image_url": imagem,
        },
        "telegram": {
            "enabled": False,
            "caption": telegram,
            "link": url,
            "image_url": imagem,
            "target_chat": None,
        },
        "bluesky": {
            "enabled": False,
            "text": bluesky,
            "link": url,
            "image_url": imagem,
            "external_embed": {
                "uri": url,
                "title": titulo,
                "description": resumo,
                "thumb_url": imagem,
            },
        },
        "media_phase_2": {
            "tiktok": {
                "enabled": False,
                "requires_media": True,
                "status": "planejado",
            },
            "youtube_shorts": {
                "enabled": False,
                "requires_media": True,
                "status": "planejado",
            },
        },
        "safety": {
            "publish_external": False,
            "mode": "lab_only",
            "prepared_networks": [
                "facebook",
                "pinterest",
                "instagram",
                "threads",
                "linkedin",
                "x",
                "telegram",
                "bluesky",
            ],
            "note": "Este arquivo apenas prepara conteúdo. Nenhuma rede social é chamada.",
        },
    }


def escolher_post_novo(posts, estado):
    processados = {
        str(item.get("post_id") or item.get("id") or "").strip()
        for item in estado
        if isinstance(item, dict)
    }

    candidatos = []
    for post in posts:
        titulo = str(post.get("title") or "").strip()
        if not titulo:
            continue
        if titulo.lower() in TITULOS_INSTITUCIONAIS:
            continue
        if str(post.get("id") or "").strip() in processados:
            continue
        candidatos.append(post)

    candidatos.sort(
        key=lambda item: str(item.get("published") or ""),
        reverse=True,
    )

    return candidatos[0] if candidatos else None


def main():
    print("=== SOCIAL LAB — PREPARAÇÃO SEGURA ===")
    print("Nenhuma publicação externa será feita.\n")

    blogger = criar_servico_blogger()
    blog_id = os.environ["BLOGGER_BLOG_ID"]

    resposta = (
        blogger.posts()
        .list(
            blogId=blog_id,
            status=["LIVE"],
            fetchBodies=True,
            maxResults=50,
        )
        .execute()
    )

    posts = resposta.get("items", [])
    estado = carregar_estado()
    post = escolher_post_novo(posts, estado)

    SAIDA_DIR.mkdir(parents=True, exist_ok=True)

    if not post:
        resultado = {
            "status": "sem_post_novo",
            "safety": {
                "publish_external": False,
                "mode": "lab_only",
            },
        }
        SAIDA_PATH.write_text(
            json.dumps(resultado, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print("Nenhum post novo elegível encontrado.")
        return

    payload = montar_payload(post)
    SAIDA_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print("Post preparado:", payload["post"]["title"])
    print("URL:", payload["post"]["url"])
    print("Imagem:", payload["post"]["featured_image_url"] or "não encontrada")
    print("Redes preparadas:", ", ".join(payload["safety"]["prepared_networks"]))
    print("Saída:", SAIDA_PATH)
    print("\nSOCIAL LAB: OK — nenhuma rede social chamada.")


if __name__ == "__main__":
    main()
