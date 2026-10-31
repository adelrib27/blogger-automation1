#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

THEME_DIR = Path(__file__).resolve().parent
THEME = THEME_DIR / "theme.xml"
PROFILE = THEME_DIR / "theme_profile.json"

REQUIRED_SECTION_IDS = {"topnav", "offerSection", "main", "sidebar", "footerlinks"}
FORBIDDEN_MARKERS = (
    "SHOPEE_SECRET",
    "SHOPEE_APP_ID",
    "BLOGGER_RUNNER_TOKEN",
    "s.shopee.com.br/",
)
EXTERNAL_SCRIPT_MARKERS = ("<script src=", "<script async src=", "<script defer src=")


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def main() -> int:
    xml_text = THEME.read_text(encoding="utf-8")
    profile = json.loads(PROFILE.read_text(encoding="utf-8"))

    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        fail(f"theme.xml não é XML válido: {exc}")

    ns = {"b": "http://www.google.com/2005/gml/b"}
    sections = root.findall(".//b:section", ns)
    section_ids = {str(node.attrib.get("id") or "") for node in sections}
    missing = sorted(REQUIRED_SECTION_IDS - section_ids)
    if missing:
        fail(f"seções obrigatórias ausentes: {', '.join(missing)}")

    blogs = root.findall(".//b:widget[@type='Blog']", ns)
    if len(blogs) != 1:
        fail(f"esperado exatamente 1 widget Blog; encontrado(s): {len(blogs)}")

    for marker in FORBIDDEN_MARKERS:
        if marker.casefold() in xml_text.casefold():
            fail(f"marcador proibido encontrado: {marker}")

    lowered = xml_text.casefold()
    for marker in EXTERNAL_SCRIPT_MARKERS:
        if marker.casefold() in lowered:
            fail("JavaScript externo não é permitido no Tema Mestre v1.0")

    if profile.get("status") != "LAB_ONLY":
        fail("theme_profile.json deve permanecer LAB_ONLY até validação no Blogger")

    if profile.get("safety", {}).get("apply_only_after_backup") is not True:
        fail("perfil deve exigir backup antes da aplicação")

    print("THEME_MASTER_V1_STATIC_VALIDATION_OK")
    print(f"sections={','.join(sorted(section_ids))}")
    print("blog_widget=1")
    print("hardcoded_affiliate_links=0")
    print("external_scripts=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
