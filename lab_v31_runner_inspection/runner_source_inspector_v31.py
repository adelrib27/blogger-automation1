"""LAB candidate: authenticated, allowlisted, read-only source inspection for V31.

The module has no network listener, makes no write, and never performs shell
execution. It must be mounted behind the existing Runner authentication layer.
Do NOT expose arbitrary path reads or attach it without a reviewed release.
"""
from __future__ import annotations

import ast
import hashlib
import re
from pathlib import Path
from typing import Any

SCHEMA = "v31-source-inspection/v1"
READ_CONFIRMATION = "READ V31 SOURCE"
MAX_SOURCE_BYTES = 128 * 1024
MAX_SOURCE_FILES = 80

# Exact-name allowlist. Extend only by reviewed, tested changes.
ALLOWED_SOURCES = frozenset({
    "active_blogger_page.py", "blogger_panel_route_guard.py",
    "browser_provision.py", "browser_provision_v03.py",
    "browser_resilience_v06.py", "blogger_session_guard.py",
    "configure_core_settings.py", "install_modelo_v31_adoption.py",
    "local_service.py", "local_service_v05.py", "local_service_v06.py",
    "local_service_v07.py", "local_service_v08.py", "local_service_v31.py",
    "normalize_blogger_backup_v08.py", "provision_new_blog_v31.py",
    "render_modelo_v31_theme.py", "resilient_create.py",
    "runtime_update_guard_v08.py", "run_with_cdp_resilience_v08.py",
    "settings_dialog_guard.py", "settings_profile.py",
    "test_browser_provision.py", "test_local_service.py",
    "test_resilient_create.py", "v31_handoff_safe.py",
    "v31_master_acceptance.py", "v31_master_policy.py",
    "validate_address_step.py", "validate_core_settings_profile.py",
    "validate_create_dialog.py", "validate_new_blog_activation.py",
    "validate_title_step.py", "_v31_native_ui_functions.py",
})

# Defensive content checks. This is not a substitute for manual source review.
SENSITIVE_LITERAL = re.compile(
    r"(?i)(?:^|\W)(?:gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,}|"
    r"sk-[A-Za-z0-9_-]{20,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|"
    r"AKIA[A-Z0-9]{16})"
)
CREDENTIAL_VARIABLE = re.compile(
    r"(?i)(?:^|_)(?:secret|password|passwd|api_key|access_key|private_key|"
    r"refresh_token|access_token|auth_token|client_secret|cookie)(?:$|_)"
)
EMAIL_ADDRESS = re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")


class InspectionDenied(RuntimeError):
    """Safe reason code only; never include a local path or source content."""


def _allowed_file(tool_dir: Path, name: str) -> Path:
    if type(name) is not str or name not in ALLOWED_SOURCES:
        raise InspectionDenied("SOURCE_NOT_ALLOWLISTED")
    root = tool_dir.resolve(strict=True)
    candidate = tool_dir / name
    if candidate.is_symlink():
        raise InspectionDenied("SYMLINK_NOT_ALLOWED")
    try:
        path = candidate.resolve(strict=True)
    except OSError as exc:
        raise InspectionDenied("SOURCE_UNAVAILABLE") from exc
    if path.parent != root or not path.is_file():
        raise InspectionDenied("INVALID_SOURCE_PATH")
    return path


def _bytes(path: Path) -> bytes:
    # Only source files <=128KiB; do not follow newly substituted symlinks.
    if path.is_symlink():
        raise InspectionDenied("SYMLINK_NOT_ALLOWED")
    try:
        if path.stat().st_size > MAX_SOURCE_BYTES:
            raise InspectionDenied("SOURCE_TOO_LARGE")
        with path.open("rb") as stream:
            raw = stream.read(MAX_SOURCE_BYTES + 1)
    except OSError as exc:
        raise InspectionDenied("SOURCE_UNAVAILABLE") from exc
    if len(raw) > MAX_SOURCE_BYTES:
        raise InspectionDenied("SOURCE_TOO_LARGE")
    return raw


def _secret_scan(text: str) -> None:
    if SENSITIVE_LITERAL.search(text):
        raise InspectionDenied("SENSITIVE_LITERAL_POSSIBLE")
    if EMAIL_ADDRESS.search(text):
        raise InspectionDenied("PERSONAL_DATA_POSSIBLE")
    try:
        parsed = ast.parse(text)
    except SyntaxError as exc:
        raise InspectionDenied("SOURCE_SYNTAX_INVALID") from exc
    for node in ast.walk(parsed):
        targets: list[str] = []
        if isinstance(node, ast.Assign):
            targets = [x.id for x in node.targets if isinstance(x, ast.Name)]
            value = node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            targets = [node.target.id]
            value = node.value
        else:
            continue
        if not targets or not isinstance(value, ast.Constant) or not isinstance(value.value, str):
            continue
        name = targets[0].lower()
        value_str = value.value
        # Treat an environment variable *name* as metadata, not a credential.
        if name.endswith("_env") and re.fullmatch(r"[A-Z][A-Z0-9_]+", value_str):
            continue
        if any(CREDENTIAL_VARIABLE.search(target) for target in targets) and len(value_str) >= 12:
            raise InspectionDenied("POSSIBLE_HARDCODED_CREDENTIAL")


def manifest(tool_dir: Path) -> dict[str, Any]:
    """Only names, file byte counts and digests; no paths or file contents."""
    items = []
    for name in sorted(ALLOWED_SOURCES):
        try:
            path = _allowed_file(tool_dir, name)
            raw = _bytes(path)
            status = "PRESENT"
            size = len(raw)
            digest = hashlib.sha256(raw).hexdigest()
        except InspectionDenied as exc:
            status = str(exc)
            size = None
            digest = None
        items.append({"name": name, "status": status, "bytes": size, "sha256": digest})
    if len(items) > MAX_SOURCE_FILES:
        raise InspectionDenied("TOO_MANY_ALLOWED_SOURCES")
    return {"schema": SCHEMA, "mode": "READ_ONLY", "files": items,
            "secrets_included": False, "execution_enabled": False}


def read_source(tool_dir: Path, *, name: str, expected_sha256: str, confirm: str) -> dict[str, Any]:
    """Return one allowlisted Python source, only when SHA matches and scan accepts."""
    if confirm != READ_CONFIRMATION:
        raise InspectionDenied("READ_CONFIRMATION_REQUIRED")
    if type(expected_sha256) is not str or not re.fullmatch(r"[0-9a-fA-F]{64}", expected_sha256):
        raise InspectionDenied("INVALID_SHA256")
    path = _allowed_file(tool_dir, name)
    raw = _bytes(path)
    sha = hashlib.sha256(raw).hexdigest()
    if sha != expected_sha256.lower():
        raise InspectionDenied("SOURCE_CHANGED_RECHECK_MANIFEST")
    try:
        content = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise InspectionDenied("SOURCE_NOT_UTF8") from exc
    _secret_scan(content)
    return {"schema": SCHEMA, "mode": "READ_ONLY", "name": name,
            "sha256": sha, "content": content, "production_writes": False}
