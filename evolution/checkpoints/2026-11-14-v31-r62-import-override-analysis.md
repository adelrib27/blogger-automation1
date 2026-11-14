# Blogger Automation V31 — R60 Verify PASS e incompatibilidade real de imports V06 × R56

**Data:** 2026-11-14, America/Recife. **Estado:** R60 Windows Verify PASS conforme operador; candidato R62 OFFLINE, **não instalado**.

## Evidência do operador no Windows — posterior ao STOP anterior
`GERENCIAR_WIZARD_R60.ps1 -Mode Verify`:
- `status=R56_DISK_AND_NEW_PROCESS_PASS_E2E_PENDING`
- `browser_sha256=2294e223ddde3ce16f847431da82bd380b68d036bca1d23866aff6e37907241f`
- `writes_to_blogger=false`, `runner_restart=false`, `gate_v2_executed=false`, `local_disk_write=false`
- `runtime_import_proven=false`.

O Verify anterior havia retornado `STOP_R59_AUTHENTICATED_HEALTH_OR_CDP_FAILED`. Causa da intermitência **não comprovada**; não houve nova correção entre os dois logs fornecidos.

## Causa nova reproduzida offline: substituição de função ao importar o Runner
Cadeia efetiva: `local_service_v31 -> local_service_v08 -> local_service_v07 -> local_service_v06`. Em `local_service_v06`, `browser_resilience_v06.install()` executa na importação.

Com o `browser_provision.py` R56, `create_blog()` invoca `click_new_blog(page, phase=phase)`. Contudo, o V06 **sobrescreve** `browser_provision.click_new_blog` com `click_new_blog_resilient(page, *, attempts=6)`, sem aceitar o argumento `phase`. Isto produz `TypeError` antes de executar a função R56 e anula a correção de clique único/espera pelo campo de título.

**Prova offline em subprocessos isolados com 104 scripts do snapshot:**
1. R56 + V06 original: `bp.click_new_blog.__module__ == 'browser_resilience_v06'`, ausência de `phase`, chamada com `phase=` resulta `TYPEERROR_BEFORE_BROWSER`.
2. R56 + V06 R62: origem `browser_provision`, `phase` presente e aceito; execução abortada por stub ANTES de qualquer acesso ao navegador.
3. R55 + V06 R62: fallback legado permanece, e `ensure_new_blog_available_resilient` continua presente.

## Candidato R62, mudança mínima
Modificar somente `browser_resilience_v06.py`: preservar o patch de `ensure_new_blog_available`, mas só substituir `click_new_blog` quando `browser_provision` **não** expuser o helper R56 `_wait_new_blog_title`.
- SHA original V06: `d6dd775ce80cd5c5d7d125290075da1b040814e348f31f1e4a9bc5540f49d2a7`
- SHA candidato V06: `3c2efec115dc120d20a8cd326aa659974f3304b1e28cfb436ab44753fc080080`
- ZIP entregue na conversa: `BLOGGER_V31_R62_WIZARD_IMPORT_FIX_SAFE_2026-11-14.zip`
- ZIP SHA256: `23c972f94029a7bc00845ce13c63be8ab4bbe41648805f4f435497f71904f14e`
- Offline: 3/3 testes integrais de import, 16/16 de integridade, 45/45 testes R56 em runtime temporário, instalação/rollback de R56 simulados.

## Próximo gate, sem alterar produção automaticamente
Fazer **somente o preflight Windows R62**, a partir do pacote extraído em pasta separada:
```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\tools\GERENCIAR_IMPORT_R62.ps1 -Mode Preflight
```
Esperado: `R62_PREFLIGHT_LEGACY_OVERRIDE_CONFIRMED_NO_WRITES`. Após este PASS, operador poderá aplicar apenas V06 com backup e janela ociosa; nova partida planejada e Verify R62 em etapa posterior. Não repetir R59/R60 Apply; não usar gate V2; sem Blogger writes.

**Classificação:** fato de import e contrato reproduzido OFFLINE; correção candidata validada OFFLINE; situação da função importada no processo vivo ainda não verificada diretamente. Sem edição de GitHub main, Cloudflare, temas, Blogger, secrets ou publicações.