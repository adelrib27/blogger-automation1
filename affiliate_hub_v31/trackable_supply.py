"""Discover potentially traceable offers, never approve facts or release a draft."""
from __future__ import annotations
import json
import re
import sqlite3
import tempfile
from pathlib import Path
from .catalog import Catalog
from .manufacturer_review import has_phrase
from .verified_supply import route_allows_sku
from .structured_review_source import catalog_gtin
from .r2_state import R2State, verify_database
from .routing import sites

HINTS = Path(__file__).with_name("trackable_supply_hints.json")
SKU = re.compile(r"shopee:[0-9]+:[0-9]+\Z")
CODE = re.compile(r"\b(?=[a-z0-9.-]{4,22}\b)(?=[a-z0-9.-]*[a-z])(?=[a-z0-9.-]*\d)[a-z0-9]+(?:[.-][a-z0-9]+)*\b", re.I)
NOISE = re.compile(r"^(?:\d+(?:v|w|cm|mm|kg|ml|l|hz|mah|btu|x|pcs)|\d+x\d+(?:cm|mm)?|\d+em\d+)$", re.I)

def discover(catalog, route, hints, *, limit=8):
    if (route.get("publish_enabled") is not False or
        not isinstance(hints, list) or not 1 <= len(hints) <= 24 or
        any(not isinstance(h,str) or not re.fullmatch(r"[a-z0-9 ]{3,30}",h) for h in hints)
        or len(set(hints)) != len(hints) or type(limit) is not int or not 1 <= limit <= 12):
        raise ValueError("trackable_supply_scope_invalid")
    # Bounded sample per brand and allowed taxonomy; GTIN is a separate search.
    # Only the title, SKU and discovery signals leave the local snapshot.
    out = {}
    for path in route.get("allowed_niches", []):
        category, niche = path.split("/",1)
        for hint in [*hints, None]:
            condition = "instr(lower(p.title),?)>0" if hint else "(instr(lower(p.description),'ean')>0 OR instr(lower(p.description),'gtin')>0)"
            params = (route["campaign"], category, niche) + ((hint,) if hint else ())
            rows = catalog.db.execute(f"""SELECT p.product_key,p.title,p.description,
                   a.product_key IS NOT NULL
                FROM products p JOIN product_taxonomy t ON t.product_key=p.product_key
                LEFT JOIN affiliate_links a ON a.product_key=p.product_key AND a.campaign=?
                WHERE p.moderation='eligible' AND t.status='matched'
                AND t.category=? AND t.niche=? AND {condition}
                ORDER BY p.last_seen_utc DESC,p.product_key LIMIT 80""",params)
            for key,title,desc,cached in rows:
                if (not isinstance(key,str) or not SKU.fullmatch(key) or
                    not isinstance(title,str) or not 12<=len(title)<=250):
                    continue
                if hint and not has_phrase(title,hint):
                    continue
                try:
                    gtin = catalog_gtin(desc or "")
                except ValueError:
                    gtin = None
                codes = sorted(set(x for x in CODE.findall(title) if not NOISE.fullmatch(x)))[:4]
                if not (gtin or (hint and codes)) or not route_allows_sku(catalog,route,key):
                    continue
                clean = " ".join(re.sub(r"[\x00-\x1f\x7f]", " ", title).split())
                if not clean:
                    continue
                item = out.setdefault(key, {"product_key":key,"title":clean[:190],
                    "brand_hints":[],"model_tokens_unverified":codes,
                    "gtin_checksum_valid":bool(gtin),"cached_for_exact_campaign":bool(cached),
                    "manufacturer_facts_verified":False,"eligible_for_draft_write":False})
                if hint and hint not in item["brand_hints"]:
                    item["brand_hints"].append(hint)
    ranked=sorted(out.values(), key=lambda x:(not x["gtin_checksum_valid"],
                    not x["cached_for_exact_campaign"], not bool(x["brand_hints"]), x["product_key"]))
    # Keep at most one candidate per identical title, for discovery only.
    seen=set()
    results=[]
    for item in ranked:
        title=item["title"].casefold()
        if title in seen:
            continue
        seen.add(title)
        results.append(item)
        if len(results)>=limit:
            break
    return {"site_key":route["site_key"],"campaign":route["campaign"],
            "candidate_sample":results,"eligible_for_draft_write":False,
            "scope":"allowed_niches_bounded_sample_not_exhaustive"}

def main():
    config=json.loads(HINTS.read_text(encoding="utf-8"))
    if config.get("version")!=1 or not isinstance(config.get("sites"),dict):
        raise ValueError("trackable_supply_config_invalid")
    registry=sites()
    with tempfile.TemporaryDirectory(prefix="v31-c180-") as tmp:
        snapshot=Path(tmp)/"catalog.sqlite3"
        if not R2State.from_env().restore_to(snapshot):
            raise ValueError("trackable_supply_snapshot_missing")
        verify_database(snapshot)
        db=sqlite3.connect("file:"+str(snapshot)+"?mode=ro",uri=True)
        try:
            db.execute("PRAGMA query_only=ON")
            catalog=Catalog.__new__(Catalog)
            catalog.db=db
            reports=[discover(catalog,registry[key],hints) for key,hints in sorted(config["sites"].items())]
        finally:
            db.close()
    print("V31_C180_TRACKABLE_SUPPLY="+json.dumps({"reports":reports,
        "cms_writes":0,"d1_writes":0,"r2_writes":0,"affiliate_mutations":0,
        "automatic_live_authorized":False},ensure_ascii=False,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
