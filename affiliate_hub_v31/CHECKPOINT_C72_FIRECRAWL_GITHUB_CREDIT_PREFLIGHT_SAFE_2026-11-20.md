# C72 — quota Firecrawl da chave GitHub, próximos gates de integração (20/11/2026)

**PRÉVIA C72 gravada ANTES da execução de diagnóstico externo. Estado: EM_ANDAMENTO.**

## Base e evidências
- `main` contém C71 via [PR #99](https://github.com/adelrib27/blogger-automation1/pull/99), merge `f040981a50ba7bbb506691b9fe785157d00e137e`; [CI #44747425029](https://github.com/adelrib27/blogger-automation1/actions/runs/44747425029) **SUCCESS 494 V31 + Casa 24 + Oficina 21 + Radar 15**. Code SAFE `final_fact_gate.py`, `d1_universal_ready.py`, migration SQL **não aplicada**, não ligada a workers/blogs.
- `vida_pet_pratica_persistence_lab.yml` guarda a chave **GitHub repo** sob nome de secret `FIRECRAWL_API_KEY` (valor nunca lido/exposto); R28 usava essa chave em LAB isolado. A conta Firecrawl conectada ao chat pode ser outra; **não inferir saldo desta**.
- Documento oficial Firecrawl confirma endpoint de **consulta de créditos somente leitura**: `GET https://api.firecrawl.dev/v2/team/credit-usage` com token Bearer; não é endpoint de pesquisa/scrape e não deve debitar pesquisas.
- Três `event=schedule` reais V31 em 19/11 conhecidos: fila Shopee [#44600350780](https://github.com/adelrib27/blogger-automation1/actions/runs/44600350780) FAILURE pós 3 links cache R2; [Blogger #44609598601](https://github.com/adelrib27/blogger-automation1/actions/runs/44609598601) SUCCESS 1 DRAFT 0 LIVE; [WordPress #44614079395](https://github.com/adelrib27/blogger-automation1/actions/runs/44614079395) SUCCESS 1 DRAFT 0 LIVE. Os agendamentos de **20/11** não foram observados por volta de 10h34 Recife; monitoramento de pontualidade continua.
- Auditoria CMS read-only 20/11 ~10h13: Blogger Móveis 3 LIVE/3 DRAFT; WP Casa 45 LIVE/59 DRAFT. Diferença de dois LIVE vs histórico C65 NÃO atribuída ao V31 sem investigação independente.

## Passo SAFE agora
1. Criar workflow GitHub TEMP estritamente amarrado a `push` de arquivo e mensagem únicos, somente GET Credit Usage usando `FIRECRAWL_API_KEY` do próprio repo, sem mostrar segredo e sem chamar API de pesquisa, sem post/CMS/R2/D1.
2. Exibir somente status agregados não privados de saldo/erro; classificar POSITIVE, ZERO, NOT_FOUND, AUTH_FAILED ou UNKNOWN. Não fazer cache miss real enquanto resultado e limite financeiro não forem confirmados.
3. Remover workflow TEMP, registrar Action, atualizar checkpoint e índice/JSON após resultado. Se secret ou endpoint falhar, manter fail-closed, não substituir por saldo de outra conta.
4. Em fase posterior, conectar runner D1 seguro a banco **V31 dedicado**, fact gate e writers via canários DRAFT. Não criar banco pet-specific nem editar WordPress Vida Pet; nunca ativar LIVE automaticamente.

**Nenhuma mutação externa na criação deste checkpoint além de documentação GitHub.**
