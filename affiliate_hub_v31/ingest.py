"""Ingestão atômica de dois CSVs com deduplicação e nichos.

Não lê variáveis de API, não publica e não grava o catálogo no Git.
Em nuvem, o banco deve ser obtido e persistido por uma camada privada R2.
"""
from __future__ import annotations

import os
import sqlite3
import tempfile
from pathlib import Path

from .catalog import Catalog
from .title_index import has_index, rebuild_index


def ingest_two(existing_db: Path | str, feed_one: Path | str,
               feed_two: Path | str) -> dict:
    """Troca o banco *somente* após ambos os feeds e a integridade passarem."""
    destination = Path(existing_db)
    if destination.is_symlink():
        raise ValueError("Banco não pode ser symlink")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".v31-stage-", dir=destination.parent) as temp:
        staged = Path(temp) / "catalog.sqlite3"
        if destination.exists():
            # SQLite backup coerente, inclusive se existir jornal de transações.
            with sqlite3.connect(f"file:{destination.resolve()}?mode=ro", uri=True) as source:
                with sqlite3.connect(staged) as target:
                    source.backup(target)
        with Catalog(staged) as catalog:
            legacy_labeled = catalog.reclassify_missing()
            one = catalog.import_csv(feed_one, "feed1")
            two = catalog.import_csv(feed_two, "feed2")
            # Se C19 já habilitou o índice FTS, feeds reimportados devem
            # atualizar o texto pesquisável no mesmo snapshot staged.
            if has_index(catalog):
                rebuild_index(catalog)
            if one["rows"] < 1 or two["rows"] < 1:
                raise ValueError("Feed sem produtos: banco anterior preservado")
            if not catalog.integrity():
                raise ValueError("Integridade SQLite inválida")
            summary = {
                "input_rows": one["rows"] + two["rows"],
                "feed1_rows": one["rows"],
                "feed2_rows": two["rows"],
                "input_duplicates_or_existing": one["duplicates"] + two["duplicates"],
                "previously_unclassified_checked": legacy_labeled,
                "catalog": catalog.stats(),
                "niches": catalog.categories(),
                "status": "STAGED_AND_COMMITTED_LOCALLY",
            }
        if os.name == "posix":
            os.chmod(staged, 0o600)
        os.replace(staged, destination)
    return summary
