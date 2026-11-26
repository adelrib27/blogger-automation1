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


def draft_window_status(*, state, route: dict, profile: dict, now_epoch: int) -> str:
    """Inspect a configurable site's dispatch window without restoring R2."""
    interval = draft_interval_seconds(profile)
    if not interval:
        return "DUE"
    tenant = {"site_key": route["site_key"], "campaign": route["campaign"]}
    daily_cap = profile["max_drafts_per_day"]
    if daily_cap is not None and state.count_draft_attempts_today(**tenant, now_epoch=now_epoch) >= daily_cap:
        return "DAILY_CAP"
    latest = state.latest_draft_attempt(**tenant)
    if latest is not None and now_epoch < latest + interval:
        return "WAITING_INTERVAL"
    if state.list_fresh_ready(**tenant, now_epoch=now_epoch):
        return "DUE"
    if not state.has_research_capacity(
            **tenant, now_epoch=now_epoch, daily_cap=profile["daily_research_attempts"]):
        return "RESEARCH_BUDGET"
    return "DUE"
