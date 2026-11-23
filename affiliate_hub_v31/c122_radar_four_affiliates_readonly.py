"""C122 — localizar ofertas exatas do Radar Tech BR no catálogo V31 R2 (somente leitura).

Não consulta API Shopee, não cria link, não muta R2/D1 e não publica CMS.
"""
from __future__ import annotations

import json
import pathlib
import re
import sqlite3
import tempfile
import unicodedata
from collections import defaultdict

from .r2_state import R2State

TARGETS = {
    "29": {
        "label": "Arctic Air Cooler portátil com umidificador e LED",
        "terms": ("arctic", "air cooler"),
        "required": (("arctic",), ("cooler", "air cooler")),
    },
    "28": {
        "label": "Mini Scanner Automotivo Universal OBD2 Bluetooth ELM327",
        "terms": ("obd2", "elm327"),
        "required": (("obd2", "elm327"), ("bluetooth",)),
    },
    "25": {
        "label": "Caixa de Som Kapbom KA-8955 Bluetooth TWS",
        "terms": ("ka-8955", "ka8955", "kapbom"),
        "required": (("kapbom",), ("ka8955",)),
    },
    "24": {
        "label": "Luz RGB portátil LED vídeo celular 3200K 6500K",
        "terms": ("3200k", "6500k", "luz rgb"),
        "required": (("rgb",), ("3200",), ("6500",)),
    },
}


def norm(t: str) -> str:
    t = unicodedata.normalize("NFKD", str(t or ""))
    return re.sub(r"[^a-z0-9]", "", "".join(c for c in t if not unicodedata.combining(c)).lower())


def exact_match(title: str, groups: tuple[tuple[str, ...], ...]) -> bool:
    cleaned = norm(title)
    return all(any(norm(v) in cleaned for v in group) for group in groups)


def score(title: str, target: str) -> float:
    target_words = set(re.findall(r"[a-z0-9]+", unicodedata.normalize("NFKD", target).encode("ascii", "ignore").decode().lower()))
    title_words = set(re.findall(r"[a-z0-9]+", unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode().lower()))
    significant = {x for x in target_words if len(x) > 2}
    return round(len(significant & title_words) / max(len(significant), 1), 3)


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="c122-r2-readonly-") as td:
        path = pathlib.Path(td) / "r2_catalog_readonly.sqlite3"
        if not R2State.from_env().restore_to(path):
            raise RuntimeError("R2_POINTER_ABSENT")
        con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA query_only=ON")
        print("C122_R2_READONLY_RESTORE_OK", flush=True)
        summary = {}
        for post_id, target in TARGETS.items():
            hits = {}
            for term in target["terms"]:
                sql = """SELECT p.product_key,p.shop_id,p.item_id,p.title,p.image_url,p.origin_url,
                                p.moderation,t.status AS taxonomy_status,t.category,t.niche,
                                l.campaign,l.affiliate_url,l.verified_origin,l.updated_utc
                         FROM products p
                         LEFT JOIN product_taxonomy t ON t.product_key=p.product_key
                         LEFT JOIN affiliate_links l ON l.product_key=p.product_key
                                  AND l.campaign='radarwp'
                         WHERE p.title LIKE ? COLLATE NOCASE LIMIT 1000"""
                for row in con.execute(sql, (f"%{term}%",)):
                    key = str(row["product_key"])
                    record = dict(row)
                    if key not in hits:
                        hits[key] = record
            candidates = []
            for row in hits.values():
                title = row["title"]
                match = exact_match(title, target["required"])
                candidates.append({
                    "key": row["product_key"],
                    "shop_id": row["shop_id"],
                    "item_id": row["item_id"],
                    "title": title,
                    "image_url": row["image_url"],
                    "origin_url": row["origin_url"],
                    "moderation": row["moderation"],
                    "taxonomy_status": row["taxonomy_status"],
                    "category": row["category"],
                    "niche": row["niche"],
                    "campaign": row["campaign"],
                    "affiliate_url_radarwp": row["affiliate_url"],
                    "affiliate_verified_origin": row["verified_origin"],
                    "affiliate_updated_utc": row["updated_utc"],
                    "required_title_match": match,
                    "relevance_score": score(title, target["label"]),
                })
            candidates.sort(key=lambda p:(not p["required_title_match"],-p["relevance_score"],not bool(p["affiliate_url_radarwp"]),p["title"].lower()))
            summary[post_id] = {
                "label": target["label"],
                "source_hits": len(hits),
                "required_title_matches": sum(c["required_title_match"] for c in candidates),
                "radarwp_affiliate_links_in_matches": sum(bool(c["affiliate_url_radarwp"]) for c in candidates if c["required_title_match"]),
                "candidates": candidates[:25],
                "status": "READ_ONLY_MATCHES_NOT_OFFER_VALIDATION",
            }
            print("C122_POST="+json.dumps({
                "id":post_id, "source_hits":len(hits),
                "exact_title_matches":summary[post_id]["required_title_matches"],
                "radarwp_affiliate_links":summary[post_id]["radarwp_affiliate_links_in_matches"],
                "top": [{
                    "key":c["key"],"title":c["title"][:160],
                    "exact":c["required_title_match"],"score":c["relevance_score"],
                    "radarwp_link":bool(c["affiliate_url_radarwp"])
                } for c in candidates[:5]]
            },ensure_ascii=False), flush=True)
        con.close()
        out = pathlib.Path("c122_radar_four_catalog_candidates.json")
        out.write_text(json.dumps({
            "schema":"v31-c122-radar-catalog-search/v1",
            "campaign_required":"radarwp",
            "read_only":True,
            "targets":summary,
            "warnings":["R2 catalog is a historical snapshot, not real-time Shopee availability",
                        "other campaign links must never be substituted",
                        "matched title alone cannot authorize new CTA"]
        },ensure_ascii=False,indent=2),encoding="utf-8")
        print("C122_SAFE_NO_WRITES_OUTPUT="+str(out),flush=True)


if __name__=="__main__":
    main()
