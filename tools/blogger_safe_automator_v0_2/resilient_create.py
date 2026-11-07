#!/usr/bin/env python3
from __future__ import annotations

import re
import time
from collections.abc import Callable

import browser_provision as bp

DEFAULT_MAX_ADDRESS_ATTEMPTS = 10
MAX_BLOGSPOT_SLUG_LENGTH = 63

# Somente erros que afirmam explicitamente que SALVAR não foi acionado
# podem disparar nova tentativa. Isso evita criação duplicada.
_PRE_SAVE_RETRY_MARKERS = (
    "nenhum clique em salvar foi executado",
    "nenhum clique em salvar/criar foi executado",
    "nenhum botão final salvar/criar foi acionado",
)


def _safe_seed() -> str:
    # Curto, somente numérico e suficientemente variável entre execuções.
    return str(time.time_ns())[-10:]


def build_address_candidates(
    requested_address: str,
    *,
    max_attempts: int = DEFAULT_MAX_ADDRESS_ATTEMPTS,
    seed: str | None = None,
) -> list[str]:
    """Gera candidatos válidos preservando o endereço pedido como 1ª opção."""
    req = bp.CreateBlogRequest.build("x", requested_address)
    base = req.address

    if not 1 <= max_attempts <= 50:
        raise bp.SafeAutomationError("max_attempts deve estar entre 1 e 50.")

    nonce = re.sub(r"[^a-z0-9]", "", (seed or _safe_seed()).lower())[-10:] or "1"
    candidates = [base]

    for attempt in range(2, max_attempts + 1):
        suffix = f"-{nonce}-{attempt}"
        room = MAX_BLOGSPOT_SLUG_LENGTH - len(suffix)
        prefix = base[:room].rstrip("-")
        if not prefix:
            prefix = "blog"
        candidate = f"{prefix}{suffix}"
        # Validação local antes de tocar no Blogger.
        validated = bp.CreateBlogRequest.build("x", candidate).address
        if validated not in candidates:
            candidates.append(validated)

    return candidates


def is_safe_pre_save_retry(error: BaseException) -> bool:
    text = re.sub(r"\s+", " ", str(error or "")).strip().casefold()
    return any(marker in text for marker in _PRE_SAVE_RETRY_MARKERS)


def execute_create_resilient(
    title: str,
    address: str,
    *,
    confirm: str,
    cdp_url: str = bp.DEFAULT_CDP_URL,
    diagnostics_dir="logs/browser_diagnostics",
    allow_remote_cdp: bool = False,
    max_address_attempts: int = DEFAULT_MAX_ADDRESS_ATTEMPTS,
    create_fn: Callable | None = None,
) -> dict:
    """Cria blog tentando slugs alternativos apenas em rejeições pré-SALVAR.

    Nunca repete após erro que possa ter ocorrido depois do clique em SALVAR.
    O sucesso continua dependendo da validação do Blog ID e HTTP 200 feita pelo
    browser_provision.execute_create.
    """
    if confirm != bp.CREATE_CONFIRMATION:
        raise bp.SafeAutomationError(
            f'Criação bloqueada: confirmação obrigatória é "{bp.CREATE_CONFIRMATION}".'
        )

    # Valida título/endereço antes de iniciar qualquer interação.
    initial_req = bp.CreateBlogRequest.build(title, address)
    candidates = build_address_candidates(
        initial_req.address,
        max_attempts=max_address_attempts,
    )
    runner = create_fn or bp.execute_create
    attempts: list[dict] = []

    for index, candidate in enumerate(candidates, start=1):
        try:
            result = runner(
                initial_req.title,
                candidate,
                confirm=confirm,
                cdp_url=cdp_url,
                diagnostics_dir=diagnostics_dir,
                allow_remote_cdp=allow_remote_cdp,
            )
            return {
                **result,
                "requested_address": initial_req.address,
                "address": candidate,
                "address_attempt_count": index,
                "address_attempts": attempts + [
                    {"attempt": index, "address": candidate, "outcome": "created"}
                ],
                "address_retry_enabled": True,
            }
        except bp.SafeAutomationError as exc:
            retryable = is_safe_pre_save_retry(exc)
            attempts.append(
                {
                    "attempt": index,
                    "address": candidate,
                    "outcome": "rejected_before_save" if retryable else "stopped_safely",
                    "reason": re.sub(r"\s+", " ", str(exc)).strip()[:500],
                }
            )
            if not retryable:
                raise
            if index >= len(candidates):
                raise bp.SafeAutomationError(
                    "O Blogger rejeitou todos os endereços tentados antes de SALVAR. "
                    f"Foram feitas {index} tentativas seguras; nenhum blog foi criado."
                ) from exc

    raise bp.SafeAutomationError("Nenhum candidato de endereço pôde ser tentado com segurança.")
