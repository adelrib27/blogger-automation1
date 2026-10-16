import os
from urllib.parse import urlparse


EXPECTED_HOST = "casaedecoracao.radartechbr.com.br"
BLOCKED_HOSTS = {"radartechbr.com.br", "www.radartechbr.com.br"}


def validate_wordpress_target() -> str:
    raw = os.getenv("WORDPRESS_URL", "").strip().rstrip("/")
    if not raw:
        raise RuntimeError("WORDPRESS_URL ausente para o projeto Casa e Decoração.")

    parsed = urlparse(raw)
    host = (parsed.hostname or "").lower()

    if host in BLOCKED_HOSTS:
        raise RuntimeError(
            "BLOQUEADO: a automação Casa e Decoração não pode publicar no Radar Tech BR principal."
        )

    if host != EXPECTED_HOST:
        raise RuntimeError(
            f"BLOQUEADO: destino inesperado {host!r}; esperado {EXPECTED_HOST!r}."
        )

    if parsed.scheme != "https":
        raise RuntimeError("BLOQUEADO: o WordPress Casa e Decoração deve usar HTTPS.")

    return raw


def validate_project_paths() -> None:
    forbidden = (
        "data/fase3/",
        "data/wordpress_historico.json",
        "data/wordpress_rascunhos.json",
        "config/fase3_politica_editorial.json",
        "config/wordpress.json",
    )
    watched = {
        "CASA_HISTORY_PATH": os.getenv("CASA_HISTORY_PATH", ""),
        "CASA_DRAFTS_PATH": os.getenv("CASA_DRAFTS_PATH", ""),
        "CASA_QUEUE_PATH": os.getenv("CASA_QUEUE_PATH", ""),
        "CASA_POLICY_PATH": os.getenv("CASA_POLICY_PATH", ""),
        "CASA_WORDPRESS_CONFIG": os.getenv("CASA_WORDPRESS_CONFIG", ""),
    }
    for name, value in watched.items():
        normalized = value.replace("\\", "/").lstrip("./")
        if any(normalized == item.rstrip("/") or normalized.startswith(item) for item in forbidden):
            raise RuntimeError(f"BLOQUEADO: {name} aponta para estado do Radar Tech BR: {value}")


def install() -> None:
    target = validate_wordpress_target()
    validate_project_paths()
    os.environ["CASA_DECORACAO_GUARD_ACTIVE"] = "1"
    print("Casa e Decoração — runtime guard ativo.")
    print("Destino validado:", target)


if __name__ == "__main__":
    install()
