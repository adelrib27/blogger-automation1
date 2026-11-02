#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
INV_PATH = ROOT / "blogger_multi_store/data/NETWORK_STORE_INVENTORY_2026-11-01.json"
ROLL_PATH = ROOT / "blogger_multi_store/config/network_store_rollout_2026-11-01.json"
CP_PATH = ROOT / "CHECKPOINT_ATUAL.md"
BLOG_ID = "5151950717041967683"


def die(msg: str) -> None:
    raise SystemExit("ESCOLHA_FINALIZE_FAIL: " + msg)


def update_inventory() -> None:
    inv = json.loads(INV_PATH.read_text(encoding="utf-8"))
    summary = inv.get("summary") or {}
    expected = {
        "modern_blogger_auto_policy_guard": 11,
        "modern_blogger_auto_20x12_needs_policy_guard_upgrade": 0,
        "store_scaffold_needs_auto_rotation": 7,
        "duplicate_writer_risks": 0,
    }
    for key, value in expected.items():
        if summary.get(key) != value:
            die(f"inventory precondition {key}={summary.get(key)!r}, esperado {value!r}")
    escolha = next((b for b in inv.get("blogs", []) if b.get("blog_id") == BLOG_ID), None)
    if not escolha or escolha.get("title") != "Escolha Certa Online":
        die("Escolha Certa Online ausente no inventário")
    if escolha.get("automation_status") != "store_scaffold_needs_auto_rotation":
        die(f"status inesperado do Escolha: {escolha.get('automation_status')}")

    summary["modern_blogger_auto_policy_guard"] = 12
    summary["store_scaffold_needs_auto_rotation"] = 6
    escolha["automation_status"] = "modern_policy_guard_20x12"
    escolha["safe_workflow"] = ".github/workflows/escolha_certa_online_store_safe.yml"
    escolha["live_workflow"] = ".github/workflows/escolha_certa_online_store_autonomous.yml"
    escolha["note"] = (
        "Concluído em 2026-11-02 como 12ª loja moderna. SAFE final 41444290462 PASS, job 125274237954, "
        "Policy Guard 20/20, regressão semântica 40/40, fallback=0/carry=0 e artifact 13140694375 SHA-256 "
        "99c68b44800270edf7e03e4a9c664e0bff3a88d8be295e0da67e250c0291c586 revisado manualmente com 20/20 intenções coerentes. "
        "Auditor pré-LIVE 41445104053 PASS 12/12. LIVE 41445195745 falhou antes de qualquer escrita por erros transitórios Shopee System Error 10000; "
        "LIVE 41445486532 publicou e validou identidade autenticada, mas recebeu 12x HTTP 429 no gate público e não persistiu; fail-closed comprovado. "
        "LIVE final 41446386899 PASS, job 125280409141, HTTP público 429,429,429,429,200, store=20, hero=12, Policy Guard público e identidade correta; "
        "persistência somente pós-PASS no commit 4acc7ef5fbfb343bf3fd47cfc07b1b1f57d47ca9. Artifact LIVE 13142278325 SHA-256 "
        "321e646e4b60a636c50199c407b3885b0c18e7231d9379fe5c2639bc18c6f5a9. Leitura independente do Blogger confirmou 20+12, cinco categorias, "
        "quatro âncoras, disclosure e links patrocinados. Schedule diário 08:20 America/Recife habilitado no commit "
        "92a6497a30aa5b365fefddf8ad31b1ca53781ab8 sem gatilho push; auditor pós-schedule 41447386251 PASS 12/12 no commit "
        "2d3c536dc499a7b193a9eb20fec97dda2c1263b8."
    )
    INV_PATH.write_text(json.dumps(inv, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def update_rollout() -> None:
    roll = json.loads(ROLL_PATH.read_text(encoding="utf-8"))
    if roll.get("enabled") is not False or roll.get("mode") != "PREPARED_NOT_DEPLOYED":
        die("rollout global não está desabilitado/prepared")
    targets = roll.get("targets") or []
    escolha = [t for t in targets if t.get("blog_id") == BLOG_ID]
    if len(escolha) != 1 or escolha[0].get("priority") != 1:
        die("Escolha Certa Online não é exatamente o alvo prioridade 1")
    done = (
        "Escolha Certa Online integrado ao padrão moderno em 2026-11-02: SAFE final 41444290462 PASS com 40/40 regressões, 20/20 Policy Guard e artifact "
        "13140694375 SHA-256 99c68b44800270edf7e03e4a9c664e0bff3a88d8be295e0da67e250c0291c586 revisado manualmente; auditor pré-LIVE 41445104053 PASS 12/12; "
        "primeiro LIVE 41445195745 falhou antes da escrita por Shopee System Error 10000; segundo LIVE 41445486532 comprovou fail-closed ao não persistir após 12x HTTP 429; "
        "LIVE final 41446386899 PASS com HTTP 429,429,429,429,200, 20 produtos + 12 hero, Policy Guard público e persistência pós-PASS commit "
        "4acc7ef5fbfb343bf3fd47cfc07b1b1f57d47ca9; artifact LIVE 13142278325 SHA-256 321e646e4b60a636c50199c407b3885b0c18e7231d9379fe5c2639bc18c6f5a9; "
        "leitura independente do Blogger confirmou a saída; schedule diário 08:20 America/Recife commit 92a6497a30aa5b365fefddf8ad31b1ca53781ab8 sem push; auditor pós-schedule "
        "41447386251 PASS 12/12, commit 2d3c536dc499a7b193a9eb20fec97dda2c1263b8."
    )
    if not any(x.startswith("Escolha Certa Online integrado ao padrão moderno") for x in roll.get("completed_prerequisites", [])):
        roll.setdefault("completed_prerequisites", []).append(done)
    roll["targets"] = [t for t in targets if t.get("blog_id") != BLOG_ID]
    for i, target in enumerate(roll["targets"], 1):
        target["priority"] = i
    if len(roll["targets"]) != 6 or roll["targets"][0].get("title") != "Achados que Valem":
        die("fila pós-Escolha não ficou com 6 alvos e Achados que Valem em primeiro")
    ROLL_PATH.write_text(json.dumps(roll, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def update_checkpoint() -> None:
    cp = CP_PATH.read_text(encoding="utf-8")
    required = [
        "O Blogger Policy Guard está integrado em **11 pipelines modernos**",
        "11. **Casa em Ordem**",
        "- `modern_blogger_auto_policy_guard: 11`",
        "- `store_scaffold_needs_auto_rotation: 7`",
        "O auditor cobre os **11 SAFE/LIVE modernos**",
        "# 10. FILA RESTANTE — 7 BLOGS",
        "# 11. PRÓXIMO BLOCO PERMITIDO — ESCOLHA CERTA ONLINE, NÃO INICIADO",
    ]
    missing = [x for x in required if x not in cp]
    if missing:
        die(f"checkpoint preconditions ausentes: {missing}")

    now = datetime.now(ZoneInfo("America/Recife")).strftime("%Y-%m-%d %H:%M America/Recife")
    cp = re.sub(r"\*\*Última atualização:\*\* .*?America/Recife", f"**Última atualização:** {now}", cp, count=1)
    cp = cp.replace(
        "antes das conclusões de Conecta Achados, Estilo no Dia a Dia e Casa em Ordem",
        "antes das conclusões de Conecta Achados, Estilo no Dia a Dia, Casa em Ordem e Escolha Certa Online",
        1,
    )
    cp = cp.replace("O Blogger Policy Guard está integrado em **11 pipelines modernos**", "O Blogger Policy Guard está integrado em **12 pipelines modernos**", 1)
    cp = cp.replace("11. **Casa em Ordem**", "11. Casa em Ordem\n12. **Escolha Certa Online**", 1)
    cp = cp.replace("- `modern_blogger_auto_policy_guard: 11`", "- `modern_blogger_auto_policy_guard: 12`", 1)
    cp = cp.replace("- `store_scaffold_needs_auto_rotation: 7`", "- `store_scaffold_needs_auto_rotation: 6`", 1)

    audit_start = cp.find("O auditor cobre os **11 SAFE/LIVE modernos**")
    audit_end = cp.find("\n\n---\n\n# 4. VITRINE PRÁTICA", audit_start)
    if audit_start < 0 or audit_end < 0:
        die("bloco auditor antigo não localizado")
    new_audit = """O auditor cobre os **12 SAFE/LIVE modernos**, `blogger_stores/src/**`, writers legados duplicados, proteção do aviso nativo de cookies e os schedules/navegações finais de Casa em Ordem e Escolha Certa Online.

Última validação, após habilitar o schedule do Escolha Certa Online:

- commit do schedule `92a6497a30aa5b365fefddf8ad31b1ca53781ab8`
- commit do reforço permanente do auditor `2d3c536dc499a7b193a9eb20fec97dda2c1263b8`
- run `41447386251` — **SUCCESS**
- job `125283757493`
- `blogger_policy_guard_self_test: 13/13 OK`
- `BLOGGER_POLICY_REPO_AUDIT_PASS`
- `SAFE/LIVE 12/12 protegidos; Casa em Ordem schedule 08:05 e Escolha Certa Online schedule 08:20 protegidos; writers legados manual-only; sem ocultação/desativação detectada do aviso nativo de cookies.`"""
    cp = cp[:audit_start] + new_audit + cp[audit_end:]

    escolha_section = """# 9. ESCOLHA CERTA ONLINE — CONCLUÍDO COMO 12ª LOJA MODERNA

Alvo:

- Blog ID `5151950717041967683`
- Page LOJA ID `3334029815604129982`
- Store Post ID `5474604520207119855`
- Page `https://escolha-certa-online.blogspot.com/p/loja.html`
- Post `https://escolha-certa-online.blogspot.com/2026/11/loja.html`
- SAFE `.github/workflows/escolha_certa_online_store_safe.yml`
- LIVE `.github/workflows/escolha_certa_online_store_autonomous.yml`
- motor `blogger_stores/src/escolha_certa_online_store.py`
- histórico independente `blogger_stores/data/escolha_certa_online_rotation.json`

Perfil final: Banheiro & Acessórios; Cama & Enxoval; Organização & Utilidades; Decoração & Jardim; Limpeza & Praticidade — 5 categorias x 4 intenções, alinhadas aos posts editoriais reais do blog.

## 9.1 SAFE e revisão semântica

- SAFE final `41444290462` — **SUCCESS**;
- job `125274237954`;
- Policy Guard 13/13 e 20/20 produtos permitidos;
- regressão semântica `40/40`;
- 20 produtos / 20 intenções / links 20/20;
- fallback 0 / carry 0;
- artifact SAFE `13140694375`;
- SHA-256 `99c68b44800270edf7e03e4a9c664e0bff3a88d8be295e0da67e250c0291c586`;
- revisão manual final: 20/20 títulos coerentes com as intenções.

## 9.2 Auditor pré-LIVE

- commit `39b16791a3f65bc046401890989c6d53a40466dc`;
- run `41445104053` — **SUCCESS**;
- job `125276140405`;
- `blogger_policy_guard_self_test: 13/13 OK`;
- `BLOGGER_POLICY_REPO_AUDIT_PASS`;
- `SAFE/LIVE 12/12 protegidos`.

## 9.3 Fail-closed comprovado em duas tentativas

Primeiro LIVE:

- run `41445195745` — **FAILURE** antes de qualquer escrita Blogger;
- job `125276442640`;
- causa: erros transitórios `Shopee System Error 10000`, deixando `lencol 400 fios` sem candidato válido;
- Store, hero, identidade e persistência foram pulados.

Segundo LIVE:

- run `41445486532` — **FAILURE**;
- job `125277398761`;
- SAFE fresco, Policy Guard, DRY-RUN e writers 20+12 passaram;
- identidade autenticada passou;
- gate público recebeu **12 respostas HTTP 429**;
- persistência foi pulada;
- artifact `13143020710`;
- SHA-256 `7c27776eab3683b91e54512915521c995e014691686a269903c468002cb7b0ab`.

Isso confirmou que nem falha da Shopee nem indisponibilidade pública permitem persistência antecipada.

## 9.4 LIVE final

- kickoff commit `f1924dd2118e78657e6f6351f0603b9ade4da4c0`;
- run `41446386899` — **SUCCESS**;
- job `125280409141`;
- regressão semântica 40/40;
- seleção fresca 20/20, fallback=0, carry=0;
- Policy Guard pré-LIVE 20/20;
- identidade, Store e hero DRY-RUN PASS;
- Store 20 + hero 12 publicados;
- gate público: HTTP `429 → 429 → 429 → 429 → 200`;
- `PUBLIC_COUNTS_ATTEMPT_5: store=20 hero=12`;
- `BLOGGER_POLICY_GUARD_PUBLIC_PASS: 20 products + 12 hero`;
- `ESCOLHA_CERTA_IDENTITY_PUBLIC_PASS`;
- persistência somente depois do PASS público;
- commit automático `4acc7ef5fbfb343bf3fd47cfc07b1b1f57d47ca9`;
- artifact LIVE `13142278325`;
- SHA-256 verificado localmente `321e646e4b60a636c50199c407b3885b0c18e7231d9379fe5c2639bc18c6f5a9`.

## 9.5 Leitura independente do Blogger

Leitura direta pós-LIVE confirmou:

- status LIVE;
- Page Loja e Store Post IDs preservados;
- layout amplo aprovado preservado;
- 20 Store cards e 12 hero;
- cinco categorias próprias;
- quatro botões do hero com âncoras corretas;
- disclosure de afiliado;
- links `rel=\"nofollow sponsored noopener\"`;
- identidade genérica de tecnologia/beleza removida;
- os mesmos 20 produtos persistidos pelo LIVE final.

## 9.6 Schedule final e auditor pós-schedule

Após verificar diretamente os horários dos 11 writers anteriores, `08:20 America/Recife` estava livre.

- workflow `.github/workflows/escolha_certa_online_store_autonomous.yml`;
- `cron: \"20 8 * * *\"`;
- `timezone: \"America/Recife\"`;
- gatilho `push` removido; workflow final usa apenas `workflow_dispatch + schedule`;
- commit `92a6497a30aa5b365fefddf8ad31b1ca53781ab8`;
- auditor reforçado para proteger horário, ausência de push e quatro âncoras;
- commit `2d3c536dc499a7b193a9eb20fec97dda2c1263b8`;
- auditor pós-schedule `41447386251` — **SUCCESS**;
- job `125283757493`;
- Policy Guard 13/13;
- `BLOGGER_POLICY_REPO_AUDIT_PASS`;
- `SAFE/LIVE 12/12 protegidos; Casa em Ordem schedule 08:05 e Escolha Certa Online schedule 08:20 protegidos`.

Escolha Certa Online está **CONCLUÍDO** como `modern_policy_guard_20x12`. Não reabrir sem evidência concreta de regressão.

---

"""
    marker = "# 9. OUTRAS CAMADAS DE PROTEÇÃO PRESERVADAS"
    if marker not in cp:
        die("marcador de OUTRAS CAMADAS ausente")
    cp = cp.replace(marker, escolha_section + "# 10. OUTRAS CAMADAS DE PROTEÇÃO PRESERVADAS", 1)

    cp = cp.replace("# 10. FILA RESTANTE — 7 BLOGS", "# 11. FILA RESTANTE — 6 BLOGS", 1)
    old_queue = """1. **Escolha Certa Online**
2. Achados que Valem
3. Guia de Achados & Ofertas
4. Moda e Ofertas
5. Achadinhos de Beleza
6. Radar Tech BR Blogger
7. Cozinha Sem Complicação"""
    new_queue = """1. **Achados que Valem**
2. Guia de Achados & Ofertas
3. Moda e Ofertas
4. Achadinhos de Beleza
5. Radar Tech BR Blogger
6. Cozinha Sem Complicação"""
    if old_queue not in cp:
        die("fila antiga não encontrada")
    cp = cp.replace(old_queue, new_queue, 1)

    cp = cp.replace(
        "# 11. PRÓXIMO BLOCO PERMITIDO — ESCOLHA CERTA ONLINE, NÃO INICIADO",
        "# 12. PRÓXIMO BLOCO PERMITIDO — ACHADOS QUE VALEM, NÃO INICIADO",
        1,
    )
    old_next = """Alvo inventariado:

- Blog ID `5151950717041967683`
- Page LOJA ID `3334029815604129982`
- Store Post ID `5474604520207119855`
- Page `https://escolha-certa-online.blogspot.com/p/loja.html`
- Post `https://escolha-certa-online.blogspot.com/2026/11/loja.html`
- estado atual `store_scaffold_needs_auto_rotation`
- perfil semântico ainda precisa ser definido e validado

**Não iniciar Escolha Certa Online automaticamente. Aguardar novo `continue` do usuário.**"""
    new_next = """Alvo inventariado:

- Blog ID `7527651041649593600`
- Page LOJA ID `2615453333851618808`
- Store Post ID `953731363427123084`
- Page `https://achados-que-valem.blogspot.com/p/loja.html`
- Post `https://achados-que-valem.blogspot.com/2026/11/loja.html`
- estado atual `store_scaffold_needs_auto_rotation`
- perfil semântico ainda precisa ser definido e validado

**Não iniciar Achados que Valem automaticamente. Aguardar novo `continue` do usuário.**"""
    if old_next not in cp:
        die("bloco próximo alvo antigo ausente")
    cp = cp.replace(old_next, new_next, 1)
    cp = cp.replace("# 12. REGRAS ESSENCIAIS PARA FUTURAS EXECUÇÕES", "# 13. REGRAS ESSENCIAIS PARA FUTURAS EXECUÇÕES", 1)
    cp = cp.replace(
        "Não reiniciar diagnóstico de Vitrine, Achados, Conecta, Estilo ou Casa em Ordem sem evidência concreta de regressão.",
        "Não reiniciar diagnóstico de Vitrine, Achados para Casa, Conecta, Estilo, Casa em Ordem ou Escolha Certa Online sem evidência concreta de regressão.",
        1,
    )
    cp = cp.replace("# 13. BACKUP / RECUPERAÇÃO", "# 14. BACKUP / RECUPERAÇÃO", 1)
    cp = cp.replace(
        "Como o R3 é anterior às conclusões de Conecta, Estilo e Casa em Ordem, um próximo backup completo deverá incluir os commits desses três blocos.",
        "Como o R3 é anterior às conclusões de Conecta, Estilo, Casa em Ordem e Escolha Certa Online, um próximo backup completo deverá incluir os commits desses quatro blocos.",
        1,
    )
    old_tail = """- Casa em Ordem = 11ª loja moderna concluída;
- auditor permanente = **11/11**;
- inventário = **11 modernas / 7 restantes**;
- próximo bloco permitido = **Escolha Certa Online**, somente após comando explícito do usuário."""
    new_tail = """- Casa em Ordem = 11ª loja moderna concluída;
- Escolha Certa Online = 12ª loja moderna concluída;
- auditor permanente = **12/12**;
- inventário = **12 modernas / 6 restantes**;
- próximo bloco permitido = **Achados que Valem**, somente após comando explícito do usuário."""
    if old_tail not in cp:
        die("resumo final antigo ausente")
    cp = cp.replace(old_tail, new_tail, 1)
    CP_PATH.write_text(cp, encoding="utf-8")


def validate_final() -> None:
    inv = json.loads(INV_PATH.read_text(encoding="utf-8"))
    roll = json.loads(ROLL_PATH.read_text(encoding="utf-8"))
    cp = CP_PATH.read_text(encoding="utf-8")
    summary = inv["summary"]
    assert summary["modern_blogger_auto_policy_guard"] == 12
    assert summary["store_scaffold_needs_auto_rotation"] == 6
    assert summary["modern_blogger_auto_20x12_needs_policy_guard_upgrade"] == 0
    assert summary["duplicate_writer_risks"] == 0
    escolha = next(b for b in inv["blogs"] if b["blog_id"] == BLOG_ID)
    assert escolha["automation_status"] == "modern_policy_guard_20x12"
    assert roll["enabled"] is False and roll["mode"] == "PREPARED_NOT_DEPLOYED"
    assert len(roll["targets"]) == 6 and roll["targets"][0]["title"] == "Achados que Valem"
    assert "ESCOLHA CERTA ONLINE — CONCLUÍDO COMO 12ª LOJA MODERNA" in cp
    assert "PRÓXIMO BLOCO PERMITIDO — ACHADOS QUE VALEM" in cp
    assert "SAFE/LIVE 12/12 protegidos" in cp
    print("ESCOLHA_FINALIZE_STATE_PASS: inventory=12/6 escolha=modern rollout=disabled targets=6 next=Achados que Valem checkpoint=updated")


def main() -> None:
    update_inventory()
    update_rollout()
    update_checkpoint()
    validate_final()


if __name__ == "__main__":
    main()
