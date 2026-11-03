# CHECKPOINT — CONTRATO VISUAL TEMA V20 + ISOLAMENTO DE IDENTIDADE

**Data operacional:** 2026-11-03  
**Projeto:** Blogger Automation — Sistema Mestre V20  
**Status:** VALIDADO EM LAB + VALIDADO EM PRODUÇÃO + REDE LEGADA 18/18 AUDITADA READ-ONLY

## 1. Problema confirmado

Casa Prática Lab e Vida Pet Prática haviam sido publicados com uma camada Page-target adicional que removia parte do enquadramento visual já validado do Tema Modelo V20. O adapter genérico continha um `PAGE_SURFACE_FIX` que escondia `.bg-photo-container` e `.bg-photo`, neutralizava o card/shell do post e forçava uma superfície clean/full-width.

Esse comportamento não correspondia ao padrão visual observado e já validado nos blogs V20 da rede legada.

Também foi confirmado um segundo vazamento: templates institucionais e rodapé ainda continham copy fixa de nicho do blog-modelo (`casa, cozinha, tecnologia e dia a dia`) em vez de derivar a identidade textual do próprio blog.

## 2. Correção genérica

O adapter `blogger_stores/src/blogger_new_blog_store_page_target.py` foi alterado para:

- remover o `PAGE_SURFACE_FIX` destrutivo;
- preservar a moldura visual do Tema V20;
- inserir `<!-- BLOGGER_NEW_STORE_PAGE_THEME_FRAME_PRESERVED -->`;
- continuar responsável somente por Page 20+12, carousel delegado, share e staging;
- falhar fechado se reaparecer CSS que esconda `.bg-photo-container` / `.bg-photo` ou neutralize globalmente o card do tema.

O contrato E2E foi atualizado para tornar essa preservação parte da Definition of Done de qualquer novo blog.

## 3. Isolamento de identidade no Runner V20

Branch operacional do Runner após a correção:

`blogger-safe-ui-provisioning-v0-2` — `54aeeee3840a86ca01d899c8f1c04ac2a6831cbb`

Alterações validadas por CI:

- `themes/blogger_modelo_v20/pages.json` e `templates/blogger_modelo_v20/pages.json` usam `{{BLOG_DESCRIPTION}}` no Sobre;
- o provisionador resolve `{{BLOG_TITLE}}` + `{{BLOG_DESCRIPTION}}`, aplica escape HTML e falha se sobrar token não resolvido;
- o runtime de rodapé sincroniza título pelo `feed.title` e descrição pelo `feed.subtitle` do próprio Blogger;
- marcador `BLOGGER_MODELO_V20_BRAND_DESCRIPTION_FEED_RUNTIME` obrigatório;
- copy fixa de outro nicho passa a ser erro de validação.

## 4. Validação LAB primeiro

Casa Prática Lab:

- Blog ID: `8930870316690519385`
- Page LOJA ID: `7110845449177208439`
- staging Post ID: `7691087355641688975`
- Tema V20 reaplicado com backup e paleta blue preservada;
- mesma seleção 20+12 preservada;
- nenhuma nova busca Shopee;
- nenhuma persistência de rotação;
- staging permaneceu DRAFT;
- Page LOJA migrada somente após dry-run;
- aceitação pública completa PASS.

Run da migração LAB: `41563263035` — SUCCESS.

## 5. Promoção para produção somente após PASS do LAB

Vida Pet Prática:

- Blog ID: `8052455848487624244`
- Page LOJA ID: `8624646966938350648`
- staging Post ID: `7332800716046515902`
- Tema V20 reaplicado com paleta teal preservada;
- runtime de identidade atualizado;
- mesma seleção 20+12 preservada;
- nenhuma nova busca Shopee;
- nenhuma alteração de rotação;
- staging final DRAFT;
- Page LOJA migrada para o contrato com Tema V20 preservado;
- aceitação pública PASS.

Run da promoção Vida Pet: `41563560342` — SUCCESS.

Auditor permanente read-only após a correção: `41564016789` — SUCCESS.

Auditor central após a correção: `41564016778` / `41563925532` — SUCCESS.

O workflow de migração visual foi encerrado como `RECOVERY_ONLY_MANUAL`, sem `push` e sem `schedule`.

## 6. Pente-fino read-only da rede legada

A auditoria foi desenhada respeitando a diferença arquitetural entre gerações:

- nos 18 legados, a Page pública é a superfície/moldura do Tema V20;
- o Store Post LIVE é o objeto canônico que contém 20 Store + 12 hero;
- os novos blogs Page-target não devem ser impostos retroativamente à rede legada.

Run final correto: `41564539089` — SUCCESS.

Resultado 18/18:

- Page pública HTTP 200;
- marcador Tema V20 presente;
- zero ocorrência do `blogger-new-store-page-surface-fix` novo;
- zero remoção de `.bg-photo-container` / `.bg-photo` pela camada Page-target;
- Store Post ID confirmado na lista `LIVE` da Blogger API;
- exatamente 20 produtos Store;
- exatamente 12 hero;
- 32 links `rel="nofollow sponsored noopener"`;
- Policy Guard PASS.

Os dois runs anteriores do scanner falharam por premissas incorretas do próprio auditor, não por regressão nos blogs: primeiro foi exigido 20+12 no HTML cru da Page legada; depois foi exigido `post.status` no `posts().get()`, campo que não é retornado nesse endpoint. O scanner final comprova LIVE pela listagem `posts().list(status="LIVE")`.

O scanner legado foi encerrado como auditor `MANUAL_ONLY`, read-only, sem `push` e sem `schedule`.

## 7. Regra permanente para próximos blogs

Toda mudança compartilhada de tema, Page-target, identidade, renderer ou layout deve seguir:

`código/CI → LAB com backup → dry-run → publicação controlada LAB → auditoria pública LAB → produção → auditoria pública produção → recovery manual → checkpoint`.

Um novo blog não pode ser aceito E2E se:

- remover a moldura visual do Tema V20;
- esconder `.bg-photo-container` / `.bg-photo` pela camada Page-target;
- neutralizar globalmente o card/shell do tema para criar superfície full-width;
- herdar copy, categoria, ID, URL, histórico, paleta ou identidade textual de outro blog;
- não usar a descrição real do próprio blog como fonte canônica de identidade institucional.

## 8. Estado final

- rede legada: **18/18 preservada e auditada read-only**;
- Casa Prática Lab: **contrato visual V20 corrigido e validado em LAB**;
- Vida Pet Prática: **contrato visual V20 corrigido e validado em produção**;
- próximos blogs: **novo contrato visual/identidade obrigatório e protegido por CI/auditores**;
- secrets: **não registrados neste checkpoint**.
