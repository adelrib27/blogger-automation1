import json
from pathlib import Path

import links_internos
import main as motor
import pautas
from wordpress_api import criar_post_rascunho


BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_WORDPRESS = BASE_DIR / "config" / "wordpress.json"
HISTORICO_WORDPRESS = BASE_DIR / "data" / "wordpress_historico.json"
RASCUNHOS_WORDPRESS = BASE_DIR / "data" / "wordpress_rascunhos.json"


# Isola o Radar Tech BR do histórico e das URLs do Blogger.
motor.CONFIG_PATH = CONFIG_WORDPRESS
motor.HISTORICO_PATH = HISTORICO_WORDPRESS
pautas.ARQUIVO_HISTORICO = HISTORICO_WORDPRESS
pautas.ARQUIVO_RASCUNHOS = RASCUNHOS_WORDPRESS
links_internos.HISTORICO_PATH = HISTORICO_WORDPRESS


def carregar_lista(caminho):
    if not caminho.exists():
        return []

    try:
        with caminho.open("r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
    except (OSError, json.JSONDecodeError):
        return []

    return dados if isinstance(dados, list) else []


def salvar_lista(caminho, dados):
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with caminho.open("w", encoding="utf-8") as arquivo:
        json.dump(
            dados,
            arquivo,
            ensure_ascii=False,
            indent=2,
        )
        arquivo.write("\n")


def registrar_rascunho(resultado, pacote):
    rascunhos = carregar_lista(RASCUNHOS_WORDPRESS)

    post_id = resultado.get("id")

    if post_id and any(
        item.get("post_id") == post_id
        for item in rascunhos
        if isinstance(item, dict)
    ):
        return

    pauta = pacote.get("pauta") or {}
    seo = pacote.get("seo") or {}
    artigo = pacote.get("artigo") or {}
    produto = artigo.get("produto_principal") or {}

    rascunhos.append(
        {
            "post_id": post_id,
            "titulo": seo.get("titulo") or pauta.get("titulo"),
            "url": resultado.get("url"),
            "status": resultado.get("status", "draft"),
            "palavra_chave": pauta.get("palavra_chave", ""),
            "categoria": pauta.get("categoria", ""),
            "categoria_wordpress": resultado.get("categoria_slug", ""),
            "produto_principal": produto.get("nome", ""),
            "link_afiliado": produto.get("link_afiliado", ""),
        }
    )

    salvar_lista(
        RASCUNHOS_WORDPRESS,
        rascunhos,
    )


def executar():
    print("=== RADAR TECH BR — WORDPRESS / MODO SEGURO ===")
    print("Destino: WordPress")
    print("Status de saída: RASCUNHO")
    print("Publicação automática no WordPress: DESATIVADA")
    print()

    pacote = motor.executar()

    if not isinstance(pacote, dict):
        raise RuntimeError(
            "O motor editorial não retornou um pacote válido."
        )

    artigo = pacote.get("artigo") or {}
    seo = pacote.get("seo") or {}

    if not artigo.get("conteudo_html") or not seo.get("titulo"):
        raise RuntimeError(
            "O pacote editorial não contém artigo aprovado para envio."
        )

    print("\n=== ENVIO SEGURO AO WORDPRESS ===")
    resultado = criar_post_rascunho(pacote)

    registrar_rascunho(
        resultado,
        pacote,
    )

    print("Rascunho criado com sucesso no Radar Tech BR.")
    print("Título:", resultado.get("titulo"))
    print("Post ID:", resultado.get("id"))
    print("Status:", resultado.get("status"))
    print("Categoria:", resultado.get("categoria_slug"))
    print("Imagem destacada ID:", resultado.get("featured_media") or "sem imagem")
    print("URL:", resultado.get("url"))

    return {
        "pacote": pacote,
        "wordpress": resultado,
    }


if __name__ == "__main__":
    executar()
