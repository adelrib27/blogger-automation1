"""C79 — Cloudflare R2 S3 conditional backend for private V31 READY envelopes.

This backend is *not* used by cron, writer, publisher, or Firecrawl.
It only implements the C78 get/put_if_absent contract. Its sole write is an
atomic PutObject If-None-Match: *; it never overwrites/deletes/list objects.

Official S3 account and bucket are fixed to the V31 editorial account. The
from_environment factory fails closed before creating a client if the account
or bucket differs. An injected client must expose the same official endpoint.
"""
from __future__ import annotations

import hashlib
import os
import re
import uuid

from .private_ready_envelope import MAX_BYTES, object_key
from .r2_state import R2State


ACCOUNT_ID = "ebb8d5b4cf9a2cb850c6d8051bd2661f"
BUCKET = "v31-editorial-shopee"
ENDPOINT = f"https://{ACCOUNT_ID}.r2.cloudflarestorage.com"
KEY_RE = re.compile(
    r"v31/private-ready/v1/([a-z0-9_]{3,50})/"
    r"([a-z0-9_-]{1,32})/([a-f0-9]{2})/([a-f0-9]{64})\.json"
)


class R2PrivateReadyError(ValueError):
    """Sanitized error; never includes endpoints, product data, or secrets."""


def _valid_key(key: str) -> None:
    if not isinstance(key, str):
        raise R2PrivateReadyError("r2_private_key_invalid")
    match = KEY_RE.fullmatch(key)
    if match is None or match.group(3) != match.group(4)[:2]:
        raise R2PrivateReadyError("r2_private_key_invalid")
    site, campaign, _, digest = match.groups()
    try:
        expected = object_key(site, campaign, digest)
    except (ValueError, KeyError, TypeError):
        raise R2PrivateReadyError("r2_private_route_invalid") from None
    if expected != key:
        raise R2PrivateReadyError("r2_private_key_invalid")


def _error_response(exc: Exception) -> tuple[str | None, int | None]:
    response = getattr(exc, "response", None)
    if not isinstance(response, dict):
        return None, None
    details = response.get("Error")
    meta = response.get("ResponseMetadata")
    code = details.get("Code") if isinstance(details, dict) else None
    status = meta.get("HTTPStatusCode") if isinstance(meta, dict) else None
    return code if isinstance(code, str) else None, status if type(status) is int else None


class R2PrivateReadyBackend:
    """Adapter supplied to ImmutablePrivateReadyEnvelope(backend=...).

    The constructor accepts R2State for explicit, already-configured clients.
    The ordinary production entrypoint is from_environment(). Neither
    constructor nor imports contact R2.
    """

    def __init__(self, storage: R2State):
        if not isinstance(storage, R2State) or storage.bucket != BUCKET:
            raise R2PrivateReadyError("r2_private_official_bucket_required")
        endpoint = getattr(getattr(storage.s3, "meta", None), "endpoint_url", None)
        if endpoint != ENDPOINT:
            raise R2PrivateReadyError("r2_private_official_account_required")
        self._s3 = storage.s3

    @classmethod
    def from_environment(cls, env=None) -> "R2PrivateReadyBackend":
        env = os.environ if env is None else env
        if (env.get("V31_EDITORIAL_R2_ACCOUNT_ID") != ACCOUNT_ID
                or env.get("V31_EDITORIAL_R2_BUCKET") != BUCKET):
            raise R2PrivateReadyError("r2_private_account_bucket_mismatch")
        try:
            return cls(R2State.from_env(env))
        except R2PrivateReadyError:
            raise
        except Exception:
            raise R2PrivateReadyError("r2_private_credentials_unavailable") from None

    def put_if_absent(self, key: str, blob: bytes) -> bool:
        _valid_key(key)
        if not isinstance(blob, bytes) or not 1 <= len(blob) <= MAX_BYTES:
            raise R2PrivateReadyError("r2_private_payload_invalid")
        digest = hashlib.sha256(blob).hexdigest()
        try:
            self._s3.put_object(
                Bucket=BUCKET, Key=key, Body=blob,
                IfNoneMatch="*",
                ContentType="application/json; charset=utf-8",
                CacheControl="private, no-store",
                Metadata={"v31sha256": digest, "writeid": uuid.uuid4().hex},
            )
        except Exception as exc:
            code, status = _error_response(exc)
            if code == "PreconditionFailed" and status == 412:
                return False
            # 409 ObjectLocked, 403 authorization, 5xx or ambiguous transport
            # failures are NOT treated as success, absence or collisions.
            raise R2PrivateReadyError("r2_private_conditional_write_failed") from None
        return True

    def get(self, key: str) -> bytes | None:
        _valid_key(key)
        try:
            result = self._s3.get_object(Bucket=BUCKET, Key=key)
        except Exception as exc:
            code, status = _error_response(exc)
            if status == 404 and code in ("NoSuchKey", "404"):
                return None
            raise R2PrivateReadyError("r2_private_get_failed_closed") from None
        if not isinstance(result, dict):
            raise R2PrivateReadyError("r2_private_untrusted_response")
        size = result.get("ContentLength")
        meta = result.get("Metadata")
        stream = result.get("Body")
        if (type(size) is not int or not 1 <= size <= MAX_BYTES
                or not isinstance(meta, dict)
                or not isinstance(meta.get("v31sha256"), str)
                or not re.fullmatch(r"[a-f0-9]{64}", meta["v31sha256"])
                or not callable(getattr(stream, "read", None))):
            close = getattr(stream, "close", None)
            if callable(close):
                close()
            raise R2PrivateReadyError("r2_private_untrusted_response")
        try:
            body = stream.read(MAX_BYTES + 1)
        except Exception:
            raise R2PrivateReadyError("r2_private_body_read_failed") from None
        finally:
            close = getattr(stream, "close", None)
            if callable(close):
                close()
        if (not isinstance(body, bytes) or len(body) != size
                or hashlib.sha256(body).hexdigest() != meta["v31sha256"]):
            raise R2PrivateReadyError("r2_private_hash_readback_mismatch")
        return body
