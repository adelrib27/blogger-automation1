# V31 C93 — Busca genérica na Shopee para novos artigos de ar-condicionado

**Data:** 22/11/2026. **Blog:** Ar-Condicionado sem Dúvidas, Blogger ID `2228849984262880811`. **Branch:** `main`.

## Mudança aprovada
O usuário observou que pesquisar na Shopee Affiliate API com termos muito específicos, como um modelo/SKU e apenas 9.000 ou 12.000 BTUs, reduz as chances de novos artigos. A regra decidida é **buscar primeiro `ar condicionado` e validar depois**, percorrendo modelos/lojas variados sem confundir anúncio duplicado com assunto editorial inédito.

## Implementação REAL
- Código novo: `affiliate_hub_v31/aircon_discovery.py`. Endpoint real `productOfferV2(keyword:"ar condicionado",sortType:1,page:1,limit:30)`, consulta autenticada via segredos GitHub `v31-editorial-safe`. Não contém `generateShortLink`, D1, Blogger API ou permissão de escrever artigos.
- Termo principal sempre `ar condicionado`, seguido de fallbacks por dia UTC rotativos entre `ar condicionado split`, `ar condicionado inverter`, `ar condicionado de janela`, `ar condicionado portatil`, `ar condicionado 18000 btus`. Máximo **4 queries** por ciclo e **2 páginas/termo**, 30 itens/página, respeita `pageInfo.hasNextPage`. Se primeira página só tem acessórios, ir para outro termo. `10000` (erro de sistema Shopee) é sinal de erro, não falta de oferta; `10030` encerra o ciclo.
- Filtro após busca: apenas unidade completa de ar-condicionado, de qualquer capacidade elegível, excluindo controles, suportes, molduras, caixonetes, caixilhos, ventiladores USB, resfriadores evaporativos, peças de climatização e veículos. Requer evidência de aparelho real por BTUs, formato ou marca; revisão editorial manual obrigatória.
- Identifica `listing_key=shopId:itemId` separado de `identity_key` de variante técnica (só agrupar com marca/código/capacidade/tensão/ciclo conhecidos); não faz merge incerto nem clona artigos.
- `affiliate_hub_v31/aircon_editorial_history.json` cadastra os três anúncios dos posts existentes LG/Midea. Necessita atualização após novas publicações para impedir repetição posterior.
- `affiliate_hub_v31/taxonomy.json` agora `v31-editorial-taxonomy-6`, incluindo termo genérico e aparelhos portáteis reais no nicho ar-condicionado, e excluindo acessórios automotivos e caixonetes. Rota do blog segue `publish_enabled=false`.
- Testes unitários: `affiliate_hub_v31/tests/test_aircon_generic_discovery.py`.
- Workflow `.github/workflows/v31_c93_arcond_generic_keyword_discovery_safe.yml` configurado para `push` do próprio workflow, `workflow_dispatch` e `schedule: '17 13 * * *'` (UTC; ~10h17 Recife diariamente). **Somente READ ONLY** e sem processo de criação/publicação de DRAFT/LIVE.
- Toda execução grava `c93_candidates.json`, validado por `python -m json.tool` e hospedado como artefato GitHub `v31-c93-arcond-readonly-shortlist` por sete dias. Nenhuma senha é impressa nos logs ou escrita no arquivo.

## Execuções realmente verificadas
- [#45060366821](https://github.com/adelrib27/blogger-automation1/actions/runs/45060366821) — busca literal `ar condicionado` retornou **30 resultados na página 1**, mas havia muitos acessórios; página 2 erro transitório `10000`, sem publicação.
- [#45060534006](https://github.com/adelrib27/blogger-automation1/actions/runs/45060534006) — busca com fallback `ar condicionado de janela` encontrou modelos de janela Consul, Midea e Hisense 7.500/8.500/10.000/12.000 BTUs, e 2 acessórios que motivaram nova correção.
- [#45060787418](https://github.com/adelrib27/blogger-automation1/actions/runs/45060787418) — busca `ar condicionado inverter` retornou 30 anúncios, entre eles LG, Gree, Daikin, Elgin; novos falsos positivos veiculares/turbinas filtrados posteriormente. Seis testes PASS; artefato criado.
- [#45061051725](https://github.com/adelrib27/blogger-automation1/actions/runs/45061051725) — **SUCCESS**, 6 testes unitários PASS e classificação ampla PASS; `ar condicionado` retornou erro `10000` nessa execução, mas fallback `ar condicionado de janela` percorreu duas páginas de 30 retornos, com **21 candidatos preliminares**, incluindo acessórios identificados e filtrados depois. Shortlist JSON gravada e artefato GitHub `14768959412` publicado (7 dias). Nenhuma chamada de escrita ao Blogger/Shopee.
- [#45061178103](https://github.com/adelrib27/blogger-automation1/actions/runs/45061178103) — execução FINAL com exclusão de caixonetes/molduras e taxonomia v6. **Pendente verificar conclusão no momento de criar checkpoint; atualizar após inspecionar logs.**

## O que NÃO está autorizado/implementado
- **Não** garante um produto único e adequado por dia: API pode falhar, devolver os mesmos anúncios ou variantes repetidas. O workflow entrega **candidatos para revisão**, não artigos.
- Não gera DRAFT ou LIVE automaticamente; não escolhe vendedor sem verificar SKU e disponibilidade; não gera link novo com SubID; não abre cota de conversão; não reativa LG sozinho.
- Não sincroniza sozinho o histórico com os posts Blogger: exige que cada publicação registrada no V31 atualize a lista de anúncios e confirme que o modelo ainda não foi abordado.
- A execução diária está configurada, mas o primeiro evento `schedule` está previsto para 23/11/2026 (~10h17 Recife) e **não é execução futura confirmada**; GitHub pode atrasar cron. Não afirmar agendamento disparado sem logs.
- `V31_AUTOLIVE_ACTIVE=false` permanece; não tocar em Pinterest, WordPress, C81 assinado, R2/D1 ou outros blogs.

**Política:** [POLITICA_BUSCA_GENERICA_API_SHOPEE_C93.md](POLITICA_BUSCA_GENERICA_API_SHOPEE_C93.md). **Próxima ação:** confirmar CI final; usar shortlist e histórico para escolher um modelo ainda sem artigo e então aplicar gate editorial, foto, campanha, disponibilidade e publicação individual/draft conforme autorização.
