#!/usr/bin/env python3
"""Read-only SHA audit of five R28 bootstrap-protected files.

Never starts or stops a process, touches secrets, downloads data or writes files.
Run against a locally inspected R28 bootstrap. The executed scheduled task
must be independently confirmed, as this tool cannot verify task wiring.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

MODULES = (
    ("Runner", "RunnerHash", "local_service_v08.py"),
    ("Installer", "InstallerHash", "apply_universal_v31.py"),
    ("MasterPolicy", "PolicyHash", "v31_master_policy.py"),
    ("MasterAcceptance", "AcceptanceHash", "v31_master_acceptance.py"),
    ("MasterRegistry", "RegistryHash", "v31_master_approved_labs.json"),
)
DEFAULT_ROOT = Path(r"C:\Blogger-Automator\blogger_safe_automator_v0_3")
REL_TOOLS = Path("tools") / "blogger_safe_automator_v0_2"
BOOTSTRAP = REL_TOOLS / "windows_autostart_v08" / "start_blogger_automation_v08.ps1"
SCHEMA = "blogger-v31-r28-bootstrap-integrity-readonly/v1"


class AuditBlocked(Exception):
    """The bootstrap shape is unexpected. Never guess which files it verifies."""


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _single(pattern: str, script: str, code: str) -> str:
    matches = re.findall(pattern, script, flags=re.MULTILINE | re.IGNORECASE)
    if len(matches) != 1:
        raise AuditBlocked(code)
    return matches[0]


def audit(root: Path, bootstrap: Path | None = None) -> dict:
    root = root.resolve()
    tools = root / REL_TOOLS
    script_candidate = bootstrap or root / BOOTSTRAP
    if script_candidate.is_symlink():
        raise AuditBlocked("BOOTSTRAP_MISSING_OR_SYMLINK")
    script_path = script_candidate.resolve()
    if script_path != (root / BOOTSTRAP).resolve():
        raise AuditBlocked("BOOTSTRAP_PATH_NOT_APPROVED")
    if not script_path.is_file():
        raise AuditBlocked("BOOTSTRAP_MISSING_OR_SYMLINK")
    script = script_path.read_text(encoding="utf-8-sig")
    if len(script) > 100_000:
        raise AuditBlocked("BOOTSTRAP_TOO_LARGE")

    records = []
    for variable, digest_var, filename in MODULES:
        target_pattern = (
            r"^\s*\$" + variable + r"\s*=\s*Join-Path\s+\$Tools\s+['\"]" +
            re.escape(filename) + r"['\"]\s*$"
        )
        _single(target_pattern, script, "UNRECOGNIZED_TARGET_" + variable)
        digest_pattern = (
            r"^\s*\$" + digest_var + r"\s*=\s*['\"]([0-9a-f]{64})['\"]\s*$"
        )
        expected = _single(digest_pattern, script, "UNRECOGNIZED_HASH_" + digest_var).lower()
        target = tools / filename
        if target.is_symlink():
            status, actual = "SYMLINK_DENIED", None
        elif not target.is_file():
            status, actual = "MISSING", None
        else:
            actual = sha256_file(target)
            status = "OK" if actual == expected else "DIVERGENT"
        records.append({"file": filename, "status": status,
                        "sha256_expected": expected, "sha256_actual": actual})
    all_ok = all(x["status"] == "OK" for x in records)
    return {"schema": SCHEMA,
            "status": "BOOTSTRAP_INTEGRITY_OK" if all_ok else "BOOTSTRAP_INTEGRITY_BLOCKED",
            "bootstrap_sha256": sha256_file(script_path), "files": records,
            "blogger_writes": False, "local_files_modified": False,
            "token_read": False, "runner_started": False,
            "task_scheduler_wiring_verified": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(DEFAULT_ROOT))
    args = parser.parse_args()
    try:
        result = audit(Path(args.root))
    except (AuditBlocked, OSError, UnicodeError, ValueError) as error:
        result = {"schema": SCHEMA, "status": "BOOTSTRAP_AUDIT_FAIL_CLOSED",
                  "reason": str(error) if isinstance(error, AuditBlocked) else type(error).__name__,
                  "blogger_writes": False, "local_files_modified": False,
                  "token_read": False, "runner_started": False}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "BOOTSTRAP_INTEGRITY_OK" else 2


if __name__ == "__main__":
    raise SystemExit(main())
