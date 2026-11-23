# V31 C102 — PRE-EXECUÇÃO: um artigo por blog Blogger elegível — 23/11/2026
**Criado antes de qualquer nova escrita de post.**
**Origem:** solicitação do proprietário em 23/11/2026: “criar um artigo para cada blog do blogger”.

## Escopo e segurança
- Inventário autenticado Blogger API: **32 blogs**. 30 blogs editoriais de produção (21 roteados V31 + 9 editoriais não roteados); 1 LAB `Casa Prática Lab` e 1 blog não lançado `Meu Céu Noturno` (0 posts, 0 páginas). Manter exclusões conforme C94 a menos que usuário peça explicitamente para lançar/testar LAB.
- Objetivo: **1 NOVO artigo para cada um dos 30 blogs ativos**, alinhado ao nicho, SEO, intenção de busca, conteúdo original e link interno contextual.
- Verificar a existência de artigo novo já produzido em 23/11, *antes* de criar, para respeitar cotas de frequência e evitar duplicações por tema ou título.
- **Nunca** editar Loja, tema ou posts existentes em C102. Em C101 as lojas Achados para Casa e Cozinha Sem Complicação foram restauradas e apenas Móveis recebeu nova vitrine.
- Cada artigo com conteúdo substancial e original, não clonado, sem jargões de tecnologia interna, falsa declaração de testes, preços/descontos absolutos, propaganda enganosa ou alegações de comissão garantida.
- Usar como fontes apenas produtos reais da Shopee com mesmo SKU+foto+link afiliado confirmado se houver, caso contrário conteúdo editorial informativo sem produto específico e sem link fictício; orientar leitores para Loja existente e leitura relacionada.
- Não gerar `generateShortLink` nem consumir D1 sem cota; não alterar R2, Cloudflare, Pinterest ou tokens; preservar `V31_AUTOLIVE_ACTIVE=false` e `publish_enabled=false` em rotas automáticas.
- Publicação MANUAL de artigo individual pela Blogger Bridge V2 somente se a edição estiver homologada (C94 precedeu com drafts e verificação) e sem outra publicação nova no dia. O pedido de criação NÃO autoriza ativação de publicação automática.
- Fluxo por blog: GET inventário de posts LIVE/drafts → verificar data/título/intenção → preparar artigo → create_post is_draft=true idempotente → get_post confirmar → eventualmente publish_post individualmente sob autorização vigente e QA → GET final e URL → registrar checkpoint/manifesto site.
- Gravar progresso incremental e ids, para evitar repetição em novo chat. Não alegar resultados sem verificação real.

## Retomada
Ler este arquivo, `V31_CONTINUAR_AQUI.md`, `affiliate_hub_v31/CONTINUIDADE_ESTADO.json`, `CHECKPOINT_C94_RODADA_ARTIGO_UNICO_BLOGS_2026-11-22.md` e o manifesto C102 que será criado após o inventário. Ao retomar, **consultar o estado de cada Blogger post via API** antes de repetir create, nunca inferir que rascunho ou publicação falhou por ausência de log.
**Estado inicial:** nenhum post C102 criado; inventário em andamento.
