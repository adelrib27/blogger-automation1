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
