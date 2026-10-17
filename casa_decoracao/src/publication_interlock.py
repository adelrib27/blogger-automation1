import os
import sys
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "casa_decoracao" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

STATUS = os.getenv("CASA_WORDPRESS_STATUS", "draft").strip().lower()
LIVE_ENABLED = os.getenv("CASA_LIVE_PUBLISH_ENABLED", "false").strip().lower() in {
    "1", "true", "yes", "on"
}

if STATUS == "publish" and not LIVE_ENABLED:
    raise RuntimeError(
        "PUBLICAÇÃO AO VIVO BLOQUEADA: CASA_LIVE_PUBLISH_ENABLED não está habilitado. "
        "A liberação deve ocorrer somente após autorização explícita e validação do gate final."
    )

import quality_gate  # noqa: E402
from publication_gate_v2 import publication_quality_v2  # noqa: E402

quality_gate.publication_quality = publication_quality_v2

import publish_generated as publisher  # noqa: E402

# Defesa em profundidade: o módulo já importou a função, então substituímos a
# referência local também.
publisher.publication_quality = publication_quality_v2


def public_posts_for_quality():
    statuses = urllib.parse.quote("publish,future", safe=",")
    fields = urllib.parse.quote("id,slug,title,excerpt,content,status,link", safe=",")
    path = f"/wp/v2/posts?context=edit&per_page=100&status={statuses}&_fields={fields}"
    rows = publisher.request("GET", path)
    return rows if isinstance(rows, list) else []


# Rascunhos automatizados não devem bloquear a atualização uns dos outros. A
# canibalização é comparada com conteúdo já público (ou já agendado). Se um
# artigo for publicado numa execução futura, a lista é recarregada e passa a
# bloquear os candidatos realmente conflitantes que vierem depois.
publisher.existing_posts_for_quality = public_posts_for_quality

publisher.main()
