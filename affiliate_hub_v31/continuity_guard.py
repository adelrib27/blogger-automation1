"""V31 C57 — verificador local da trilha de continuidade.

Este script lê SOMENTE arquivos do repositório; nenhum acesso R2, Github API,
Shopee, Blogger ou WordPress; nunca altera checkpoints automaticamente.
"""
from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path

REQUIRED_STATUSES = frozenset({
    "EM_ANDAMENTO", "PRONTO_PARA_PROXIMA_ETAPA", "BLOQUEADO"
})
BANNED_FIELDS = re.compile(
    r"(^|_)(password|credential|private_key|access_token|api_token|"
    r"refresh_token|client_secret|app_secret|cookie|session_key)($|_)",
    re.I
)


class ContinuityGuardError(ValueError):
    pass


def check_repository(root: Path) -> dict:
    root = Path(root)
    index = root / "V31_CONTINUAR_AQUI.md"
    protocol = root / "affiliate_hub_v31" / "CONTINUIDADE_PROTOCOLO.md"
    state_file = root / "affiliate_hub_v31" / "CONTINUIDADE_ESTADO.json"
    agents = root / "AGENTS.md"
    if not all(p.is_file() for p in (index, protocol, state_file, agents)):
        raise ContinuityGuardError("continuity_entrypoint_missing")

    try:
        state = json.loads(state_file.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        raise ContinuityGuardError("continuity_json_unreadable") from None
    if not isinstance(state, dict) or state.get("schema_version") != 1:
        raise ContinuityGuardError("continuity_schema_invalid")
    if (state.get("repository") != "adelrib27/blogger-automation1" or
        state.get("branch") != "main"):
        raise ContinuityGuardError("continuity_repo_invalid")

    status = state.get("continuity_status")
    active = state.get("active_work")
    if (status not in REQUIRED_STATUSES or
        not isinstance(active, dict) or
        active.get("status") != status):
        raise ContinuityGuardError("continuity_status_mismatch")
    if (not isinstance(active.get("objective"), str) or
        len(active["objective"].strip()) < 20 or
        not isinstance(active.get("latest_verified_step"), str) or
        not active["latest_verified_step"].strip() or
        not isinstance(active.get("next_safe_step"), str) or
        not active["next_safe_step"].strip()):
        raise ContinuityGuardError("continuity_active_work_incomplete")
    for gate in ("mutation_in_progress", "remote_operation_in_progress",
                 "rollback_needed"):
        if type(active.get(gate)) is not bool:
            raise ContinuityGuardError("continuity_mutation_gate_invalid")

    pointer = state.get("checkpoint_detail")
    if (not isinstance(pointer, str) or
        not pointer.startswith("affiliate_hub_v31/") or
        pointer.startswith("/") or ".." in Path(pointer).parts or
        not (root / pointer).is_file()):
        raise ContinuityGuardError("continuity_checkpoint_not_found")
    if (state.get("start_here") != "V31_CONTINUAR_AQUI.md" or
        not isinstance(state.get("next_priorities"), list) or
        not state["next_priorities"] or
        any(not isinstance(s, str) or not s.strip()
            for s in state["next_priorities"])):
        raise ContinuityGuardError("continuity_missing_next_steps")

    content = index.read_text(encoding="utf-8")
    if (len(content) < 1000 or
        "CONTINUIDADE_ESTADO.json" not in content or
        "CHECKPOINT_ATUAL.md" not in content or
        "Shopee" not in content or "universal" not in content.lower()):
        raise ContinuityGuardError("continuity_index_incomplete")

    def reject_private_keys(value, path=()):
        if isinstance(value, dict):
            for key, nested in value.items():
                if BANNED_FIELDS.search(str(key)):
                    raise ContinuityGuardError("continuity_secret_field_prohibited")
                reject_private_keys(nested, path + (str(key),))
        elif isinstance(value, list):
            for nested in value:
                reject_private_keys(nested, path)

    reject_private_keys(state)
    if state.get("continuity_contract", {}).get("contains_secrets") is not False:
        raise ContinuityGuardError("continuity_secret_policy_not_declared")

    return {
        "status": status,
        "phase": state.get("continuity_protocol_phase"),
        "latest_checkpoint": state.get("last_checkpoint_phase"),
        "checkpoint_detail": pointer,
        "active_objective": active["objective"],
        "latest_verified_step": active["latest_verified_step"],
        "next_safe_step": active["next_safe_step"],
        "pending_priorities": len(state["next_priorities"]),
        "gate_check": "PASS",
        "external_mutations": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="V31 continuity guard")
    parser.add_argument("--root", default=str(
        Path(__file__).resolve().parent.parent))
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args()
    try:
        report = check_repository(Path(args.root))
        print("V31_CONTINUITY_GUARD_PASS")
        print(json.dumps(report, sort_keys=True, ensure_ascii=False))
        if args.summary and os.getenv("GITHUB_STEP_SUMMARY"):
            p = Path(os.environ["GITHUB_STEP_SUMMARY"])
            with p.open("a", encoding="utf-8") as stream:
                stream.write(
                    "## V31 — ponto de continuidade GitHub\n\n"
                    f"- Estado: **{report['status']}**; fase: "
                    f"**{report['phase']}**\n"
                    f"- Checkpoint: \`{report['checkpoint_detail']}\`\n"
                    f"- Última evidência: {report['latest_verified_step']}\n"
                    f"- Próximo passo: {report['next_safe_step']}\n"
                    "- Entrada: [V31_CONTINUAR_AQUI.md]"
                    "(../blob/main/V31_CONTINUAR_AQUI.md)\n")
        return 0
    except ContinuityGuardError as exc:
        print("V31_CONTINUITY_GUARD_FAILED_" + str(exc))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
