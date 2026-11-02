#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

INV = Path('blogger_multi_store/data/NETWORK_STORE_INVENTORY_2026-11-01.json')
ROLL = Path('blogger_multi_store/config/network_store_rollout_2026-11-01.json')
CP = Path('CHECKPOINT_ATUAL.md')


def update_inventory() -> None:
    data = json.loads(INV.read_text(encoding='utf-8'))
    s = data['summary']
    if s.get('modern_blogger_auto_policy_guard') != 10 or s.get('store_scaffold_needs_auto_rotation') != 8:
        raise SystemExit(f'CASA_FINALIZE_V2_FAIL inventory precondition: {s}')
    if s.get('duplicate_writer_risks') != 0:
        raise SystemExit('CASA_FINALIZE_V2_FAIL duplicate_writer_risks != 0')
    casa = next((b for b in data['blogs'] if b.get('blog_id') == '4177382081459143374'), None)
    if not casa or casa.get('title') != 'Casa em Ordem' or casa.get('automation_status') != 'store_scaffold_needs_auto_rotation':
        raise SystemExit(f'CASA_FINALIZE_V2_FAIL Casa inventory: {casa}')
    s['modern_blogger_auto_policy_guard'] = 11
    s['store_scaffold_needs_auto_rotation'] = 7
    casa['automation_status'] = 'modern_policy_guard_20x12'
    casa['safe_workflow'] = '.github/workflows/casa_em_ordem_store_safe.yml'
    casa['live_workflow'] = '.github/workflows/casa_em_ordem_store_autonomous.yml'
    casa['note'] = (
        'Concluído em 2026-11-02 como 11ª loja moderna. Primeiro SAFE 41438524634 falhou corretamente antes de qualquer escrita por falso positivo do bloqueio pet dentro de tapete; '
        'SAFE técnico 41438830523 ficou verde, mas inspeção manual do artifact detectou caixa organizadora selecionando cesto e prateleira de banheiro selecionando porta-papel. '
        'Perfil semântico v3 endurecido; SAFE final 41439295948 PASS, 40/40 regressões e artifact revisado manualmente com 20/20 intenções coerentes. '
        'Auditor pré-LIVE 41439709960 PASS 11/11. LIVE 41439797912 PASS com HTTP público 429,200, 20 produtos + 12 hero, Policy Guard público e persistência somente pós-PASS no commit 909382b375afc9dae578d7965873d9ece3736f9c. '
        'Artifact LIVE ID 13138591112 SHA-256 782b0bb47371bdc67d53a7e14e424152f65a2df45a4154fdde6f51f0e1d19cb9. '
        'Leitura independente detectou quatro âncoras deslocadas no hero; correção permanente commit d37e91fb922541f46770a759064e1016552d67b7 e run 41440262021 PASS, 4/4 âncoras corretas e 20+12 preservado. '
        'Schedule diário 08:05 America/Recife habilitado no commit c77915f81c004774992b54487c31afd32ab06efd; auditor pós-schedule 41440836794 PASS 11/11 com proteção permanente do horário e navegação.'
    )
    INV.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def update_rollout() -> None:
    data = json.loads(ROLL.read_text(encoding='utf-8'))
    if data.get('enabled') is not False or data.get('mode') != 'PREPARED_NOT_DEPLOYED':
        raise SystemExit('CASA_FINALIZE_V2_FAIL rollout global não está bloqueado')
    targets = data.get('targets') or []
    casa = [t for t in targets if t.get('blog_id') == '4177382081459143374']
    if len(casa) != 1 or casa[0].get('priority') != 1:
        raise SystemExit('CASA_FINALIZE_V2_FAIL Casa não é target prioridade 1')
    note = (
        'Casa em Ordem integrado ao padrão moderno em 2026-11-02: SAFE final 41439295948 PASS após endurecimento semântico v3 e inspeção manual dos 20 produtos; auditor pré-LIVE 41439709960 PASS 11/11; '
        'LIVE 41439797912 PASS com HTTP público 429,200, 20 produtos + 12 hero, Policy Guard público e persistência pós-PASS commit 909382b375afc9dae578d7965873d9ece3736f9c; '
        'artifact LIVE 13138591112 SHA-256 782b0bb47371bdc67d53a7e14e424152f65a2df45a4154fdde6f51f0e1d19cb9; correção de 4 âncoras do hero validada no run 41440262021; '
        'schedule diário 08:05 America/Recife commit c77915f81c004774992b54487c31afd32ab06efd; auditor pós-schedule 41440836794 PASS 11/11.'
    )
    if not any(x.startswith('Casa em Ordem integrado ao padrão moderno') for x in data['completed_prerequisites']):
        data['completed_prerequisites'].append(note)
    data['targets'] = [t for t in targets if t.get('blog_id') != '4177382081459143374']
    for i, target in enumerate(data['targets'], 1):
        target['priority'] = i
    if len(data['targets']) != 7 or data['targets'][0].get('title') != 'Escolha Certa Online':
        raise SystemExit('CASA_FINALIZE_V2_FAIL fila rollout final inválida')
    ROLL.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def update_checkpoint() -> None:
    cp = CP.read_text(encoding='utf-8')
    checks = [
        '**Última atualização:** 2026-11-02 08:20 America/Recife',
        'O Blogger Policy Guard está integrado em **10 pipelines modernos**',
        '# 9. FILA RESTANTE — 8 BLOGS',
        '# 10. PRÓXIMO BLOCO PERMITIDO — CASA EM ORDEM, NÃO INICIADO',
    ]
    missing = [x for x in checks if x not in cp]
    if missing:
        raise SystemExit(f'CASA_FINALIZE_V2_FAIL checkpoint preconditions: {missing}')

    cp = cp.replace('**Última atualização:** 2026-11-02 08:20 America/Recife', '**Última atualização:** 2026-11-02 09:00 America/Recife', 1)
    cp = cp.replace('antes das conclusões de Conecta Achados e Estilo no Dia a Dia', 'antes das conclusões de Conecta Achados, Estilo no Dia a Dia e Casa em Ordem', 1)
    cp = cp.replace('O Blogger Policy Guard está integrado em **10 pipelines modernos**', 'O Blogger Policy Guard está integrado em **11 pipelines modernos**', 1)
    cp = cp.replace('10. **Estilo no Dia a Dia**', '10. Estilo no Dia a Dia\n11. **Casa em Ordem**', 1)
    cp = cp.replace('- `modern_blogger_auto_policy_guard: 10`', '- `modern_blogger_auto_policy_guard: 11`', 1)
    cp = cp.replace('- `store_scaffold_needs_auto_rotation: 8`', '- `store_scaffold_needs_auto_rotation: 7`', 1)

    audit_re = re.compile(
        r'O auditor cobre os 10 SAFE/LIVE modernos, `blogger_stores/src/\*\*/\*?`.*?`SAFE/LIVE 10/10 protegidos; writers legados manual-only; sem ocultação/desativação detectada do aviso nativo de cookies\.`',
        re.S,
    )
    # O glob está escrito literalmente como blogger_stores/src/** no Markdown; use bloco exato se regex não casar.
    old_audit = '''O auditor cobre os 10 SAFE/LIVE modernos, `blogger_stores/src/**`, writers legados duplicados e proteção do aviso nativo de cookies.\n\nÚltima validação, após habilitar o schedule do Estilo no Dia a Dia:\n\n- commit do schedule `821fb4e6a7ef16348c7432a7094065ba56b418b2`\n- run `41435835886` — **SUCCESS**\n- job `125245260514`\n- `blogger_policy_guard_self_test: 13/13 OK`\n- `BLOGGER_POLICY_REPO_AUDIT_PASS`\n- `SAFE/LIVE 10/10 protegidos; writers legados manual-only; sem ocultação/desativação detectada do aviso nativo de cookies.`'''
    new_audit = '''O auditor cobre os **11 SAFE/LIVE modernos**, `blogger_stores/src/**`, writers legados duplicados, proteção do aviso nativo de cookies e o schedule/navegação final do Casa em Ordem.\n\nÚltima validação, após habilitar o schedule do Casa em Ordem:\n\n- commit do schedule `c77915f81c004774992b54487c31afd32ab06efd`\n- commit do reforço permanente do auditor `d7e6c29cd519360ec1a2421986813ccc6263c729`\n- run `41440836794` — **SUCCESS**\n- job `125261986171`\n- `blogger_policy_guard_self_test: 13/13 OK`\n- `BLOGGER_POLICY_REPO_AUDIT_PASS`\n- `SAFE/LIVE 11/11 protegidos; Casa em Ordem schedule 08:05 protegido; writers legados manual-only; sem ocultação/desativação detectada do aviso nativo de cookies.`'''
    if old_audit not in cp:
        raise SystemExit('CASA_FINALIZE_V2_FAIL bloco auditor antigo ausente')
    cp = cp.replace(old_audit, new_audit, 1)

    section = '''# 8. CASA EM ORDEM — CONCLUÍDO COMO 11ª LOJA MODERNA\n\nAlvo:\n\n- Blog ID `4177382081459143374`\n- Page LOJA ID `4031853959690608178`\n- Store Post ID `5566188787681469799`\n- Page `https://casa-em-ordem-pratica.blogspot.com/p/loja.html`\n- Post `https://casa-em-ordem-pratica.blogspot.com/2026/11/loja.html`\n- SAFE `.github/workflows/casa_em_ordem_store_safe.yml`\n- LIVE `.github/workflows/casa_em_ordem_store_autonomous.yml`\n- motor `blogger_stores/src/casa_em_ordem_store.py`\n- histórico independente `blogger_stores/data/casa_em_ordem_rotation.json`\n\nPerfil final: Organização & Armazenamento; Quarto & Roupa de Cama; Banheiro & Organização; Lavanderia & Limpeza; Decoração & Conforto — 5 categorias x 4 intenções.\n\n## 8.1 SAFE e revisão semântica\n\n- primeiro SAFE `41438524634` falhou corretamente antes de qualquer escrita: o bloqueio `pet` casava dentro de `tapete`;\n- SAFE técnico `41438830523` ficou verde, mas não foi aceito: inspeção manual encontrou cesto em `caixa organizadora` e porta-papel em `prateleira banheiro`;\n- perfil v3 endurecido;\n- SAFE final `41439295948` — **SUCCESS**;\n- 40/40 regressões semânticas;\n- 20 produtos / 20 intenções / links 20/20;\n- fallback 0 / carry 0;\n- artifact SAFE final `13136984336`;\n- SHA-256 `6d5a9c16eee3e3184a22ed399e3d65cbd69ae46d2a0daf2016d2fe9e377e06eb`;\n- revisão manual final 20/20 coerente.\n\n## 8.2 Auditor pré-LIVE\n\n- run `41439709960` — **SUCCESS**;\n- job `125258208273`;\n- Policy Guard 13/13;\n- `BLOGGER_POLICY_REPO_AUDIT_PASS`;\n- `SAFE/LIVE 11/11 protegidos`.\n\n## 8.3 LIVE final\n\n- run `41439797912` — **SUCCESS**;\n- job `125258499502`;\n- Store 20 + hero 12;\n- gate público HTTP `429 → 200`;\n- `BLOGGER_POLICY_GUARD_PUBLIC_PASS: 20 products + 12 hero`;\n- persistência somente depois do PASS público;\n- commit automático `909382b375afc9dae578d7965873d9ece3736f9c`;\n- artifact LIVE ID `13138591112`;\n- SHA-256 `782b0bb47371bdc67d53a7e14e424152f65a2df45a4154fdde6f51f0e1d19cb9`.\n\n## 8.4 Leitura independente e navegação\n\nA leitura direta do Blogger confirmou a seleção e detectou quatro botões do hero com rótulo correto e âncora deslocada. A correção ocorreu sem nova rotação de produtos.\n\n- commit do motor `d37e91fb922541f46770a759064e1016552d67b7`;\n- run `41440262021` — **SUCCESS**;\n- job `125260056522`;\n- `CASA_ORDEM_NAV_FIX_PASS: 4/4 âncoras corretas; 20+12 preservado`;\n- segunda leitura independente confirmou os quatro destinos e os 20 produtos inalterados.\n\n## 8.5 Schedule final\n\n- `cron: "5 8 * * *"`;\n- `timezone: "America/Recife"`;\n- commit `c77915f81c004774992b54487c31afd32ab06efd`;\n- auditor reforçado para proteger horário e quatro âncoras;\n- commit do auditor `d7e6c29cd519360ec1a2421986813ccc6263c729`;\n- auditor pós-schedule `41440836794` — **SUCCESS**;\n- job `125261986171`;\n- Policy Guard 13/13;\n- `BLOGGER_POLICY_REPO_AUDIT_PASS`;\n- `SAFE/LIVE 11/11 protegidos; Casa em Ordem schedule 08:05 protegido`.\n\nCasa em Ordem está **CONCLUÍDO** como `modern_policy_guard_20x12`. Não reabrir sem regressão concreta.\n\n---\n\n'''
    marker = '# 8. OUTRAS CAMADAS DE PROTEÇÃO PRESERVADAS'
    if marker not in cp:
        raise SystemExit('CASA_FINALIZE_V2_FAIL marcador seção 8 ausente')
    cp = cp.replace(marker, section + '# 9. OUTRAS CAMADAS DE PROTEÇÃO PRESERVADAS', 1)

    cp = cp.replace('# 9. FILA RESTANTE — 8 BLOGS', '# 10. FILA RESTANTE — 7 BLOGS', 1)
    old_queue = '''1. **Casa em Ordem**\n2. Escolha Certa Online\n3. Achados que Valem\n4. Guia de Achados & Ofertas\n5. Moda e Ofertas\n6. Achadinhos de Beleza\n7. Radar Tech BR Blogger\n8. Cozinha Sem Complicação'''
    new_queue = '''1. **Escolha Certa Online**\n2. Achados que Valem\n3. Guia de Achados & Ofertas\n4. Moda e Ofertas\n5. Achadinhos de Beleza\n6. Radar Tech BR Blogger\n7. Cozinha Sem Complicação'''
    if old_queue not in cp:
        raise SystemExit('CASA_FINALIZE_V2_FAIL fila antiga ausente')
    cp = cp.replace(old_queue, new_queue, 1)

    cp = cp.replace('# 10. PRÓXIMO BLOCO PERMITIDO — CASA EM ORDEM, NÃO INICIADO', '# 11. PRÓXIMO BLOCO PERMITIDO — ESCOLHA CERTA ONLINE, NÃO INICIADO', 1)
    next_re = re.compile(r'Alvo inventariado:\n\n- Blog ID `4177382081459143374`.*?\*\*Não iniciar Casa em Ordem automaticamente\. Aguardar novo `continue` do usuário\.\*\*', re.S)
    new_next = '''Alvo inventariado:\n\n- Blog ID `5151950717041967683`\n- Page LOJA ID `3334029815604129982`\n- Store Post ID `5474604520207119855`\n- Page `https://escolha-certa-online.blogspot.com/p/loja.html`\n- Post `https://escolha-certa-online.blogspot.com/2026/11/loja.html`\n- estado atual `store_scaffold_needs_auto_rotation`\n- perfil semântico ainda precisa ser definido e validado\n\n**Não iniciar Escolha Certa Online automaticamente. Aguardar novo `continue` do usuário.**'''
    cp, n = next_re.subn(new_next, cp, count=1)
    if n != 1:
        raise SystemExit(f'CASA_FINALIZE_V2_FAIL next block replacements={n}')

    cp = cp.replace('# 11. REGRAS ESSENCIAIS PARA FUTURAS EXECUÇÕES', '# 12. REGRAS ESSENCIAIS PARA FUTURAS EXECUÇÕES', 1)
    cp = cp.replace('Não reiniciar diagnóstico de Vitrine, Achados, Conecta ou Estilo sem evidência concreta de regressão.', 'Não reiniciar diagnóstico de Vitrine, Achados, Conecta, Estilo ou Casa em Ordem sem evidência concreta de regressão.', 1)
    cp = cp.replace('# 12. BACKUP / RECUPERAÇÃO', '# 13. BACKUP / RECUPERAÇÃO', 1)
    cp = cp.replace('Como o R3 é anterior às conclusões de Conecta e Estilo, um próximo backup completo deverá incluir os commits desses dois blocos.', 'Como o R3 é anterior às conclusões de Conecta, Estilo e Casa em Ordem, um próximo backup completo deverá incluir os commits desses três blocos.', 1)
    old_tail = '- Estilo no Dia a Dia = 10ª loja moderna concluída;\n- auditor permanente = **10/10**;\n- inventário = **10 modernas / 8 restantes**;\n- próximo bloco permitido = **Casa em Ordem**, somente após comando explícito do usuário.'
    new_tail = '- Estilo no Dia a Dia = 10ª loja moderna concluída;\n- Casa em Ordem = 11ª loja moderna concluída;\n- auditor permanente = **11/11**;\n- inventário = **11 modernas / 7 restantes**;\n- próximo bloco permitido = **Escolha Certa Online**, somente após comando explícito do usuário.'
    if old_tail not in cp:
        raise SystemExit('CASA_FINALIZE_V2_FAIL tail antigo ausente')
    cp = cp.replace(old_tail, new_tail, 1)
    CP.write_text(cp, encoding='utf-8')


def validate() -> None:
    inv = json.loads(INV.read_text(encoding='utf-8'))
    roll = json.loads(ROLL.read_text(encoding='utf-8'))
    cp = CP.read_text(encoding='utf-8')
    casa = next(b for b in inv['blogs'] if b['blog_id'] == '4177382081459143374')
    checks = {
        'inventory_modern_11': inv['summary']['modern_blogger_auto_policy_guard'] == 11,
        'inventory_remaining_7': inv['summary']['store_scaffold_needs_auto_rotation'] == 7,
        'casa_modern': casa['automation_status'] == 'modern_policy_guard_20x12',
        'rollout_disabled': roll['enabled'] is False and roll['mode'] == 'PREPARED_NOT_DEPLOYED',
        'targets_7': len(roll['targets']) == 7,
        'next_escolha': roll['targets'][0]['title'] == 'Escolha Certa Online',
        'checkpoint_casa': 'CASA EM ORDEM — CONCLUÍDO COMO 11ª LOJA MODERNA' in cp,
        'checkpoint_next': 'PRÓXIMO BLOCO PERMITIDO — ESCOLHA CERTA ONLINE' in cp,
        'checkpoint_11_7': 'inventário = **11 modernas / 7 restantes**' in cp,
    }
    bad = [k for k, ok in checks.items() if not ok]
    if bad:
        raise SystemExit(f'CASA_FINALIZE_V2_FAIL validation: {bad}')
    print('CASA_FINALIZE_STATE_PASS: inventory=11/7 casa=modern rollout=disabled targets=7 next=Escolha Certa Online checkpoint=updated')


if __name__ == '__main__':
    update_inventory()
    update_rollout()
    update_checkpoint()
    validate()
