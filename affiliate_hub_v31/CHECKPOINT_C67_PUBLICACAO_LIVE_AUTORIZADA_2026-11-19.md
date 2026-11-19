# C67 — publicação LIVE individual autorizada: WordPress Casa #305 (19/11/2026)

**STATUS: EM_ANDAMENTO, CHECKPOINT DE PRÉ-EXECUÇÃO (nenhuma publicação confirmada nesta etapa).**

## Contexto e autorização verdadeira
- Retomada pela `main`: [índice](../V31_CONTINUAR_AQUI.md), [estado JSON](CONTINUIDADE_ESTADO.json) e [checkpoint C66](CHECKPOINT_C66_REVISAO_REAL_LIVE_2026-11-19.md).
- **Autorização explícita do proprietário nesta conversa:** após apresentação do título e do post exatos e pergunta “Você autoriza publicar exclusivamente o artigo WordPress Casa #305 — ‘Como escolher um vaso decorativo âmbar para sua sala’ — após essa conferência, sem liberar os demais rascunhos?”, o proprietário respondeu **“sim! Autorizo”**. Escopo: SOMENTE WordPress `wordpress_casa_decoracao` POST #305, nenhuma automação LIVE em massa, nenhum outro rascunho.
- Antes da autorização, PR93 corrigiu subtítulos para Blogger+WordPress (CI405) e PR94 vinculou hash ao título+HTML, identidade WordPress exata (CI407). [Preflight LIVE oficial #44577760603](https://github.com/adelrib27/blogger-automation1/actions/runs/44577760603) SUCCESS/0 POST/`AWAITING_OWNER_APPROVAL`, digest: `ccc848b143a51235dba21b89be4b5dad92c538300678b9b8854347a5297d9b63`. Conteúdo validado `753` palavras, 8 seções, bloco comercial inalterado.
- API remota nesta retomada: site autenticado `https://casaedecoracao.radartechbr.com.br`, WordPress #305 `draft`, título “Como escolher um vaso decorativo âmbar para sua sala”, slug `v31-31856a8a43a1-58259898640`, HTML editorial+oferta, WP totais **43 LIVE +59 DRAFT**. Dois links internos verificáveis, foto catálogo CSV e SKU `shopee:1718605288:58259898640`.

## Conferência comercial externa antes de publicar
- **Anúncio Shopee exato encontrado no catálogo público atual da loja**, acessado pelo pesquisador em **19/11** com URL `https://shopee.com.br/Vaso-Decorativo-R%C3%B4mulo-%C3%82mbar-30cm-%E2%80%93-Design-Moderno-e-Elegante-i.1718605288.58259898640`; HTML público exibiu título igual ao produto cadastrado e preço visível (não reproduzido no artigo). Identificadores em URL correspondem **shop_id=1718605288**, **item_id=58259898640**.
- **Link oficial de afiliado do DRAFT**, `https://s.shopee.com.br/8pnOgLent4`, foi testado via navegador de scraping live com cache desativado (`maxAge=0`); o redirecionamento apontou ao caminho de anúncio `/product/1718605288/58259898640` **com identificador de campanha afiliada (`mmp_pid`)**. A Shopee exibiu verificação de tráfego/login ao navegador de automação após o redirect; checkout/estoque individual e comissão efetiva não são comprováveis; o artigo **não** contém alegação de estoque garantido, comissão específica, prazo ou preço fixo. O R2 já continha link oficial dessa campanha, confirmado no preflight C66.
- **Resultado da revisão comercial C67:** identidade SKU + URL anunciada + redirect exato+tracking + foto CSV e transparência comercial sustentam publicação prudente; não afirmar que pedidos ou disponibilidade foram verificados. Nenhuma especificação não comprovada foi acrescentada.

## Sequência de liberação controlada (execução a registrar abaixo)
1. Persistir este checkpoint + marcar `active_work` C67 `EM_ANDAMENTO` antes de criar manifesto.
2. Conferir WP #305 ainda `draft`, título/slug/hash intactos e ausência de manifesto `live_approvals.d/wordpress_casa_decoracao__305.json`.
3. Criar **UM** manifesto de aprovação real no GitHub main com `owner_authorized:true` (declaração explícita acima), `editorial_reviewed:true` (revisão C66), `commercial_reviewed:true` (checagens externas C67), SHA de título+HTML e timestamp UTC válido. Nenhum outro manifesto.
4. Disparar via API GitHub o workflow PERMANENTE `.github/workflows/v31_manual_live_release.yml` **UMA ÚNICA VEZ**, com `site_key=wordpress_casa_decoracao`, `post_id=305`, `execute_live=true`, `confirm_exact_post=PUBLISH:wordpress_casa_decoracao:305`. Usar disparador temporário de uso único com token efêmero limitado a Actions write e exclusão da main após o disparo. Não chamar o endpoint de WordPress fora da trilha com gate.
5. Aguardar terminal do run, verificar logs `LIVE_CONFIRMED` e `publication_calls=1`, realizar readback WordPress independente para ID/título/URL/status e contagens. **Se o POST falhar ou for incerto, não repetir** até investigação CMS.
6. Limpar workflows TEMP, atualizar checkpoint, estado JSON e índice permanente. Manter os crons Writer DRAFT-only e a conferência `event=schedule` de 20/11 à parte.

## Controle de riscos
- Nenhum LIVE na C67 até readback positivo. Nenhuma edição de título/HTML após aprovação sem novo digest.
- Não ativar `publish_enabled` global nem editar outros blogs/links/CSV.
- Motivo de qualquer bloqueio será registrado com status `PENDENTE` e readback, nunca simular sucesso.

## C67.1 — manifesto de aprovação REAL e conferência pré-POST
- API WordPress antes de qualquer publicação: **#305 = draft**, título exato “Como escolher um vaso decorativo âmbar para sua sala”, slug `v31-31856a8a43a1-58259898640`, 7249 caracteres, SKU exato, fotografia, link afiliado, CTA e disclosure presentes. Nenhum run Actions prévio estava executando.
- Manifesto criado **uma única vez** em `live_approvals.d/wordpress_casa_decoracao__305.json`, commit [`efabd77941d4bccf0cc2e375429b968b84b7078f`](https://github.com/adelrib27/blogger-automation1/commit/efabd77941d4bccf0cc2e375429b968b84b7078f). `owner_authorized=true` apoiado pelo “sim! Autorizo” do proprietário ao post específico. `editorial_reviewed=true` pela revisão manual C66; `commercial_reviewed=true` limitado à prova do SKU na Shopee, redirecionamento para mesmo SKU e programa afiliado cadastrado em R2 (antibot Shopee impediu checkout; não inferir comissão ou estoque). `approved_utc=2026-11-19T17:58:58.214Z`; `content_sha256=ccc848b143a51235dba21b89be4b5dad92c538300678b9b8854347a5297d9b63` (título+HTML conforme PR94).
- **NÃO PUBLICADO AINDA** ao gravar manifesto: a publicação exige execução separada do workflow manual, confirmação literal e readback CMS. Próxima mutação: dispatch de execução individual apenas.
