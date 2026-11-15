"""Entrada SAFE: 2 feeds em arquivos locais ou GitHub Actions + R2 privado.

Sem secrets e bucket R2 completos, --mode cloud falha antes de tocar no estado.
Nunca imprime links dos feeds, nomes dos produtos ou segredos.
"""
from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path

from .feed_download import check_feed_url, download_feed
from .ingest import ingest_two
from .r2_state import R2State


def run_cloud() -> dict:
    url1 = os.environ.get("V31_EDITORIAL_DATAFEED_URL_1", "").strip()
    url2 = os.environ.get("V31_EDITORIAL_DATAFEED_URL_2", "").strip()
    check_feed_url(url1)
    check_feed_url(url2)
    # Requer 4 credenciais/variáveis de storage antes de download/importação.
    storage = R2State.from_env()
    with tempfile.TemporaryDirectory(prefix="v31-editorial-private-") as root:
        folder = Path(root)
        first, second = folder / "first.csv", folder / "second.csv"
        state = folder / "state.sqlite3"
        download_feed(url1, first)
        download_feed(url2, second)
        loaded = storage.restore_to(state)
        report = ingest_two(state, first, second)
        status = storage.save_from(state)
        return {**report, "previous_snapshot_restored": loaded, **status}


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingestão V31 Editorial (sem publicação)")
    parser.add_argument("--mode", choices=("local", "cloud"), required=True)
    parser.add_argument("--db")
    parser.add_argument("--feed1")
    parser.add_argument("--feed2")
    args = parser.parse_args()
    try:
        if args.mode == "cloud":
            if args.db or args.feed1 or args.feed2:
                raise ValueError("Modo cloud não aceita caminhos locais")
            report = run_cloud()
        else:
            if not (args.db and args.feed1 and args.feed2):
                raise ValueError("Modo local exige --db --feed1 --feed2")
            report = ingest_two(Path(args.db), Path(args.feed1), Path(args.feed2))
    except Exception as exc:
        # Não adicionar str(exc), tracebacks ou URLs em logs de Actions.
        print("V31_C2_INGEST_FAILED_" + type(exc).__name__)
        return 3
    print("V31_C2_INGEST_PASS")
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
