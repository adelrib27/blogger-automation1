"""Reserve safe numeric queue IDs when editorial reuse is enabled.

Existing generated JSON files are authoritative: never allocate a new ID
that could overwrite an article, even if the current queue was reset.
No IO writes or network access.
"""
from __future__ import annotations

import json
from pathlib import Path


def highest_reserved_id(queue_path: Path, generated_dir: Path) -> int:
    queue=Path(queue_path)
    generated=Path(generated_dir)
    if queue.is_symlink() or generated.is_symlink():
        raise ValueError("queue_state_untrusted")
    current=0
    if queue.exists():
        try:
            data=json.loads(queue.read_text(encoding="utf-8"))
        except (OSError,UnicodeError,ValueError):
            raise ValueError("queue_state_unreadable") from None
        if not isinstance(data,dict) or not isinstance(data.get("items"),list):
            raise ValueError("queue_state_invalid")
        for row in data["items"]:
            if not isinstance(row,dict):
                raise ValueError("queue_row_invalid")
            try:
                n=int(row.get("id") or 0)
            except (TypeError,ValueError):
                raise ValueError("queue_row_id_invalid") from None
            if n<0 or n>999999:
                raise ValueError("queue_row_id_invalid")
            current=max(current,n)
    if not generated.exists():
        return current
    if not generated.is_dir():
        raise ValueError("generated_path_invalid")
    paths=list(generated.glob("*.json"))
    if len(paths)>12000:
        raise ValueError("generated_files_excessive")
    for f in paths:
        if f.is_symlink() or not f.is_file() or not f.stem.isdigit():
            raise ValueError("generated_file_invalid")
        n=int(f.stem)
        if not 1<=n<=999999:
            raise ValueError("generated_file_id_invalid")
        current=max(current,n)
    if current>=999999:
        raise ValueError("queue_id_capacity_exhausted")
    return current
