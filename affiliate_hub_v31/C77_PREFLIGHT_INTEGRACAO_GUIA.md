# C77 — contrato do preflight universal antes da reserva READY (SAFE)

Este módulo é uma integração de gates, não um publicador. Nunca habilitar em cron até haver prova de credenciais, revisão independente e canário no D1 oficial.

## Ordem de execução
1. Ler apenas o catálogo V31 (foto original do SKU, produto elegível, campanha exata e URL afiliada cacheada). O D1 não armazena nem substitui os dois CSVs/R2.
2. Conferir imagem do mesmo SKU e link Shopee EXATO no mesmo HTML, rel="nofollow sponsored", CTA visível e aviso de afiliado. Recusar outra URL Shopee no corpo.
3. Calcular novamente o relatório SEO C68 sobre **aquele HTML**, com pesquisa de intenção fornecida por fonte externa independente, cluster e posts LIVE existentes — sem aceitar `seo_audit` pronto gerado pela IA.
4. Revalidar evidence whitelist C69 (fonte exata autorizada, SHA, TTL), e o fact gate C71 com spans de evidências e hashes dos trechos editoriais revisados.
5. Exigir manifesto HMAC-SHA256 produzido **fora da IA/escritor**, com chave dedicada, vinculando site, campanha, SKU, HTML hash, pacote de evidência hash, pesquisa SEO hash, pauta e hashes dos trechos editoriais. O pré-validador NÃO assina manifestos.
6. Só depois adquirir lease de refill e registrar cache de evidência + READY no estado D1 C76 (SQL atômico); liberar o lease mesmo na falha. Não aciona CMS nem LIVE.

## Limites e cautelas
- A chave `V31_READY_REVIEW_HMAC_KEY` é uma especificação de controle futuro, não existe como segredo configurado nesta fase. Mantê-la exclusivamente no serviço revisor com permissões separadas do writer e da IA.
- **HMAC comprova posse da chave e integridade dos bytes, não comprova sozinho revisão humana**. O serviço emissor precisa de aprovação/identidade/trilha editorial verdadeiras e revisão comercial; a saída do modelo nunca poderá invocá-lo diretamente.
- A validação SEO sintática não prova volume de buscas, Search Console, posição, desempenho ou comissão. As evidências `AUTHORIZED` precisam ser autenticamente registradas por um verificador externo.
- `articles:null` permite geração contínua. `min_ready=3` limita somente reserva simultânea, não quantidade de artigos, produtos ou blogs.
- Falta integrar credencial GitHub D1 de privilégio mínimo, teste de runner HTTP SELECT no D1 oficial, ensaio concorrente com dados sintéticos, validadores de links publicados em CMS, canário real DRAFT Blogger/WordPress e monitoramento.
- `ready_publication_authorized=false` é invariante. Cada LIVE continua com aprovação individual do proprietário por post+hash (gate C67).
- C77 testa com arquivo SQLite sintético e mocks, não com R2/Cloudflare reais; a rede do adaptador D1 só ocorrerá se um executor explicitamente autenticado for injetado em fase futura.

## Contrato de integração
- Código: `affiliate_hub_v31/reviewed_ready_promotion.py`, função `stage_reviewed_ready`.
- Pre-requisitos: `Catalog` da rota real, `UniversalD1ReadyState` com executor isolado, HTML+SEO confiáveis e manifesto assinado fora do motor de geração.
- Saídas seguras: `READY_RESERVED_FOR_DRAFT_REVIEW`, `READY_NOT_RESERVED` ou `LEASE_BUSY`; todas retornam 0 publicações LIVE; exceções bloqueiam por padrão.
- Testes: `tests/test_c77_reviewed_ready_promotion.py` (fontes sintéticas, documento de revisão sintético).

Não usar os testes para afirmar que existiu aprovação editorial de um artigo real ou que o V31 já gera READY em produção.
