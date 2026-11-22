#!/usr/bin/env python3
"""V31: corrige FeaturedPost1 que reserva o artigo mais recente fora de Blog1.

Uso:
  python blogger_themes/tools/fix_featuredpost1_legacy_v31.py \
    --input TEMA_EXPORTADO_PELO_BLOGGER.xml \
    --output TEMA_CORRIGIDO.xml

Operação offline, segura e idempotente. Sempre exporte o tema LIVE do próprio
blog antes de corrigir. Não instala no Blogger, não toca posts nem API.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path
from xml.etree import ElementTree as ET

SECTION = re.compile(
    r"<b:section\b[^>]*\bid=(['\"])featured_post\1[^>]*>.*?</b:section>",
    re.DOTALL,
)
WIDGET_ID = re.compile(r"<b:widget\b[^>]*\bid=(['\"])FeaturedPost1\1")
BLOG1_ID = re.compile(r"<b:widget\b[^>]*\bid=(['\"])Blog1\1")
OLD_SELECT = "#FeaturedPost1 .post-wrapper, #Blog1 .post-wrapper"
NEW_SELECT = "#Blog1 .post-wrapper"


def patch(source: str) -> tuple[str, dict]:
    matches = list(SECTION.finditer(source))
    if len(matches) != 1:
        raise ValueError("Encontrada quantidade inesperada de sections featured_post: " + str(len(matches)))
    section = matches[0].group()
    if len(WIDGET_ID.findall(section)) != 1 or section.count("<b:widget ") != 1:
        raise ValueError("A section featured_post não contém apenas o FeaturedPost1: revisão manual obrigatória")
    if len(BLOG1_ID.findall(source)) != 1:
        raise ValueError("Blog1 ausente ou duplicado: abortado")
    if not source.count("ub-v21-featured"):
        raise ValueError("Tema sem carrossel universal V31 esperado: abortado")

    initial = section[:section.index(">") + 1]
    if "showaddelement" not in initial:
        raise ValueError("Seção sem atributo padrão showaddelement: revisar tema antes")
    # Mantém a seção e o mesmo ID de gadget para impedir migração
    # automática do FeaturedPost1 para outra seção pelo Blogger.
    disabled = (
        initial
        + "\n  <b:widget id='FeaturedPost1' locked='true' title='Destaque legado desativado'"
        + " type='FeaturedPost' visible='false'>\n"
        + "    <b:widget-settings>\n"
        + "      <b:widget-setting name='showSnippet'>false</b:widget-setting>\n"
        + "      <b:widget-setting name='showPostTitle'>true</b:widget-setting>\n"
        + "      <b:widget-setting name='showFirstImage'>true</b:widget-setting>\n"
        + "      <b:widget-setting name='useMostRecentPost'>false</b:widget-setting>\n"
        + "    </b:widget-settings>\n"
        + "    <b:includable id='main' var='this'/>\n"
        + "  </b:widget>\n"
        + "</b:section>"
    )
    fixed = source[:matches[0].start()] + disabled + source[matches[0].end():]
    if OLD_SELECT in fixed:
        if fixed.count(OLD_SELECT) != 1:
            raise ValueError("Seletor FeaturedPost1 duplicado: revisar antes")
        fixed = fixed.replace(OLD_SELECT, NEW_SELECT, 1)
    elif "querySelectorAll('#Blog1 .post-wrapper')" not in fixed:
        raise ValueError("Seletor do carrossel V31 desconhecido: abortado")

    ET.fromstring(source)
    ET.fromstring(fixed)
    if len(WIDGET_ID.findall(fixed)) != 1 or len(BLOG1_ID.findall(fixed)) != 1:
        raise ValueError("IDs de widgets alterados inesperadamente")
    if not re.search(r"<b:widget\b[^>]*\bid=['\"]FeaturedPost1['\"][^>]*\bvisible=['\"]false['\"]", fixed):
        raise ValueError("FeaturedPost1 não ficou desativado")
    if "useMostRecentPost'>true" in fixed or 'useMostRecentPost">true' in fixed:
        raise ValueError("Configuração antiga useMostRecentPost ainda está ativa")
    return fixed, {
        "featuredpost_legacy_disabled": True,
        "carousel_blog1_only": "querySelectorAll('#Blog1 .post-wrapper')" in fixed,
        "bytes": len(fixed.encode("utf-8")),
        "sha256": hashlib.sha256(fixed.encode("utf-8")).hexdigest(),
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args()
    a, b = args.input.resolve(), args.output.resolve()
    if a == b:
        raise SystemExit("Input e output não podem ter o mesmo caminho")
    if not a.is_file():
        raise SystemExit("XML exportado do Blogger não localizado")
    original = a.read_text(encoding="utf-8-sig")
    fixed, evidence = patch(original)
    if b.exists():
        raise SystemExit("Output já existe; não sobrescrever versões anteriores")
    backup = b.with_suffix(".ANTES_C95_BACKUP.xml")
    if backup.exists():
        raise SystemExit("Backup já existe; abortado sem sobrescrever")
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(a, backup)
    b.write_text(fixed, encoding="utf-8")
    evidence.update({
        "source_export": str(a),
        "theme_output": str(b),
        "source_backup": str(backup),
        "live_blogger_installation": False,
    })
    print(json.dumps(evidence, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
