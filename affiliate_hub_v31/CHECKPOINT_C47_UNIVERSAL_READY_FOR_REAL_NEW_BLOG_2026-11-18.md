# V31 C47 — Biblioteca universal autônoma operacional, aguardando pedido REAL de novo blog (18/11/2026)

**Código de continuação:** `V31-C47-203649-194370REVIEW-10565HINTS-79PATHS-C45C47CRONS-20261118`

## Missão
Não fixar nichos/mercadorias/blogs futuros. Dois CSVs entram no acervo R2 cumulativo e pesquisável; classificar por hierarquia oficial e sugestões de revisão; quando chegar um pedido REAL de novo Blogger/WordPress com tema e quantidade, descobrir produtos aprovados, converter com campanha do próprio blog, entregar pauta e rascunho ao editor/publicador autorizado. Não publicar produtos REVIEW, nem inventar receitas, campanhas, desempenho ou métricas.

## Dados reais, comprovados no GitHub Actions

- Catálogo R2: **203.649** produtos, 29 grupos raiz oficiais, FTS5, 1.399 termos extraídos dos feeds e 118 caminhos L1/L2 com suporte agregado; sidecar universal tem registro de TODO o acervo.
- C43 [44351103492](https://github.com/adelrib27/blogger-automation1/actions/runs/44351103492) 10 + C44 [44352445875](https://github.com/adelrib27/blogger-automation1/actions/runs/44352445875) 584 = **594 produtos históricos reclassificados** com evidência dupla, snapshots e índice restaurados; **194.370 REVIEW** ainda existentes. Sidecar: 8.997 aprovados e utilizáveis pela origem, 282 antigas aprovações bloqueadas pela origem, 194.370 em revisão. Não confundir `approved` bruto com publicável.
- [PR #64 C45](https://github.com/adelrib27/blogger-automation1/pull/64): rotina permanente semanal de reclassificação auditável (quarta ~09:13 Recife), **até 100 SKUs** com revisão anterior apenas `taxonomy_*`, título + faceta oficial compatíveis, política/origem seguras, R2 read-after-write, reconstrução automática do sidecar caso atrasado, zero writes se sem mudanças. [CI 44368868767](https://github.com/adelrib27/blogger-automation1/actions/runs/44368868767) **298 V31 + 24 Casa + 21 Oficina + crossblog PASS**. [C45 real 44369302157](https://github.com/adelrib27/blogger-automation1/actions/runs/44369302157) **SUCCESS, 0 candidatos novos, 0 writes, 0 posts, 0 links**.
- [PR #65 C46](https://github.com/adelrib27/blogger-automation1/pull/65): propostas privadas L1/L2 só para REVIEW de SKUs sem faceta; usa léxico agregado dos próprios feeds, exige vários sinais e margem contra ambiguidade. [R2 real 44370697407](https://github.com/adelrib27/blogger-automation1/actions/runs/44370697407): **88.239** analisados, **10.565** propostas em **79** caminhos L1/L2, **77.674** sem sugestão suficientemente fundamentada, **2.434 ambíguos** e **183 títulos sensíveis/inválidos**. 0 promoções, links ou publicações; sidecar salvo/restaurado. [CI 44370341734](https://github.com/adelrib27/blogger-automation1/actions/runs/44370341734): **304 V31 + regressões PASS**.
- [PR #66 C47](https://github.com/adelrib27/blogger-automation1/pull/66): verificação pós-restauro da quantidade e `review_only=1` das sugestões, relatório agregado privado de qualidade. [CI 44372184412](https://github.com/adelrib27/blogger-automation1/actions/runs/44372184412) **307 V31 + 24 Casa + 21 Oficina + crossblog PASS**. [R2 real C47 44372472666](https://github.com/adelrib27/blogger-automation1/actions/runs/44372472666): **10.565 hints confirmados no arquivo restaurado**, sobre 88.239 sem faceta e 77.674 pendentes sem pista. Lê somente o índice e mostra contagens agregadas por L1/L2, 0 writes, 0 posts. Principais revisões por volume: `home living/furniture` 1.288, `pets/pet food` 517, `spare parts.../external accessories for automobiles` 515, etc.; nenhum virou aprovado/publicável.
- **Removidos os workflows e triggers temporários** C44/C45/C46/C47 após respectivos PASS. Nenhuma reconfiguração das flags V31 LIVE/Pinterest.

## Jobs permanentes em main, independentes dos blogs

1. `v31_c17_catalog_refresh_safe.yml`: atualização cumulativa dos DOIS feeds, terça ~07:23 Recife, restaura FTS e sidecar; não cria links/posts.
2. `v31_universal_safe_maintenance_weekly.yml`: quarta ~09:13 Recife, reclassifica apenas casos de evidência dupla e repara sidecar quando necessário. Não recebe credenciais Shopee, Blogger, WordPress.
3. `v31_universal_review_quality_weekly.yml`: quinta ~09:31 Recife, lê R2 sidecar e informa grupos de REVIEW em agregados, 0 mutações/posts.
4. `v31_universal_request_queue_daily.yml`: diariamente ~08:47 Recife, só atua com `site_requests.d/<site_key>.json` real e habilitado, campanha real correspondente, no máximo **3 mutations Shopee globais**. Gera envelopes privados `REVIEW_REQUIRED` sem publicações.
5. `v31_universal_converter_on_demand.yml` e `v31_universal_handoff_safe.yml` permitem processamento sob solicitação real. Os crons futuros ainda **não tiveram seu primeiro evento programado observado** após as mudanças. Testes de canário não substituem observação de cron.

## Pendência externa real para prova LIVE em NOVO blog

O sistema já demonstra catálogo universal, busca por tema livre, campanha correta após registrar site real, conversão oficial R2, filas privadas e preparação de rascunhos Blogger/WordPress. Porém **nenhum blog futuro ainda não solicitado foi criado/publicado**: o proprietário deve especificar o **tema, plataforma Blogger/WordPress e quantidade de artigos**, permitir criar/conectar a identidade real e campanha de afiliado correspondente e aprovar o primeiro conteúdo original. Isto é dado de negócio/autorização, não deve ser inventado para declarar sistema pronto. C40 já validou link/handoff real para Blogger cadastrado, mas sem post LIVE.

Os **194.370** produtos em revisão permanecem catalogados e pesquisáveis no modo de revisão; só os itens com autorização verificável entram em conversão/publicação. Não transformar faltas de comissão/venda em bloqueio técnico.

**Decisão atual:** infraestrutura universal programada/validada, resta canário de primeiro blog novo LIVE com dados e autenticação reais. Não pedir ativação das flags dos três WordPress para substituir essa etapa.
