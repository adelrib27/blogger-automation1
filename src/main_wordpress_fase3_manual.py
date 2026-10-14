import os
from datetime import datetime
from zoneinfo import ZoneInfo

import main_wordpress_fase3 as fase3


if os.getenv("GITHUB_EVENT_NAME", "").strip() != "workflow_dispatch":
    raise RuntimeError(
        "Este wrapper só pode ser usado em execução manual via workflow_dispatch."
    )

_carregar_json_original = fase3.carregar_json


def carregar_json_manual(caminho, padrao):
    dados = _carregar_json_original(caminho, padrao)

    if caminho == fase3.POLICY_PATH and isinstance(dados, dict):
        politica = dict(dados)
        modo = dict(politica.get("phase3_mode") or {})
        fuso = ZoneInfo(str(politica.get("timezone") or "America/Sao_Paulo"))
        modo["activation_date"] = datetime.now(fuso).date().isoformat()
        politica["phase3_mode"] = modo
        return politica

    return dados


fase3.carregar_json = carregar_json_manual
fase3.executar()
