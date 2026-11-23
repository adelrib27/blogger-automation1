"""C134: observabilidade SAFE do agendamento DRAFT sem confundir job e entrega.

Sem conexões, credenciais, novas cotas, autorização LIVE ou writes CMS.
A fonte da confirmação é o recibo DRAFT_VERIFIED, não o status SUCCESS do job.
"""
from __future__ import annotations

import json
import re


def _parse_object(raw: str) -> dict | None:
    try:
        decoded = json.loads(raw) if isinstance(raw, str) and raw else None
    except (TypeError, ValueError):
        return None
    return decoded if isinstance(decoded, dict) else None


def summarize_draft_cycle(*, site_key: str, verification_receipt: str,
                          verified_draft: str, draft_job: str,
                          live_job: str) -> dict:
    """Produz apenas telemetria categórica, sem URLs ou dados de produtos.

    O resultado do job GitHub nunca é usado sozinho para afirmar que
    houve criação de DRAFT. A saída do verificador pode ser NO_NEW_OFFER
    mesmo quando o workflow completo consta como success.
    """
    receipt = _parse_object(verification_receipt)
    proof = _parse_object(verified_draft)
    status = str(receipt.get("status", "")) if receipt else ""
    reason = str(receipt.get("reason", "")) if receipt else ""
    outcome = "UNVERIFIED"
    if receipt and receipt.get("site_key") == site_key and status == "NO_NEW_OFFER" and not proof:
        outcome = {
            "research_budget_exhausted": "BLOCKED_RESEARCH_BUDGET",
            "draft_daily_cap_reached": "BLOCKED_DRAFT_DAILY_CAP",
            "site_quota_reached": "BLOCKED_SITE_ARTICLE_LIMIT",
            "pilot_offer_already_present": "NO_NEW_DRAFT_DUPLICATE_PREVENTED",
            "no_new_offer_with_trusted_source": "NO_APPROVED_NEW_OFFER",
        }.get(reason, "NO_NEW_OFFER_UNCLASSIFIED")
    elif (receipt and receipt.get("site_key") == site_key
          and status in {"READY", "USED"}
          and draft_job == "success" and proof
          and proof.get("site_key") == site_key
          and proof.get("fingerprint") == receipt.get("fingerprint")
          and proof.get("status") == "DRAFT_VERIFIED"
          and str(proof.get("draft_id", "")).isdigit()
          and re.fullmatch(r"[a-f0-9]{64}", str(proof.get("html_sha256", "")))):
        outcome = "DRAFT_VERIFIED"
    return {
        "site_key": site_key,
        "draft_outcome": outcome,
        "verification_status": status if status in {"NO_NEW_OFFER", "READY", "USED"} else "UNAVAILABLE",
        "draft_job": draft_job,
        "live_job": live_job,
        "draft_verified_or_reconciled": outcome == "DRAFT_VERIFIED",
        "new_post_creation_unproven_by_summary": True,
        "automatic_live_confirmation": False,
        "note": "O resultado de um job SUCCESS não prova criação de DRAFT nem publicação LIVE",
    }
