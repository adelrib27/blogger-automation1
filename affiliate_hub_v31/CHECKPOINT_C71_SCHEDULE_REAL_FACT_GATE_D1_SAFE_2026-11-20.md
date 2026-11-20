# C71 — homologação dos schedules e engenharia SAFE Facts/D1 universal (20/11/2026)

**PRÉVIA registrada em main antes de desenvolvimento C71. STATUS: EM_ANDAMENTO.**

## Missão e proteção
Continuar V31 após C70 e concluir as próximas pendências técnicas sem transformar V31 em motor exclusivo Vida Pet: catálogo universal de 2 CSV Shopee, seleção por nicho/site real, campanha exata, DRAFT Blogger/WordPress com imagem e CTA, SEO C68 e Evidence/READY C69. Preservar sites/rotas, URLs, campanhas e dados R2; **não ativar LIVE, não editar WordPress Vida Pet nem o LAB legado; não reutilizar D1 do Pet**. `articles:null` permanece sem teto total.

## Estado remoto auditado ANTES de alterar código
- `main` SHA `8210fec0f01206bad903e578c2d8270135dc59fd` consultado 20/11. Entrada C70 e JSON lidos; C70 PR #98 471 testes V31 e handoffs R2 reais.
- **Novas provas de `event=schedule` real dos workflows V31 em 19/11**, observadas agora:
  - Fila Shopee [#44600350780](https://github.com/adelrib27/blogger-automation1/actions/runs/44600350780): `failure` após 3 links cache R2 verificados (falha handoff `articles:null` corrigida C70).
  - Blogger [#44609598601](https://github.com/adelrib27/blogger-automation1/actions/runs/44609598601) `success`: log `V31_C55_BLOGGER_DRAFT_AUTOMATION_SAFE_PASS`, `status=DRAFT_CREATED`, `draft_creation_calls=1`, `publication_calls=0`, foto real/link/campanha/CTA/internos OK.
  - WordPress [#44614079395](https://github.com/adelrib27/blogger-automation1/actions/runs/44614079395) `success`: log `V31_C60_UNIVERSAL_WORDPRESS_SAFE_PASS`, `status=DRAFT_CREATED`, `wordpress_posts_created=1`, `publication_calls=0`, campanha exata/foto e 2 internos.
- O gatilho ficou **muito atrasado** em 19/11: fila 16h38, Blogger 17h31, WP 17h58 (Recife), frente a cron pretendido 08h47/09h18/09h41.
- **No horário desta retomada (20/11 ~10h34 Recife), os novos `event=schedule` dos três diários V31 de 20/11 não aparecem na listagem GitHub**; logo não homologar pontualidade nem execução desse dia. Outros workflows legados aparecem em 20/11, então não atribuir causalmente a falha ao scheduler global.
- Automação READ-ONLY C65 de 20/11 10h10 concluiu sua checagem; relatório de leitura via CMS indica Blogger Móveis 3 LIVE/3 DRAFT e WP Casa 45 LIVE/59 DRAFT. Essas contagens são observação externa, NÃO afirmam causa dos 2 LIVE WP adicionais vs C65. Não executar novas mutações nos CMS por inferência.
- Engine Evidence/READY C69 `universal_evidence_ready.py` permanece simulação SQLite offline; ainda sem Firecrawl GitHub confirmado, fact gate HTML integrado ou D1 produtivo. `wordpress.writes_enabled=false` do LAB Vida Pet é intocável.

## Próximas execuções SAFE C71
1. Criar adaptador/padrão SQL D1 de persistência por site_key+campaign com locks/lease/idempotência transacionais e testes SQLite simulando corridas, **sem criar/alterar banco Cloudflare real**.
2. Implementar fact gate pós-IA vinculando evidências EXATAS aprovadas e verificáveis ao HTML final; bloquear alegações não autorizadas e evitar `editorial_quality_verified:true` sozinho, com testes de fuga/ausência de evidências. **Não ligar automaticamente aos writers** até integrar/validar canário DRAFT.
3. Fazer PR, CI SAFE, revisar resultados, preservar vias de rollback. Evitar Firecrawl externo até conferir quota da *mesma credencial GitHub* e orçamento durável.
4. Consolidar mudanças, evidências e pendências no `CONTINUIDADE_ESTADO.json` e no ponto de entrada `V31_CONTINUAR_AQUI.md`.

## Efeitos de produção desta prévia
Zero R2/Shopee/CMS/D1/Firecrawl/Pet mutações. A criação da própria prévia é apenas documentação GitHub. O C71 não presume cron do dia 20 e não autoriza publicação LIVE.
