# J.A.R.V.I.S. V31 — evolução por evidências, LAB v2

## Estado e limites

O observador, a memória de tentativas e o registro de resultados são automáticos por push no LAB.
O pipeline de candidatos possui geração por API, teste isolado e publicação de PR rascunho
**para o LAB**, sem merge automático. Não é retreinamento do ChatGPT nem garantia de qualidade E2E.
Nenhum blog, tema, credencial comercial ou workflow de produção é alterado por este pacote.

A geração real por IA fica bloqueada até configurar **neste repositório**:

- Secret exclusivo `AUTOEVOLUTION_API_KEY` (não reutilizar chaves de blogs).
- Variable `AUTOEVOLUTION_MODEL`: modelo compatível com Chat Completions, JSON mode e
  `max_completion_tokens`, na API OpenAI usada pelo adaptador `propose.py`.
- Variable `AUTOEVOLUTION_ENABLED=true` para habilitar a chamada paga, no máximo uma por ciclo.
- Permissão do repositório para Actions criar PRs. Sem ela, o candidato validado permanece
  na branch e no artifact, com o bloqueio de PR identificado. Não conceder permissão de autoaprovação.

Não há modelo padrão, fallback para outra conta nem teste pago silencioso. A integração HTTP
é testada por mocks; uma execução real depende dessas configurações. Outros provedores requerem
um adaptador explicitamente validado antes de configurar a chave. Não colocar secrets em arquivos.

## Pipeline

1. Observer executa toda a suíte V31, coleta até 10 páginas de 100 metadados do próprio repo.
2. Memória usa `(run_id, run_attempt)`. Reexecução legítima não é adulteração de histórico.
   Importação v1 preserva tentativa desconhecida como `0`, sem inventar a tentativa original.
   Totais por execução consideram a última tentativa observada; falhas anteriores são preservadas.
3. Job separado revalida os artifacts e grava apenas relatório e estado no LAB. Nunca force-push.
   Conflito concorrente mantém evidência no artifact e bloqueia a gravação, sem sobrescrever.
4. Proposer lê fontes permitidas, métricas e resultados anteriores. Pode responder sem alteração.
   Contexto já tentado não gera repetidamente o mesmo experimento nos 20 resultados recentes.
5. Validador exige SHA base, hash do conteúdo original, alteração pequena e um novo teste.
   Não pode modificar workflows, AGENTS, guardas do JARVIS, testes existentes, temas ou secrets.
6. Runner exporta o commit confiável sem `.git`, sem credenciais, em container sem rede,
   filesystem read-only, usuário sem privilégios e limites de tempo, memória, CPU e processos.
   Exige baseline aprovada, regressão por **asserção** no original (erro de importação não vale)
   e suíte inteira aprovada no candidato. Não importa código gerado fora do container.
7. Publisher em outro job revalida candidato e SHA256 da prova, cria branch determinística e PR
   rascunho para LAB. Não executa fonte gerada; nunca mergeia. Retry não sobrescreve branch existente.
8. Feedback persiste resultados sanitizados em `experiments/<run>-<attempt>.json` no LAB.
   A IA recebe esses resultados no próximo ciclo; não recebem logs brutos nem saída do modelo.

O smoke test é **sintético**, verifica isolamento e o trajeto red/green, não é uma melhoria de
produto e nunca é publicado como candidato real. PASS de testes não prova estoque, conversões,
qualidade visual ou causa raiz de uma falha de API. PR precisa de revisão técnica e QA pertinente.

## Autonomia e proteção

- Fontes candidatas iniciais: `store_stock_commission_safe.py` e `shopee_r2_safe.py`.
- Teste novo: `v31_master/tests/test_autoevolution_candidate_<sha-base-12>.py`.
  O nome muda por revisão base; testes já integrados nunca podem ser sobrescritos.
- Os controles são executados na revisão confiável; a IA não pode editar esses controles.
- O modelo recebe metadados de falhas, não diagnóstico de causa. Deve justificar a correção
  pelo código e reproduzir a regressão. A avaliação semântica continua necessária na revisão.
- Testes de candidatos são código não confiável, isolado. Docker não garante ausência de
  vulnerabilidades de kernel; usar runners hospedados efêmeros, nunca um runner com secrets locais.
- Os arquivos AGENTS orientam os agentes que os leem; não obrigam chats externos automaticamente.
- Não habilitar `pull_request_target` para executar código candidato com credenciais.

## Continuidade e operação

A leitura é uma janela recente **limitada**, não todo o histórico. O relatório expõe o limite e
se ele foi atingido; intervalos longos podem deixar lacunas e requerem coleta de backfill revisada.
A memória admite 50.000 observações, alerta aos 80% e bloqueia ao atingir o teto. Não descarta
histórico silenciosamente; arquivamento verificável deve preceder nova expansão de capacidade.
Relatórios no git são permanentes; artifacts de execução têm retenção de 30 dias.

O LAB roda por **push**, e por `workflow_dispatch` onde disponível. Não há cron global ativo.
GitHub exige o workflow na branch padrão para disponibilizar dispatch/schedule normalmente.
A habilitação contínua por relógio exige implantar um dispatcher revisado na branch padrão;
não mover os workflows produtivos nem publicar a branch LAB inteira em `main`.

Se não houver chave/modelo/enable, o workflow registra `BLOCKED_MODEL_CONFIGURATION`, executa
smoke test e não chama a API. Isso é infraestrutura validada, **não IA de código ativa**.

## Promoção e recuperação

Antes de integrar: comparar base atual, confirmar regressões, revisar diffs e validar o destino
exato. PR candidato é para LAB, não para `main`. Não misturar experimentos com instalação da
engenharia em outro blog. Integrar em produção só a mudança revisada, com snapshot e readback
quando houver alteração externa. Reverter commit não desfaz publicação em Blogger/WordPress.
Recuperação de efeitos externos exige backup e procedimento próprio do destino.

## Replicação por blog

Copiar somente código da engenharia, testes e workflows; **não copiar** state.json, relatórios,
experimentos, tokens ou configurações comerciais. Alterar `ALLOWED_REPO`, `ALLOWED_BRANCH`,
allowlist de fontes, guards e branch nos dois workflows. Criar estado vazio com o schema v2.
Executar testes e smoke no repo novo, depois configurar chave/modelo próprios. Não alegar cota
independente só por copiar a mesma chave em outro repositório. Revisar a política de publicação
por destino antes de promover qualquer candidato.

## Verificação local

`python -m unittest discover -s v31_master/tests -v`

Com Docker e um commit contendo o pacote:
`python v31_master/autoevolution/sandbox_smoke.py`

O workflow repete o smoke no GitHub Actions; os testes normais são offline e não usam secrets.

Referências de implementação:
- https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax
- https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow
- https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create
