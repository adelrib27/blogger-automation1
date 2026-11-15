"""Benchmark reproduzível para 100 mil + 10 mil registros sintéticos.

NÃO contém produtos comerciais, dados reais ou chamadas a serviços.
Executar: python -m affiliate_hub_v31.bench_scale
"""
from __future__ import annotations

import csv
import tempfile
import time
from pathlib import Path

from .catalog import Catalog
from .ingest import ingest_two

TITLES = (
    "Organizador de Cozinha", "Air Fryer Digital", "Liquidificador 1000W",
    "Ventilador de Mesa", "Parafusadeira 12V", "Produto Importado Sem Nicho",
)


def write_feed(path: Path, identifiers):
    with path.open("w", encoding="utf-8", newline="") as target:
        out = csv.writer(target)
        out.writerow(("shopId", "itemId", "productName", "productLink", "imageUrl"))
        for idx in identifiers:
            out.writerow(("900", str(idx), TITLES[idx % len(TITLES)],
                          f"https://shopee.com.br/produto-i.900.{idx}",
                          "https://cdn.example.invalid/product.jpg"))


def main() -> int:
    start=time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="v31-scale-synthetic-") as root:
        path=Path(root)
        first=path/"feed1.csv"
        second=path/"feed2.csv"
        write_feed(first,range(1,100001))
        write_feed(second,list(range(1,5001))+list(range(100001,105001)))
        summary=ingest_two(path/"catalog.sqlite3",first,second)
        with Catalog(path/"catalog.sqlite3") as catalog:
            healthy=catalog.integrity()
            count=catalog.stats()
        if (summary["input_rows"]!=110000 or
                summary["feed1_rows"]!=100000 or
                summary["feed2_rows"]!=10000 or
                summary["input_duplicates_or_existing"]!=5000 or
                count["products"]!=105000 or not healthy):
            raise RuntimeError("V31_SCALE_CONTRACT_FAILED")
        seconds=round(time.perf_counter()-start,2)
        print(f"V31_C2_SCALE_110K_PASS: rows=110000, duplicates=5000, unique=105000, "
              f"eligible={count['eligible']}, review={count['review']}, seconds={seconds}")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
