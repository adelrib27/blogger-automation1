import json
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
ENTRADA_PATH = BASE_DIR / "artifacts" / "social_payload.json"
SAIDA_PATH = BASE_DIR / "artifacts" / "facebook_dry_run.json"


def carregar_payload():
    if not ENTRADA_PATH.exists():
        raise RuntimeError(
            "social_payload.json não encontrado. Execute preparar_social_lab.py antes."
        )

    with ENTRADA_PATH.open("r", encoding="utf-8") as arquivo:
        return json.load(arquivo)


def main():
    print("=== FACEBOOK DRY-RUN ===")
    print("Nenhuma publicação será enviada ao Facebook.\n")

    page_id = str(os.getenv("FACEBOOK_PAGE_ID") or "").strip()
    if not page_id:
        raise RuntimeError("FACEBOOK_PAGE_ID ausente.")

    payload = carregar_payload()

    if payload.get("status") == "sem_post_novo":
        resultado = {
            "status": "sem_post_novo",
            "target": {
                "network": "facebook",
                "page_id_present": True,
            },
            "safety": {
                "dry_run": True,
                "publish_external": False,
                "will_publish": False,
            },
        }
    else:
        post = payload.get("post") or {}
        facebook = payload.get("facebook") or {}

        mensagem = str(facebook.get("text") or "").strip()
        link = str(facebook.get("link") or post.get("url") or "").strip()
        imagem = str(facebook.get("image_url") or post.get("featured_image_url") or "").strip()

        if not mensagem:
            raise RuntimeError("Texto do Facebook ausente no social_payload.json.")
        if not link:
            raise RuntimeError("Link do artigo ausente no social_payload.json.")

        resultado = {
            "status": "dry_run_pronto",
            "target": {
                "network": "facebook",
                "page_id_present": True,
            },
            "post": {
                "blogger_post_id": post.get("id"),
                "title": post.get("title"),
                "url": post.get("url"),
                "featured_image_url": imagem,
            },
            "request_preview": {
                "method": "POST",
                "endpoint_template": "/{FACEBOOK_PAGE_ID}/feed",
                "params": {
                    "message": mensagem,
                    "link": link,
                },
                "access_token_included": False,
            },
            "safety": {
                "dry_run": True,
                "publish_external": False,
                "will_publish": False,
                "note": "A requisição acima é apenas uma prévia. Nenhuma chamada POST é executada.",
            },
        }

    SAIDA_PATH.parent.mkdir(parents=True, exist_ok=True)
    SAIDA_PATH.write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print("Status:", resultado.get("status"))
    if resultado.get("post"):
        print("Post:", resultado["post"].get("title"))
        print("URL:", resultado["post"].get("url"))
    print("Saída:", SAIDA_PATH)
    print("\nFACEBOOK DRY-RUN: OK — nenhuma publicação realizada.")


if __name__ == "__main__":
    main()
