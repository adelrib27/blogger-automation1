# V31 R64 → R65 — diagnóstico comprovado de duplicidade e correção isolada do teste

**Data:** 2026-11-14. **Estado:** R64 PASS no Windows (operador); R65 PASS offline, Chrome real R65 PENDENTE.

## Causa EXATA do STOP R63 (comprovada)
Saída enviada pelo operador da sondagem R64 (somente leitura): `contexts=1`, `pages_total=28`, `r63_exact_matches_all_contexts=10`, `first_context_r63_matches=10`, `expected_path_matches_all_contexts=10`. São dez abas `draft.blogger.com/blog/posts/2228849984262880811`, sem parâmetros na URL. O R63 interrompia quando `len(candidates) != 1`. Portanto `STOP_EXACT_BLOGGER_DASHBOARD_NOT_UNIQUE_OR_ABSENT` decorreu de **duplicidade**, não de URL malformada; `click_possibly_dispatched=false` e `blogger_write=false`.

**Não comprovado:** qual operação anterior abriu cada aba. Existem vários scripts com `context.new_page()`, inclusive rotas de tema/configuração, mas não há rastreamento de criação de targets suficiente para atribuir a origem destas dez abas.

## Solução R65 isolada (não instala nada)
Pacote de conversa `BLOGGER_V31_R65_WIZARD_DEDUP_SELECT_SAFE_2026-11-14.zip`.
- SHA-256 ZIP: `7ec8311df54a6b026d955a7285d9b316c80b553610b22927729374af66a805ba`;
- SHA-256 `tools/PROBE_WIZARD_R65.py`: `a24ef5975577b77f78e8f003eb866d574e87b645e3c5a3d42ef1222e7c1a04ae`.
- R65 mantém hash pinning do Runner V31 R59, `browser_provision.py` R56, `browser_resilience_v06.py` R62 e `active_blogger_page.py` SHA `e714cd0a0790a107b53f09781983800184c15aca043ca0c7d9416f8fcd0556f7`.
- Filtra pelo host/caminho/Blog ID exatos, inspeciona diálogo pré-aberto entre todas as correspondências, e passa **somente essas páginas já existentes** a `browser_provision.select_page`, reaproveitando o mecanismo original `active_blogger_page.select_active_blogger_page` de prioridade da aba visível/mais recente. Não abre nem fecha abas, não navega, não preenche dados.
- Executa um único `bp.click_new_blog(page, phase=phase)` para abrir o diálogo e comprovar o campo Título. Nenhum Save ou criação. Sem retry após possível click.
- O teste aborta se o número de contextos CDP mudou (esperado 1), se há wizard já aberto, se hashes ou imports divergem, se não há alvo exato, ou se a aba selecionada saiu do conjunto filtrado.

## Evidências de teste
- Testes unitários simulados **15/15 PASS** (inclusive dez duplicatas e aba em primeiro plano; mudança de contexto; proteção de abas erradas).
- Importação completa dos scripts V31 do snapshot com R56/R62, dez páginas artificiais e a função efetiva `bp.select_page`: `REAL_V31_IMPORT_CHAIN_SELECTOR_PASS`.
- ZIP extraído em diretório limpo; testes **15/15 PASS** novamente; CRC e SHA-256 de todos os cinco arquivos declarados: PASS.
- **Não executado no Windows/Chrome real. Nenhum arquivo de produção alterado.**

## Única ação local necessária
Com Runner ocioso e nenhuma criação em andamento, extrair o R65 em Downloads e executar uma única vez em PowerShell 5.1:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\tools\ABRIR_WIZARD_R65_SEM_SALVAR.ps1
```

Esperado: `R65_LIVE_WIZARD_TITLE_VISIBLE_NO_SAVE`. Se `STOP_*`, não repetir. Se abrir janela, não salvar e fechar com **Cancelar**.

## Próximas etapas depois do PASS
1. Auditoria específica da origem das duplicatas, com identificação de abertura/reutilização/fechamento de target nas funções que usam `new_page()`, em LAB, não fechamento em massa.
2. Validar abertura automatizada no Chrome real.
3. Homologação completa E2E somente com novo destino LAB explicitamente autorizado e sem risco de duplicação.
4. Tratar contato/tema e Shopee em trilhas separadas.

Branch de auditoria somente; sem alteração na `main`, Runner, Blogger, Chrome, Cloudflare, workflow ou secrets.
