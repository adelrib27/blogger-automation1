#!/usr/bin/env python3
"""Small verified job outputs replace metered Actions artifact storage."""
import base64
import json
import os
from pathlib import Path
from candidate import MAX_BYTES
from engine import SafetyStop

MAX_PACKAGE_BYTES = MAX_BYTES + 4096


def encode_package(folder: Path) -> str:
    # Preserve original bytes: the verification binds their SHA256.
    candidate = (folder / 'candidate.json').read_bytes()
    verification = (folder / 'verification.json').read_bytes()
    raw = json.dumps({'candidate': candidate.decode(), 'verification': verification.decode()}).encode()
    if len(raw) > MAX_PACKAGE_BYTES:
        raise SafetyStop('JOB_OUTPUT_TOO_LARGE')
    return base64.b64encode(raw).decode()


def decode_package(encoded: str, folder: Path):
    if not isinstance(encoded, str) or len(encoded) > MAX_PACKAGE_BYTES * 2:
        raise SafetyStop('INVALID_JOB_PACKAGE')
    raw = base64.b64decode(encoded, validate=True)
    if len(raw) > MAX_PACKAGE_BYTES:
        raise SafetyStop('JOB_PACKAGE_TOO_LARGE')
    package = json.loads(raw)
    if not isinstance(package, dict) or set(package) != {'candidate', 'verification'}:
        raise SafetyStop('INVALID_JOB_PACKAGE_FIELDS')
    if any(not isinstance(v, str) for v in package.values()):
        raise SafetyStop('INVALID_JOB_PACKAGE_CONTENT')
    folder.mkdir(exist_ok=True)
    for key, value in package.items():
        # Fixed names only. Publisher subsequently validates every candidate path/hash.
        (folder / (key + '.json')).write_bytes(value.encode())


if __name__ == '__main__':
    import sys
    folder = Path('autoevolution-output')
    if sys.argv[1:] == ['export']:
        with open(os.environ['GITHUB_OUTPUT'], 'a') as output:
            output.write('package=' + encode_package(folder) + '\n')
    elif sys.argv[1:] == ['import']:
        decode_package(os.environ['VERIFIED_PACKAGE'], folder)
    else:
        raise SystemExit('USAGE: transfer.py export|import')
