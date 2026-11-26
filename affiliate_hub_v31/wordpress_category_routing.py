"""Universal declarative category binding; no CMS mutations."""
import json
import re
from pathlib import Path

CONFIG=Path(__file__).with_name("wordpress_category_routes.json")


def validate_binding(value):
    if (not isinstance(value,dict) or set(value)!={"id","parent","slug","taxonomy_path"}
            or type(value["id"]) is not int or value["id"]<=0
            or type(value["parent"]) is not int or value["parent"]<0
            or value["parent"]==value["id"]
            or not isinstance(value["slug"],str) or not re.fullmatch(r"[a-z0-9-]+",value["slug"])
            or not isinstance(value["taxonomy_path"],str)
            or not re.fullmatch(r"[a-z0-9_]+/[a-z0-9_]+",value["taxonomy_path"])):
        raise ValueError("wordpress_category_binding_invalid")
    return dict(value)


def category_map(route):
    doc=json.loads(CONFIG.read_text(encoding="utf-8"))
    if doc.get("version")!=1 or not isinstance(doc.get("sites"),dict):
        raise ValueError("wordpress_category_registry_invalid")
    mapping=doc["sites"].get(route["site_key"])
    if mapping is None:
        return None
    if (route["platform"]!="wordpress" or not isinstance(mapping,dict)
            or not mapping or set(mapping)!=set(route["allowed_niches"])):
        raise ValueError("wordpress_category_route_incomplete")
    result={path:validate_binding({**value,"taxonomy_path":path})
            for path,value in mapping.items()}
    if any(v["parent"] and not any(p["id"]==v["parent"] and p["parent"]==0
                                   for p in result.values()) for v in result.values()):
        raise ValueError("wordpress_category_parent_unmapped")
    return result


def category_for_product(catalog,route,product_key):
    mapping=category_map(route)
    if mapping is None:
        return None
    from .verified_supply import route_allows_sku
    if not route_allows_sku(catalog,route,product_key):
        raise ValueError("wordpress_category_sku_ineligible")
    row=catalog.db.execute("SELECT category,niche FROM product_taxonomy WHERE product_key=? AND status='matched'",(product_key,)).fetchone()
    if not row or "/".join(row) not in mapping:
        raise ValueError("wordpress_category_unmapped")
    return mapping["/".join(row)]


def verify_remote_category(client,route,binding):
    mapping=category_map(route)
    if mapping is None:
        if binding is not None:
            raise ValueError("wordpress_category_unexpected")
        return None
    binding=validate_binding(binding)
    if mapping.get(binding["taxonomy_path"])!=binding:
        raise ValueError("wordpress_category_policy_drift")
    def check(expected):
        term=client.get_category(expected["id"])
        if (not isinstance(term,dict) or type(term.get("id")) is not int
                or type(term.get("parent")) is not int
                or any(term.get(k)!=expected[k] for k in ("id","parent","slug"))):
            raise ValueError("wordpress_category_remote_drift")
    check(binding)
    if binding["parent"]:
        check(next(v for v in mapping.values() if v["id"]==binding["parent"] and v["parent"]==0))
    return binding["id"]


def check_post_category(post,category_id):
    if category_id is not None and post.get("categories")!=[category_id]:
        raise ValueError("wordpress_category_readback_mismatch")
