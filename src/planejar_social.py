import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config" / "social.json"
PAYLOAD_PATH = BASE_DIR / "artifacts" / "social_payload.json"
PLAN_PATH = BASE_DIR / "artifacts" / "social_plan.json"


def carregar_json(caminho):
    with caminho.open("r", encoding="utf-8") as arquivo:
        return json.load(arquivo)


def validar_config(config):
    if config.get("mode") != "lab":
        raise RuntimeError("Social Lab deve permanecer em mode=lab nesta fase.")

    if config.get("publish_external") is not False:
        raise RuntimeError("publish_external deve permanecer false nesta fase.")

    redes = config.get("networks")
    if not isinstance(redes, dict) or not redes:
        raise RuntimeError("Configuração de redes sociais ausente ou inválida.")

    habilitadas = [
        nome
        for nome, dados in redes.items()
        if isinstance(dados, dict) and dados.get("enabled") is True
    ]

    if habilitadas:
        raise RuntimeError(
            "Nenhuma rede pode estar enabled=true enquanto o Social Lab estiver bloqueado. "
            + "Redes habilitadas: "
            + ", ".join(habilitadas)
        )


def montar_plano(payload, config):
    if payload.get("status") == "sem_post_novo":
        return {
            "status": "sem_post_novo",
            "mode": "lab",
            "publish_external": False,
            "actions": [],
        }

    post = payload.get("post") or {}
    redes = config.get("networks") or {}
    acoes = []

    for nome, dados in sorted(
        redes.items(),
        key=lambda item: int((item[1] or {}).get("priority", 99)),
    ):
        conteudo = payload.get(nome)
        if not isinstance(conteudo, dict):
            status = "payload_ausente"
        elif dados.get("enabled") is True:
            status = "bloqueado_por_modo_lab"
        else:
            status = "pronto_para_conectar"

        acoes.append(
            {
                "network": nome,
                "priority": dados.get("priority"),
                "configured_enabled": bool(dados.get("enabled")),
                "status": status,
                "will_publish": False,
            }
        )

    return {
        "status": "planejado",
        "mode": "lab",
        "publish_external": False,
        "post": {
            "id": post.get("id"),
            "title": post.get("title"),
            "url": post.get("url"),
            "featured_image_url": post.get("featured_image_url"),
        },
        "actions": acoes,
        "future_video_channels": config.get("future_video_channels", {}),
        "safety": {
            "external_calls": False,
            "note": "Plano gerado somente para inspeção. Nenhuma API social é chamada.",
        },
    }


def main():
    print("=== SOCIAL LAB — PLANEJAMENTO ===")

    config = carregar_json(CONFIG_PATH)
    validar_config(config)

    payload = carregar_json(PAYLOAD_PATH)
    plano = montar_plano(payload, config)

    PLAN_PATH.parent.mkdir(parents=True, exist_ok=True)
    PLAN_PATH.write_text(
        json.dumps(plano, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print("Modo:", plano.get("mode"))
    print("Publicação externa:", plano.get("publish_external"))

    for acao in plano.get("actions", []):
        print(
            "-",
            acao.get("network"),
            "=>",
            acao.get("status"),
            "| publicar:",
            acao.get("will_publish"),
        )

    print("\nSOCIAL PLAN: OK — nenhuma rede social chamada.")


if __name__ == "__main__":
    main()
