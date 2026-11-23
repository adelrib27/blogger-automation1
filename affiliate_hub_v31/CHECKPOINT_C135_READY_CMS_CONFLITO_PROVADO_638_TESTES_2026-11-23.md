# V31 C135 — auditoria independente READY x CMS homologada (GET + SELECT)

**Data:** 2026-11-23, America/Recife. **Repositório:** `adelrib27/blogger-automation1`, branch `main`.
**Código de retomada:** `V31-C135-20261123-638-TESTS-READY-CMS-CONFLICT-PROVEN-LIVE-OFF`.
**Status:** C135 CONCLUÍDA (auditoria READ-ONLY); homologação E2E de novo DRAFT universal e LIVE **NÃO CONCLUÍDAS**.
**LIVE automático:** DESATIVADO; política `pending_policy_approval`.

## Bases obrigatórias lidas antes de executar
`V31_CONTINUAR_AQUI.md`, `affiliate_hub_v31/CONTINUIDADE_ESTADO.json`, `CHECKPOINT_C134_HOMOLOGACAO_SEGURANCA_OPERACIONAL_623_TESTES_2026-11-23.md` da `main`. PREVIEW incremental [C135](CHECKPOINT_C135_PREVIEW_READY_CMS_RECONCILIACAO_SEM_WRITES_2026-11-23.md), commit `1b5632b7640ed53f9c6a5cc9f1c316dd4177e643`, salvo ANTES de alterar código.

## 1. Problema confirmado por duas fontes independentes
- D1 oficial `v31-universal-ready-safe`, tenant `wordpress_casa_decoracao` / `casaedecoracaowp`, job `READY` SKU `shopee:306698991:8503898928`; SHA-256 do HTML esperado `c2b8bb85f453c43b37b50ebf8dae9c59522870cc4d0291824fd981f45bd0e495`.
- WordPress Casa API autenticada `GET /wp/v2/posts/314?context=edit` revelou `status=draft`, slug `v31-31856a8a43a1-8503898928`, mesmo marcador `data-v31-product-key` para esse SKU. SHA-256 calculado sobre os bytes UTF-8 do `content.raw`: `f87330fcc9a00c9d9a564f60385a56327af87e3bdaf828022cdc8013b2d2c987`.
- Portanto **mesma identidade comercial, bytes de HTML diferentes**. Não executar entrega do READY nem sobrescrever o #314, nem publicar versões duplicadas. O job READY foi preservado; não alteramos bancos/CMS.
- O antigo `reviewed_draft_delivery._wordpress_draft` já tinha bloqueio para conteúdo conflitante, mas faltava prova por auditor remoto e observabilidade sem tentativa de POST.

## 2. Correção C135 integrada — PR #138
[PR #138](https://github.com/adelrib27/blogger-automation1/pull/138) **MERGED** via squash `0f497271132ea6b9db68f2018b414c8f8d0a0022`.

- `affiliate_hub_v31/ready_cms_collision_audit.py` reconhece sites Blogger ou WordPress pela rota segura do registry; valida identidade CMS, lê histórico autenticado (incluindo DRAFT), consulta somente jobs `READY` do tenant por **D1 SELECT**, calcula SHA-256 local do HTML bruto e classifica: `CONFLICTING_DRAFT_HTML`, `IDENTICAL_DRAFT_ALREADY_PRESENT`, `CONFLICTING_PRODUCT_IDENTITY`, `CONFLICTING_SLUG`, `MULTIPLE_CMS_MATCHES`, `EXISTING_NON_DRAFT_POST`, `NOT_PRESENT_IN_ACTIVE_HISTORY`.
- TODOS os status são **diagnósticos, não permissões para criar/usar DRAFT**. Se histórico incompleto/RAW ausente, erro fechado. Nenhum objeto de catálogo, título, HTML, link ou token é emitido no resumo.
- `.github/workflows/v31_c135_ready_cms_collision_readonly.yml`: manual por `site_key` para qualquer rota V31; `push` inicial exclusivamente após alteração do próprio workflow; `contents:read`; só credenciais GET CMS e token SELECT D1; não usa segredo R2/Shopee/Firecrawl nem enable D1 writes.
- `affiliate_hub_v31/tests/test_c135_ready_cms_collision.py`: 15 testes offline adicionais. [CI V31 #45268392814](https://github.com/adelrib27/blogger-automation1/actions/runs/45268392814) **638/638 PASS** + testes Casa 24/24, Oficina 21/21, Radar 15/15 e antirrepetição PASS.

## 3. Homologação remota da auditoria
[Action C135 #45268529600](https://github.com/adelrib27/blogger-automation1/actions/runs/45268529600) disparada automaticamente por merge na `main`, **COMPLETED SUCCESS**.
- Etapa de regressão: 15 testes PASS.
- Etapa remota GET/SELECT: `C135_READY_CMS_AUDIT` retornou `mode=READ_ONLY_NO_DELIVERY_NO_LIVE`, `site_key=wordpress_casa_decoracao`, `ready_jobs_checked=1`, `outcomes.CONFLICTING_DRAFT_HTML=1`, `cms_ids=[314]`.
- Confirmações do retorno: `ready_delivery_authorized=false`, `automatic_live_authorized=false`, `cms_writes=0`, `d1_writes=0`.
- A execução **não gerou um novo DRAFT** nem liberou publicação. Apenas confirmou o bloqueio por divergência de HTML.

## 4. LIVE e autores legados
- PR #137 permanece integrado; writers legados agendados Casa e Oficina bloqueados com `false &&` e flags LIVE false/status draft. Novo workflow não interfere nos agendamentos universais nem no publisher manual.
- API GitHub Actions últimas 100 execuções consultadas até 23/11 ~21:22 UTC: nenhum `schedule` posterior ao merge #137 dos dois writers legados observado, **não considerar comprovado SKIPPED em um schedule real até ocorrer**. Esse gate fica pendente.
- Último canário programado de Móveis `#45260835997`: `NO_NEW_OFFER/research_budget_exhausted`, DRAFT delivery/release SKIPPED; cota 23/11 Móveis SEARCH 3/3 e HTTP 3/3 (conforme D1 da C134). Não reexecutar pesquisa no mesmo dia UTC. Após renovação natural, verificar novo DRAFT por GET/hash/SEO/foto/CTA/campanha/idempotência.
- `V31_AUTODRAFT_ACTIVE` e `V31_AUTOLIVE_ACTIVE` **não foram alteradas** nesta C135; arquivo `autonomous_live_policy.json` mantém `pending_policy_approval`.
- Biblioteca R2, D1, posts Blogger/WordPress e Pinterest permanecem intocados pela C135.

## 5. Pendências C136+
1. Observar workflow agendado Casa/Oficina após PR137, exigir jobs `SKIPPED` e ausência de novas publicações provenientes desses writers.
2. Observar canário Blogger Móveis após renovação NATURAL de quota D1; não fazer disparo em duplicata ou contornar orçamento.
3. Job READY do WP Casa com SKU no draft #314 **permanece CONFLICTING_DRAFT_HTML**: não consumir nem forçar reconciliação. Selecionar outro SKU com prova externa exata e link convertido da campanha para canário posterior, preservando conteúdo #314.
4. Os 8 prioritários seguem 2 com perfil+request, 5 com rota mas sem perfil/request, 1 Vida Pet com blog verdadeiro mas campanha não verificada. Iniciar onboarding de um site por vez, a partir de fontes externas reais, sem inventar produtos nem atalhos de verificação.
5. LIVE automático só poderá ser habilitado depois de homologação fim a fim e **autorização expressa final do proprietário**, inicialmente piloto único, política assinada e limite diário.

**Indicador C135:** 638 testes offline PASS; auditoria remota SUCCESS; conflito WP existente provado; **novos DRAFTs nesta etapa = 0; novos posts LIVE nesta etapa = 0; D1/R2/CMS writes = 0**.

## Contrato de retomada
Ler primeiro `V31_CONTINUAR_AQUI.md` -> `CONTINUIDADE_ESTADO.json` -> ESTE checkpoint -> resultados Actions e quotas D1 reais. Não repetir #136–#138; não apagar/consumir READY conflitado; não confundir SUCCESS da auditoria com DRAFT entregue. **LIVE OFF**.
