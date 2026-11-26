"""Declarative interval shared by the verifier and the atomic draft claim."""
import re


def draft_interval_seconds(profile: dict) -> int:
    interval = profile.get("draft_interval")
    if interval is None:
        return 0
    match = re.fullmatch(r"([1-9][0-9]{0,7})(m|h)", interval) if isinstance(interval, str) else None
    if not match:
        raise ValueError("draft_interval_invalid")
    quantity, unit = match.groups()
    seconds = int(quantity) * (60 if unit == "m" else 3600)
    if seconds > 2_147_483_647:
        raise ValueError("draft_interval_invalid")
    return seconds
