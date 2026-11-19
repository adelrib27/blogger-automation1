# V31 C61 — teste real e remoção de teto total de artigos (19/11/2026)

**Estado inicial: EM_ANDAMENTO.** Prévia durável antes de alterar geração ou publicar qualquer coisa.

## Pedido explícito do proprietário

- Realizar um teste, preferencialmente ponta a ponta com um **novo RASCUNHO** no Blogger piloto e/ou WordPress real, sem transformar o teste em publicação LIVE indiscriminada.
- **Eliminar a limitação de apenas três artigos** no piloto e tornar a capacidade de artigos contínuos disponível a qualquer blog Blogger/WordPress registrado, sem trocar uma barreira de 3 por uma barreira de 24.
- Manter controle de frequência (por execução), anti-duplicação, campanha real e fotos verdadeiras, só produtos aprovados, quality gates e postagem LIVE separada.

## Observações antes das mutações

- `main` consultada no início: HEAD `97ae717f625458cf518559740b710cbff1ef9d69` (Casa editorial automático atualizou dados).
- Blogger conectado Móveis para Cada Canto ID `1439741542627895062`: **3 LIVE, 0 DRAFT**, às 13:27 UTC de 19/11/2026; pedido atual tem `articles=3` e bloqueia novos rascunhos.
- Workflows WP agendados recentes: Casa `44451960384` SUCCESS e Oficina `44444741047` SUCCESS; Radar `44447410967` FAILURE (causa ainda não concluída). Não confundir execução agendada com artigo publicado.
- C60 PR #79 e canário real WP em PREVIEW #44412775615 PASS; nenhum POST draft WP confirmado até aqui.

## Implementação alvo

1. Estender schema `site_requests.d` com `articles:null` = **sem limite total**, preservando números finitos para pedidos que os desejem. O valor 24 continuará apenas como tamanho de lote de busca R2, **não quota total**.
2. Ajustar Blogger C55, WordPress C60 e fila de cache para interpretar `null` sem inventar temas ou aprovar SKUs pendentes; atualizar pedido real Móveis para modo contínuo e regressões.
3. CI e testes reais em modo seguro. Testar um novo rascunho somente se houver SKU aprovado com imagem e link exato em cache, conteúdo original de qualidade e credenciais válidas. Caso contrário registrar bloqueio real, sem artigo de enchimento.
4. Confirmar Blogger/WordPress read-after-write se houver POST. Não criar duplicatas por retomada.
5. Concluir checkpoint, índice e JSON depois das evidências, com distinção entre código, cron, rascunho e LIVE.

**Restrições:** nunca divulgar credenciais, criar LIVE automático, alterar Runner/tema, Worker v1.0 ou Pins. Nem todos os produtos em REVIEW são publicáveis.

## Marcos
- **FEITO:** prévia C61 gravada com pedido e estado inicial.
- **PENDENTE:** commits de código, CI, prova do teste real, encerramento.


## Marcos adicionais — evidência conectada

- **FEITO:** [PR #81](https://github.com/adelrib27/blogger-automation1/pull/81) MERGED commit `ede7a41001c40840f80900112d33ce6f43f7f5c6`: `articles:null` para Blogger e WordPress; piloto mudou de 3 para contínuo, mantendo modo DRAFT, limite por ciclo e anti-repetição.
- **FEITO:** [CI C61 #44534635387](https://github.com/adelrib27/blogger-automation1/actions/runs/44534635387) SUCCESS, testes regressivos.
- **FEITO:** [C61 Blogger PREVIEW real #44534753873](https://github.com/adelrib27/blogger-automation1/actions/runs/44534753873) PASS de execução, status `NO_VERIFIED_CAMPAIGN_PRODUCT_YET` (3 LIVE, nenhum novo SKU cacheado), 0 posts.
- **FEITO:** [C61 fila R2 preview #44535072335](https://github.com/adelrib27/blogger-automation1/actions/runs/44535072335): 1 candidato de conversão, 2 ofertas cacheadas já existentes, 0 mutações.
- **FEITO:** [C61 conversão REAL controlada #44535276120](https://github.com/adelrib27/blogger-automation1/actions/runs/44535276120) SUCCESS: **1 chamada Shopee, 1 link convertido, R2 salvo e read-after-write verificado**, 0 publicações, 12 itens ainda pendentes de curadoria.
- **PRÓXIMA MUTACÃO REMOTA**: disparar canário no Blogger piloto com `--execute-draft`, APENAS `isDraft=True`, fonte R2; **confirmar no Blogger conectado read-after-write** antes de considerar novo teste, nunca repetir POST cegamente.


## C61 canário DRAFT real — achado de qualidade (necessita patch)

- [Workflow C61 #44535723037](https://github.com/adelrib27/blogger-automation1/actions/runs/44535723037) **SUCCESS**: `DRAFT_CREATED`, `draft_creation_calls=1`, `publication_calls=0`, imagem+CTA, campanha correta, após 1 conversão real.
- Blogger API read-after-write: rascunho ID `3612281866616913629`, título `Guia de compra: Guarda Roupa Casal 6 Portas 2 Gavetas Porto Preto com Escrivaninha`, **3 LIVE + 1 DRAFT**. HTML conferido: imagem/URL Shopee/aviso/CTA presentes.
- **FALHA parcial de qualidade detectada:** `internal_links_from_real_posts=false`; rascunho contém **0 links internos**. Não chamar E2E comercial completo até corrigir. Possível origem: `_list_posts` Blogger não atribui `status=live` aos posts recuperados pela listagem com filtro `LIVE` quando a API omite a propriedade em cada item.
- **PRÓXIMA AÇÃO:** corrigir normalização do status no adaptador sem confundir draft com live; regressão fakes, PR+CI, corrigir **o mesmo rascunho** (não criar outro), confirmar dois links internos e status DRAFT via API.


## Encerramento C61 — sucesso comprovado, 19/11/2026

**Status: PRONTO_PARA_PROXIMA_ETAPA — geração Blogger de rascunho real comprovada, sem teto total e com os 2 links internos reparados.**

- [PR #81 MERGED](https://github.com/adelrib27/blogger-automation1/pull/81), `articles:null` significa **sem limite total** para pedidos de Blogger/WordPress, sem liberar LIVE; finite 1-24 continua opcional; 24 ofertas é só lote de busca. Novo pedido real piloto salvo em `site_requests.d/blogger_moveis_para_cada_canto.json` com `null`.
- [CI C61 #44534635387](https://github.com/adelrib27/blogger-automation1/actions/runs/44534635387): PASS da implementação de quota contínua.
- [Blogger real #44534753873](https://github.com/adelrib27/blogger-automation1/actions/runs/44534753873): sem 4º SKU em cache, falha **segura**, sem novo artigo. [Fila preview #44535072335](https://github.com/adelrib27/blogger-automation1/actions/runs/44535072335): 1 candidato. [Conversão #44535276120](https://github.com/adelrib27/blogger-automation1/actions/runs/44535276120): 1 oferta aprovada convertida na campanha exata, R2 persistido+verificado, 0 posts.
- [Blogger real DRAFT #44535723037](https://github.com/adelrib27/blogger-automation1/actions/runs/44535723037): 1 novo rascunho Google API `isDraft=True`, `publication_calls=0`; conferido diretamente no Blogger ID `1439741542627895062`: rascunho ID `3612281866616913629`, título `Guia de compra: Guarda Roupa Casal 6 Portas 2 Gavetas Porto Preto com Escrivaninha`. O PDF/HTML não foi divulgado, nenhuma publicação LIVE.
- Achado no teste: 0 links internos por `status` ausente nos itens da listagem Blogger mesmo com filtro `LIVE`. [PR #82 MERGED](https://github.com/adelrib27/blogger-automation1/pull/82) normaliza status pelo filtro autorizado, rejeita contradições e adiciona regressão. [CI #44536428588](https://github.com/adelrib27/blogger-automation1/actions/runs/44536428588) **372 V31 +24 Casa +21 Oficina+crossblog PASS**.
- O **MESMO rascunho** foi atualizado pela conexão Blogger V2, nunca duplicado. Read-after-write verificado: HTML possui **foto HTTPS do SKU, link afiliado da Shopee, CTA, aviso comercial e exatamente dois links internos** para posts publicados do próprio blog; status continua `draft`. Leitura final do Blogger: **3 LIVE + 1 DRAFT**.
- Workflow temporário C61 e trigger removidos da `main` após os testes, mantendo o workflow diário permanente `v31_universal_blogger_autodraft_daily.yml` no projeto.
- **Não comprovado:** execução de cron diário C55 posterior a esta mudança, primeiro POST autenticado de DRAFT pelo writer **WordPress** C60 (precisa de pedido/site/credenciais reais no GitHub), nova publicação LIVE (não autorizada). Radar Tech BR teve [cron 44447410967](https://github.com/adelrib27/blogger-automation1/actions/runs/44447410967) FAILURE na etapa de confirmar publicação; não ignorar nem remover quality gates. Casa e Oficina crons recentes passaram, mas sucesso não é confirmação de novo post.

### Próximo passo técnico
1. Verificar o próximo cron real Blogger após `articles:null`: sem criar rascunhos em excesso, sem repetir SKU, no máximo 1 por execução; se não houver novo link convertido, terminar com status seguro.
2. Conferir disponibilidade do cache afiliado para geração contínua e funcionamento da fila sem ultrapassar orçamento diário de conversão.
3. Fazer primeiro teste autenticado WordPress C60 quando houver credenciais específicas daquele site e pedido real (ou se o proprietário nomear um destino seguro), sempre DRAFT; nunca improvisar token.
4. Investigar falha recorrente de confirmação do workflow Radar em seu próprio escopo, sem publicar por fora de seus gates.
5. Conservar biblioteca dos dois CSVs e curadoria REVIEWS; Runner/tema permanece adiado.

**Sem segredo em checkpoints. Sem rascunho extra na finalização.**
