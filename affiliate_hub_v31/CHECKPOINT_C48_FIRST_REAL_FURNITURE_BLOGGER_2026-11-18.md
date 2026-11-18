# V31 C48 — Primeiro Blogger NOVO real criado + campanha Shopee independente (18/11/2026)

**Código de continuidade:** `V31-C48-MOVEIS-BLOGGER-1439741542627895062-R2-1LINK-310TESTS-20261118`

## Missão preservada

V31 continua biblioteca universal: dois feeds CSV → 203.649 produtos R2 e índice FTS/sidecar → categoria/nicho/revisão → tema solicitado no momento de um blog novo → blog REAL e campanha exclusiva → conversor Shopee → gerador/rascunho → publicação autorizada. Não antecipar nichos futuros, não reutilizar links de campanhas anteriores e não declarar REVIEW como aprovado. Não tocar nos três WordPress nem no Pinterest/Worker v1.0.

## Identidade real do primeiro Blogger novo

- **Título:** Móveis para Cada Canto
- **URL pública Blogger:** https://moveisparacadacanto.blogspot.com/
- **ID verificado na Blogger API:** `1439741542627895062`
- **Data:** 18/11/2026, idioma pt-BR, criado via Blogger Local Runner `provision_new_blog_v31`. O provisionamento retornou `safe_automation_error` em etapa posterior à criação; o blog foi localizado e verificado pela API Blogger v3. Não duplicar blog!
- **Configurações:** descrição editorial e search description aplicadas por `configure_settings`; search visibility ON, HTTPS redirect ON, lazy images/WebP ON, timezone `GMT-03:00 Brasília/São Paulo`. Rechecado por `preflight_settings`.
- **Tema V31: PENDENTE.** `adopt_model_v31_exact` recusou com `target_not_authorized`: o Runner local ainda não autorizou o ID **exato** `1439741542627895062`. Não contornar allowlist nem afirmar tema aplicado. É uma etapa manual/operacional de autorização do destino, não impedimento para usar o catálogo/conversor.
- **Posts e páginas:** zero no momento do cadastro. O usuário não definiu a quantidade de artigos nem autorizou publicação imediata; não inventar demanda.

## Integração V31 REAL

- [PR #67 MERGED](https://github.com/adelrib27/blogger-automation1/pull/67): `affiliate_hub_v31/sites.d/blogger_moveis_para_cada_canto.json` na `main`: `platform=blogger`, `identifier=1439741542627895062`, `site_key=blogger_moveis_para_cada_canto`, `campaign=moveisparacadacanto`, `allowed_niches=[casa/moveis]`, `allowed_source_paths=[home living/furniture]`, `publish_enabled=false`. O conversor usa subId `MOVEISPARACADACANTO` para esta campanha, sem cruzar links de outros sites. A lista de rotas é declarativa; teste antigo com contagem fixa de 21 sites foi corrigido para contar `site_routes.json` + `sites.d`.
- [CI 44376082992](https://github.com/adelrib27/blogger-automation1/actions/runs/44376082992): **310 testes V31** + **24 Casa** + **21 Oficina** + cross-blog guard PASS.
- [**Canário E2E real R2+Shopee 44376578794**](https://github.com/adelrib27/blogger-automation1/actions/runs/44376578794): seis temas de móveis consultados com **6 SKUs aprovados cada** (não presumir 36 SKUs únicos), limite de **1 chamada mutation Shopee**, **1 novo link oficial criado**, cache salvo e RESTAURADO no R2 e validado para campanha exclusiva, `api_interrupted=false`, `no_cross_campaign_links=true`, 0 publicações.
- No mesmo canário, `plan_editorial_handoff` retornou **1 oferta/pauta pronta para revisão**, **0 links pendentes** naquela seleção de 1, **12 candidatos em revisão segregados**, `editorial_approval_required=true`, `can_publish=false`. O handoff foi VALIDADO, não publicado e não tratado como artigo pronto.
- Workflow/gatilho temporários `v31_c48_real_furniture_link_once.yml` e `C48_FIRST_REAL_FURNITURE_LINK_TRIGGER.txt` **removidos** após conclusão. Cron permanente de conversão só atua em pedidos habilitados de site real; nenhum `site_requests.d/<site_key>.json` foi criado sem quantidade solicitada.

## O que ainda exige ação fora da automação segura

1. Para aplicar o modelo visual V31, autorizar no Blogger Local Runner o destino exato **ID `1439741542627895062`**, título e URL; depois executar instalador oficial ou reprise idempotente, sem criar outro Blogger. A permissão atual não inclui o novo ID.
2. Definir **quantos artigos** e autorizar redação/publicação do primeiro artigo original. O mecanismo de seleção e conversão está comprovado; o gerador/editor para esse blog precisa entregar texto original com revisão conforme o contrato C41. Não criar rascunhos/publicações com conteúdo fabricado de produto.
3. Opcionalmente criar páginas institucionais e aplicar tema/projeto visual quando houver autorização de publicar e configuração real de contato/privacidade.
4. O acervo universal e a curadoria C45–C47 continuam independentes desta criação. Falta de dados de comissões/vendas não bloqueia testes ou execução técnica.

**Estado:** blog criado, SEO aplicado, cadastro V31 na `main`, 1 link afiliado real convertido e preservado; **tema V31 e primeira publicação ainda não concluídos**.
