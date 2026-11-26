"""Signed WordPress SEO fields with explicit site-level adapter selection."""
import html
import json
import re

from .wordpress_category_routing import CONFIG, category_map


def seo_adapter(route: dict) -> str | None:
    sites = json.loads(CONFIG.read_text(encoding="utf-8")).get("seo_adapters", {})
    adapter = sites.get(route["site_key"])
    if adapter is not None and (adapter not in {"excerpt", "aioseo"} or not category_map(route)):
        raise ValueError("wordpress_seo_adapter_invalid")
    return adapter


def validate_seo_binding(binding: dict) -> dict:
    if (not isinstance(binding, dict) or set(binding) != {"adapter", "description"}
            or not isinstance(binding["adapter"], str)
            or binding["adapter"] not in {"excerpt", "aioseo"}):
        raise ValueError("wordpress_seo_binding_invalid")
    description = binding["description"]
    if (not isinstance(description, str) or len(description) not in range(70, 171)
            or description.strip() != description or re.search(r"[<>\x00-\x1f\x7f]", description)):
        raise ValueError("wordpress_seo_description_invalid")
    return dict(binding)


def seo_for_article(route: dict, description: str) -> dict | None:
    adapter = seo_adapter(route)
    return validate_seo_binding({"adapter": adapter, "description": description}) if adapter else None


def draft_seo_fields(binding: dict) -> dict:
    seo = validate_seo_binding(binding)
    payload = {"excerpt": seo["description"]}
    if seo["adapter"] == "aioseo":
        payload["aioseo_meta_data"] = {"description": seo["description"]}
    return payload


def verify_seo_readback(post: dict, binding: dict) -> None:
    seo = validate_seo_binding(binding)
    description = seo["description"]
    if (post.get("excerpt") or {}).get("raw") != description:
        raise ValueError("wordpress_seo_excerpt_readback_mismatch")
    if seo["adapter"] == "aioseo":
        metadata = post.get("aioseo_meta_data")
        head = post.get("aioseo_head_json")
        rendered = head.get("description") if isinstance(head, dict) else None
        if (not isinstance(metadata, dict) or metadata.get("description") != description
                or not isinstance(rendered, str) or html.unescape(rendered) != description):
            raise ValueError("wordpress_seo_aioseo_readback_mismatch")
