#!/usr/bin/env python3
"""V31 R23 — autoriza APENAS os dois blogs LAB conhecidos para instalação V31.

Este módulo é uma política isolada e testável. NÃO instala temas, não chama
Chrome/CDP/Blogger, não altera configurações do Runner e não publica conteúdo.
A adoção deve ser integrada ao serviço LOCAL após revisão do runtime real.
"""
from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from urllib.parse import urlsplit

THEME_FAMILY = "TEMA_BLOGGER_UNIVERSAL_V31_R1_PLAY_REFINADO_LAB"
ACTION = "ADOPT_CURRENT_UNIVERSAL_V31"
OLD_LAB_ID = "4739187376492839837"
NEW_REPLICATION_LAB_ID = "1625257710858445955"


@dataclass(frozen=True)
class AuthorizedLab:
    blog_id: str
    url: str
    loja_page_id: str


EXACT_LABS = MappingProxyType({
    OLD_LAB_ID: AuthorizedLab(
        OLD_LAB_ID, "https://blog-teste-tema-worpress.blogspot.com/",
        "2446067640331732447",
    ),
    NEW_REPLICATION_LAB_ID: AuthorizedLab(
        NEW_REPLICATION_LAB_ID, "https://lab-v31-loja-20261105.blogspot.com/",
        "8266917849571219350",
    ),
})


class V31LabAuthorizationError(PermissionError):
    """Falha fechada antes de qualquer modificação ou chamada de tema."""


def authorize_v31_lab_theme(
    *, blog_id: str, blog_url: str, loja_page_id: str,
    operation: str, confirm: str,
) -> AuthorizedLab:
    """Confere identidade EXATA e confirmação específica por Blog ID.

    Integração futura obrigatória: comparar também Blog ID/URL lidos AO VIVO
    do painel Blogger, conferir backup e SHA canônico do tema antes da escrita.
    """
    if not isinstance(blog_id, str) or blog_id not in EXACT_LABS:
        raise V31LabAuthorizationError("Blog ID fora da allowlist exata dos LABs V31.")
    if not isinstance(blog_url, str) or not isinstance(loja_page_id, str):
        raise V31LabAuthorizationError("Tipos de identidade inválidos.")
    if operation != ACTION:
        raise V31LabAuthorizationError("Operação do tema V31 não autorizada.")
    if confirm != f"ADOPT UNIVERSAL V31 BLOG {blog_id}":
        raise V31LabAuthorizationError("Confirmação explícita específica do Blog ID ausente.")
    expected = EXACT_LABS[blog_id]
    parsed = urlsplit(blog_url)
    if (blog_url != expected.url or parsed.scheme != "https"
            or parsed.netloc != urlsplit(expected.url).netloc
            or parsed.path != "/" or parsed.query or parsed.fragment):
        raise V31LabAuthorizationError("URL canônica do blog divergente.")
    if loja_page_id != expected.loja_page_id:
        raise V31LabAuthorizationError("Page ID da LOJA divergente.")
    return expected
