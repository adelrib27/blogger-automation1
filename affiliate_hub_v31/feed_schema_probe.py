"""C16 — Detectar metadados de categoria nos CSV oficiais, sem imprimir os CSV.

Dois downloads GET da Shopee nos URLs já configurados; SEM GraphQL,
geração de links, banco R2, artigos ou chamadas aos blogs.
"""
from __future__ import annotations

import csv
import json
import re
from collections import Counter
import os
import tempfile
from pathlib import Path

from .catalog import normalized
from .taxonomy import normalize
from .feed_download import download_feed,check_feed_url

def schema(path: Path) -> dict:
    with Path(path).open("r",encoding="utf-8-sig",newline="") as stream:
        sample=stream.read(8192)
        stream.seek(0)
        try:
            dialect=csv.Sniffer().sniff(sample,delimiters=",;\t|")
        except csv.Error:
            dialect=csv.excel
        reader=csv.DictReader(stream,delimiter=dialect.delimiter,
                              quotechar='"',doublequote=True,strict=True)
        headers=reader.fieldnames or []
        if not headers or len(headers)>128:
            raise ValueError("csv_header_invalid")
        indices=[i for i,h in enumerate(headers) if (
            "categor" in normalized(h) or
            "niche" in normalized(h) or "nicho" in normalized(h)
        )]
        # Não assumir que categoryId/categoryName já são uma taxonomia
        # editorial confiável. Apenas detectar disponibilidade.
        present=[0]*len(indices)
        frequently_seen=[Counter() for _ in indices]
        sample_count=0
        for row in reader:
            if sample_count>=5000:
                break
            if None in row or any(v is None for v in row.values()):
                raise ValueError("csv_columns_invalid")
            sample_count+=1
            for j,i in enumerate(indices):
                raw_value=str(row.get(headers[i]) or "").strip()
                if raw_value:
                    present[j]+=1
                    label=normalize(raw_value)
                    # Analisar somente labels de grupo que se repetem;
                    # um identificador ou título de produto nunca vira
                    # saída de diagnóstico isolada.
                    if (4<=len(label)<=65 and not label.isdigit() and
                            re.fullmatch(r"[a-z0-9 /_-]+",label)):
                        frequently_seen[j][label]+=1
        fields=[]
        for j,i in enumerate(indices):
            identifier=normalized(headers[i])
            if not re.fullmatch(r"[a-z][a-z0-9]{2,49}",identifier):
                identifier="category_metadata_field"
            fields.append({
                "column":identifier,
                "nonempty_in_sample":present[j],
                "distinct_safe_labels":len(frequently_seen[j]),
                "frequent_labels":[
                    {"label":name,"count":count}
                    for name,count in frequently_seen[j].most_common(18)
                    if count>=10
                ]
            })
        return {"has_csv_taxonomy_metadata":bool(indices),
                "taxonomy_metadata_columns":len(indices),
                "taxonomy_metadata_nonempty_per_column_first_1000":present,
                "sample_rows_checked":sample_count,
                "fields":fields,
                "raw_product_titles_reported":0,
                "raw_product_urls_reported":0}

def run()->dict:
    urls=[os.environ.get("V31_EDITORIAL_DATAFEED_URL_1",""),
          os.environ.get("V31_EDITORIAL_DATAFEED_URL_2","")]
    for u in urls:
        check_feed_url(u)
    with tempfile.TemporaryDirectory(prefix="v31-c16-feed-schema-") as root:
        report=[]
        for i,url in enumerate(urls,1):
            path=Path(root)/f"feed_{i}.csv"
            download_feed(url,path)
            report.append({"feed_number":i,**schema(path)})
            path.unlink()
    return {"mode":"OFFICIAL_CSV_SCHEMA_READ_ONLY",
            "feeds":report,
            "downloads":2,
            "graphql_calls":0,"r2_writes":0,"publication_calls":0}

def main()->int:
    try:
        result=run()
        print("V31_C16_FEED_SCHEMA_PASS")
        print(json.dumps(result,sort_keys=True))
        return 0
    except Exception:
        print("V31_C16_FEED_SCHEMA_FAILED")
        return 3

if __name__=="__main__":
    raise SystemExit(main())
