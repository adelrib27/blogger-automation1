# V31 R65 — alvos CDP ausentes após fechamento das abas

**Data:** 2026-11-14 (America/Recife). Evidência Windows do operador e leitura ao vivo do conector.

## Saída R65 (Windows, operador)
`status=STOP_EXACT_BLOGGER_DASHBOARD_ABSENT`, `stage=CDP_CONNECTED`, `exact_candidates_count=0`, `selected_candidate_index=-1`, `click_possibly_dispatched=false`, `title_field_visible=false`, `save_clicked=false`, `blogger_write=false`, `runner_restarted=false`, `import_function=browser_provision`. Teste parou antes de qualquer clique. Sem evidência de falha funcional R56/R62.

## Consultas ao vivo posteriores
- `mcp__Browser__list_tabs`: uma aba `https://draft.blogger.com/blog/posts/2228849984262880811` na lista de abas do Chrome conectado ao ChatGPT.
- `mcp__Blogger_Local_Runner__health`: `ok=true`, versão `0.9-v31-r52-candidate`, `v31_files_ready=true`.
- `mcp__Blogger_Local_Runner__audit`: respondeu `internal_error` (não `AUDIT_OK`).

## Código revisado
O R65 lê apenas `context.pages` do contexto do CDP loopback `127.0.0.1:9222`. O Chrome acessível ao conector Browser não fornece identidade de CDP 9222. Não inferir que as listas representam a mesma janela.
O `active_blogger_page.select_active_blogger_page` original tem fallback para a primeira página existente quando **não identifica nenhuma aba Blogger**; `execute_audit` então exige sessão Blogger e pode falhar. A sequência `health PASS` + `audit internal_error` + `R65 zero abas` é compatível com ausência do painel Blogger no Chrome dedicado. **Hipótese prioritária; causa exata do internal_error não confirmada sem logs.**

## Próxima ação mínima
Restaurar somente **uma aba exata do painel Blogger** na instância Chrome exposta por `localhost:9222`, sem abrir outro Chrome independente, sem repetir Apply ou instalar novos módulos. Antes de criar tab, consultar `GET /json/list` e contar coincidências exatas; abrir `https://draft.blogger.com/blog/posts/2228849984262880811` via `PUT /json/new?` **apenas se a contagem for zero**, no endpoint loopback do Chrome CDP. Essa ação altera somente o estado transitório da janela Chrome, não salva blog. Depois revalidar audit; não repetir R65 automaticamente em caso de erro.

## Proteções
Não compartilhar `/json/list` completo se houver abas com URLs sensíveis; apenas imprimir contagem. Nenhum token, cookie, credencial, publicação, tema, workflow ou serviço deve ser alterado. Sem edição de main.
