# V31 R60 — auditoria do gate V2 e desacoplamento da aplicação R56

**Data:** 2026-11-14 · **Status:** `OFFLINE_CANDIDATE_NOT_INSTALLED` · **Escopo:** somente leitura e desenvolvimento isolado.

## Origem e comprovações
- Gate V2 recebido na conversa: `FINALIZAR_V31_WINDOWS_GATE_SAFE_V2_2026-11-13.ps1`, 272 linhas; SHA-256 `22b9e1f7bcc507b2147f309478c17e3395315434865b387dd4e26941f4227db4`. Coincide com a dependência exata do instalador R56.
- R59 no Windows: operador informou `BOOT_RESTORED_RUNTIME_READ_ONLY_PASS`, bootstrap `2115f2d50c34771b6a4404d11910408cb599799ee7690e786dcb6b2ba6efb311`, health autenticado e Chrome/CDP PASS. Esse resultado não prova reboot longitudinal nem E2E.
- R56: baseline do `browser_provision.py` `e4b10eeb7bd123c4c94723842d3293c41e17b0639068feac26565941dae65ee5`; candidato `2294e223ddde3ce16f847431da82bd380b68d036bca1d23866aff6e37907241f`. O estado atual do disco após R59 ainda precisa de preflight.

## Achados do gate V2 (código lido, não executado)
1. Abre instância paralela do Runner em 18765 (linhas 196–204).
2. Interrompe o processo ativo da 8765 e inicia outro com inspeção de fontes habilitada (linhas 206–224).
3. Executa eventual `rollback_v31.py` após verificar apenas sua existência, sem conferir digest do próprio script nesse gate (linhas 184–185 e 253).
4. O encerramento de PID pode deixar processo-filho do redirecionador venv em alguns cenários; **risco teórico**, sem prova de que ocorreu.
5. O wrapper R56 invoca o gate após atualizar disco e pode invocá-lo novamente após rollback — mistura implantação de wizard e ativação de inspeção.
6. `HEALTH_V31_INCOMPATIVEL` é condição de contrato multivalorado; a causa exata de uma ocorrência passada não está comprovada.

## Decisão
**NÃO usar gate V2 nem o PowerShell original R56 nesta recuperação.**
Criado R60 SAFE de duas fases, separado da troca de processos:
- `Preflight` padrão: R59 -CheckOnly + SHA R55/R56 + suíte offline; **nenhuma escrita no Runner**.
- `Apply`: instalador Python R56 original, backup e substituição apenas do arquivo `browser_provision.py`; requer janela ociosa explicitamente afirmada; **sem reinício**.
- `Verify` somente após reboot planejado: hash, health/CDP e processo posterior à modificação; E2E ainda pendente.
- `Rollback` guardado por backup SHA; disco revertido sem restart automático.

## Testes realizados
- **16/16** verificações estáticas R60 PASS.
- **45/45** testes originais R56 PASS em container com cópia dos arquivos V31.
- Instalador Python R56 aplicado em runtime **temporário**, SHA candidato verificado e rollback executado, restaurando SHA anterior: PASS.
- ZIP R60 (14 entradas) com CRC e hashes de 13 arquivos verificados.
- SHA-256 ZIP: `e9c585b664254a5cfcb99e3e54d84942bc82314b75017c1ef4230e368363dad6`.
- **PowerShell 5.1 não executado nesta rodada**, não houve escrita no Windows/Blogger/Cloudflare/produção.

## Bloqueio e próximo passo mínimo
O chat não tem acesso operacional autorizado ao Runner local. Operador deve executar **apenas** o preflight R60 em Windows PowerShell 5.1, fora da instalação, e fornecer o JSON sanitizado:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\tools\GERENCIAR_WIZARD_R60.ps1 -Mode Preflight
```

Somente depois de PASS, na janela de manutenção com Runner ocioso, avaliar Apply. Nunca iniciar criação de blog no mesmo passo. O tema V31 Contato e a falha Shopee GraphQL seguem em trilhas independentes.

**Preservação:** `main`, workflows, temas, publicações, secrets, tarefas Windows e serviço ativo não alterados por esta auditoria.