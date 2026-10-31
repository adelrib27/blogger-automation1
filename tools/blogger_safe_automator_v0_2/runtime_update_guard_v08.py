#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import py_compile
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO = "adelrib27/blogger-automation1"
BRANCH = "blogger-safe-ui-provisioning-v0-2"
WORKFLOW = "blogger_runtime_safe_sync_validation.yml"
STATUS = "BLOGGER_RUNTIME_SYNC_GUARD_PASS"

ALLOWED_FILES = (
    "tools/blogger_safe_automator_v0_2/runtime_update_guard_v08.py",
    "tools/blogger_safe_automator_v0_2/extend_modelo_v20_store.py",
    "tools/blogger_safe_automator_v0_2/extend_modelo_v20_store_visible_nav.py",
    "tools/blogger_safe_automator_v0_2/install_modelo_v20_adoption.py",
    "tools/blogger_safe_automator_v0_2/validate_modelo_v20_store.py",
    "tools/blogger_safe_automator_v0_2/render_modelo_v20_pages.py",
    "tools/blogger_safe_automator_v0_2/provision_new_blog_v20.py",
    "templates/blogger_modelo_v20/model_manifest.json",
    "templates/blogger_modelo_v20/pages.json",
    "themes/blogger_modelo_v20/pages.json",
)


def _get_json(url: str) -> dict:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "blogger-runtime-update-guard-v08",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def _get_bytes(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "blogger-runtime-update-guard-v08"})
    with urllib.request.urlopen(req, timeout=45) as r:
        data = r.read()
    if not data:
        raise RuntimeError(f"download vazio: {url}")
    return data


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _state_path() -> Path:
    p = Path(r"C:\Blogger-Automator\maintenance")
    p.mkdir(parents=True, exist_ok=True)
    return p / "runtime_update_guard_v08.json"


def _branch_sha() -> str:
    data = _get_json(f"https://api.github.com/repos/{REPO}/branches/{urllib.parse.quote(BRANCH, safe='')}")
    sha = str(((data.get("commit") or {}).get("sha") or "")).strip()
    if len(sha) != 40:
        raise RuntimeError("SHA do ramo oficial invalido")
    return sha


def _require_green_ci(sha: str) -> int:
    branch = urllib.parse.quote(BRANCH, safe="")
    url = f"https://api.github.com/repos/{REPO}/actions/workflows/{WORKFLOW}/runs?branch={branch}&event=push&per_page=10"
    runs = (_get_json(url).get("workflow_runs") or [])
    for run in runs:
        if str(run.get("head_sha") or "") != sha:
            continue
        if run.get("status") != "completed" or run.get("conclusion") != "success":
            raise RuntimeError(
                f"CI ainda nao esta verde para {sha}: status={run.get('status')} conclusion={run.get('conclusion')}"
            )
        return int(run.get("id") or 0)
    raise RuntimeError(f"CI do runtime nao encontrada para o commit {sha}")


def _read_state() -> dict:
    path = _state_path()
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _write_state(data: dict) -> None:
    path = _state_path()
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def _stage_files(root: Path, sha: str) -> None:
    raw = f"https://raw.githubusercontent.com/{REPO}/{sha}"
    for rel in ALLOWED_FILES:
        dst = root / Path(rel)
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(_get_bytes(f"{raw}/{rel}"))


def _validate_stage(stage_root: Path) -> None:
    tools = stage_root / "tools" / "blogger_safe_automator_v0_2"
    for rel in ALLOWED_FILES:
        p = stage_root / rel
        if not p.exists() or p.stat().st_size == 0:
            raise RuntimeError(f"arquivo permitido ausente no staging: {rel}")
        if p.suffix == ".py":
            py_compile.compile(str(p), doraise=True)
    validator = tools / "validate_modelo_v20_store.py"
    proc = subprocess.run([sys.executable, str(validator)], text=True, capture_output=True, timeout=90)
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout)[-1600:]
        raise RuntimeError("validacao V20 falhou no staging: " + detail)


def _apply(stage_root: Path, repo_root: Path) -> tuple[Path, int]:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    backup = Path(r"C:\Blogger-Automator\backups") / f"runtime-update-guard-{stamp}"
    backup.mkdir(parents=True, exist_ok=True)
    created: list[Path] = []
    backed: list[tuple[Path, Path]] = []
    try:
        for rel in ALLOWED_FILES:
            src = stage_root / rel
            dst = repo_root / rel
            if dst.exists():
                saved = backup / rel
                saved.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(dst, saved)
                backed.append((saved, dst))
            else:
                created.append(dst)

        for rel in ALLOWED_FILES:
            src = stage_root / rel
            dst = repo_root / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            tmp = dst.with_name(dst.name + ".syncing.tmp")
            shutil.copy2(src, tmp)
            os.replace(tmp, dst)

        local_validator = repo_root / "tools" / "blogger_safe_automator_v0_2" / "validate_modelo_v20_store.py"
        proc = subprocess.run([sys.executable, str(local_validator)], text=True, capture_output=True, timeout=90)
        if proc.returncode != 0:
            detail = (proc.stderr or proc.stdout)[-1600:]
            raise RuntimeError("validacao V20 falhou apos escrita: " + detail)
        return backup, len(ALLOWED_FILES)
    except Exception:
        for p in created:
            try:
                if p.exists():
                    p.unlink()
            except Exception:
                pass
        for saved, dst in backed:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(saved, dst)
        raise


def sync_v20() -> dict:
    repo_root = _repo_root()
    sha = _branch_sha()
    run_id = _require_green_ci(sha)
    state = _read_state()
    if state.get("sha") == sha and state.get("status") == STATUS:
        return {
            "status": STATUS,
            "changed": False,
            "sha": sha,
            "ci_run_id": run_id,
            "allowed_file_count": len(ALLOWED_FILES),
        }

    with tempfile.TemporaryDirectory(prefix="blogger-runtime-guard-") as td:
        stage = Path(td)
        _stage_files(stage, sha)
        _validate_stage(stage)
        backup, count = _apply(stage, repo_root)

    result = {
        "status": STATUS,
        "changed": True,
        "sha": sha,
        "ci_run_id": run_id,
        "allowed_file_count": count,
        "backup": str(backup),
        "scope": "v20-only",
        "arbitrary_command_execution": False,
    }
    _write_state(result)
    return result


def main() -> int:
    p = argparse.ArgumentParser(description="Sincroniza somente arquivos V20 permitidos apos CI verde.")
    p.add_argument("--mode", choices=("v20",), default="v20")
    p.parse_args()
    try:
        print(json.dumps(sync_v20(), ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print(json.dumps({"status": "BLOGGER_RUNTIME_SYNC_GUARD_FAIL", "error": str(exc)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
