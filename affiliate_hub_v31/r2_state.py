"""Snapshots privados do catálogo no Cloudflare R2 (S3 compatível).

R2 guarda SQLite e o ponteiro CURRENT; GitHub Actions deve ser o ÚNICO writer,
com concurrency group compartilhado por ingestão/conversão. Falhar fechado
se houver corrupção, credenciais ausentes ou bucket inesperado.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

PREFIX = "v31-editorial"
POINTER = PREFIX + "/CURRENT.json"
# O histórico já ocupa ~1.053 GB; ampliar cap com verificação SHA/integridade
# permite crescimento cumulativo dos feeds sem anexar o índice universal.
# A indexação de facetas é um arquivo R2 separado, não eleva este limite.
MAX_STATE_BYTES = 2 * 1024 * 1024 * 1024
SNAPSHOT_RE = re.compile(r"v31-editorial/snapshots/\d{8}T\d{6}Z-[0-9a-f]{16}\.sqlite3")


class StorageError(RuntimeError):
    """Mensagens curtas que nunca incluem bucket, IDs, chaves ou respostas remotas."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_database(path: Path):
    if not path.is_file() or path.stat().st_size > MAX_STATE_BYTES:
        raise StorageError("invalid_local_state")
    try:
        uri = path.resolve().as_uri() + "?mode=ro"
        with closing(sqlite3.connect(uri, uri=True)) as db:
            if db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise StorageError("sqlite_corruption")
    except sqlite3.DatabaseError:
        raise StorageError("sqlite_corruption") from None


def validate_manifest(data: dict):
    if not isinstance(data, dict) or set(data) != {"schema", "key", "sha256", "created_utc"}:
        raise StorageError("invalid_manifest")
    if data["schema"] != "v31-editorial-state/v1":
        raise StorageError("invalid_manifest_schema")
    if not isinstance(data["key"], str) or not SNAPSHOT_RE.fullmatch(data["key"]):
        raise StorageError("invalid_object_key")
    if not isinstance(data["sha256"], str) or not re.fullmatch(r"[a-f0-9]{64}", data["sha256"]):
        raise StorageError("invalid_hash")
    if not isinstance(data["created_utc"], str) or len(data["created_utc"]) > 40:
        raise StorageError("invalid_date")


class R2State:
    def __init__(self, client, bucket: str):
        if not isinstance(bucket, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,61}[a-z0-9]", bucket):
            raise ValueError("Nome de bucket inválido")
        self.s3 = client
        self.bucket = bucket

    @classmethod
    def from_env(cls, env=None):
        env = os.environ if env is None else env
        names = [
            "V31_EDITORIAL_R2_ACCOUNT_ID",
            "V31_EDITORIAL_R2_BUCKET",
            "V31_EDITORIAL_R2_ACCESS_KEY_ID",
            "V31_EDITORIAL_R2_SECRET_ACCESS_KEY",
        ]
        vals = [str(env.get(n, "")).strip() for n in names]
        if any(not x for x in vals) or not re.fullmatch(r"[a-f0-9]{32}", vals[0]):
            raise StorageError("storage_credentials_missing_or_invalid")
        try:
            import boto3
            from botocore.config import Config
        except ImportError:
            raise StorageError("boto3_not_installed") from None
        client = boto3.client(
            "s3",
            endpoint_url=f"https://{vals[0]}.r2.cloudflarestorage.com",
            aws_access_key_id=vals[2],
            aws_secret_access_key=vals[3],
            region_name="auto",
            config=Config(signature_version="s3v4", s3={"addressing_style": "path"},
                          retries={"max_attempts": 2, "mode": "standard"}),
        )
        return cls(client, vals[1])

    def _read_manifest(self):
        try:
            result = self.s3.get_object(Bucket=self.bucket, Key=POINTER)
        except Exception as exc:
            error_code = getattr(exc, "response", {}).get("Error", {}).get("Code")
            if error_code in ("NoSuchKey", "404"):
                return None
            raise StorageError("r2_pointer_read_failed") from None
        try:
            raw = result["Body"].read(4097)
            if len(raw) > 4096:
                raise StorageError("manifest_too_large")
            data = json.loads(raw)
            validate_manifest(data)
            return data
        except (KeyError, ValueError, TypeError):
            raise StorageError("invalid_manifest") from None

    def restore_to(self, path: Path | str) -> bool:
        destination = Path(path)
        if destination.exists() or destination.is_symlink():
            raise StorageError("restore_target_already_exists")
        manifest = self._read_manifest()
        if manifest is None:
            return False
        destination.parent.mkdir(parents=True, exist_ok=True)
        try:
            self.s3.download_file(self.bucket, manifest["key"], str(destination))
        except Exception:
            destination.unlink(missing_ok=True)
            raise StorageError("r2_snapshot_download_failed") from None
        try:
            if sha256_file(destination) != manifest["sha256"]:
                raise StorageError("snapshot_sha256_mismatch")
            verify_database(destination)
            if os.name == "posix":
                os.chmod(destination, 0o600)
        except Exception:
            destination.unlink(missing_ok=True)
            raise
        return True

    def _prune_old_snapshots(self, keep: set[str]) -> int:
        """Retenção limitada a estado atual + estado anterior.

        Só remove snapshots conhecidos sob este prefixo. Nunca remove CURRENT.json
        nem objetos de outra aplicação. Um erro de limpeza não apaga o estado atual.
        """
        prefix = PREFIX + "/snapshots/"
        scanned = 0
        obsolete = []
        token = None
        for _ in range(100):
            options = {"Bucket": self.bucket, "Prefix": prefix, "MaxKeys": 1000}
            if token:
                options["ContinuationToken"] = token
            result = self.s3.list_objects_v2(**options)
            objects = result.get("Contents", [])
            scanned += len(objects)
            if scanned > 100000:
                raise StorageError("retention_list_limit")
            for obj in objects:
                key = obj.get("Key")
                if isinstance(key, str) and SNAPSHOT_RE.fullmatch(key) and key not in keep:
                    obsolete.append(key)
            if not result.get("IsTruncated"):
                break
            new_token = result.get("NextContinuationToken")
            if not new_token or new_token == token:
                raise StorageError("retention_pagination_failed")
            token = new_token
        else:
            raise StorageError("retention_list_limit")
        for key in obsolete:
            self.s3.delete_object(Bucket=self.bucket, Key=key)
        return len(obsolete)

    def save_from(self, path: Path | str) -> dict:
        source = Path(path)
        verify_database(source)
        prior = self._read_manifest()
        sha = sha256_file(source)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        key = f"{PREFIX}/snapshots/{timestamp}-{sha[:16]}.sqlite3"
        if not SNAPSHOT_RE.fullmatch(key):
            raise StorageError("invalid_object_key")
        try:
            self.s3.upload_file(str(source), self.bucket, key,
                                ExtraArgs={"Metadata": {"sha256": sha}})
            head = self.s3.head_object(Bucket=self.bucket, Key=key)
            if head.get("Metadata", {}).get("sha256") != sha:
                raise StorageError("r2_snapshot_verification_failed")
        except StorageError:
            raise
        except Exception:
            raise StorageError("r2_snapshot_upload_failed") from None
        pointer = {"schema": "v31-editorial-state/v1", "key": key,
                   "sha256": sha, "created_utc": datetime.now(timezone.utc).isoformat()}
        try:
            self.s3.put_object(Bucket=self.bucket, Key=POINTER,
                               Body=json.dumps(pointer, separators=(",", ":")).encode(),
                               ContentType="application/json",
                               CacheControl="no-store")
        except Exception:
            raise StorageError("r2_pointer_update_failed") from None
        # O ponteiro novo já é durável. Falha de limpeza é relatada, não
        # apaga o estado; monitorar retenção para impedir custos cumulativos.
        keep = {key}
        if prior:
            keep.add(prior["key"])
        try:
            cleaned = self._prune_old_snapshots(keep)
            pending = False
        except Exception:
            cleaned = 0
            pending = True
        return {"snapshot_sha256": sha, "state_saved": True,
                "retention_deleted": cleaned, "retention_pending": pending}
