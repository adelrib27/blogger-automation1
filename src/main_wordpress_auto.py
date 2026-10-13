import json
import os
from pathlib import Path

import requests

import main_wordpress
import sincronizar_wordpress


BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config" / "wordpress.json"
TIMEOUT = 45


def carregar_config():
    try:
        with CONFIG_PATH.open("r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
    except (OSError, json.JSONDecodeError):
        return {}

    return dados if isinstance(dados, dict) else {}


def publicar_post(post_id):
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
            "Configuração WordPress ausente: " + ", ".join(ausentes)
        )

    resposta = requests.post(
        f"{url}/wp-json/wp/v2/posts/{int(post_id)}",
        auth=(usuario, senha_app),
        headers={"User-Agent": "RadarTechBR-Automation/1.0"},
        json={"status": "publish"},
        timeout=TIMEOUT,
    )

    if resposta.status_code >= 400:
        detalhe = resposta.text[:700]
        if senha_app:
            detalhe = detalhe.replace(senha_app, "***")
        raise RuntimeError(
            f"Falha ao publicar post {post_id}: HTTP {resposta.status_code}: {detalhe}"
        )

    dados = resposta.json()
    return {
        "id": dados.get("id"),
        "status": dados.get("status"),
        "url": dados.get("link"),
        "titulo": (
            dados.get("title", {}).get("rendered", "")
            if isinstance(dados.get("title"), dict)
            else ""
        ),
    }


def executar():
    config = carregar_config()
    publicacao_automatica = bool(config.get("publicacao_automatica", False))

    if not publicacao_automatica:
        print("Publicação automática WordPress: DESATIVADA")
        return main_wordpress.executar()

    if os.getenv("RADARTECH_TEST_PRODUCT_KEYWORD", "").strip():
        raise RuntimeError(
            "O fluxo automático não publica execuções direcionadas de teste. "
            "Use main_wordpress_teste_seguro.py para manter o teste como rascunho."
        )

    print("=== RADAR TECH BR — PUBLICAÇÃO AUTOMÁTICA SEGURA ===")
    print("Publicação automática WordPress: ATIVA")
    print("A segunda trava editorial continua obrigatória antes da publicação.")

    resultado = main_wordpress.executar()

    if not isinstance(resultado, dict):
        raise RuntimeError(
            "O fluxo WordPress não retornou um resultado publicável."
        )

    wordpress = resultado.get("wordpress") or {}
    post_id = wordpress.get("id")

    if not post_id:
        raise RuntimeError(
            "O fluxo WordPress não retornou ID do rascunho aprovado."
        )

    if wordpress.get("status") == "publish":
        publicado = wordpress
    else:
        publicado = publicar_post(post_id)

    if publicado.get("status") != "publish":
        raise RuntimeError(
            f"O post {post_id} não confirmou status publish após o envio."
        )

    print("\n=== POST PUBLICADO AUTOMATICAMENTE ===")
    print("Post ID:", publicado.get("id"))
    print("Título:", publicado.get("titulo") or wordpress.get("titulo"))
    print("Status:", publicado.get("status"))
    print("URL:", publicado.get("url"))

    # Reconcilia histórico/rascunhos após a mudança de status para publish.
    sincronizar_wordpress.executar()

    resultado["wordpress"] = {
        **wordpress,
        **publicado,
    }
    return resultado


if __name__ == "__main__":
    executar()
