# V31 C46 — Biblioteca universal, reclassificação contínua e pistas dos CSVs (18/11/2026)

**Código para retomar sem se desviar:** `V31-C46-203649-194370-10565REVIEW-HINTS-79PATHS-C45WEEKLY-20261118`.

## Missão original e não negociável

O V31 organiza continuamente os **dois CSVs Shopee** em uma biblioteca histórica UNIVERSAL, independente de nichos ou blogs previstos. Quando o proprietário pedir um blog Blogger/WordPress novo, com tema e quantidade informados naquele momento, a automação busca produtos pertinentes, só usa os aprovados, converte links na campanha REAL daquele site e prepara o conteúdo para o gerador/publicador correspondente. Não transferir links entre campanhas, inventar blog, comissão ou venda, nem transformar categorização Shopee em autorização de publicidade. Pinterest/Worker v1.0 e publicadores antigos não foram alterados nesta etapa.

## Estado R2 comprovado

- **203.649 produtos históricos** deduplicados, 29 raízes oficiais e hierarquia L1/L2/L3; índice textual FTS5 e sidecar universal com compartimento `sem_categoria_oficial`. Taxonomia independente de blogs.
- **C43** [run 44351103492](https://github.com/adelrib27/blogger-automation1/actions/runs/44351103492): 10 SKUs classificados após evidência dupla e restauro R2.
- **C44** [run 44352445875](https://github.com/adelrib27/blogger-automation1/actions/runs/44352445875): mais **584** SKUs classificados em 6 ciclos até 100, com snapshot e sidecar restaurados em cada ciclo; os **594** candidatos seguros da ampliação de móveis foram esgotados. **194.370** continuam em revisão. Sidecar final C44: **8.997 approved**, **282 legacy_source_blocked**, **194.370 review_required**; aprovado no catálogo e apto para publicidade são conceitos distintos. **0 links/0 posts gerados na curadoria**.
- Workflows e triggers temporários C44 removidos.

## C45 — execução recorrente automática de segurança

- [PR #64 MERGED](https://github.com/adelrib27/blogger-automation1/pull/64) incluiu `universal_maintenance.py` e `.github/workflows/v31_universal_safe_maintenance_weekly.yml`.
- Cron de **quarta 09:13 Recife** (12:13 UTC) roda independentemente dos blogs, após refresh dos feeds na terça. Mantém gates de título + faceta oficial revisada, origem, moderação, URLs e política, até **100 histórico REVIEW reversíveis por execução**. Não recebe segredos Shopee/Blogger/WordPress, não publica nem converte.
- Repara sidecar automaticamente se o catálogo avançou, contagem divergiu ou índice não existe. Se 0 mudanças, evita R2 writes; se etapa de índice falhar após catalog core write, a execução falha e o próximo ciclo tenta reparo sem duplicar reclassificação.
- [CI C45 44368868767](https://github.com/adelrib27/blogger-automation1/actions/runs/44368868767): **298 V31 +24 Casa +21 Oficina +crossblog PASS**.
- [Canário real R2 C45 44369302157](https://github.com/adelrib27/blogger-automation1/actions/runs/44369302157): **SUCCESS**, 194.370 pendentes, 0 novos candidatos cobertos pelas regras atuais, 0 writes catálogo, 0 writes sidecar, 0 mutações, 0 posts. Workflow/gatilho temporários removidos.
- **Primeiro disparo cron futuro ainda não observado**; não declarar cron comprovado em produção por antecipação.

## C46 — filas privadas para produtos sem categoria oficial

- [PR #65 MERGED](https://github.com/adelrib27/blogger-automation1/pull/65) inclui `unclassified_review_hints.py` e integração tanto no refresh dos dois CSVs como na reconstrução do índice universal C45.
- O léxico deriva **1.399 termos agregados** de dados dos feeds (25+ produtos, 8+ lojas por termo). Para SKUs em `NO_OFFICIAL_CATEGORY`, propõe caminhos L1/L2 **somente para revisão** quando título contém sinais múltiplos e há margem suficiente sobre categorias concorrentes. Títulos sensíveis, ambiguidade, política, conflito e fontes protegidas não são utilizados. A tabela privada `v31_unclassified_review_hints` tem `review_only=1`; nunca habilita conversão/post ou altera o catálogo comercial.
- [CI C46 44370341734](https://github.com/adelrib27/blogger-automation1/actions/runs/44370341734): **304 testes V31 +24 Casa +21 Oficina +crossblog PASS**.
- [**Real C46 no R2 44370697407**](https://github.com/adelrib27/blogger-automation1/actions/runs/44370697407): **88.239** SKUs sem categoria oficial analisados, **10.565** sugestões privadas por título/lexicon para **79** caminhos L1/L2; **2.434** ambíguos, **183** com títulos sensíveis/invalidos, **75.057** com evidência insuficiente, **77.674** sem pista suficientemente fundamentada. Sidecar separado salvo e restaurado, catálogo original intacto, **0 novas aprovações, 0 conversões, 0 posts**. Não contar 10.565 como produtos comercialmente aptos!
- Workflow/gatilho temporários C46 removidos.

## Fluxo de novos blogs: capacidade versus limite real

- `sites.d` e `site_request_queue` aceitam cadastro declarativo de blogs reais de qualquer tema solicitado no momento (sem pré-preparar blog), com `allowed_source_paths` ou nichos oficiais, `identifier` e `campaign` reais.
- Workflow de fila diário (**08:47 Recife**) planeja/converte até 3 links pela campanha real, grava envelope privado `REVIEW_REQUIRED` e não publica. `universal_draft_adapter` prepara draft Blogger/WordPress sob texto original e aprovação editorial, sem postar.
- [C40](https://github.com/adelrib27/blogger-automation1/actions/runs/44347429827) provou cache/link/handoff em Blogger já registrado. **Nunca afirmar que um blog FUTURO já foi criado/publicado:** para o primeiro novo site de verdade, o proprietário ainda precisa solicitar tema, plataforma, número de artigos e autorizar a identidade/campanha real; permissões OAuth/WordPress precisam estar conectadas.
- A falta de métricas comerciais reais não bloqueia nada disso; não inventar conversão/venda. Flags de publicação V31 continuam OFF, Pinterest separado.

**Próxima prioridade:** desenvolver consultas/relatórios auditáveis das 10.565 pistas privadas e verificação pós-restauro de contagem/segurança, ampliar cobertura dos 77.674 sem pista quando surgirem novos dados dos feeds, depois executar o primeiro novo blog REAL quando o proprietário indicar tema/plataforma/quantidade. Não pressionar usuário para ativar flags de publicação dos três WordPress como substituto da meta universal.
