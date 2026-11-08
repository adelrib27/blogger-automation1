"""Bounded Firecrawl calls in Vida Pet Pratica LAB SAFE only.

The budget is per GitHub Actions job, shared by separate Python processes through
the sanitized aggregate telemetry JSON. In non-LAB runs this is a no-op wrapper
around the existing telemetry semantics.
"""
import json
import os

import firecrawl_telemetry as telemetry

COUNTERS = {"SEARCH_CALL": ("search_calls", "VIDAPET_FIRECRAWL_MAX_SEARCH_CALLS", 2),
            "HTTP_ATTEMPT": ("http_attempts", "VIDAPET_FIRECRAWL_MAX_HTTP_ATTEMPTS", 3)}


def enabled() -> bool:
    return os.getenv("VIDAPET_FIRECRAWL_BUDGET_GUARD", "") == "1"


def _limit(name: str, default: int) -> int:
    raw = os.getenv(name, str(default))
    if not raw.isdecimal() or not (1 <= int(raw) <= 20):
        raise RuntimeError("FIRECRAWL_LAB_BUDGET_POLICY_INVALID")
    return int(raw)


def _strict_snapshot() -> dict:
    """Never treat a corrupt/missing counter file as an empty budget."""
    try:
        data = json.loads(telemetry._path().read_text(encoding="utf-8"))
        if data.get("version") != "FIRECRAWL_TELEMETRY_V1" or data.get("lab_only") is not True:
            raise ValueError("invalid telemetry identity")
        counters = data["counters"]
        for field in ("search_calls", "http_attempts", "rate_limit_429"):
            value = counters[field]
            if type(value) is not int or value < 0:
                raise ValueError("invalid telemetry counter")
        return data
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        raise RuntimeError("FIRECRAWL_LAB_BUDGET_STATE_UNAVAILABLE") from exc


def claim(event: str) -> None:
    event = str(event).upper()
    if event not in COUNTERS:
        raise ValueError("unsupported budget counter")
    if not enabled():
        telemetry.record(event)
        return
    field, env_name, default = COUNTERS[event]
    limit = _limit(env_name, default)
    previous = _strict_snapshot()
    if previous["counters"]["rate_limit_429"] > 0:
        raise RuntimeError("FIRECRAWL_LAB_429_CIRCUIT_OPEN")
    before = previous["counters"][field]
    if before >= limit:
        raise RuntimeError("FIRECRAWL_LAB_CALL_BUDGET_EXHAUSTED")
    after = telemetry.record(event)
    # The telemetry module is best-effort; the budget guard is strictly fail-closed.
    if after.get("counters", {}).get(field) != before + 1:
        raise RuntimeError("FIRECRAWL_LAB_BUDGET_PERSISTENCE_FAILED")


def trip_on_429() -> None:
    """429 may mean quota exhaustion; never retry blindly in bounded LAB mode."""
    if enabled():
        raise RuntimeError("FIRECRAWL_LAB_429_CIRCUIT_OPEN")
