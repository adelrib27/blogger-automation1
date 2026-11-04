#!/usr/bin/env python3
"""Read-only transaction preview for a Shopee V23 SAFE_READY to Blogger V31.

Uses the canonical V31 publisher's validation/render code. NO Blogger update.
Copies current page and candidate to a temporary artifact for forensic review.
"""
from __future__ import annotations
import argparse
from datetime import datetime,timezone
from hashlib import sha256
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'v31_core'))
from v31_from_v23_selection import convert_selection
from v31_store_safe import validate_profile
from v31_daily_page_publisher import (LAB_ID,PAGE_ID,require_guard,create_service,
    fetch_page,inspect_mutable_page,prepare_page,public_check)


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument('--repo-root',type=Path,required=True)
    p.add_argument('--selection',type=Path,required=True)
    p.add_argument('--profile',type=Path,required=True)
    p.add_argument('--output-dir',type=Path,required=True)
    args=p.parse_args()
    try:
        profile=validate_profile(json.loads(args.profile.read_text(encoding='utf8')))
        if profile['blog_id']!=LAB_ID or profile['page_id']!=PAGE_ID:
            raise RuntimeError('ALVO NAO AUTORIZADO')
        raw=json.loads(args.selection.read_text(encoding='utf8'))
        converted=convert_selection(raw,profile,require_product_allowed=require_guard(args.repo_root))
        if len(converted['products'])!=16 or sum(bool(x['image_url']) for x in converted['products'])!=16:
            raise RuntimeError('Quantidade ou imagens incompletas')
        service=create_service(args.repo_root)
        page=fetch_page(service)
        original,before=inspect_mutable_page(page,profile)
        candidate,proof=prepare_page(original,converted,profile)
        if proof['cards']!=16 or proof['affiliate_links']!=16 or proof['photos']!=16:
            raise RuntimeError('Contrato de cards/links/imagens falhou')
        public=public_check(profile,16)
        if args.output_dir.exists():raise RuntimeError('Diretorio de saida ja existe, evitando overwrite')
        args.output_dir.mkdir(parents=True,exist_ok=False)
        (args.output_dir/'LOJA_ORIGINAL_BACKUP.html').write_text(original,encoding='utf8',newline='')
        (args.output_dir/'LOJA_CANDIDATA_NAO_PUBLICAR.html').write_text(candidate,encoding='utf8',newline='')
        report={'status':'V31_LAB_PREFLIGHT_SAFE_PASS','publication':False,
            'blog_id':LAB_ID,'page_id':PAGE_ID,'source_selection_sha256':sha256(args.selection.read_bytes()).hexdigest(),
            'source_updated_at':page.get('updated'),'before':before,'candidate':proof,
            'candidate_sha256':sha256(candidate.encode('utf8')).hexdigest(),
            'public_before':public,'timestamp':datetime.now(timezone.utc).isoformat()}
        (args.output_dir/'RELATORIO_SAFE.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
        print(json.dumps(report,ensure_ascii=False))
        return 0
    except Exception as e:
        print(json.dumps({'status':'V31_LAB_PREFLIGHT_BLOCKED','error_type':type(e).__name__,
                          'reason':str(e)[:240]},ensure_ascii=False),file=sys.stderr)
        return 2

if __name__=='__main__':raise SystemExit(main())