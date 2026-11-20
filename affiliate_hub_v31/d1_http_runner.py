"""C75 — Cloudflare D1 HTTPS query runner for the dedicated V31 SAFE database.

This module has NO side effects on import. It is NOT wired into any writer,
scheduler or publisher. Writes require two independent explicit switches.
Products, campaigns and tenant validation remain in d1_universal_ready.py;
this transport never authorizes evidence, posts or LIVE publication.

Only the official V31 R2 account and its separate D1 database can be addressed.
No configurable host, redirects, SQL logging or authentication fallback.
"""
from __future__ import annotations

import json
import os
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

# Non-secret resource identifiers, independently verified at C74.
OFFICIAL_ACCOUNT_ID = "ebb8d5b4cf9a2cb850c6d8051bd2661f"
OFFICIAL_DATABASE_ID = "9bfce7a4-6167-4bfc-a65e-a74c1a34f064"
D1_ENDPOINT = (
    "https://api.cloudflare.com/client/v4/accounts/"
    + OFFICIAL_ACCOUNT_ID + "/d1/database/" + OFFICIAL_DATABASE_ID + "/query"
)
WRITE_CONFIRMATION = "V31_D1_SAFE_SQL_ONLY"
WRITE_KINDS = frozenset({"INSERT", "UPDATE", "DELETE"})
MAX_SQL_BYTES = 20_000
MAX_REQUEST_BYTES = 262_144
MAX_RESPONSE_BYTES = 1_048_576
MAX_ROWS = 10_000
MAX_PARAMS = 64


class D1HTTPError(ValueError):
    """Fail closed; exception messages never include token, SQL or row values."""


class CloudflareD1HTTPRunner:
    """Callable (sql, tuple(params)) -> list[dict] for UniversalD1ReadyState.

    By default only a single SELECT statement can be sent.
    To allow metadata writes, constructor allow_mutations=True AND runtime
    V31_D1_SAFE_WRITES_ENABLED=V31_D1_SAFE_SQL_ONLY are BOTH mandatory.
    No CMS privileges are used and this is not a LIVE publishing permission.
    """

    def __init__(
        self, *,
        token: str,
        account_id: str,
        database_id: str,
        allow_mutations: bool = False,
        timeout_seconds: int = 15,
    ) -> None:
        if account_id != OFFICIAL_ACCOUNT_ID or database_id != OFFICIAL_DATABASE_ID:
            raise D1HTTPError("d1_official_resource_mismatch")
        if not isinstance(token, str) or not re.fullmatch(r"[^\s]{20,512}", token):
            raise D1HTTPError("d1_token_missing_or_invalid")
        if type(allow_mutations) is not bool:
            raise D1HTTPError("d1_mutation_flag_invalid")
        if type(timeout_seconds) is not int or not 1 <= timeout_seconds <= 30:
            raise D1HTTPError("d1_timeout_policy_invalid")
        self._token = token
        self._allow_mutations = allow_mutations
        self._timeout_seconds = timeout_seconds

    @classmethod
    def from_environment(cls, *, allow_mutations: bool = False) -> "CloudflareD1HTTPRunner":
        """Require explicit resource IDs; never guess from other Cloudflare accounts."""
        return cls(
            token=os.environ.get("V31_D1_API_TOKEN", ""),
            account_id=os.environ.get("V31_D1_ACCOUNT_ID", ""),
            database_id=os.environ.get("V31_D1_DATABASE_ID", ""),
            allow_mutations=allow_mutations,
        )

    def __call__(self, sql: str, params: tuple) -> list[dict]:
        if not isinstance(sql, str) or not sql.strip():
            raise D1HTTPError("d1_sql_invalid")
        if len(sql.encode("utf-8")) > MAX_SQL_BYTES:
            raise D1HTTPError("d1_sql_too_large")
        # SQL comes from the trusted state module, never an AI or user response.
        # Disallow batch statements, inline comments and unsafe SQL kinds.
        statement = sql.strip()
        if (";" in statement or "--" in statement or "/*" in statement
                or "*/" in statement):
            raise D1HTTPError("d1_sql_batch_or_comment_denied")
        kind_match = re.match(r"([A-Za-z]+)\b", statement)
        kind = kind_match.group(1).upper() if kind_match else ""
        if kind not in {"SELECT", *WRITE_KINDS}:
            raise D1HTTPError("d1_sql_kind_denied")
        if kind in WRITE_KINDS and not (
            self._allow_mutations is True and
            os.environ.get("V31_D1_SAFE_WRITES_ENABLED") == WRITE_CONFIRMATION
        ):
            raise D1HTTPError("d1_metadata_write_disabled")

        if not isinstance(params, tuple) or len(params) > MAX_PARAMS:
            raise D1HTTPError("d1_parameters_invalid")
        for value in params:
            if type(value) not in (str, int, float, type(None)):
                raise D1HTTPError("d1_parameter_type_invalid")
            if isinstance(value, str) and len(value.encode("utf-8")) > 120_000:
                raise D1HTTPError("d1_parameter_too_large")
        try:
            data = json.dumps(
                {"sql": statement, "params": list(params)},
                ensure_ascii=False, allow_nan=False, separators=(",", ":"),
            ).encode("utf-8")
        except (TypeError, ValueError, OverflowError) as exc:
            raise D1HTTPError("d1_parameters_invalid") from None
        if len(data) > MAX_REQUEST_BYTES:
            raise D1HTTPError("d1_request_too_large")

        request = Request(
            D1_ENDPOINT,
            data=data,
            headers={
                "Authorization": "Bearer " + self._token,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )
        try:
            # urllib's redirect handling is disabled below: a token must NEVER
            # be forwarded from Cloudflare's pinned endpoint to another host.
            opener = _no_redirect_opener()
            with opener.open(request, timeout=self._timeout_seconds) as response:
                if response.status != 200:
                    raise D1HTTPError("d1_http_status_invalid")
                raw = response.read(MAX_RESPONSE_BYTES + 1)
        except D1HTTPError:
            raise
        except (HTTPError, URLError, TimeoutError, OSError, ValueError):
            raise D1HTTPError("d1_http_request_failed_closed") from None
        if len(raw) > MAX_RESPONSE_BYTES:
            raise D1HTTPError("d1_response_too_large")
        try:
            document = json.loads(raw)
        except (ValueError, UnicodeDecodeError):
            raise D1HTTPError("d1_response_not_json") from None
        if (not isinstance(document, dict) or document.get("success") is not True
                or not isinstance(document.get("result"), list)
                or len(document["result"]) != 1):
            raise D1HTTPError("d1_api_envelope_invalid")
        item = document["result"][0]
        if not isinstance(item, dict) or item.get("success") is not True:
            raise D1HTTPError("d1_statement_failed_closed")
        rows = item.get("results")
        if (not isinstance(rows, list) or len(rows) > MAX_ROWS
                or not all(isinstance(row, dict) for row in rows)):
            raise D1HTTPError("d1_statement_rows_invalid")
        return rows


def _no_redirect_opener():
    """Construct fresh transport; no redirect, proxy URL or alternate endpoint."""
    from urllib.request import HTTPRedirectHandler, build_opener

    class DenyRedirect(HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            raise D1HTTPError("d1_redirect_denied")

    return build_opener(DenyRedirect)
