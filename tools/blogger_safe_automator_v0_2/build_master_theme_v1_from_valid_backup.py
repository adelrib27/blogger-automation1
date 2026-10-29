#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import browser_provision as bp

LAB_BLOG_ID = "99449222854490000"
AUDITED_BACKUP_SHA256 = "6983387A78622EA2CA290B3B10704F92DC12FFED7AD7166B196BC67FFA919778"
AUDITED_MASTER_SHA256 = "6A7CBB17DB45A4AF1B4C66AE01EC0AFE86CE68317ABE198F8C7786DFC81AA0F8"

B_NS = "http://www.google.com/2005/gml/b"
NS = {"b": B_NS}

MASTER_MARKERS = (
    "Tema Mestre Blogger v1.0",
    "tm-topbar",
    "tm-brand",
    "Conteúdo editorial independente com foco em informação útil e decisões de compra.",
)
FORBIDDEN_MARKERS = (
    "SHOPEE_SECRET",
    "SHOPEE_APP_ID",
    "BLOGGER_RUNNER_TOKEN",
    "s.shopee.com.br/",
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def read_bytes(path_value: str, *, label: str) -> tuple[Path, bytes]:
    path = Path(path_value).expanduser().resolve()
    if not path.is_file():
        raise bp.SafeAutomationError(f"{label} não encontrado: {path}")
    data = path.read_bytes()
    if not data:
        raise bp.SafeAutomationError(f"{label} está vazio: {path}")
    return path, data


def parse_xml(data: bytes, *, label: str) -> ET.Element:
    try:
        return ET.fromstring(data)
    except ET.ParseError as exc:
        raise bp.SafeAutomationError(f"{label} não é XML válido: {exc}") from exc


def count_blogger_structure(root: ET.Element) -> dict:
    return {
        "section": len(root.findall(".//b:section", NS)),
        "widget": len(root.findall(".//b:widget", NS)),
        "includable": len(root.findall(".//b:includable", NS)),
        "include": len(root.findall(".//b:include", NS)),
        "defaultmarkups": len(root.findall(".//b:defaultmarkups", NS)),
        "defaultmarkup": len(root.findall(".//b:defaultmarkup", NS)),
        "skin": len(root.findall(".//b:skin", NS)),
        "template_skin": len(root.findall(".//b:template-skin", NS)),
        "blog_widgets": len(root.findall(".//b:widget[@type='Blog']", NS)),
    }


def extract_skin_payload(text: str, *, label: str) -> str:
    match = re.search(
        r"<b:skin\b[^>]*>\s*<!\[CDATA\[(.*?)\]\]>\s*</b:skin>",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )
    if not match:
        raise bp.SafeAutomationError(f"{label}: bloco b:skin CDATA não encontrado com segurança.")
    return match.group(1).strip()


def append_master_css_to_backup(backup_text: str, master_css: str) -> str:
    if "TM_COMPAT_LAYER_V1" in backup_text:
        raise bp.SafeAutomationError("Backup de entrada já contém a camada TM_COMPAT_LAYER_V1; operação bloqueada.")

    close_marker = "]]></b:skin>"
    index = backup_text.find(close_marker)
    if index < 0:
        raise bp.SafeAutomationError("Backup válido não contém fechamento literal ]]> </b:skin> esperado.")

    compat_css = (
        "\n\n/* TM_COMPAT_LAYER_V1 — Tema Mestre Blogger v1.0 */\n"
        + master_css
        + "\n/* /TM_COMPAT_LAYER_V1 */\n"
    )
    return backup_text[:index] + compat_css + backup_text[index:]


def inject_master_identity(text: str) -> str:
    if "TM_COMPAT_IDENTITY_V1" in text:
        raise bp.SafeAutomationError("Tema candidato já contém TM_COMPAT_IDENTITY_V1; operação bloqueada.")

    body = re.search(r"<body\b[^>]*>", text, flags=re.IGNORECASE)
    if not body:
        raise bp.SafeAutomationError("Elemento <body> não encontrado no backup válido.")

    fragment = """
    <!-- TM_COMPAT_IDENTITY_V1 -->
    <div class='tm-topbar'>
      <div class='tm-shell'>Conteúdo editorial independente com foco em informação útil e decisões de compra.</div>
    </div>
    <div class='tm-shell tm-header-inner' id='tm-master-identity'>
      <a class='tm-brand' expr:href='data:blog.homepageUrl'><data:blog.title/></a>
      <p class='tm-tagline'>Guias, comparativos, dicas práticas e oportunidades selecionadas.</p>
    </div>
    <!-- /TM_COMPAT_IDENTITY_V1 -->
"""
    return text[: body.end()] + fragment + text[body.end() :]


def validate_preservation(before: dict, after: dict) -> None:
    required_equal = (
        "section",
        "widget",
        "includable",
        "include",
        "defaultmarkups",
        "defaultmarkup",
        "template_skin",
        "blog_widgets",
    )
    mismatches = {
        key: {"before": before[key], "after": after[key]}
        for key in required_equal
        if before[key] != after[key]
    }
    if mismatches:
        raise bp.SafeAutomationError(
            f"Estrutura Blogger do backup não foi preservada integralmente: {mismatches}"
        )

    if after["defaultmarkups"] < 1 or after["defaultmarkup"] < 1:
        raise bp.SafeAutomationError("Candidato perdeu b:defaultmarkups/defaultmarkup.")
    if after["template_skin"] < 1:
        raise bp.SafeAutomationError("Candidato perdeu b:template-skin.")
    if after["includable"] < 1:
        raise bp.SafeAutomationError("Candidato perdeu b:includable.")
    if after["blog_widgets"] != 1:
        raise bp.SafeAutomationError(
            f"Candidato precisa preservar exatamente 1 widget Blog; encontrado(s): {after['blog_widgets']}."
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Constrói um candidato Tema Mestre a partir de backup Blogger já aceito, "
            "preservando a mecânica v2/v3 e adicionando somente a camada visual Mestre."
        )
    )
    parser.add_argument("--expected-blog-id", required=True)
    parser.add_argument("--valid-backup", required=True)
    parser.add_argument("--master-theme", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    blog_id = str(args.expected_blog_id).strip()
    if blog_id != LAB_BLOG_ID:
        raise bp.SafeAutomationError(
            f"Builder permanece LAB_ONLY. Blog permitido: {LAB_BLOG_ID}."
        )

    backup_path, backup_bytes = read_bytes(args.valid_backup, label="Backup Blogger válido")
    master_path, master_bytes = read_bytes(args.master_theme, label="Tema Mestre original")

    backup_sha = sha256_bytes(backup_bytes)
    master_sha = sha256_bytes(master_bytes)
    if backup_sha != AUDITED_BACKUP_SHA256:
        raise bp.SafeAutomationError(
            f"Backup diferente do auditado. esperado={AUDITED_BACKUP_SHA256} observado={backup_sha}"
        )
    if master_sha != AUDITED_MASTER_SHA256:
        raise bp.SafeAutomationError(
            f"Tema Mestre original mudou desde a auditoria. esperado={AUDITED_MASTER_SHA256} observado={master_sha}"
        )

    backup_root = parse_xml(backup_bytes, label="Backup Blogger válido")
    master_root = parse_xml(master_bytes, label="Tema Mestre original")
    before_counts = count_blogger_structure(backup_root)
    master_counts = count_blogger_structure(master_root)

    backup_text = backup_bytes.decode("utf-8-sig")
    master_text = master_bytes.decode("utf-8-sig")
    master_css = extract_skin_payload(master_text, label="Tema Mestre original")

    candidate = append_master_css_to_backup(backup_text, master_css)
    candidate = inject_master_identity(candidate)
    candidate_bytes = candidate.encode("utf-8")
    candidate_root = parse_xml(candidate_bytes, label="Tema candidato")
    after_counts = count_blogger_structure(candidate_root)
    validate_preservation(before_counts, after_counts)

    lowered = candidate.casefold()
    for marker in FORBIDDEN_MARKERS:
        if marker.casefold() in lowered:
            raise bp.SafeAutomationError(f"Marcador proibido encontrado no candidato: {marker}")
    missing_markers = [marker for marker in MASTER_MARKERS if marker not in candidate]
    if missing_markers:
        raise bp.SafeAutomationError(f"Marcadores do Tema Mestre ausentes no candidato: {missing_markers}")

    output = Path(args.output).expanduser().resolve()
    if output.name.lower() != "theme.xml":
        raise bp.SafeAutomationError("O candidato deve ser gravado com o nome exato theme.xml.")
    if output == master_path or output == backup_path:
        raise bp.SafeAutomationError("Saída não pode sobrescrever o Tema Mestre original nem o backup válido.")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(candidate_bytes)

    written = output.read_bytes()
    if written != candidate_bytes:
        raise bp.SafeAutomationError("Validação pós-gravação falhou: bytes da saída divergem do candidato.")

    result = {
        "status": "MASTER_THEME_V1_COMPAT_CANDIDATE_BUILT",
        "lab_only": True,
        "blog_id": blog_id,
        "source_valid_backup": {
            "path": str(backup_path),
            "size_bytes": len(backup_bytes),
            "sha256": backup_sha,
            "structure": before_counts,
        },
        "source_master": {
            "path": str(master_path),
            "size_bytes": len(master_bytes),
            "sha256": master_sha,
            "structure": master_counts,
        },
        "candidate": {
            "path": str(output),
            "size_bytes": len(written),
            "sha256": sha256_bytes(written),
            "xml_valid": True,
            "structure": after_counts,
            "blogger_structure_preserved": before_counts == after_counts,
            "master_markers_present": {marker: (marker in candidate) for marker in MASTER_MARKERS},
        },
        "safety": {
            "original_master_overwritten": False,
            "valid_backup_overwritten": False,
            "blogger_write_performed": False,
        },
        "message": (
            "Candidato criado a partir do backup já aceito pelo Blogger. "
            "A mecânica v2/v3 foi preservada e a camada visual do Tema Mestre foi adicionada."
        ),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
