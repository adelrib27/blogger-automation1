"""V31 C3.1: verificação real mínima de leitura/gravação/exclusão no R2 privado.

Não toca catálogos, snapshots, ponteiros ou dados comerciais. Falha fechada,
sem expor URLs de endpoint, headers, valores de secrets ou exceções remotas.
"""
from __future__ import annotations

import hashlib
import os

from .r2_state import R2State

EXPECTED_BUCKET = "v31-editorial-shopee"
OBJECT_PREFIX = "v31-editorial/diagnostics/"


def smoke(storage: R2State, run_id: str) -> str:
    if storage.bucket != EXPECTED_BUCKET:
        raise ValueError("unexpected_bucket")
    if not (isinstance(run_id, str) and run_id.isdecimal() and 1 <= len(run_id) <= 20):
        raise ValueError("invalid_run_id")
    object_key = f"{OBJECT_PREFIX}check-{run_id}.txt"
    # Payload sintético, não o catálogo nem dados de pessoas.
    body = b"V31_EDITORIAL_R2_SMOKE_TEST_v1\n"
    sha = hashlib.sha256(body).hexdigest()
    uploaded = False
    try:
        storage.s3.put_object(Bucket=storage.bucket, Key=object_key, Body=body,
                              ContentType="text/plain")
        uploaded = True
        returned = storage.s3.get_object(Bucket=storage.bucket, Key=object_key)
        raw = returned["Body"].read(128)
        if hashlib.sha256(raw).hexdigest() != sha or raw != body:
            raise ValueError("roundtrip_mismatch")
        return "V31_C3_R2_SMOKE_PASS"
    finally:
        if uploaded:
            storage.s3.delete_object(Bucket=storage.bucket, Key=object_key)


def main() -> int:
    try:
        storage = R2State.from_env()
        print(smoke(storage, os.environ.get("GITHUB_RUN_ID", "")))
        return 0
    except Exception:
        print("V31_C3_R2_SMOKE_FAILED")
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
