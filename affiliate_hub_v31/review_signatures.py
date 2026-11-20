"""Public verification lets the DRAFT writer run without the review HMAC key."""

import hashlib
import hmac
import json
import re


def _canonical(value: dict) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def payload_digest(payload: dict) -> str:
    return hashlib.sha256(_canonical(payload)).hexdigest()


def approval_receipt(*, candidate_sha256: str, payload_sha256: str, key: bytes) -> dict:
    for digest in (candidate_sha256, payload_sha256):
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError("review_receipt_digest_invalid")
    if not isinstance(key, bytes) or len(key) < 32:
        raise ValueError("review_receipt_hmac_key_invalid")
    receipt = {"candidate_sha256": candidate_sha256, "payload_sha256": payload_sha256}
    signature = hmac.new(key, b"v31:review-receipt:1\x00" + _canonical(receipt),
                         hashlib.sha256).hexdigest()
    return {**receipt, "signature": signature}


def _message(attestation: dict) -> bytes:
    if set(attestation) == {"payload", "candidate_sha256", "signature"}:
        attestation = {"payload_sha256": payload_digest(attestation["payload"]),
                       "candidate_sha256": attestation["candidate_sha256"],
                       "signature": attestation["signature"]}
    return b"v31:approved-draft:1\x00" + _canonical(attestation)


def verify_public_attestation(payload: dict, *, attestation: dict, signature: str,
                              public_key: str, require_receipt: bool = False) -> None:
    fields = {"payload", "signature"}
    if require_receipt or "candidate_sha256" in attestation:
        fields.add("candidate_sha256")
        if not re.fullmatch(r"[0-9a-f]{64}", str(attestation.get("candidate_sha256", ""))):
            raise ValueError("review_receipt_candidate_invalid")
    if (set(attestation) != fields or attestation["payload"] != payload
            or not re.fullmatch(r"[0-9a-f]{64}", str(attestation["signature"]))):
        raise ValueError("public_review_attestation_invalid")
    verify_release(attestation, signature=signature, public_key=public_key)


def _key(raw: str) -> bytes:
    if not isinstance(raw, str) or not re.fullmatch(r"[0-9a-f]{64}", raw):
        raise ValueError("invalid_review_signing_key")
    return bytes.fromhex(raw)


def configured_signing_keys(*, private_key: str, receipt_key: str) -> tuple[str, bytes, str]:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    seed, hmac_key = _key(private_key), _key(receipt_key)
    if hmac.compare_digest(seed, hmac_key):
        raise ValueError("review_signing_keys_must_be_distinct")
    public = Ed25519PrivateKey.from_private_bytes(seed).public_key().public_bytes_raw().hex()
    return private_key, hmac_key, public


def sign_release(attestation: dict, *, private_key: str) -> str:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    return Ed25519PrivateKey.from_private_bytes(_key(private_key)).sign(
        _message(attestation)).hex()


def verify_release(attestation: dict, *, signature: str, public_key: str) -> None:
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

    if not isinstance(signature, str) or not re.fullmatch(r"[0-9a-f]{128}", signature):
        raise ValueError("invalid_review_release_signature")
    try:
        Ed25519PublicKey.from_public_bytes(_key(public_key)).verify(
            bytes.fromhex(signature), _message(attestation))
    except InvalidSignature:
        raise ValueError("invalid_review_release_signature") from None
