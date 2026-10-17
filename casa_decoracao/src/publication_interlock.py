import os
import runpy
import sys
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

# Defesa em profundidade: o publicador legado passa a usar o gate v2 nesta execução.
import quality_gate  # noqa: E402
from publication_gate_v2 import publication_quality_v2  # noqa: E402

quality_gate.publication_quality = publication_quality_v2

runpy.run_path(str(SRC / "publish_generated.py"), run_name="__main__")
