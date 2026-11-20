"""Public verification lets the DRAFT writer run without the review HMAC key."""

import json
import re


def _message(attestation: dict) -> bytes:
    canonical = json.dumps(attestation, sort_keys=True, ensure_ascii=False,
                           separators=(",", ":"), allow_nan=False)
    return b"v31:approved-draft:1\x00" + canonical.encode("utf-8")


def _key(raw: str) -> bytes:
    if not isinstance(raw, str) or not re.fullmatch(r"[0-9a-f]{64}", raw):
        raise ValueError("invalid_review_signing_key")
    return bytes.fromhex(raw)


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
