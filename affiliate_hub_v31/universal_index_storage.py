"""R2 privado separado para inventário de facetas, sem aumentar o catálogo principal.

Não altera v31-editorial/CURRENT.json nem snapshots da biblioteca comercial.
O sidecar é somente índice/revisão: qualquer permissão de conversão continua
sendo verificada contra a fonte principal e os gates existentes.
"""
from __future__ import annotations

import json
import re
from datetime import datetime,timezone
from pathlib import Path
from contextlib import closing

from .r2_state import R2State, StorageError, sha256_file, verify_database

POINTER="v31-editorial/UNIVERSAL_INDEX_CURRENT.json"
PREFIX="v31-editorial/universal-index/snapshots/"
KEY_RE=re.compile(
    r"v31-editorial/universal-index/snapshots/\d{8}T\d{6}Z-[a-f0-9]{16}\.sqlite3"
)
SCHEMA="v31-universal-index/v1"


def validate_manifest(data:dict)->None:
    if not isinstance(data,dict) or set(data)!={
        "schema","key","sha256","created_utc","product_count"}:
        raise StorageError("universal_index_manifest_invalid")
    if data["schema"]!=SCHEMA or not isinstance(data["key"],str) or \
        not KEY_RE.fullmatch(data["key"]) or \
        not isinstance(data["sha256"],str) or \
        not re.fullmatch(r"[a-f0-9]{64}",data["sha256"]) or \
        type(data["product_count"]) is not int or \
        not 1<=data["product_count"]<=10_000_000 or \
        not isinstance(data["created_utc"],str) or len(data["created_utc"])>40:
        raise StorageError("universal_index_manifest_invalid")


class UniversalIndexStorage:
    def __init__(self,r2:R2State):
        self.s3=r2.s3
        self.bucket=r2.bucket

    @classmethod
    def from_env(cls):
        return cls(R2State.from_env())

    def _manifest(self):
        try:
            result=self.s3.get_object(Bucket=self.bucket,Key=POINTER)
        except Exception as exc:
            code=getattr(exc,"response",{}).get("Error",{}).get("Code")
            if code in ("NoSuchKey","404"):
                return None
            raise StorageError("universal_index_pointer_read_failed") from None
        try:
            raw=result["Body"].read(4097)
            if len(raw)>4096:
                raise StorageError("universal_index_manifest_too_large")
            data=json.loads(raw)
            validate_manifest(data)
            return data
        except (KeyError,ValueError,TypeError):
            raise StorageError("universal_index_manifest_invalid") from None

    def restore_to(self,path:Path|str,*,expected_product_count:int|None=None,
                   expected_review_hint_count:int|None=None)->bool:
        # Contagem opcional: snapshots anteriores ao C46 não tinham pistas.
        if (expected_review_hint_count is not None and
            (type(expected_review_hint_count)is not int or
             expected_review_hint_count<0)):
            raise StorageError("universal_index_hint_count_invalid")
        file=Path(path)
        if file.exists() or file.is_symlink():
            raise StorageError("universal_index_destination_exists")
        meta=self._manifest()
        if meta is None:
            return False
        if expected_product_count is not None and \
           meta["product_count"]!=expected_product_count:
            raise StorageError("universal_index_stale_product_count")
        file.parent.mkdir(parents=True,exist_ok=True)
        try:
            self.s3.download_file(self.bucket,meta["key"],str(file))
        except Exception:
            file.unlink(missing_ok=True)
            raise StorageError("universal_index_download_failed") from None
        if sha256_file(file)!=meta["sha256"]:
            file.unlink(missing_ok=True)
            raise StorageError("universal_index_hash_mismatch")
        verify_database(file)
        import sqlite3
        try:
            uri = file.resolve().as_uri() + "?mode=ro"
            with closing(sqlite3.connect(uri, uri=True)) as db:
                n=db.execute("SELECT count(*) FROM v31_universal_inventory").fetchone()[0]
                if n!=meta["product_count"]:
                    raise StorageError("universal_index_count_mismatch")
                if expected_review_hint_count is not None:
                    row=db.execute("""
                      SELECT count(*),sum(CASE WHEN review_only=1
                        THEN 1 ELSE 0 END)
                      FROM v31_unclassified_review_hints
                    """).fetchone()
                    total,valid=row[0],row[1] or 0
                    if (total!=expected_review_hint_count or valid!=total or
                        total>meta["product_count"]):
                        raise StorageError("universal_index_hint_count_mismatch")
        except StorageError:
            file.unlink(missing_ok=True)
            raise
        except sqlite3.Error:
            file.unlink(missing_ok=True)
            raise StorageError("universal_index_invalid_schema") from None
        return True

    def _prune(self,keep:set[str])->int:
        token=None
        obsolete=[]
        for _ in range(100):
            args={"Bucket":self.bucket,"Prefix":PREFIX,"MaxKeys":1000}
            if token:
                args["ContinuationToken"]=token
            result=self.s3.list_objects_v2(**args)
            for obj in result.get("Contents",[]):
                key=obj.get("Key")
                if isinstance(key,str) and KEY_RE.fullmatch(key) and key not in keep:
                    obsolete.append(key)
            if not result.get("IsTruncated"):
                break
            next_token=result.get("NextContinuationToken")
            if not next_token or next_token==token:
                raise StorageError("universal_index_retention_pagination")
            token=next_token
        else:
            raise StorageError("universal_index_retention_limit")
        for key in obsolete:
            self.s3.delete_object(Bucket=self.bucket,Key=key)
        return len(obsolete)

    def save_from(self,path:Path|str,*,product_count:int)->dict:
        if type(product_count) is not int or not 1<=product_count<=10_000_000:
            raise StorageError("universal_index_product_count_invalid")
        source=Path(path)
        verify_database(source)
        import sqlite3
        uri = source.resolve().as_uri() + "?mode=ro"
        with closing(sqlite3.connect(uri, uri=True)) as db:
            count=db.execute(
                "SELECT count(*) FROM v31_universal_inventory").fetchone()[0]
        if count!=product_count:
            raise StorageError("universal_index_count_mismatch")
        previous=self._manifest()
        sha=sha256_file(source)
        stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        key=f"{PREFIX}{stamp}-{sha[:16]}.sqlite3"
        if not KEY_RE.fullmatch(key):
            raise StorageError("universal_index_object_key_invalid")
        try:
            self.s3.upload_file(str(source),self.bucket,key,
                                ExtraArgs={"Metadata":{"sha256":sha}})
            head=self.s3.head_object(Bucket=self.bucket,Key=key)
            if head.get("Metadata",{}).get("sha256")!=sha:
                raise StorageError("universal_index_object_verify_failed")
        except StorageError:
            raise
        except Exception:
            raise StorageError("universal_index_upload_failed") from None
        data={"schema":SCHEMA,"key":key,"sha256":sha,
              "created_utc":datetime.now(timezone.utc).isoformat(),
              "product_count":product_count}
        try:
            self.s3.put_object(Bucket=self.bucket,Key=POINTER,
                Body=json.dumps(data,separators=(",",":")).encode("utf-8"),
                ContentType="application/json",CacheControl="no-store")
        except Exception:
            raise StorageError("universal_index_pointer_write_failed") from None
        keep={key}
        if previous:
            keep.add(previous["key"])
        try:
            removed=self._prune(keep)
            pending=False
        except Exception:
            removed=0
            pending=True
        return {"index_saved":True,"index_product_count":product_count,
                "retention_deleted":removed,"retention_pending":pending}
