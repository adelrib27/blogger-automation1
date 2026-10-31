#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

KNOWN_NAMESPACES = {
    "b": "http://www.google.com/2005/gml/b",
    "data": "http://www.google.com/2005/gml/data",
    "expr": "http://www.google.com/2005/gml/expr",
    "macro": "http://www.google.com/2005/gml/macro",
    "mexpr": "http://www.google.com/2005/gml/mexpr",
    "g": "http://www.google.com/2005/gml/g",
}
BLOGGER_MARKERS = ("<b:skin", "<b:section", "<b:widget", "<b:template-skin")


class NormalizeError(RuntimeError):
    pass


def _used_prefixes(text: str) -> set[str]:
    out: set[str] = set()
    for tag in re.findall(r"<[^>]+>", text, flags=re.S):
        if tag.startswith("<!--") or tag.startswith("<![CDATA["):
            continue
        for prefix in re.findall(r"(?:<|</|\s)([A-Za-z_][\w.-]*):[A-Za-z_][\w.-]*", tag):
            if prefix not in {"xml", "xmlns"}:
                out.add(prefix)
    return out


def normalize(source: Path, output: Path) -> dict:
    data = source.read_bytes()
    if len(data) < 1024:
        raise NormalizeError("Backup pequeno demais para ser tema Blogger.")
    text = data.decode("utf-8-sig", errors="strict")
    low = text.lower()
    if "<html" not in low:
        raise NormalizeError("Backup não contém raiz HTML.")
    matched = [m for m in BLOGGER_MARKERS if m in text]
    if len(matched) < 2:
        raise NormalizeError("Backup não contém marcadores Blogger suficientes.")

    root = re.search(r"<html\b[^>]*>", text, flags=re.I | re.S)
    if not root:
        raise NormalizeError("Tag raiz <html> não encontrada.")
    root_text = root.group(0)
    declared = set(re.findall(r"xmlns:([A-Za-z_][\w.-]*)\s*=", root_text))
    used = _used_prefixes(text)
    missing = sorted(used - declared)
    unknown = [p for p in missing if p not in KNOWN_NAMESPACES]
    if unknown:
        raise NormalizeError("Prefixes XML sem declaração e sem mapeamento seguro: " + ", ".join(unknown))

    additions = [f' xmlns:{prefix}="{KNOWN_NAMESPACES[prefix]}"' for prefix in missing]
    normalized = text
    if additions:
        replacement = root_text[:-1] + "".join(additions) + ">"
        normalized = text[: root.start()] + replacement + text[root.end() :]

    try:
        ET.fromstring(normalized)
    except Exception as exc:
        raise NormalizeError(f"Backup continuou sem XML estrito após normalização segura: {exc}") from exc

    output.parent.mkdir(parents=True, exist_ok=True)
    tmp = output.with_suffix(output.suffix + ".tmp")
    tmp.write_text(normalized, encoding="utf-8")
    ET.parse(tmp)
    tmp.replace(output)

    return {
        "status": "BLOGGER_THEME_BACKUP_NORMALIZED",
        "source": str(source),
        "output": str(output),
        "original_bytes": len(data),
        "normalized_bytes": output.stat().st_size,
        "matched_markers": matched,
        "used_prefixes": sorted(used),
        "declared_prefixes_before": sorted(declared),
        "added_prefixes": missing,
        "original_preserved": source.resolve() != output.resolve(),
        "strict_xml_well_formed": True,
    }


def main() -> int:
    p = argparse.ArgumentParser(description="Normaliza somente namespaces Blogger conhecidos em backup já validado.")
    p.add_argument("--source", required=True)
    p.add_argument("--output", required=True)
    args = p.parse_args()
    try:
        result = normalize(Path(args.source).resolve(), Path(args.output).resolve())
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print(json.dumps({"status": "BLOGGER_THEME_BACKUP_NORMALIZE_FAIL", "error": str(exc)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
