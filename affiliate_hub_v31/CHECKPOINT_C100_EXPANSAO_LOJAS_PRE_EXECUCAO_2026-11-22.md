# V31 — C100 | Checkpoint PRÉ-EXECUÇÃO: replicar Loja Café na Medida em blogs sem vitrine

**Criado:** 22/11/2026 (America/Recife)
**Projeto:** V31 Hub Editorial Shopee — Blogger & WordPress
**Repositório principal:** `adelrib27/blogger-automation1`, branch `main`.
**Gatilho:** solicitação expressa do proprietário de expandir a estrutura HOMOLOGADA da Loja do Café na Medida para outros blogs ainda sem loja/produtos; criar este checkpoint ANTES de qualquer alteração nos outros sites.
**Estado inicial:** INVENTÁRIO PENDENTE; NENHUMA OUTRA LOJA ALTERADA POR ESTA ETAPA.

## Origem aprovada (C96–C99)
- **Café na Medida**, Blogger blog ID `4820923154548273510`, página Loja ID `4202100014512520679`, URL `https://cafe-na-medida.blogspot.com/p/loja.html`.
- C96: 35 anúncios reais Shopee Affiliate API da conta, fotos `imageUrl` por anúncio, `offerLink` correspondente, tags de afiliado, curadoria por relevância e comissão.
- C97: corrigir cartão gigante: foto com altura estável e grade responsiva.
- C98: grade CONTÍNUA única para todos os cartões (não uma grade por categoria); preservar atalhos de categorias e seção de guias; ocultar via CSS específico da página o aviso legado de foto/carrossel vazio e cabeçalho duplicado, quando existirem. **Não copiar ID do Café para outros blogs:** verificar tema e elemento DOM de cada site antes de aplicar seletores.
- C99: 35 botões `Ver oferta na Shopee` em laranja-avermelhado `#D83F00`, texto branco e brilho, sem alterar demais elementos. Texto branco com contraste calculado ~4,53:1.
- Arquivo-fonte da vitrine do Café atual via Blogger `get_page`; checkpoints:
  - `affiliate_hub_v31/CHECKPOINT_C96_CAFE_NA_MEDIDA_LOJA_35_LIVE_2026-11-22.md`;
  - `affiliate_hub_v31/CHECKPOINT_C97_CAFE_NA_MEDIDA_LOJA_CARD_RESPONSIVO_2026-11-22.md`;
  - `affiliate_hub_v31/CHECKPOINT_C98_CAFE_LOJA_GRADE_CONTINUA_2026-11-22.md`;
  - `affiliate_hub_v31/CHECKPOINT_C99_CAFE_LOJA_BOTOES_LARANJA_2026-11-22.md`.

## Escopo
- Inventariar **todos** os blogs Blogger e sites WordPress alcançáveis pelo conector autorizado do usuário.
- Detectar os que não possuem página Loja, cuja página Loja esteja vazia/sem anúncios, ou cuja vitrine atual não contenha fotos e afiliados reais; distinguir blog de produção dos blogs de laboratório ou não lançados.
- **Antes de criar/atualizar página:** confirmar blog ID, título, nicho e site; verificar se já existe `/p/loja.html`/slug de loja e se há edição concorrente; fazer backup de HTML antigo no GitHub.
- **Nunca substituir** vitrines com produtos reais já funcionais sem necessidade. Só atualizar páginas vazias/sem produtos, criando página Loja quando não existir e a elegibilidade/nicho forem comprovados.
- Curadoria REAL: Shopee Affiliate Open API usando secrets do environment `v31-editorial-safe` em GitHub Actions READ ONLY (consultas `productOfferV2`); validar `shopId:itemId`, `imageUrl`, `productLink` e `offerLink` da mesma oferta, reputação, relevância, variedade de vendedores e comissão. Não inventar produtos, fotos, links ou comissões. `offerLink` da conta não comprova SubID do blog; **não usar `generateShortLink` sem observar cota D1**.
- Meta orientadora: 24+ produtos por Loja quando disponíveis e válidos; se não houver quantidade suficiente, **não completar com produtos de outros nichos nem publicar vitrine fictícia**. Guardar shortlist e registrar bloqueio.
- Manter o tema e páginas institucionais intactos, não duplicar páginas, artigos, links, nem crons. Preservar `V31_AUTOLIVE_ACTIVE=false`; não tocar em Pinterest, R2/D1, assinaturas HMAC de rascunhos, ou outros projetos.
- QA pós-escrita: Blogger/WP GET e HTML público, conteúdo exato, 24+ cards quando possível, fotos 1:1 da API, `rel="nofollow sponsored noopener noreferrer"`, links de guias pertinentes, menus/categorias, desktop/mobile e CSS de botões #D83F00. Confirmar que nenhuma informação interna da automação está visível.

## Protocolo de retomada sem duplicação
1. Ler `V31_CONTINUAR_AQUI.md`, `affiliate_hub_v31/CONTINUIDADE_ESTADO.json`, este checkpoint e registros `C100_*` feitos posteriormente.
2. Conferir **estado atual do CMS** por blog/página antes de qualquer escrita; um log `pending` não é prova de que a edição falhou nem licença para duplicar.
3. Para cada blog, registrar: ID, URL, plataforma, nicho, página Loja ID, estado antigo, backup, quantidade de offers verificados, evidência da API, ação exata, request_id, GET final, URL pública, status e pendências.
4. Atualizar o checkpoint progressivamente e o índice permanente `V31_CONTINUAR_AQUI.md` nas etapas de entrega; preservar caminho do rollback para cada site.
5. Se a conversa expirar, **não reexecutar cegamente**: começar pela última etapa com status não verificado, reler CMS/GitHub e comparar assinatura/contagem.

**Próxima ação autorizada:** iniciar inventário READ ONLY; depois aplicar modelos validados a blogs elegíveis, com operações de escrita individuais, registro e reconciliação. 
