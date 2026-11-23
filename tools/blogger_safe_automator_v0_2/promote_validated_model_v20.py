#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
import xml.etree.ElementTree as ET

import render_modelo_v20_theme as renderer

CONFIRMATION = "PROMOTE VALIDATED V20"
EXPECTED_SOURCE_SHA256 = "DF6A3B40003FE64889157F60A6C00A1E05D85DC5CF02425C12091E8738D6F21D"
SOURCE_BLOG_ID = "1719259388907013414"
SOURCE_TITLE = "Conecta Achados"
SOURCE_URL = "https://conectaachados.blogspot.com/"
SOURCE_PALETTE = "emerald"
SOURCE_COLORS = {
    "primary": "#0F8A5F",
    "header_bg": "#F2FBF7",
    "footer_bg": "#12372A",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def fail(message: str) -> None:
    raise SystemExit(message)


def canonicalize_validated_source(source_text: str) -> str:
    if renderer.MARKER not in source_text:
        fail(f"Tema-fonte não contém o marker V20: {renderer.MARKER}")

    # O source validado do Conecta foi renderizado com a paleta emerald. Removemos
    # SOMENTE o bloco que o renderer injeta, para voltar ao template neutro.
    identity_block = renderer.identity_css(
        SOURCE_COLORS["primary"],
        SOURCE_COLORS["header_bg"],
        SOURCE_COLORS["footer_bg"],
    )
    needle = identity_block + "\n"
    count = source_text.count(needle)
    if count != 1:
        fail(
            "Não foi possível identificar exatamente um bloco de identidade V20 "
            f"renderizado. Encontrados: {count}. Nenhuma substituição foi feita."
        )
    text = source_text.replace(needle, "", 1)

    if renderer.STYLE_MARKER in text:
        fail("Marker de identidade permaneceu após limpeza. Nenhuma substituição foi feita.")

    source_url = SOURCE_URL.rstrip("/") + "/"
    source_url_no_slash = source_url.rstrip("/")
    text = text.replace(SOURCE_TITLE, renderer.TITLE_TOKEN)
    text = text.replace(source_url, renderer.URL_TOKEN + "/")
    text = text.replace(source_url_no_slash, renderer.URL_TOKEN)

    if SOURCE_TITLE in text:
        fail("Título do blog-fonte ainda aparece no candidato canônico.")
    if "conectaachados.blogspot.com" in text:
        fail("URL do blog-fonte ainda aparece no candidato canônico.")
    if renderer.TITLE_TOKEN not in text or renderer.URL_TOKEN not in text:
        fail("Tokens de título/URL não foram reconstruídos corretamente.")
    if "s.shopee.com.br/" in text:
        fail("Link de produto Shopee encontrado no candidato canônico.")

    return text


def render_roundtrip(template_path: Path, output_path: Path) -> dict:
    script = Path(renderer.__file__).resolve()
    cmd = [
        sys.executable,
        str(script),
        "--template-theme", str(template_path),
        "--blog-title", SOURCE_TITLE,
        "--blog-url", SOURCE_URL,
        "--output-theme", str(output_path),
        "--palette", SOURCE_PALETTE,
    ]
    proc = subprocess.run(cmd, text=True, capture_output=True, timeout=120)
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "")[-1600:]
        fail("Round-trip do candidato canônico falhou: " + detail)

    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError:
        fail("Renderer terminou sem JSON válido no round-trip.")

    actual = sha256(output_path)
    if actual != EXPECTED_SOURCE_SHA256:
        fail(
            "Round-trip NÃO reproduziu o tema validado byte a byte. "
            f"Esperado {EXPECTED_SOURCE_SHA256}; obtido {actual}. "
            "Template canônico NÃO foi substituído."
        )
    return payload


def main() -> int:
    p = argparse.ArgumentParser(
        description="Promove o V20 validado do Conecta Achados a template canônico, com backup e round-trip exato."
    )
    p.add_argument("--confirm", required=True)
    p.add_argument("--source-theme")
    p.add_argument("--canonical-template")
    p.add_argument("--backup-root")
    args = p.parse_args()

    if args.confirm != CONFIRMATION:
        fail(f'Confirmação obrigatória: --confirm "{CONFIRMATION}"')

    repo_root = Path(__file__).resolve().parents[2]
    source = Path(args.source_theme).resolve() if args.source_theme else (
        repo_root / "themes" / "blogger_modelo_v20" / "rendered" / SOURCE_BLOG_ID / "theme.xml"
    )
    canonical = Path(args.canonical_template).resolve() if args.canonical_template else (
        repo_root / "themes" / "blogger_modelo_v20" / "theme.xml.tpl"
    )
    backup_root = Path(args.backup_root).resolve() if args.backup_root else (
        repo_root.parent / "backups" / "blogger-modelo-v20-canonical"
    )

    if not source.exists():
        fail(f"Tema validado não encontrado: {source}")
    source_sha = sha256(source)
    if source_sha != EXPECTED_SOURCE_SHA256:
        fail(
            "Tema-fonte local não é exatamente o XML validado esperado. "
            f"Esperado {EXPECTED_SOURCE_SHA256}; obtido {source_sha}. Nenhuma substituição foi feita."
        )

    source_text = source.read_text(encoding="utf-8")
    candidate_text = canonicalize_validated_source(source_text)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_dir = backup_root / stamp
    backup_dir.mkdir(parents=True, exist_ok=False)

    candidate = backup_dir / "theme.xml.tpl.candidate"
    roundtrip = backup_dir / "theme.roundtrip.xml"
    candidate.write_text(candidate_text, encoding="utf-8")
    ET.parse(candidate)
    candidate_sha = sha256(candidate)

    roundtrip_payload = render_roundtrip(candidate, roundtrip)
    roundtrip_sha = sha256(roundtrip)

    previous_exists = canonical.exists()
    previous_sha = sha256(canonical) if previous_exists else None
    previous_backup = backup_dir / "theme.xml.tpl.before"
    if previous_exists:
        shutil.copy2(canonical, previous_backup)

    # Só substitui depois do round-trip EXATO e do backup anterior.
    canonical.parent.mkdir(parents=True, exist_ok=True)
    temp_target = canonical.with_name(canonical.name + ".promoting.tmp")
    temp_target.write_text(candidate_text, encoding="utf-8")
    ET.parse(temp_target)
    os.replace(temp_target, canonical)
    final_sha = sha256(canonical)

    manifest = {
        "status": "BLOGGER_MODELO_V20_CANONICAL_PROMOTED",
        "source_blog_id": SOURCE_BLOG_ID,
        "source_title": SOURCE_TITLE,
        "source_url": SOURCE_URL,
        "source_palette": SOURCE_PALETTE,
        "validated_source": str(source),
        "validated_source_sha256": source_sha,
        "expected_validated_sha256": EXPECTED_SOURCE_SHA256,
        "canonical_template": str(canonical),
        "canonical_template_sha256": final_sha,
        "previous_template_existed": previous_exists,
        "previous_template_sha256": previous_sha,
        "previous_template_backup": str(previous_backup) if previous_exists else None,
        "backup_dir": str(backup_dir),
        "candidate_sha256": candidate_sha,
        "roundtrip_theme": str(roundtrip),
        "roundtrip_sha256": roundtrip_sha,
        "roundtrip_exact_match": roundtrip_sha == EXPECTED_SOURCE_SHA256,
        "marker": renderer.MARKER,
        "identity_marker_present_in_canonical": renderer.STYLE_MARKER in candidate_text,
        "title_token_present": renderer.TITLE_TOKEN in candidate_text,
        "url_token_present": renderer.URL_TOKEN in candidate_text,
        "xml_valid": True,
        "renderer_result": roundtrip_payload,
    }
    manifest_path = backup_dir / "promotion-manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
