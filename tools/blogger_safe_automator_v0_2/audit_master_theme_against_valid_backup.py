#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

B_NS = "http://www.google.com/2005/gml/b"
B = "{%s}" % B_NS


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def opening_html_tag(text: str) -> str:
    m = re.search(r"<html\b[^>]*>", text, flags=re.I | re.S)
    return m.group(0) if m else ""


def attrs_from_opening_html(text: str) -> dict[str, str]:
    tag = opening_html_tag(text)
    attrs: dict[str, str] = {}
    for name, q, value in re.findall(r"([:\w-]+)\s*=\s*(['\"])(.*?)\2", tag, flags=re.S):
        attrs[name] = value
    return attrs


def block_presence(text: str) -> dict[str, bool]:
    return {
        "b_skin": bool(re.search(r"<b:skin\b", text)),
        "b_template_skin": bool(re.search(r"<b:template-skin\b", text)),
        "b_defaultmarkups": bool(re.search(r"<b:defaultmarkups\b", text)),
        "b_defaultmarkup": bool(re.search(r"<b:defaultmarkup\b", text)),
        "b_includable": bool(re.search(r"<b:includable\b", text)),
        "b_include": bool(re.search(r"<b:include\b", text)),
    }


def tag_counts(root: ET.Element) -> dict[str, int]:
    names = ["section", "widget", "includable", "include", "defaultmarkups", "defaultmarkup", "skin", "template-skin"]
    return {name: len(root.findall(f".//{B}{name}")) for name in names}


def section_snapshot(root: ET.Element) -> list[dict]:
    out = []
    for section in root.findall(f".//{B}section"):
        children = list(section)
        invalid_children = []
        for child in children:
            if child.tag != f"{B}widget":
                invalid_children.append(str(child.tag))
        out.append({
            "id": section.get("id"),
            "class": section.get("class"),
            "maxwidgets": section.get("maxwidgets"),
            "showaddelement": section.get("showaddelement"),
            "growth": section.get("growth"),
            "widget_ids": [c.get("id") for c in children if c.tag == f"{B}widget"],
            "invalid_child_tags": invalid_children,
        })
    return out


def widget_snapshot(root: ET.Element) -> list[dict]:
    out = []
    for widget in root.findall(f".//{B}widget"):
        out.append({
            "id": widget.get("id"),
            "type": widget.get("type"),
            "title": widget.get("title"),
            "locked": widget.get("locked"),
            "version": widget.get("version"),
            "visible": widget.get("visible"),
            "mobile": widget.get("mobile"),
            "includables": len(widget.findall(f".//{B}includable")),
        })
    return out


def xml_info(path: Path) -> dict:
    text = read_text(path)
    try:
        root = ET.fromstring(text)
        xml_valid = True
        xml_error = None
    except Exception as exc:
        return {
            "path": str(path),
            "size_bytes": path.stat().st_size,
            "sha256": sha256(path),
            "xml_valid": False,
            "xml_error": str(exc),
        }

    return {
        "path": str(path),
        "size_bytes": path.stat().st_size,
        "sha256": sha256(path),
        "xml_valid": xml_valid,
        "xml_error": xml_error,
        "root_tag": root.tag,
        "html_attrs": attrs_from_opening_html(text),
        "blocks": block_presence(text),
        "counts": tag_counts(root),
        "sections": section_snapshot(root),
        "widgets": widget_snapshot(root),
    }


def values(items: list[dict], key: str) -> list[str]:
    return sorted({str(item.get(key)) for item in items if item.get(key) is not None})


def build_risks(master: dict, backup: dict) -> list[dict]:
    risks: list[dict] = []
    if not master.get("xml_valid") or not backup.get("xml_valid"):
        risks.append({"severity": "BLOCKER", "code": "XML_INVALID", "detail": "Um dos XMLs não é bem-formado."})
        return risks

    ma = master["html_attrs"]
    ba = backup["html_attrs"]
    for attr in ["b:css", "b:defaultwidgetversion", "b:layoutsVersion", "b:responsive", "b:templateVersion", "b:version"]:
        if ma.get(attr) != ba.get(attr):
            risks.append({
                "severity": "INFO",
                "code": "ROOT_ATTR_DIFF",
                "attribute": attr,
                "master": ma.get(attr),
                "backup": ba.get(attr),
            })

    mb = master["blocks"]
    bb = backup["blocks"]
    if ma.get("b:defaultwidgetversion") == "2" and bb.get("b_defaultmarkups") and not mb.get("b_defaultmarkups"):
        risks.append({
            "severity": "HIGH",
            "code": "MISSING_DEFAULTMARKUPS_V2",
            "detail": "Backup válido usa b:defaultmarkups, mas o Tema Mestre v2/v3 não possui esse bloco.",
        })
    if bb.get("b_template_skin") and not mb.get("b_template_skin"):
        risks.append({
            "severity": "MEDIUM",
            "code": "MISSING_TEMPLATE_SKIN",
            "detail": "Backup válido possui b:template-skin e o Tema Mestre não.",
        })

    invalid_sections = [s for s in master["sections"] if s["invalid_child_tags"]]
    if invalid_sections:
        risks.append({
            "severity": "BLOCKER",
            "code": "SECTION_HAS_NON_WIDGET_CHILD",
            "detail": invalid_sections,
        })

    for s in master["sections"]:
        sid = s.get("id") or ""
        if not re.fullmatch(r"[A-Za-z0-9]+", sid):
            risks.append({
                "severity": "HIGH",
                "code": "SECTION_ID_NOT_ALNUM",
                "section_id": sid,
            })

    for w in master["widgets"]:
        wid = w.get("id") or ""
        if not re.fullmatch(r"[A-Za-z0-9]+", wid):
            risks.append({
                "severity": "HIGH",
                "code": "WIDGET_ID_NOT_ALNUM",
                "widget_id": wid,
            })

    backup_versions = values(backup["widgets"], "version")
    master_versions = values(master["widgets"], "version")
    if backup_versions and not master_versions:
        risks.append({
            "severity": "HIGH",
            "code": "WIDGET_VERSION_ATTRS_MISSING",
            "detail": "Widgets do backup válido possuem atributo version; widgets do Tema Mestre não.",
            "backup_versions": backup_versions,
        })

    if backup["counts"].get("includable", 0) > 0 and master["counts"].get("includable", 0) == 0:
        risks.append({
            "severity": "HIGH",
            "code": "NO_WIDGET_INCLUDABLE_MARKUP",
            "detail": "Backup válido contém b:includable e o Tema Mestre não contém nenhum.",
            "backup_includables": backup["counts"].get("includable", 0),
        })

    if master["size_bytes"] < backup["size_bytes"] * 0.15:
        risks.append({
            "severity": "INFO",
            "code": "MASTER_MUCH_SMALLER_THAN_VALID_BACKUP",
            "master_size": master["size_bytes"],
            "backup_size": backup["size_bytes"],
        })

    return risks


def main() -> int:
    parser = argparse.ArgumentParser(description="Audita Tema Mestre contra backup Blogger válido sem alterar arquivos.")
    parser.add_argument("--master-theme", required=True)
    parser.add_argument("--valid-backup", required=True)
    args = parser.parse_args()

    master_path = Path(args.master_theme).expanduser().resolve()
    backup_path = Path(args.valid_backup).expanduser().resolve()
    if not master_path.is_file():
        raise SystemExit(f"Tema Mestre não encontrado: {master_path}")
    if not backup_path.is_file():
        raise SystemExit(f"Backup válido não encontrado: {backup_path}")

    master = xml_info(master_path)
    backup = xml_info(backup_path)
    risks = build_risks(master, backup)

    report = {
        "status": "MASTER_THEME_STRUCTURAL_AUDIT_COMPLETE",
        "read_only": True,
        "master": master,
        "valid_backup": backup,
        "risks": risks,
        "high_or_blocker_count": sum(1 for r in risks if r.get("severity") in {"HIGH", "BLOCKER"}),
        "note": "Nenhum arquivo foi modificado. O relatório contém estrutura e metadados, não o conteúdo completo do backup.",
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
