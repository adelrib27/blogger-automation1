import json
import math
import os
import sys
import time
from pathlib import Path

LAB_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TELEMETRY_PATH = LAB_ROOT / "data" / "architecture_lab" / "firecrawl_telemetry.json"

_EVENT_COUNTERS = {
    "CACHE_HIT": "cache_hits",
    "CACHE_MISS": "cache_misses",
    "FALLBACK_REQUIRED": "fallback_required",
    "FALLBACK_SUCCESS": "fallback_successes",
    "FALLBACK_FAILURE": "fallback_failures",
    "SEARCH_CALL": "search_calls",
    "HTTP_ATTEMPT": "http_attempts",
    "RATE_LIMIT_429": "rate_limit_429",
    "SEARCH_SUCCESS": "search_successes",
    "SEARCH_FAILURE": "search_failures",
}


def _path() -> Path:
    configured = os.getenv("VIDAPET_FIRECRAWL_TELEMETRY_PATH", "").strip()
    return Path(configured) if configured else DEFAULT_TELEMETRY_PATH


def _fresh() -> dict:
    return {
        "version": "FIRECRAWL_TELEMETRY_V1",
        "lab_only": True,
        "updated_at": None,
        "counters": {name: 0 for name in _EVENT_COUNTERS.values()},
        "credits_reported_total": 0.0,
    }


def _safe_credits(value):
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except Exception:
        return None
    if not math.isfinite(number) or number < 0:
        return None
    return number


def _load() -> dict:
    path = _path()
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return _fresh()
    if not isinstance(doc, dict):
        return _fresh()
    counters = doc.get("counters")
    if not isinstance(counters, dict):
        counters = {}
    clean = _fresh()
    clean["updated_at"] = doc.get("updated_at")
    for name in clean["counters"]:
        try:
            clean["counters"][name] = max(0, int(counters.get(name, 0)))
        except Exception:
            clean["counters"][name] = 0
    clean["credits_reported_total"] = _safe_credits(doc.get("credits_reported_total")) or 0.0
    return clean


def _write(doc: dict) -> dict:
    path = _path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)
    return doc


def reset() -> dict:
    return _write(_fresh())


def snapshot() -> dict:
    return _load()


def record(event: str, credits_used=None) -> dict:
    counter = _EVENT_COUNTERS.get(str(event or "").strip().upper())
    if not counter:
        return snapshot()
    try:
        doc = _load()
        doc["counters"][counter] += 1
        credits = _safe_credits(credits_used)
        if credits is not None:
            doc["credits_reported_total"] = round(doc["credits_reported_total"] + credits, 6)
        doc["updated_at"] = int(time.time())
        return _write(doc)
    except Exception:
        return _fresh()


def _main() -> None:
    command = (sys.argv[1] if len(sys.argv) > 1 else "snapshot").strip().lower()
    if command == "reset":
        doc = reset()
    elif command == "snapshot":
        doc = snapshot()
    else:
        raise SystemExit("usage: firecrawl_telemetry.py [reset|snapshot]")
    print(json.dumps(doc, ensure_ascii=False))


if __name__ == "__main__":
    _main()
