import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

GRAPH_VERSION = "v26.0"
BASE_DIR = Path(__file__).resolve().parent.parent
SAIDA_DIR = BASE_DIR / "artifacts"
SAIDA_PATH = SAIDA_DIR / "facebook_connection_test.json"


def exigir_variavel(nome):
    valor = str(os.getenv(nome) or "").strip()
    if not valor:
        raise RuntimeError(f"Variável ausente: {nome}")
    return valor


def consultar_pagina(page_id, page_token):
    url = (
        f"https://graph.facebook.com/{GRAPH_VERSION}/"
        f"{page_id}?fields=id,name,link"
    )

    requisicao = Request(
        url,
        headers={
            "Authorization": f"Bearer {page_token}",
            "Accept": "application/json",
            "User-Agent": "blogger-automation1-facebook-lab/1.0",
        },
        method="GET",
    )

    try:
        with urlopen(requisicao, timeout=30) as resposta:
            corpo = resposta.read().decode("utf-8")
    except HTTPError as erro:
        detalhe = erro.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"Facebook Graph API retornou HTTP {erro.code}: {detalhe[:500]}"
        ) from erro
    except URLError as erro:
        raise RuntimeError(
            f"Falha de transporte ao consultar Facebook Graph API: {erro}"
        ) from erro

    dados = json.loads(corpo)
    if not isinstance(dados, dict):
        raise RuntimeError("Resposta inesperada da Facebook Graph API.")

    return dados


def main():
    print("=== FACEBOOK LAB — TESTE DE CONEXÃO ===")
    print("Somente leitura. Nenhuma publicação será feita.\n")

    page_id = exigir_variavel("FACEBOOK_PAGE_ID")
    page_token = exigir_variavel("FACEBOOK_PAGE_ACCESS_TOKEN")

    dados = consultar_pagina(page_id, page_token)

    id_retornado = str(dados.get("id") or "").strip()
    if id_retornado != page_id:
        raise RuntimeError(
            "A página retornada pela API não corresponde ao FACEBOOK_PAGE_ID configurado."
        )

    resultado = {
        "status": "ok",
        "mode": "lab",
        "publish_external": False,
        "graph_version": GRAPH_VERSION,
        "page": {
            "id": id_retornado,
            "name": dados.get("name"),
            "link": dados.get("link"),
        },
        "safety": {
            "method": "GET",
            "external_write": False,
            "token_persisted_in_artifact": False,
            "note": "Teste somente de leitura da Página. Nenhum post é criado, editado ou excluído.",
        },
    }

    SAIDA_DIR.mkdir(parents=True, exist_ok=True)
    SAIDA_PATH.write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print("Página validada:", resultado["page"]["name"] or "sem nome")
    print("Page ID:", resultado["page"]["id"])
    print("Link:", resultado["page"]["link"] or "não retornado")
    print("Saída:", SAIDA_PATH)
    print("\nFACEBOOK LAB: OK — nenhuma publicação realizada.")


if __name__ == "__main__":
    main()
