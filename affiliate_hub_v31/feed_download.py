"""Download SAFE dos feeds oficiais, a partir de secrets de ambiente.

Não armazena tokens em logs/relatórios; redirecionamentos de domínio não
verificado são bloqueados. CSVs ficam apenas no diretório temporário privado.
"""
from __future__ import annotations

import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

MAX_FEED_BYTES = 512 * 1024 * 1024
BUFFER = 1024 * 1024


class DownloadFeedError(ValueError):
    """Código estático seguro; não contém URL, token ou corpo de resposta."""


class RedirectNotAllowed(ValueError):
    """Um redirecionamento tentou sair do endereço permitido."""


def redirect_category(raw: str) -> str:
    """Retorna apenas uma classificação estática, nunca a URL ou o hostname."""
    try:
        address = urllib.parse.urlsplit(raw)
        host = (address.hostname or "").lower()
        if host == "affiliate.shopee.com.br" or host.endswith(".shopee.com.br"):
            return "SHOPEE_BR"
        if host == "storage.googleapis.com" or host.endswith(".storage.googleapis.com"):
            return "CLOUD_STORAGE"
        if host.endswith(".amazonaws.com"):
            return "AWS_OBJECT_STORAGE"
        if host.endswith(".cloudfront.net"):
            return "CLOUDFRONT"
        if host.endswith(".shopee.io") or host.endswith(".shopeemobile.com"):
            return "SHOPEE_CDN"
    except ValueError:
        pass
    return "OTHER_HOST"


def check_feed_url(raw: str) -> None:
    if not isinstance(raw, str) or len(raw) > 1500 or any(c.isspace() for c in raw):
        raise ValueError("URL de feed inválida")
    try:
        u = urllib.parse.urlsplit(raw)
        q = urllib.parse.parse_qs(u.query, keep_blank_values=True)
        if (u.scheme != "https" or u.hostname != "affiliate.shopee.com.br"
                or u.port not in (None, 443) or u.username or u.password
                or u.path != "/api/v1/datafeed/download" or u.fragment
                or set(q) != {"id"} or len(q["id"]) != 1
                or not re.fullmatch(r"[A-Za-z0-9_-]{20,512}", q["id"][0])):
            raise ValueError("URL de feed fora da lista permitida")
    except (ValueError, AttributeError):
        raise ValueError("URL de feed inválida") from None


def redirect_allowed(raw: str) -> bool:
    try:
        if not isinstance(raw, str) or len(raw) > 2500 or any(c.isspace() for c in raw):
            return False
        u = urllib.parse.urlsplit(raw)
        host = (u.hostname or "").lower().rstrip(".")
        return (u.scheme == "https" and u.username is None and u.password is None
                and u.port in (None, 443) and not u.fragment
                and (host == "shopee.com.br" or host.endswith(".shopee.com.br")))
    except (TypeError, ValueError, AttributeError):
        return False


class RestrictRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not redirect_allowed(newurl):
            raise RedirectNotAllowed(redirect_category(newurl)) from None
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def download_feed(raw_url: str, destination: Path | str, *, max_bytes=MAX_FEED_BYTES) -> int:
    check_feed_url(raw_url)
    if not 1024 <= max_bytes <= MAX_FEED_BYTES:
        raise ValueError("Limite inválido")
    dest = Path(destination)
    if dest.exists() or dest.is_symlink():
        raise ValueError("Destino já existe")
    dest.parent.mkdir(parents=True, exist_ok=True)
    opener = urllib.request.build_opener(RestrictRedirect())
    request = urllib.request.Request(
        raw_url, method="GET", headers={"User-Agent": "V31EditorialFeedImport/0.2"}
    )
    size = 0
    try:
        with opener.open(request, timeout=55) as response, dest.open("xb") as output:
            content_length = response.headers.get("Content-Length")
            if content_length and int(content_length) > max_bytes:
                raise ValueError("Feed excede limite")
            while True:
                block = response.read(BUFFER)
                if not block:
                    break
                size += len(block)
                if size > max_bytes:
                    raise ValueError("Feed excede limite")
                output.write(block)
    except Exception as exc:
        # Suprimir URL/token/response do traceback e remover download parcial.
        dest.unlink(missing_ok=True)
        if isinstance(exc, RedirectNotAllowed):
            code = "REDIRECT_BLOCKED_" + str(exc)
        elif isinstance(exc, urllib.error.HTTPError):
            code = "HTTP_" + str(exc.code) if 100 <= exc.code <= 599 else "HTTP_INVALID"
        elif isinstance(exc, urllib.error.URLError):
            code = "NETWORK_ERROR"
        elif isinstance(exc, TimeoutError):
            code = "NETWORK_TIMEOUT"
        elif isinstance(exc, ValueError):
            code = "INVALID_RESPONSE_OR_SIZE"
        else:
            code = "DOWNLOAD_UNKNOWN"
        raise DownloadFeedError(code) from None
    if size < 10:
        dest.unlink(missing_ok=True)
        raise ValueError("Feed vazio ou inválido")
    return size
