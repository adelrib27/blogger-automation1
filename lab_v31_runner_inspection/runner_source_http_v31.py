"""LAB adapter for existing local_service_v31.Handler; not enabled by default.

Mount ONLY after reviewing current Windows service source, tests and token scope.
Adds two read-only paths while preserving the prior Handler behavior.
"""
from __future__ import annotations

from http import HTTPStatus
from pathlib import Path

from runner_source_inspector_v31 import InspectionDenied, manifest, read_source

SOURCE_DIR = Path(__file__).resolve().parent
GET_PATH = "/v1/source-manifest-v31"
POST_PATH = "/v1/source-read-v31"


def handle_get(handler) -> bool:
    if handler.path != GET_PATH:
        return False
    if not handler._require_auth():
        return True
    try:
        result = manifest(SOURCE_DIR)
        handler._send(HTTPStatus.OK, {"ok": True, "result": result})
    except (InspectionDenied, OSError, ValueError):
        handler._send(HTTPStatus.CONFLICT,
                      {"ok": False, "error": "inspection_unavailable"})
    return True


def handle_post(handler) -> bool:
    if handler.path != POST_PATH:
        return False
    if not handler._require_auth():
        return True
    try:
        payload = handler._read_json()
        result = read_source(
            SOURCE_DIR,
            name=payload.get("name"),
            expected_sha256=payload.get("expected_sha256"),
            confirm=payload.get("confirm"),
        )
        handler._send(HTTPStatus.OK, {"ok": True, "result": result})
    except InspectionDenied as exc:
        handler._send(HTTPStatus.CONFLICT,
                      {"ok": False, "error": str(exc)})
    except (ValueError, TypeError, KeyError):
        handler._send(HTTPStatus.BAD_REQUEST,
                      {"ok": False, "error": "invalid_inspection_request"})
    except OSError:
        handler._send(HTTPStatus.CONFLICT,
                      {"ok": False, "error": "inspection_unavailable"})
    return True
