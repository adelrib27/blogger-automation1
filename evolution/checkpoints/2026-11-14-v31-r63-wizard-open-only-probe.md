# V31 R63 — Teste seguro de abertura de wizard, sem salvar

**Data:** 2026-11-14; **status:** `OFFLINE_PASS_LIVE_WIZARD_PENDING`; **produção não modificada**.

## Novo recheck AO VIVO
Conector autorizado `mcp__Blogger_Local_Runner__health` respondeu `ok=true`, versão `0.9-v31-r52-candidate`, `v31_files_ready=true`, `v31_public_e2e_validated=false`.
`audit` respondeu `AUDIT_OK`, `new_blog_available=true`, `browser_connected=true`, Chrome `157.0.8103.51`, URL do painel `https://draft.blogger.com/blog/posts/2228849984262880811`. **Auditoria não abre o diálogo nem prova criação.**

## Procedimento preparado em ambiente isolado
Pacote: `BLOGGER_V31_R63_WIZARD_OPEN_ONLY_LAB_SAFE_2026-11-14.zip`
SHA256 ZIP: `df9a41a801ca2eead56b01ff87714dfae608759da1b9c0932efdf0c918874f32`. Cinco arquivos; CRC ZIP e hashes internos verificados.
O script `tools/PROBE_WIZARD_R63.py` valida integridade exata de `local_service_v31.py` R59 (`d3bef1...`), `browser_provision.py` R56 (`2294e223...`) e `browser_resilience_v06.py` R62 (`3c2efec1...`). Reimporta a cadeia V31 em subprocesso novo, exige a implementação final `browser_provision.click_new_blog(page, phase=...)`, conecta ao CDP loopback 9222 e exige uma única aba de painel exatamente correspondente ao blog ID já aberto. Chama a função R56 uma única vez para abrir o assistente e verificar o campo Título.

**Nenhum título ou endereço é preenchido e nunca se chama Save, create_blog, API de publicação, tema ou configurações.** Se o clique tiver possivelmente sido disparado, o procedimento não tenta clicar novamente e pode deixar o diálogo aberto para inspeção e fechamento manual com Cancelar.

## Testes
- 8/8 testes simulados em Python: sucesso com apenas uma chamada, diálogo previamente aberto, aba errada, abas duplicadas, import legado, erro após tentativa de clique sem repetição, hash divergente, rejeição de host/rota alternativos.
- Importação V31 completa com 104 scripts e substituições R56/R62 em cópia offline: `browser_provision.click_new_blog` aceita `phase`; PASS.
- **Não executado no Windows, Chrome real ou navegador do usuário nesta etapa.**
- A função do Runner na memória da porta 8765 não é observada diretamente por este script; futuro PASS confirma a cadeia carregada no processo de teste e a UI real, não o processo do serviço ativo.

## Etapa humana mínima, se Runner ocioso
Extrair ZIP em pasta nova, sem copiar para instalação, abrir PowerShell 5.1 na raiz do pacote e executar:
```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\tools\ABRIR_WIZARD_R63_SEM_SALVAR.ps1
```
Esperado: `R63_LIVE_WIZARD_TITLE_VISIBLE_NO_SAVE`, `NEW_BLOG_TITLE_VISIBLE`, `save_clicked=false`, `blogger_write=false`.
Se `STOP_*`, não repetir; preservar JSON e inspecionar o diálogo. Não executar novo provisionamento nem SALVAR. Fechar a janela com Cancelar.

## Governança
Script e testes entregues apenas em anexo; checkpoint registrado nesta branch isolada. Sem edição de `main`, tema, workflows, Runner ativo, Cloudflare, credenciais ou Blogger; E2E de criação continua pendente.
