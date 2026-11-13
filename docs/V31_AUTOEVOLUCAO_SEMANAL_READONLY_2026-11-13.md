# Proposta SAFE — auditoria semanal de autoevolucao V31 (13/11/2026)

## Escopo, estado e proveniencia

**Estado: PROPOSTA EM BRANCH ISOLADA. Nao ativado na main.**
Repositorio: `adelrib27/blogger-automation1`; main lida no inicio: `1a56a09fd2c4733fbc9655b1b1a0c70b87913609`.
Fonte do motor existente: `lab/v31-autoevolucao-safe-20261112`, commit imutavel
`867a7167b1d496090471cb15239084ccae63994c`.
Nao alteramos a branch LAB nem seus workflows automaticos.

A arquitetura de autoevolucao ja existe em `v31_master/autoevolution/` na branch LAB,
incluindo `engine.py`, `knowledge.py`, `offline.py`, `verify_candidate.py`,
`feedback.py`, testes e dois workflows de evidencias/candidatos. A implementacao atual
opera **offline, sem API paga**, por receitas deterministicas pre-revisadas.
Nao criar motor concorrente em `evolution/` sem consolidar o existente.

Evidencia observada em 13/11 (workflow terminado com success, nao prova E2E):
- observer: GitHub run `43435806063`;
- receitas offline: run `43435806170`.
Houve falhas em runs anteriores; sucesso pontual nao elimina os bloqueios de Shopee GraphQL 10000,
UX Blogger/CDP ou QA publico por blog.

## O que esta proposta adiciona

`.github/workflows/v31_autoevolucao_weekly_readonly.yml` e uma **auditoria complementar**:

1. Roda somente em `main`, no repositorio publico exato; manual ou toda segunda 12:37 UTC.
2. Faz checkout **por SHA fixo** do motor LAB verificado (nao acompanha codigo futuro automaticamente).
3. Executa `python -m unittest discover -s v31_master/tests -v` antes de coletar evidencias.
4. Reutiliza `v31_master/autoevolution/engine.py` para consultar **metadados** de Actions
   com `GITHUB_TOKEN` de leitura. Sem logs integrais ou segredos de Blogger/Shopee.
5. Gera relatorio JSON **apenas no filesystem efemero** do job.
6. Valida schema, repo, branch, seguranca e totais, e publica contagens no
   `GITHUB_STEP_SUMMARY` do run; NAO envia artifact, nao faz push/commit.
7. Se a regressao, a API do GitHub ou qualquer guarda falhar, o job falha fechado.
8. Nenhuma atualizacao de `main`, outro branch, blog, tema, pagina, secret ou workflow LIVE.

**Limitacao consciente:** esta auditoria semanal **nao grava memoria cumulativa no Git**.
A memoria e os resultados persistentes ja existentes continuam sendo alimentados pelos
workflows LAB ativados por eventos de push. O resumo semanal existe no historico de Actions
enquanto o run/log for retido. Persistencia semanal em LAB, alertas e promocao automatica
exigiriam um segundo contrato de escrita separado e revisao de seguranca.

## Gates antes de integrar a PR

- Comparar diff somente dos arquivos desta proposta contra a main atual (nao contra checkpoint antigo).
- Garantir `permissions.contents=read` e `permissions.actions=read`.
- Nenhum `contents: write`, `pull-requests: write`, secrets Shopee/Blogger ou POST/PUT.
- Verificar `if` de repo + branch + publico e SHA fixo.
- Executar auditoria estatica da sintaxe YAML e do escopo, sem disparar workflow.
- Conferir que os testes V31 na revisao fixada ainda passam no runner GitHub.
- Avaliar gasto de minutos, limites da API Github e politica de dados antes de merge.
- Obter aprovacao explicita para integrar `main`. **Nao usar auto-merge.**
- Depois de eventual merge: observar uma execucao real (manual/agenda), conferir
  `GITHUB_STEP_SUMMARY`, falhas e duracao; somente entao marcar agendamento validado.

## Riscos e rollback

| Risco | Mitigacao |
|---|---|
| Alteracao futura nao revisada no LAB | Checkout por commit SHA fixo; novo SHA requer PR |
| API GitHub retorna 403/429/timeout | Job falha; nao grava nem publica |
| Busca recente omite historico | Relatorio declara limite de 1.000 runs, sem alegar historico completo |
| Runner/repo privado gera custo | Job bloqueado se repo privado, `ubuntu-latest`, sem artifacts/cache |
| Execucao duplicada | `concurrency` do workflow sem cancelar execucao existente |
| Regressao nos testes V31 | Auditoria nao executa coleta ate regressoes aprovadas |
| Main contem workflows produtivos | Nenhuma alteracao em arquivos existentes; novo workflow somente read-only |

**Rollback futuro caso aprovado:** desabilitar apenas o workflow de auditoria semanal
pelas configuracoes do GitHub, sem alterar rotinas de blog, e reverter o commit da PR
depois de conferencia de estado e autorizacao. Nunca desligar workflows alheios por atacado.

## Relacao com outros problemas

- Shopee `productOfferV2` GraphQL `10000`: P0 ainda exige diagnostico SAFE separado.
- Blogger Local Runner: saude HTTP nao equivale a provisionamento E2E; nao executar cria/blog/theme.
- `resume-provision-new-blog-v31`: capacidade anunciada pelo Runner, ainda nao exposta no plugin.
- A auditoria semanal acompanha falhas de CI por **camada**, sem inferir causa-raiz.

## Criterio de sucesso desta etapa

Nesta branch: workflow e documentacao revisados, sem execucao nem escrita em producao.
PR em rascunho para `main`. Sem merge, o agendamento **NAO esta ativo**.
Uma execucao futura com status PASS prova apenas a auditoria de metadados, nao
autonomia de publicacao ou evolucao livre de IA.
