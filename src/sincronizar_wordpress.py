import json
from pathlib import Path

from wordpress_api import listar_posts


BASE_DIR = Path(__file__).resolve().parent.parent
HISTORICO_PATH = BASE_DIR / "data" / "wordpress_historico.json"
RASCUNHOS_PATH = BASE_DIR / "data" / "wordpress_rascunhos.json"


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
    with caminho.open("w", encoding="utf-8") as arquivo:
        json.dump(
            dados,
            arquivo,
            ensure_ascii=False,
            indent=2,
        )
        arquivo.write("\n")


def indexar_existentes():
    base = {}

    for caminho in (HISTORICO_PATH, RASCUNHOS_PATH):
        for item in carregar_lista(caminho):
            if not isinstance(item, dict):
                continue
            post_id = item.get("post_id")
            if post_id:
                base[post_id] = dict(item)

    return base


def mesclar(post, existentes):
    post_id = post.get("post_id")
    registro = dict(existentes.get(post_id, {}))

    registro.update(
        {
            "post_id": post_id,
            "titulo": post.get("titulo") or registro.get("titulo", ""),
            "url": post.get("url") or registro.get("url"),
            "status": post.get("status") or registro.get("status", ""),
        }
    )

    registro.setdefault("palavra_chave", "")
    registro.setdefault("categoria", "")
    registro.setdefault("categoria_wordpress", "")
    registro.setdefault("produto_principal", "")
    registro.setdefault("link_afiliado", "")

    return registro


def executar():
    print("=== SINCRONIZAÇÃO WORDPRESS ===")

    existentes = indexar_existentes()

    publicados = [
        mesclar(item, existentes)
        for item in listar_posts("publish")
    ]

    rascunhos = [
        mesclar(item, existentes)
        for item in listar_posts("draft")
    ]

    salvar_lista(HISTORICO_PATH, publicados)
    salvar_lista(RASCUNHOS_PATH, rascunhos)

    print("Publicados encontrados:", len(publicados))
    print("Rascunhos encontrados:", len(rascunhos))
    print("Histórico e rascunhos sincronizados.")


if __name__ == "__main__":
    executar()
