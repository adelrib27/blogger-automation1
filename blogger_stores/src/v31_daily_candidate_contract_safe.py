#!/usr/bin/env python3
"""V31 LAB: preview a NEW daily Shopee rotation, entirely offline and fail-closed.

Uses the existing SAFE scan, V23-to-V31 adapter, page renderer and ledger
machine. Handles the scanner's 14-day rotation policy without imposing the
historical contract's permanent item-ID exclusion. This module never calls an
API, writes Git state, publishes, schedules or grants permission to do so.

Any actual transaction STILL requires authenticated Blogger GET + ETag,
remote Git HEAD/blobs CAS, an explicitly authorised claim+backup, one
conditional PUT, independent PUBLIC_EXACT_PASS and atomic persistence.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
CORE = HERE.parent / "v31_core"
for directory in (HERE, CORE):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

from v31_daily_cycle_gate_safe import gate as daily_gate, REPO, BRANCH  # noqa: E402
from v31_shopee_safe_scan import current_history_ids  # noqa: E402
from v31_from_v23_selection import convert_selection  # noqa: E402
from v31_multicycle_cas_contract import selection_ids  # noqa: E402
from v31_rotation_ledger import stage  # noqa: E402
from v31_store_safe import prepare_safe, AUTO_START, AUTO_END  # noqa: E402


class DailyCandidateBlocked(ValueError):
    """Unsafe or stale candidate; the published store must be preserved."""


def need(ok: bool, reason: str) -> None:
    if not ok:
        raise DailyCandidateBlocked(reason)


def preview_daily_candidate(*, profile: dict, ledger: dict, history: dict,
                            selection_bytes: bytes, current_page_bytes: bytes,
                            now: datetime, policy_guard, repository: str = REPO,
                            branch: str = BRANCH) -> dict:
    """Return an in-memory candidate and proposed PLAN; NEVER persist either.

    Inputs must be independently authenticated by a future caller. `policy_guard`
    must be the REAL central Blogger policy function outside synthetic tests.
    Result is only a SAFE preview, not a write authorisation or write plan.
    """
    need(callable(policy_guard), "Policy Guard callback obrigatória")
    need(isinstance(now, datetime) and now.tzinfo is not None, "Timezone obrigatório")
    need(type(selection_bytes) is bytes and 0 < len(selection_bytes) < 1024 * 1024,
         "Seleção JSON bruta ausente/grande")
    need(type(current_page_bytes) is bytes and 1000 < len(current_page_bytes) < 180000,
         "Página Blogger bruta ausente/grande")

    decision = daily_gate(profile, ledger, history, now=now,
                          repo=repository, branch=branch)
    need(decision["safeScanAllowed"] is True, "Mesmo dia ou histórico bloqueado")
    need(all(op.get("status") == "PERSISTED" for op in ledger["operations"]),
         "Operação não persistida")
    before_sha = sha256(current_page_bytes).hexdigest()
    need(before_sha == ledger["operations"][-1].get("candidateSha"),
         "HTML atual diverge da última publicação persistida")

    try:
        page = current_page_bytes.decode("utf-8", "strict")
        selection = json.loads(selection_bytes.decode("utf-8", "strict"))
    except (UnicodeError, ValueError) as exc:
        raise DailyCandidateBlocked("Seleção/página não são UTF-8 válido") from exc
    need(isinstance(selection, dict), "Seleção não é objeto JSON")
    need(page.count(AUTO_START) == 1 and page.count(AUTO_END) == 1,
         "Marcadores da LOJA ausentes ou duplicados")

    selection_sha, selected_ids = selection_ids(selection_bytes, profile)
    recent, previous = current_history_ids(history, now=now, days=14)
    need(len(previous) == profile["expected_products"], "Última rotação incompleta")
    chosen = [p for cat in profile["categories"] for p in selection["categories"][cat]]
    need(len(chosen) == len(selected_ids), "Seleção interna inconsistente")
    allowed = {"new", "fallback_older", "carry_forward_last"}
    modes = Counter()
    for product in chosen:
        item_id = str(product["itemId"])
        mode = product.get("rotationSelectionMode")
        need(mode in allowed, "Modo de rotação não permitido")
        if mode == "new":
            need(item_id not in recent, "Produto recente marcado incorretamente como novo")
        elif mode == "fallback_older":
            need(item_id in recent and item_id not in previous,
                 "Fallback antigo não condiz com histórico")
        else:
            need(item_id in previous, "Carry-forward não pertence à última vitrine")
        modes[mode] += 1
    need(set(selected_ids) != previous,
         "Vitrine idêntica à anterior: não publicar atualização sem mudança")

    # Central policy is re-run for each Shopee candidate (no trusted flags alone).
    catalog = convert_selection(selection, profile,
                                require_product_allowed=policy_guard, now=now)
    planned = prepare_safe(catalog, profile, original=page)
    checks = planned["check"]
    need(checks["cards"] == checks["photos"] == checks["affiliate_links"] ==
         profile["expected_products"], "Cards, fotos ou links incompletos")
    candidate = planned["html"].encode("utf-8")
    candidate_sha = sha256(candidate).hexdigest()
    need(candidate_sha != before_sha, "HTML sem diferença efetiva")
    proposed = stage(ledger, selection_sha, before_sha, candidate_sha)
    need(len(proposed["operations"]) == len(ledger["operations"]) + 1 and
         proposed["operations"][-1]["status"] == "PLAN",
         "Reserva PLAN duplicada/inesperada")

    return {
        "status": "V31_LAB_DAILY_CANDIDATE_DYNAMIC_SAFE_ONLY",
        "blogId": profile["blog_id"], "pageId": profile["page_id"],
        "selectionSha256": selection_sha, "currentHtmlSha256": before_sha,
        "candidateHtmlSha256": candidate_sha,
        "candidateHtmlBytes": candidate,  # NEVER print or upload automatically
        "proposedLedger": proposed,         # NEVER commit automatically
        "operationId": proposed["operations"][-1]["operationId"],
        "rotationModes": dict(modes), "cards": checks["cards"],
        "historyEntries": len(history["runs"]),
        "gitRemoteWriteAllowed": False, "bloggerPutAllowed": False,
        "cronEnabled": False, "publicationAuthorized": False,
    }
