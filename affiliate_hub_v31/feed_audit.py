"""C2.1: auditoria de dois feeds REAIS sem gravar catálogo ou revelar dados.

A execução lê somente Environment Secrets dos links CSV, sem Shopee API
credentials e sem publicar/armazenar arquivos. Os dados são descartados ao fim.
Saída limitada a contagens agregadas e códigos fixos.
"""
from __future__ import annotations

import csv
import os
import re
import tempfile
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit

from .catalog import ALIASES, classify, fields, normalized
from .feed_download import DownloadFeedError, download_feed
from .taxonomy import classify_title

LIMIT_ROWS_PER_FEED = 250_000
MAX_COLUMNS = 128
MAX_CELL_CHARS = 25_000
MAX_KEYS = 300_000

class FeedAuditError(Exception):
    """Exception messages are static codes, never URL/headers/field values."""


def inspect_csv(path: Path, seen: set[str], source_name: str) -> dict:
    counters = Counter()
    niches = Counter()
    with path.open("rb") as raw:
        magic = raw.read(4)
    if magic[:2] == b"PK":
        raise FeedAuditError("UNEXPECTED_ZIP")
    if magic[:2] == b"\x1f\x8b":
        raise FeedAuditError("UNEXPECTED_GZIP")
    try:
        with path.open("r", encoding="utf-8-sig", errors="strict", newline="") as stream:
            sample=stream.read(8192)
            stream.seek(0)
            try:
                dialect=csv.Sniffer().sniff(sample, delimiters=",;\t|")
            except csv.Error:
                dialect=csv.excel
            reader=csv.DictReader(stream, dialect=dialect)
            names=reader.fieldnames
            if not names or len(names)>MAX_COLUMNS or any(not name for name in names):
                raise FeedAuditError("CSV_HEADERS_INVALID")
            headers={normalized(x) for x in names}
            if not (headers & set(ALIASES["title"])):
                raise FeedAuditError("MISSING_PRODUCT_TITLE_COLUMN")
            if not (headers & set(ALIASES["url"])):
                raise FeedAuditError("MISSING_PRODUCT_URL_COLUMN")
            counters["columns"]=len(names)
            counters["has_item_id"]=int(bool(headers & set(ALIASES["item"])))
            counters["has_shop_id"]=int(bool(headers & set(ALIASES["shop"])))
            counters["has_affiliate_link"]=int(bool(headers & set(ALIASES["affiliate"])))
            for raw_row in reader:
                counters["rows"]+=1
                if counters["rows"]>LIMIT_ROWS_PER_FEED:
                    raise FeedAuditError("MAX_ROWS_EXCEEDED")
                if None in raw_row or any(v is None for v in raw_row.values()):
                    # Apenas métricas estruturais, nunca valores do CSV.
                    raise FeedAuditError(
                        f"CSV_COLUMN_COUNT_MISMATCH_{source_name}_ROW_{counters['rows']}"
                        f"_PHYSICAL_LINE_{reader.line_num}_EXPECTED_{len(names)}"
                        f"_KEYS_{len(raw_row)}_EXTRA_{int(None in raw_row)}"
                    )
                if any(len(v)>MAX_CELL_CHARS for v in raw_row.values()):
                    raise FeedAuditError("MAX_CELL_LENGTH_EXCEEDED")
                row=fields(raw_row)
                key, moderation, _=classify(row)
                taxonomy=classify_title(row["title"])
                if taxonomy.status == "matched":
                    niches[(taxonomy.category,taxonomy.niche)] += 1
                    counters["classified"]+=1
                else:
                    counters["unclassified"]+=1
                if moderation=="review":
                    counters["base_review"]+=1
                if key in seen:
                    counters["duplicates_or_existing"]+=1
                else:
                    if len(seen)>=MAX_KEYS:
                        raise FeedAuditError("MAX_UNIQUE_KEYS_EXCEEDED")
                    seen.add(key)
                if not row["title"] or not row["url"]:
                    counters["missing_core_fields"]+=1
    except UnicodeDecodeError:
        raise FeedAuditError("CSV_ENCODING") from None
    except csv.Error:
        raise FeedAuditError("CSV_PARSE_ERROR") from None
    if not counters["rows"]:
        raise FeedAuditError("EMPTY_FEED")
    return {"source": source_name,
            "rows": counters["rows"],
            "columns": counters["columns"],
            "shop_id_column": bool(counters["has_shop_id"]),
            "item_id_column": bool(counters["has_item_id"]),
            "affiliate_link_column": bool(counters["has_affiliate_link"]),
            "duplicates_or_existing": counters["duplicates_or_existing"],
            "classified": counters["classified"],
            "unclassified": counters["unclassified"],
            "base_review": counters["base_review"],
            "missing_core_fields": counters["missing_core_fields"],
            "niches": {f"{c}/{n}": count for (c,n), count in sorted(niches.items())}}


def run() -> int:
    urls = (os.environ.get("V31_EDITORIAL_DATAFEED_URL_1", ""),
            os.environ.get("V31_EDITORIAL_DATAFEED_URL_2", ""))
    if not all(urls):
        print("V31_C2_REAL_FEEDS_MISSING_SECRETS")
        return 2
    try:
        seen=set()
        reports=[]
        with tempfile.TemporaryDirectory(prefix="v31-real-feed-audit-") as t:
            folder=Path(t)
            for index, url in enumerate(urls, 1):
                path=folder/f"feed_{index}.csv"
                size=download_feed(url, path)
                report=inspect_csv(path, seen, f"feed_{index}")
                report["download_bytes"]=size
                reports.append(report)
                print(f"V31_{report['source'].upper()}_STRUCTURE_PASS: rows={report['rows']}, columns={report['columns']}")
                # Descarta o CSV antes da próxima etapa; nenhum artifact produzido.
                path.unlink()
        print("V31_C2_REAL_FEEDS_PASS")
        for item in reports:
            # Campos agregados, sem links, títulos ou identificadores.
            print(f"V31_FEED_{item['source']}: rows={item['rows']}, bytes={item['download_bytes']}, "
                  f"columns={item['columns']}, has_shop_id={int(item['shop_id_column'])}, "
                  f"has_item_id={int(item['item_id_column'])}, has_affiliate_link={int(item['affiliate_link_column'])}, "
                  f"duplicates={item['duplicates_or_existing']}, classified={item['classified']}, "
                  f"unclassified={item['unclassified']}, base_review={item['base_review']}, "
                  f"missing_core_fields={item['missing_core_fields']}")
        print(f"V31_UNIQUE_PRODUCTS={len(seen)}")
        counts=Counter()
        for report in reports:
            counts.update(report["niches"])
        for route, count in sorted(counts.items()):
            # Only taxonomy-controlled names, never content derived from CSV.
            if re.fullmatch(r"[a-z0-9_]+/[a-z0-9_]+", route):
                print(f"V31_NICHE_{route.upper().replace('/', '_')}={count}")
        return 0
    except FeedAuditError as exc:
        # Whitelisted static diagnostic codes only, no exception trace.
        print("V31_C2_REAL_FEEDS_FAILED_" + str(exc))
        return 3
    except UnicodeDecodeError:
        print("V31_C2_REAL_FEEDS_FAILED_CSV_ENCODING")
        return 3
    except DownloadFeedError as exc:
        print("V31_C2_REAL_FEEDS_FAILED_" + str(exc))
        return 3
    except ValueError:
        print("V31_C2_REAL_FEEDS_FAILED_DOWNLOAD_OR_CSV")
        return 3
    except (OSError, csv.Error):
        print("V31_C2_REAL_FEEDS_FAILED_IO_OR_CSV")
        return 3


if __name__ == "__main__":
    raise SystemExit(run())
