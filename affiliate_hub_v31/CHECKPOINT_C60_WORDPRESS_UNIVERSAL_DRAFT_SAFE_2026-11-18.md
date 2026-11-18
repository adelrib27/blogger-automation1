# V31 C60 — WordPress UNIVERSAL: prévia real e writer apenas rascunho (18/11/2026)

**Estado:** implementação segura concluída em `main` com canário R2 + WordPress real. O writer universal ainda não criou um NOVO draft por REST em produção porque não existe pedido WordPress novo/credenciais específicas autorizadas no GitHub para esse writer. **Não chamar LIVE concluído nem fingir que o cron futuro ocorreu.**

**Código de retomada:** `V31-C60-UNIVERSAL-WP-DRAFT-365TESTS-R2-WP-REAL-PREVIEW-20261118`.

## Objetivo original, sem desvio

A biblioteca V31 continua **universal**: dois CSVs Shopee, R2 cumulativo, classificação/nicho, revisão segura, cadastro real de qualquer Blogger/WordPress, campanha afiliada específica de cada blog, imagem REAL do SKU, texto original, CTA, link em palavra-chave, divulgação de afiliados, links internos de posts reais e publicação controlada. Blog futuro **não precisa existir antecipadamente**. Não criar cron LIVE irrestrito, não publicar SKUs REVIEW, não inventar URL/campanha/estoque/preço/vendas.

## O que ocorreu nesta sequência

### C58 — WordPress legados com dados reais

- [PR #75 MERGED](https://github.com/adelrib27/blogger-automation1/pull/75): corrigiu `ModuleNotFoundError: affiliate_hub_v31` nos construtores de fila Casa/Oficina; introduziu links para posts WordPress REAIS do mesmo blog, aceitando `/slug/` além de Blogger `*.html`. Preservou quality gate Radar.
- [C58 real 44407697822](https://github.com/adelrib27/blogger-automation1/actions/runs/44407697822) **PASS**: Casa **9**, Oficina **6**, Radar **15** produtos aprovados e cacheados com imagem real/campanha exata. Casa reuniu 6 posts WP reais e prévia em memória com **8 parágrafos/537 palavras**, CTA e 2 internos, **0 writes/posts**.

### C59 — IA real, quality gate e três SAFE workflows

- [PR #76](https://github.com/adelrib27/blogger-automation1/pull/76) centralizou modelo Workers AI suportado `@cf/meta/llama-3.3-70b-instruct-fp8-fast` para os 3 geradores WP com plano+CTA JSON Schema e corpo HTML submetido ao quality gate original.
- Primeira IA real [44409264710](https://github.com/adelrib27/blogger-automation1/actions/runs/44409264710) **FAIL protegido**: título IA tinha 22 caracteres; o gate exige 35–65. [PR #77](https://github.com/adelrib27/blogger-automation1/pull/77) permite 3 tentativas sem relaxar regra. [Segundo teste real 44410047121](https://github.com/adelrib27/blogger-automation1/actions/runs/44410047121) **PASS**, `DRAFT_READY`, **743 palavras**, foto do SKU, afiliado exato, CTA, 2 links internos, 0 posts.
- Os primeiros SAFE dos próprios WordPress detectaram outro `ModuleNotFoundError` no publicador Casa/Oficina; [PR #78](https://github.com/adelrib27/blogger-automation1/pull/78) corrigiu. [CI](https://github.com/adelrib27/blogger-automation1/actions/runs/44410794453) **357 V31+24 Casa+21 Oficina+crossblog PASS**.
- **3 workflows SAFE dos sistemas REAIS:** [Casa 44410965031](https://github.com/adelrib27/blogger-automation1/actions/runs/44410965031) PASS, [Oficina 44410976595](https://github.com/adelrib27/blogger-automation1/actions/runs/44410976595) PASS, [Radar 44410496620](https://github.com/adelrib27/blogger-automation1/actions/runs/44410496620) PASS. Nenhum deles publicou. Radar LIVE anterior ficou em QUARENTENA por alegação de acessibilidade não comprovada; a proteção foi mantida.

### C60 — QUALQUER WordPress novo, sem criar código por blog

- [PR #79 MERGED](https://github.com/adelrib27/blogger-automation1/pull/79) commit `7417c742c91b5cc450843ba6bc4fcb48f6083e55` criou `affiliate_hub_v31/automatic_wordpress_drafts.py`, cron `v31_universal_wordpress_autodraft_daily.yml` e [contrato de onboarding](WORDPRESS_AUTODRAFT_ANY_SITE.md).
- O motor usa `sites()` (registro declarativo de qualquer WordPress), `site_requests.d` (pedido/tema/quantidade REAL do proprietário) e produtos R2 aprovados com URL imagem Shopee e link de campanha exata. Conta somente rascunhos de sua autoria (slug estável V31 por site e SKU), não substitui posts legados e impede duplicação por slug/link. Cria somente `POST status=draft`, confirma `GET` e falha fechado se identidade WordPress, credenciais, conteúdo, foto ou afiliado não forem válidos. Links internos apenas de posts `publish` do mesmo host.
- A variável `V31_UNIVERSAL_WORDPRESS_AUTODRAFT_ENABLED` não foi ativada nesta execução. Cron existe, mas **default é PREVIEW**, sem escritas. Para criar novo draft real, é necessário site real registrado, pedido `enabled=true` e credenciais específicas no segredo protegido `V31_WORDPRESS_SITE_CREDENTIALS_JSON`. A aplicação WordPress conectada no ChatGPT não fornece automaticamente esses segredos ao GitHub Actions.
- [CI PR #79 44412438334](https://github.com/adelrib27/blogger-automation1/actions/runs/44412438334) **365 V31 +24 Casa +21 Oficina +crossblog PASS**. Testes mockados cobrem REST draft-only, identidade, idempotência, quota, foto/link campanha, internos e ausência de pedido.
- [**Canário REAL C60 44412775615**](https://github.com/adelrib27/blogger-automation1/actions/runs/44412775615) **PASS**: `wordpress_casa_decoracao` validado por rota real; REST público retornou **43 posts**, plano genérico achou produto R2 aprovado com foto real e cache de sua campanha na primeira consulta, gerou `READY_FOR_DRAFT_REVIEW`, **2 links internos**, `wordpress_posts_created=0`, `r2_writes=0`, `shopee_mutations=0`. Nenhuma criação REAL de draft neste canário.
- Workflows/triggers temporários C58, C59 e C60 removidos da `main` após seus testes PASS. Os permanentes continuam versionados.

## Estado real: pronto vs pendente

| Capacidade | Evidência/estado |
|---|---|
| Catálogo R2 para qualquer tema | **203.649** SKUs na última auditoria C33; revisão **194.370** na C44; não alegar contagem atual sem nova consulta |
| Conversor oficial por campanha | Operacional e validado; novos links conforme site real (não cruzar campanhas) |
| Artigo comercial com foto/CTA/internos | 3 posts LIVE no Blogger de móveis; componente genérico C54 em Blogger/WordPress; preview real C58-C60 |
| Gerador Blogger universal | C55, até 1 novo draft/dia só com pedido real/quota; Blogger piloto 3/3 já publicados, não criar 4º |
| Geradores dos 3 WordPress existentes | C59 modelo IA suportado; workflows SAFE reais PASS; **nova publicação automática pós-patch não observada** |
| WordPress FUTURO genérico | C60 configurado para qualquer rota nova; mock de POST status=draft PASS; **preview R2/WP real PASS**, **novo draft real ainda não observado** |
| Publicação LIVE automática genérica novos blogs | **Não habilitada** e não autorizada indiscriminadamente |
| Runner Windows tema Blogger ID | Proprietário adiou correção; usa tema provisório manual (não tocar no Runner) |

## Próximo passo em novo chat ou futura etapa

1. Abrir [`V31_CONTINUAR_AQUI.md`](../V31_CONTINUAR_AQUI.md), [`CONTINUIDADE_ESTADO.json`](CONTINUIDADE_ESTADO.json) e Issue #54. Verificar estados reais antes de repetir mutações.
2. Observar próxima execução agendada dos 3 WP legados e dos 2 writers universais; investigar falhas com logs sem burlar quality gate.
3. Para validar o **primeiro novo draft WordPress de ponta a ponta com REST real**: obter/confirmar pedido do usuário (site, tema, quantidade), credenciais reais separadas no GitHub secret, habilitar writer só para o site e executar um canário de `status=draft`. **Não inventar blog/credenciais**, não publicar LIVE sem aprovação.
4. Corrigir novas falhas que surjam, sempre com prévia `EM_ANDAMENTO` e checkpoint parcial ANTES das mudanças; preservar escala universal e nunca priorizar apenas os 3 WordPress.

**Frase curta de retomada:** `Continue V31 a partir de V31_CONTINUAR_AQUI.md e CONTINUIDADE_ESTADO.json; valide C60 e prossiga por evidência, sem posts duplicados.`
