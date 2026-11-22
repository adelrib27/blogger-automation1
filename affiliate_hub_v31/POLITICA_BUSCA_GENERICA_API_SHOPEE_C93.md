# V31 C93 — Busca ampla primeiro, seleção editorial depois (Shopee Affiliate API)

**Decisão do proprietário:** 22/11/2026, no projeto V31 Blogger & WordPress. **Primeiro piloto:** Ar-Condicionado sem Dúvidas, Blogger ID `2228849984262880811`.

## Objetivo
Ampliar a quantidade e variedade de aparelhos candidatos a artigos: começar pela busca genérica `productOfferV2(keyword: "ar condicionado")` e somente depois aplicar a classificação. **Não confundir encontrar um anúncio diferente com necessariamente merecer um novo artigo.** Um mesmo modelo pode aparecer em vários vendedores; o blog deve evitar posts clonados.

## Algoritmo C93 implementado
1. **Busca primária por termo amplo:** `"ar condicionado"`, sem exigir BTUs 9.000/12.000, inverter, split ou uma marca no GraphQL.
2. **Consulta limitada e paginada:** `sortType=1`, até 30 itens por página, no máximo 2 páginas por termo e no máximo 4 chamadas de API por execução. Seguir `hasNextPage` quando houver produtos relevantes; não insistir na página 2 se a primeira teve apenas acessórios.
3. **Fallback com rotação diária**, sem abandonar a consulta genérica: `ar condicionado split`, `ar condicionado inverter`, `ar condicionado de janela`, `ar condicionado portatil`, `ar condicionado 18000 btus`. A ordem do fallback muda por dia UTC para não ficar preso à mesma seleção.
4. **Filtro de objeto principal após retorno da API:** aceitar aparelhos completos de capacidades e tecnologias diversas. Excluir controles, suportes, filtros, tubos, peças automotivas, evaporadoras avulsas, turbinas, radiadores, molduras, vedações, climatizadores evaporativos e itens USB disfarçados de ar-condicionado. Uma correspondência nominal não basta para prova de aparelho completo.
5. **Identidade do anúncio:** conferir `shopId:itemId`, URL original da Shopee, foto, título, preço de referência positivo, período da oferta e `offerLink` original retornado pela API. Link não comprova estoque.
6. **Identidade técnica do modelo:** para agrupar anúncios de vendedores diferentes exige marca, código do fabricante, capacidade, ciclo, tensão e variante correspondentes; quando algum dado faltar, **não mesclar automaticamente**. Anúncios adicionais do mesmo modelo servem como alternativas de compra em um artigo existente.
7. **Novidade editorial:** comparar com anúncios já publicados e com os temas dos artigos do Blogger; selecionar para revisão um produto ou ângulo editorial distinto, não criar artigo só porque `itemId` mudou. Manter o permalink do guia existente quando vendedores mudam.
8. **Disponibilidade proporcional:** utilizar a política de estoque C92. Um único alerta de esgotamento não bane o modelo; procurar outras lojas, revalidar variante e permitir reposição. Não prometer estoque.
9. **API resiliente:** `10000` é erro transitório de sistema, não equivale a zero produto. Não fazer repetição ilimitada; registrar o erro e avançar para outro termo se estiver dentro do orçamento. `10030` encerra a execução; respeitar limites.
10. **Nenhuma publicação automática autorizada por este módulo:** descoberta é READ ONLY, não usa `generateShortLink`, não consome D1 e não envia posts ao Blogger. A integração com geração de DRAFT depende do gate/editor de conteúdo e confirmação de SKU, foto, estoque e não duplicidade; `V31_AUTOLIVE_ACTIVE=false` permanece.

## Artefatos e cadência
- Código: `affiliate_hub_v31/aircon_discovery.py`.
- Testes puros: `affiliate_hub_v31/tests/test_aircon_generic_discovery.py`.
- Histórico inicial de 3 anúncios já cobertos: `affiliate_hub_v31/aircon_editorial_history.json`. **Deve ser atualizado sempre que novos artigos forem publicados**; o script nunca edita esse histórico por conta própria.
- Taxonomia universal v5: `affiliate_hub_v31/taxonomy.json`, com `climatizacao/ar_condicionado` genérico, janela, portátil legítimo e negativos de acessórios.
- GitHub Actions: `.github/workflows/v31_c93_arcond_generic_keyword_discovery_safe.yml`.
- Agendado diariamente às **13:17 UTC / 10:17 de Recife**, com possibilidade de atrasos na plataforma GitHub Actions; também permite disparo manual; no `main`, workflow de **consulta e shortlist**.
- Saída de cada execução: `c93_candidates.json` armazenado como artefato `v31-c93-arcond-readonly-shortlist` por 7 dias, para seleção editorial posterior, sem segredos.
- O workflow roda até 4 chamadas de API por ciclo. Candidatos podem se repetir entre dias enquanto não houver nova revisão/publicação; **não existe garantia de um artigo inédito em todo ciclo**.

## Evidências de testes reais
- GitHub run [#45060366821](https://github.com/adelrib27/blogger-automation1/actions/runs/45060366821): primeiro termo amplo trouxe **30 resultados na primeira página**, muitos acessórios e peças, demandando filtro posterior; página 2 retornou código `10000`.
- GitHub run [#45060534006](https://github.com/adelrib27/blogger-automation1/actions/runs/45060534006): após filtro mais rigoroso, fallback `ar condicionado de janela` identificou modelos Consul, Hisense e Midea (7.500, 8.500, 10.000 e 12.000 BTUs) e também revelou 2 acessórios residuais, depois bloqueados.
- GitHub run [#45060787418](https://github.com/adelrib27/blogger-automation1/actions/runs/45060787418): `ar condicionado inverter` retornou **30 resultados**, com candidatos de LG, Elgin, Gree, Daikin e outros; duas peças/uso veicular vistas no log levaram a filtros adicionais. Seis testes unitários PASS e taxonomia PASS; JSON de shortlist escrito e validado.
- O resultado exato muda com a API e horário. A execução final C93 deve ser confirmada nos logs antes de afirmar todos os testes concluídos.

## Proteção e continuidade
Este fluxo não altera posts de outros blogs, C81, Pinterest, D1, R2, automação LIVE nem a campanha Shopee. Novo artigo = assunto/variante que justifique conteúdo próprio; anúncio adicional do mesmo modelo = alternativa na oferta existente após verificação de link e foto. Manter relatório de decisões e status de cada candidato.
