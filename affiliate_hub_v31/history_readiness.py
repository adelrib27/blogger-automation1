"""C13 — auditoria READ-ONLY de históricos locais para reutilização segura.

Não lê lojas, não chama APIs, não altera filas/históricos e não imprime
IDs de produto, títulos, URL de postagem, texto dos artigos ou credenciais.
Compatível com novos projetos em shadow.d com publication_history.json.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from .reuse_policy import normalize
from .shadow_audit import load_profiles

ROOT = Path(__file__).resolve().parents[1]


def _load_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeError):
        raise ValueError("history_or_draft_invalid") from None


def _body_tokens(value: str) -> int:
    text=re.sub(r"<[^>]*>"," ",str(value or ""))
    return len(re.findall(r"\b[\wÀ-ÿ]{3,}\b",text))


def audit_project(project: Path) -> dict:
    """Histórico sem publicar; potencial de reuso exige draft anterior verificável."""
    if project.is_symlink() or not project.is_dir():
        raise ValueError("project_dir_untrusted")
    history=project/"data/publication_history.json"
    generated=project/"data/generated"
    if not history.is_file() or history.is_symlink():
        return {"state":"NO_HISTORY","records":0,
                "reusable_products_with_verified_body":0}
    doc=_load_json(history)
    if not isinstance(doc,dict) or not isinstance(doc.get("items"),list):
        raise ValueError("history_schema_invalid")
    records=doc["items"]
    if len(records)>100000:
        raise ValueError("history_count_limit")
    indexed=defaultdict(list)
    with_id=0
    with_title=0
    for row in records:
        if not isinstance(row,dict):
            raise ValueError("history_row_invalid")
        key=str(row.get("shopee_item_id") or "").strip()
        title=normalize(row.get("editorial_title") or row.get("title") or "")
        with_id+=bool(key)
        with_title+=bool(title)
        if key:
            indexed[key].append(title)
    if not generated.is_dir() or generated.is_symlink():
        files=[]
    else:
        files=sorted(generated.glob("*.json"))
    if len(files)>12000:
        raise ValueError("generated_files_count_limit")
    drafts=defaultdict(set)
    for file in files:
        if file.is_symlink() or not file.is_file():
            raise ValueError("generated_file_untrusted")
        article=_load_json(file)
        if not isinstance(article,dict):
            raise ValueError("generated_schema_invalid")
        key=str(article.get("shopee_item_id") or "").strip()
        title=normalize(article.get("editorial_title") or article.get("seo_title") or "")
        if key and title and _body_tokens(article.get("editorial_html") or "")>=120:
            drafts[key].add(title)
    eligible=sum(1 for k,titles in indexed.items()
                 if len(titles)==1 and bool(titles[0])
                 and titles[0] in drafts.get(k,set()))
    history_missing_body=sum(1 for k,titles in indexed.items()
                             if len(titles)==1 and bool(titles[0])
                             and titles[0] not in drafts.get(k,set()))
    repeated=sum(1 for titles in indexed.values() if len(titles)>1)
    duplicate_titles=sum(1 for titles in indexed.values()
                         if len(titles)>1 and len(set(titles))<len(titles))
    return {
        "state":"AUDITED",
        "records":len(records),
        "records_with_product_id":with_id,
        "records_with_editorial_title":with_title,
        "unique_product_ids":len(indexed),
        "generated_json_files":len(files),
        "reusable_products_with_verified_body":eligible,
        "single_publication_products_missing_matching_body":history_missing_body,
        "products_with_multiple_publications":repeated,
        "products_with_repeated_title":duplicate_titles,
        "r2_reads":0,"r2_writes":0,"shopee_api_calls":0,
        "publication_calls":0,
    }


def audit_all(root: Path=ROOT, *, profiles: dict | None=None) -> dict:
    profiles=load_profiles() if profiles is None else profiles
    result=[]
    for key,profile in sorted(profiles.items()):
        config=Path(profile["config"])
        # Um config em config/ na raiz (Radar) não implica estrutura
        # publication_history para esse adaptador específico.
        if len(config.parts)<3 or config.parts[1]!="config":
            result.append({"site_key":key,"state":"NOT_LEGACY_QUEUE_PROJECT",
                           "publication_calls":0})
            continue
        target=(root/config.parts[0]).resolve()
        if not target.is_relative_to(root.resolve()):
            raise ValueError("project_outside_repository")
        entry=audit_project(target)
        result.append({"site_key":key,**entry})
    return {
        "mode":"LOCAL_HISTORY_READ_ONLY",
        "sites_checked":len(result),
        "publication_calls":0,"api_calls":0,"r2_writes":0,
        "sites":result
    }


def main()->int:
    parser=argparse.ArgumentParser(description="C13: auditoria histórico editorial local")
    parser.add_argument("--site",default="all")
    args=parser.parse_args()
    try:
        report=audit_all()
        if args.site!="all":
            report["sites"]=[r for r in report["sites"] if r["site_key"]==args.site]
            if not report["sites"]:
                raise ValueError("site_not_registered")
            report["sites_checked"]=len(report["sites"])
        print("V31_C13_HISTORY_READONLY_PASS")
        print(json.dumps(report,ensure_ascii=False,sort_keys=True))
        return 0
    except Exception:
        print("V31_C13_HISTORY_READONLY_FAILED")
        return 3


if __name__=="__main__":
    raise SystemExit(main())
