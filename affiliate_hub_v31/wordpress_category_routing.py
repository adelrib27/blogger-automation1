"""Universal declarative category binding; no CMS mutations."""
import json
import re
from pathlib import Path

from .taxonomy import excluded_for_niche

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
    for value in result.values():
        ancestors(result,value)
    return result


def ancestors(mapping,binding):
    """Every parent must be known and consistent; reject cyclic hierarchies."""
    terms={}
    for value in mapping.values():
        identity={k:value[k] for k in ("id","parent","slug")}
        if value["id"] in terms and terms[value["id"]]!=identity:
            raise ValueError("wordpress_category_id_conflict")
        terms[value["id"]]=identity
    chain=[]
    seen={binding["id"]}
    parent=binding["parent"]
    while parent:
        if parent in seen or parent not in terms:
            raise ValueError("wordpress_category_parent_unmapped_or_cyclic")
        seen.add(parent)
        term=terms[parent]
        chain.append(term)
        parent=term["parent"]
    return chain


class ExcludedCategoryProduct(ValueError):
    """A legacy taxonomy row conflicts with the current product exclusions."""


def category_for_product(catalog,route,product_key):
    mapping=category_map(route)
    if mapping is None:
        return None
    from .verified_supply import route_allows_sku
    if not route_allows_sku(catalog,route,product_key):
        raise ValueError("wordpress_category_sku_ineligible")
    row = catalog.db.execute("""
        SELECT t.category, t.niche, p.title FROM product_taxonomy t
        JOIN products p ON p.product_key=t.product_key
        WHERE t.product_key=? AND t.status='matched'
    """, (product_key,)).fetchone()
    if not row or "/".join(row[:2]) not in mapping:
        raise ValueError("wordpress_category_unmapped")
    category, niche, title = row
    if excluded_for_niche(title, category, niche):
        raise ExcludedCategoryProduct("wordpress_category_product_excluded")
    return mapping[f"{category}/{niche}"]


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
    for parent in ancestors(mapping,binding):
        check(parent)
    return binding["id"]


def check_post_category(post,category_id):
    if category_id is not None and post.get("categories")!=[category_id]:
        raise ValueError("wordpress_category_readback_mismatch")


def audit_registered_categories():
    """Read-only authenticated preflight; no category or article creation."""
    from .routing import sites
    from .automatic_wordpress_drafts import WordPressRestClient, credentials_for
    result=[]
    for route in sites().values():
        mapping=category_map(route)
        if mapping is None:
            continue
        username,password=credentials_for(route["site_key"])
        client=WordPressRestClient(base_url=route["identifier"],username=username,
                                   application_password=password)
        client.site_settings()
        ids=sorted({verify_remote_category(client,route,v) for v in mapping.values()})
        result.append({"site_key":route["site_key"],"category_ids":ids,"status":"GET_VERIFIED"})
    if not result:
        raise ValueError("wordpress_category_registry_empty")
    return {"status":"CATEGORY_READ_ONLY_VERIFIED","sites":result,
            "cms_writes":0,"publication_calls":0}


if __name__=="__main__":
    try:
        print(json.dumps(audit_registered_categories(),sort_keys=True))
    except Exception:
        print("WORDPRESS_CATEGORY_READ_ONLY_FAILED_CLOSED")
        raise SystemExit(1)
