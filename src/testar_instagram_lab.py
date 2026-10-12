import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

GRAPH_VERSION = "v26.0"
BASE_DIR = Path(__file__).resolve().parent.parent
SAIDA_DIR = BASE_DIR / "artifacts"
SAIDA_PATH = SAIDA_DIR / "instagram_connection_test.json"


def exigir_variavel(nome):
    valor = str(os.getenv(nome) or "").strip()
    if not valor:
        raise RuntimeError(f"Variável ausente: {nome}")
    return valor


def consultar_instagram(page_id, page_token):
    campos = "id,name,instagram_business_account{id,username,name,profile_picture_url}"
    url = (
        f"https://graph.facebook.com/{GRAPH_VERSION}/"
        f"{page_id}?fields={campos}"
    )
    requisicao = Request(
        url,
        headers={
            "Authorization": f"Bearer {page_token}",
            "Accept": "application/json",
            "User-Agent": "blogger-automation1-instagram-lab/1.0",
        },
        method="GET",
    )

    try:
        with urlopen(requisicao, timeout=30) as resposta:
            corpo = resposta.read().decode("utf-8")
    except HTTPError as erro:
        detalhe = erro.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"Meta Graph API retornou HTTP {erro.code}: {detalhe[:800]}"
        ) from erro
    except URLError as erro:
        raise RuntimeError(
            f"Falha de transporte ao consultar Meta Graph API: {erro}"
        ) from erro

    dados = json.loads(corpo)
    if not isinstance(dados, dict):
        raise RuntimeError("Resposta inesperada da Meta Graph API.")
    return dados


def main():
    print("=== INSTAGRAM LAB — TESTE DE CONEXÃO ===")
    print("Somente leitura. Nenhuma publicação será feita.\n")

    page_id = exigir_variavel("FACEBOOK_PAGE_ID")
    page_token = exigir_variavel("FACEBOOK_PAGE_ACCESS_TOKEN")

    dados = consultar_instagram(page_id, page_token)
    id_retornado = str(dados.get("id") or "").strip()
    if id_retornado != page_id:
        raise RuntimeError("A Página retornada não corresponde ao FACEBOOK_PAGE_ID configurado.")

    conta = dados.get("instagram_business_account")
    if not isinstance(conta, dict) or not str(conta.get("id") or "").strip():
        resultado = {
            "status": "instagram_professional_account_not_found",
            "mode": "lab",
            "publish_external": False,
            "graph_version": GRAPH_VERSION,
            "facebook_page": {
                "id": id_retornado,
                "name": dados.get("name"),
            },
            "instagram": None,
            "safety": {
                "method": "GET",
                "external_write": False,
                "token_persisted_in_artifact": False,
            },
        }
        SAIDA_DIR.mkdir(parents=True, exist_ok=True)
        SAIDA_PATH.write_text(
            json.dumps(resultado, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print("Nenhuma conta profissional do Instagram foi encontrada vinculada a esta Página.")
        print("Saída:", SAIDA_PATH)
        return

    resultado = {
        "status": "ok",
        "mode": "lab",
        "publish_external": False,
        "graph_version": GRAPH_VERSION,
        "facebook_page": {
            "id": id_retornado,
            "name": dados.get("name"),
        },
        "instagram": {
            "id": str(conta.get("id") or ""),
            "username": conta.get("username"),
            "name": conta.get("name"),
            "profile_picture_url": conta.get("profile_picture_url"),
        },
        "safety": {
            "method": "GET",
            "external_write": False,
            "token_persisted_in_artifact": False,
            "note": "Teste somente de leitura. Nenhum conteúdo é criado no Instagram.",
        },
    }

    SAIDA_DIR.mkdir(parents=True, exist_ok=True)
    SAIDA_PATH.write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print("Página:", resultado["facebook_page"]["name"] or "sem nome")
    print("Instagram ID:", resultado["instagram"]["id"])
    print("Username:", resultado["instagram"]["username"] or "não retornado")
    print("Saída:", SAIDA_PATH)
    print("\nINSTAGRAM LAB: OK — nenhuma publicação realizada.")


if __name__ == "__main__":
    main()
