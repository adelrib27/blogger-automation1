"""Synthetic sites for legacy unit scenarios; NEVER production registry entries.

These fixtures replace removed Blogger routes only inside offline tests.
The 24 deleted real IDs/keys are never reintroduced in routing.py.
"""
from contextlib import ExitStack, contextmanager
from unittest.mock import patch

from affiliate_hub_v31.routing import sites as current_sites

AIR_KEY="test_blogger_air_fryers"
LIQ_KEY="test_blogger_liquidificadores"
AIR_ID="111111111111111111"
LIQ_ID="222222222222222222"


def fixture_routes():
    entries={k:dict(v) for k,v in current_sites().items()}
    entries[AIR_KEY]={
        "site_key":AIR_KEY, "platform":"blogger", "identifier":AIR_ID,
        "campaign":"airfryers", "allowed_niches":["cozinha/air_fryers"],
        "allowed_source_paths":[], "publish_enabled":False,
    }
    entries[LIQ_KEY]={
        "site_key":LIQ_KEY, "platform":"blogger", "identifier":LIQ_ID,
        "campaign":"liquidificadores", "allowed_niches":["cozinha/liquidificadores"],
        "allowed_source_paths":[], "publish_enabled":False,
    }
    return entries


@contextmanager
def synthetic_routes():
    fixtures=fixture_routes()
    paths=(
        "affiliate_hub_v31.routing.sites",
        "affiliate_hub_v31.editorial.sites",
        "affiliate_hub_v31.draft_adapter.sites",
        "affiliate_hub_v31.editorial_plan.sites",
        "affiliate_hub_v31.site_launch_plan.sites",
    )
    with ExitStack() as stack:
        for name in paths:
            stack.enter_context(patch(name,return_value=fixtures))
        yield fixtures
