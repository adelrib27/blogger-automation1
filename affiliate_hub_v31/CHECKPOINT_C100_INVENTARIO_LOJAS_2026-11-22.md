# V31 C100 — Inventário READ ONLY de Lojas — 22/11/2026

> **RETIFICAÇÃO OBRIGATÓRIA (22/11):** este documento registra a PRIMEIRA fotografia de leitura das **Pages**, mas a inferência de **19 lojas sem produtos está errada**. 18 Pages redirecionavam para posts com 20 links afiliados cada (Achados para Casa: 32). A única Loja comercial realmente vazia é **Móveis para Cada Canto**, conforme [C100 auditoria definitiva](CHECKPOINT_C100_CORRECAO_REDIRECIONAMENTOS_LOJAS_2026-11-22.md). Não usar a lista antiga de 19 para novas escritas. Manifesto e estado foram corrigidos.


**Pré-condição:** checkpoint anterior [C100 PRÉ-EXECUÇÃO](CHECKPOINT_C100_EXPANSAO_LOJAS_PRE_EXECUCAO_2026-11-22.md) já salvo e indexado antes das leituras.

## Resumo confirmado via Blogger API v3
- **32 blogs Blogger** inventariados, todas páginas listadas por ID.
- **31** têm página `/p/loja.html` existente e LIVE. **1** blog não iniciado (*Meu Céu Noturno*, 0 artigos e 0 páginas) excluído.
- **19 lojas Blogger sem produtos no HTML** (0 tags IMG, 0 shortlinks afiliados), elegíveis para abastecimento do V31 após obter 24+ anúncios reais e compatíveis.
- **11 lojas Blogger comerciais com produtos** (de 1 a 35 anúncios com imagens e shortlinks afiliados). Não substituir em C100 sem necessidade.
- **1 LAB** (*Casa Prática Lab*, 20 ofertas e 32 imgs) excluído como laboratório.
- **3 WordPress conectados** (Radar Tech, Casa e Decoração, Oficina & Garagem) têm páginas publicadas `/loja/` e **vitrines comerciais já preenchidas**, verificadas por leitura de HTML público: Radar Tech BR **21** destinos Shopee distintos e 29 imagens; Casa e Decoração **32** destinos e 44 imagens; Oficina & Garagem **24** destinos e 36 imagens. **Preservar, não sobrescrever** na C100. O conector WP `get_page` não retornou corpo utilizável; por isso não houve edição WordPress.

## Fila prioritária — 19 lojas vazias
1. **Liquidificadores em Foco** — blog_id `5271798990390532475`; Loja page_id `5473313787015756722`; `status=PENDING_REAL_OFFERS`, `updated_by_C100=false`.
2. **Cozinha Sem Complicação** — blog_id `3552757910439359679`; Loja page_id `6913756651435112886`; `status=PENDING_REAL_OFFERS`, `updated_by_C100=false`.
3. **Portal Radar Tech** — blog_id `7487888217273188851`; Loja page_id `6887385207246667244`; `status=PENDING_REAL_OFFERS`, `updated_by_C100=false`.
4. **Achadinhos de Beleza** — blog_id `2562496977098748229`; Loja page_id `455853998448723529`; `status=PENDING_REAL_OFFERS`, `updated_by_C100=false`.
5. **Moda e Ofertas** — blog_id `2858597309582499028`; Loja page_id `1341310014099438949`; `status=PENDING_REAL_OFFERS`, `updated_by_C100=false`.
6. **Vitrine Prática** — blog_id `9144338307944682868`; Loja page_id `8344701886444887322`; `status=PENDING_REAL_OFFERS`, `updated_by_C100=false`.
7. **Guia de Achados & Ofertas** — blog_id `1453188702831337099`; Loja page_id `9156313162825773745`; `status=PENDING_REAL_OFFERS`, `updated_by_C100=false`.
8. **Achados que Valem** — blog_id `7527651041649593600`; Loja page_id `2615453333851618808`; `status=PENDING_REAL_OFFERS`, `updated_by_C100=false`.
9. **Escolha Certa Online** — blog_id `5151950717041967683`; Loja page_id `3334029815604129982`; `status=PENDING_REAL_OFFERS`, `updated_by_C100=false`.
10. **Casa em Ordem** — blog_id `4177382081459143374`; Loja page_id `4031853959690608178`; `status=PENDING_REAL_OFFERS`, `updated_by_C100=false`.
11. **Estilo no Dia a Dia** — blog_id `4830103887652146866`; Loja page_id `4843501559117111153`; `status=PENDING_REAL_OFFERS`, `updated_by_C100=false`.
12. **Conecta Achados** — blog_id `1719259388907013414`; Loja page_id `2386698852540729057`; `status=PENDING_REAL_OFFERS`, `updated_by_C100=false`.
13. **Limpeza Inteligente** — blog_id `7757953554206491487`; Loja page_id `4457645831148890823`; `status=PENDING_REAL_OFFERS`, `updated_by_C100=false`.
14. **Ventiladores em Foco** — blog_id `4473989735719981382`; Loja page_id `8010344677278545283`; `status=PENDING_REAL_OFFERS`, `updated_by_C100=false`.
15. **Achados para Casa** — blog_id `1426630233929943394`; Loja page_id `3841238517239710135`; `status=PENDING_REAL_OFFERS`, `updated_by_C100=false`.
16. **Eletroportáteis na Cozinha** — blog_id `8658632621591002634`; Loja page_id `2989554269967771834`; `status=PENDING_REAL_OFFERS`, `updated_by_C100=false`.
17. **Cabelos em Foco** — blog_id `6319734511998091378`; Loja page_id `3590970839633701768`; `status=PENDING_REAL_OFFERS`, `updated_by_C100=false`.
18. **Air Fryers em Foco** — blog_id `9113728635217260884`; Loja page_id `6090919827060846509`; `status=PENDING_REAL_OFFERS`, `updated_by_C100=false`.
19. **Móveis para Cada Canto** — blog_id `1439741542627895062`; Loja page_id `5105320514641154037`; `status=PENDING_REAL_OFFERS`, `updated_by_C100=false`.

## Já possuem produtos, preservar por enquanto
- Jardim e Horta na Prática: **16 links afiliados diferentes** encontrados na página Loja (consulta do CMS).
- Vida Pet Prática: **20 links afiliados diferentes** encontrados na página Loja (consulta do CMS).
- Mala Pronta e Viagem Prática: **16 links afiliados diferentes** encontrados na página Loja (consulta do CMS).
- Ateliê Criativo em Casa: **16 links afiliados diferentes** encontrados na página Loja (consulta do CMS).
- Achados da Rotina: **16 links afiliados diferentes** encontrados na página Loja (consulta do CMS).
- Casa Leve e Funcional: **16 links afiliados diferentes** encontrados na página Loja (consulta do CMS).
- Pedal Leve: **16 links afiliados diferentes** encontrados na página Loja (consulta do CMS).
- Violão do Começo: **16 links afiliados diferentes** encontrados na página Loja (consulta do CMS).
- Café na Medida: **35 links afiliados diferentes** encontrados na página Loja (consulta do CMS).
- Ar-Condicionado sem Dúvidas: **2 links afiliados diferentes** encontrados na página Loja (consulta do CMS).
- Cadeira Certa no Home Office: **1 links afiliados diferentes** encontrados na página Loja (consulta do CMS).

## Não operar
- Casa Prática Lab: ambiente de teste (20 links Shopee e 32 imagens).
- Meu Céu Noturno: blog ainda não lançado, sem conteúdo nem loja.

## Gates para implementar
1. Obter shortlist **READ ONLY Shopee Affiliate Open API**, por nicho; `shopId`, `itemId`, `productName`, `imageUrl`, `productLink`, `offerLink` e dados para ranking de comissão. Imagem, URL e produto devem se corresponder.
2. Apurar 24+ ofertas distintas válidas por loja sem usar produtos fictícios e sem selecionar acessórios incorretos do nicho. Não inventar estoque, conversões ou taxas.
3. Antes de cada update: GET página LIVE e backup do HTML pré-existente. Não criar página de mesmo título se já existe. Registrar request_id individual.
4. Implantar estrutura C98/C99: grade única, categorias, links internos reais, botões CTA #D83F00, CSS do tema limitado ao `post-body-{page_id}`; nenhum texto técnico da API exposto aos visitantes.
5. GET CMS e verificação pública; só então registrar site como `LIVE_VERIFIED` e avançar para próximo.
6. Se menos de 24 produtos: registrar número e razão `BLOCKED_INSUFFICIENT_REAL_OFFERS`; preservar loja antiga, nunca preencher meta com imagens ou URLs inventadas.
7. Todos os crons, `V31_AUTOLIVE_ACTIVE`, D1/R2, links do Pinterest e artigos permanecem intactos.

**C100 inventário: CONCLUÍDO. Implementação da fila: INICIAR mediante shortlist Shopee REAL por nicho.**
