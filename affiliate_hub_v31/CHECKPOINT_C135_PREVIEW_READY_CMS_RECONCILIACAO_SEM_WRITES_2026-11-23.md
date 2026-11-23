# V31 — C135 PREVIEW: reconciliação READY ↔ CMS sem mutações

**Data:** 2026-11-23, Brasil UTC−3. **Ramo:** `main`. **Base:** `a878cf30bb010f7d9651d014999b0415fc478716`.
**Código:** `V31-C135-20261123-PREVIEW-READY-CMS-HASH-CONFLICT-LIVE-OFF`.
**Status:** EXECUÇÃO INICIADA / SAFE / nenhum LIVE autorizado.

## Contexto antes de mudanças
Fontes da `main` consultadas nesta retomada: `V31_CONTINUAR_AQUI.md`, `affiliate_hub_v31/CONTINUIDADE_ESTADO.json` e `CHECKPOINT_C134_HOMOLOGACAO_SEGURANCA_OPERACIONAL_623_TESTES_2026-11-23.md`.

- PRs #136/#137 integrados, 623 testes offline PASS e writer LIVE legado Casa/Oficina em HOLD com `false &&`.
- GitHub Actions até última leitura (23/11 ~21:06 UTC): nenhum schedule pós-merge #137 de Casa/Oficina; não declarar observação de cron sem run real.
- D1 READY pré-existente: tenant `wordpress_casa_decoracao` / `casaedecoracaowp`, SKU `shopee:306698991:8503898928`, HTML SHA-256 esperado `c2b8bb85f453c43b37b50ebf8dae9c59522870cc4d0291824fd981f45bd0e495`.
- GET WordPress autenticado do `/wp/v2/posts/314?context=edit`: `status=draft`, slug do mesmo SKU `v31-31856a8a43a1-8503898928`, marcador de produto exato. SHA-256 do `content.raw` calculado localmente com algoritmo testado contra vetores padrão (vazio e `abc`): `f87330fcc9a00c9d9a564f60385a56327af87e3bdaf828022cdc8013b2d2c987`.
- **SHA-256 DIVERGENTE**: a identidade comercial do produto coincide, mas os bytes do artigo NÃO. Não tentar publicar/recriar/editar/consumir READY; reconciliar.
- No runner `reviewed_draft_delivery._wordpress_draft` já existe bloqueio `reviewed_wordpress_prior_content_conflict` após GET quando slug coincide e texto diverge. Em `autonomous_review`, histórico CMS impede repetição da SKU. O problema real para observabilidade é que o READY de D1 permanece registrado, podendo ser confundido com oferta ainda entregável.
- Política AUTO LIVE do V31: `pending_policy_approval`. Nenhuma variável/live policy alterada.

## Próxima mudança isolada prevista
Criar auditor read-only universal (Blogger + WordPress), executável por GitHub Actions apenas para tenant já registrado, que cruza jobs READY D1 com inventário CMS autenticado e registra `CONFLICTING_DRAFT_HTML`, `IDENTICAL_DRAFT_ALREADY_PRESENT`, `MULTIPLE_CMS_MATCHES`, `OTHER_STATUS` ou `NOT_PRESENT`, sem autorizar entrega com base apenas nesses rótulos. Regra invariante: auditoria não pode realizar POST/PUT/PATCH/DELETE no D1, R2 ou CMS, consumir READY, renovar pesquisa ou publicar LIVE. Suíte de regressões offline + PR, CI e merge somente após aprovação. Registrar resultado remoto por GitHub Action no checkpoint final.

## Gatilhos externos pendentes
Aguardar cron natural do piloto Blogger após renovação de cota; monitorar execuções reais legadas pós-PR137; cinco rotas demandam fontes independentes/perfil/pedido e Vida Pet exige campanha verificada. Não habilitar rollout `all` nem LIVE sem autorização expressa.
