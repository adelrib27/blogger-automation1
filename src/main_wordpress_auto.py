import json
import os
import re
from pathlib import Path

import requests

import main_wordpress
import sincronizar_wordpress


BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config" / "wordpress.json"
TIMEOUT = 45
SHOPEE_AFFILIATE_URL = "https://s.shopee.com.br/40hIZe6zgm"


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


def garantir_ancora_oferta(post_id):
    """Garante que o CTA do template consiga saltar até o bloco afiliado."""
    url = os.getenv("WORDPRESS_URL", "").strip().rstrip("/")
    usuario = os.getenv("WORDPRESS_USERNAME", "").strip()
    senha_app = os.getenv("WORDPRESS_APP_PASSWORD", "").strip()

    if not url or not usuario or not senha_app:
        return False

    resposta = requests.get(
        f"{url}/wp-json/wp/v2/posts/{int(post_id)}",
        params={"context": "edit", "_fields": "content"},
        auth=(usuario, senha_app),
        headers={"User-Agent": "RadarTechBR-Automation/1.0"},
        timeout=TIMEOUT,
    )

    if resposta.status_code >= 400:
        detalhe = resposta.text[:700]
        if senha_app:
            detalhe = detalhe.replace(senha_app, "***")
        raise RuntimeError(
            f"Falha ao preparar CTA do post {post_id}: "
            f"HTTP {resposta.status_code}: {detalhe}"
        )

    dados = resposta.json()
    conteudo = dados.get("content", {})
    if isinstance(conteudo, dict):
        html = str(conteudo.get("raw") or "")
    else:
        html = str(conteudo or "")

    marcador = '<div class="produto-principal-contextual"'
    marcador_com_id = '<div id="oferta" class="produto-principal-contextual"'

    if marcador_com_id in html or marcador not in html:
        return False

    atualizado = html.replace(marcador, marcador_com_id, 1)

    resposta = requests.post(
        f"{url}/wp-json/wp/v2/posts/{int(post_id)}",
        auth=(usuario, senha_app),
        headers={"User-Agent": "RadarTechBR-Automation/1.0"},
        json={"content": atualizado},
        timeout=TIMEOUT,
    )

    if resposta.status_code >= 400:
        detalhe = resposta.text[:700]
        if senha_app:
            detalhe = detalhe.replace(senha_app, "***")
        raise RuntimeError(
            f"Falha ao salvar âncora de oferta no post {post_id}: "
            f"HTTP {resposta.status_code}: {detalhe}"
        )

    print("Âncora #oferta adicionada ao bloco afiliado do post.")
    return True


def linkar_shopee_no_html(conteudo_html):
    """
    Transforma cada ocorrência textual de "Shopee" em link afiliado.

    Segurança:
    - não altera ocorrências que já estejam dentro de um <a>;</n    - não altera atributos ou nomes de tags HTML;
    - preserva a grafia original encontrada no texto;
    - usa rel="nofollow sponsored" por ser link de afiliado.
    """
    conteudo_html = str(conteudo_html or "")
    if not conteudo_html:
        return conteudo_html, 0

    partes = re.split(
        r"(<a\b[^>]*>.*?</a>)",
        conteudo_html,
        flags=re.IGNORECASE | re.DOTALL,
    )

    total = 0
    saida = []
    padrao = re.compile(
        r"(?<![\wÀ-ÿ])Shopee(?![\wÀ-ÿ])",
        flags=re.IGNORECASE,
    )

    for indice, parte in enumerate(partes):
        # Partes ímpares são anchors completos capturados pelo split.
        if indice % 2 == 1:
            saida.append(parte)
            continue

        segmentos = re.split(r"(<[^>]+>)", parte)
        for posicao, segmento in enumerate(segmentos):
            # Segmentos ímpares são tags HTML; não tocar em atributos.
            if posicao % 2 == 1:
                continue

            def substituir(match):
                return (
                    f'<a href="{SHOPEE_AFFILIATE_URL}" '
                    'target="_blank" rel="nofollow sponsored">'
                    f'{match.group(0)}</a>'
                )

            segmentos[posicao], quantidade = padrao.subn(
                substituir,
                segmento,
            )
            total += quantidade

        saida.append("".join(segmentos))

    return "".join(saida), total


def garantir_link_shopee(post_id):
    """Aplica o link fixo da Shopee ao conteúdo aprovado antes de publicar."""
    url = os.getenv("WORDPRESS_URL", "").strip().rstrip("/")
    usuario = os.getenv("WORDPRESS_USERNAME", "").strip()
    senha_app = os.getenv("WORDPRESS_APP_PASSWORD", "").strip()

    if not url or not usuario or not senha_app:
        return 0

    resposta = requests.get(
        f"{url}/wp-json/wp/v2/posts/{int(post_id)}",
        params={"context": "edit", "_fields": "content"},
        auth=(usuario, senha_app),
        headers={"User-Agent": "RadarTechBR-Automation/1.0"},
        timeout=TIMEOUT,
    )

    if resposta.status_code >= 400:
        detalhe = resposta.text[:700]
        if senha_app:
            detalhe = detalhe.replace(senha_app, "***")
        raise RuntimeError(
            f"Falha ao preparar link Shopee no post {post_id}: "
            f"HTTP {resposta.status_code}: {detalhe}"
        )

    dados = resposta.json()
    conteudo = dados.get("content", {})
    if isinstance(conteudo, dict):
        html = str(conteudo.get("raw") or "")
    else:
        html = str(conteudo or "")

    atualizado, quantidade = linkar_shopee_no_html(html)

    if quantidade <= 0 or atualizado == html:
        print("Nenhuma menção textual à Shopee precisou ser linkada.")
        return 0

    resposta = requests.post(
        f"{url}/wp-json/wp/v2/posts/{int(post_id)}",
        auth=(usuario, senha_app),
        headers={"User-Agent": "RadarTechBR-Automation/1.0"},
        json={"content": atualizado},
        timeout=TIMEOUT,
    )

    if resposta.status_code >= 400:
        detalhe = resposta.text[:700]
        if senha_app:
            detalhe = detalhe.replace(senha_app, "***")
        raise RuntimeError(
            f"Falha ao salvar link Shopee no post {post_id}: "
            f"HTTP {resposta.status_code}: {detalhe}"
        )

    print(
        "Link afiliado da Shopee aplicado a",
        quantidade,
        "menção(ões) textual(is).",
    )
    return quantidade


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

    garantir_ancora_oferta(post_id)
    garantir_link_shopee(post_id)

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
