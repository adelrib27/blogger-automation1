# Checkpoint J.A.R.V.I.S. V31 LAB v2 — 12/11/2026

## Estado verificado

- Repositório: adelrib27/blogger-automation1.
- Branch exclusiva: lab/v31-autoevolucao-safe-20261112.
- Implementação: 540a3b08148f77ee833650fa45582e0eda5a4b1d.
- Base anterior: cdbe7bba122ae3130cdc25b5bd410f492bf387fc.
- Main observada antes da alteração: 2286726c6353fc2bfc454fd8b54bd7207cd36aec; não foi modificada por esta implementação.
- 142 testes da base passaram antes das alterações. Suíte ampliada: 166 testes aprovados localmente e no Actions.

## Evidências reais

- Observer e persistência: https://github.com/adelrib27/blogger-automation1/actions/runs/43239086965 — jobs observe e persist aprovados.
- Candidatos e smoke: https://github.com/adelrib27/blogger-automation1/actions/runs/43239084969 — smoke de sandbox aprovado; registro do resultado aprovado.
- Memória após o ciclo: schema v2; 992 execuções distintas; 1.027 observações incluindo tentativas desconhecidas preservadas da v1.
- O total maior decorre da coleta paginada, não de falhas novas causadas por esta revisão. Camadas de falha continuam sendo classificação, não diagnóstico de causa raiz.
- Feedback persistido: experiments/43239084969-1.json.
- Estado real da geração IA: BLOCKED_MODEL_CONFIGURATION. Verify/publish de candidato real foram SKIPPED; não declarar candidato real gerado ou PR de IA validado E2E.

## Correções e extensão

1. Deduplicação por run_id e run_attempt, preservação de tentativas e migração v1 sem inventar tentativa histórica.
2. Janela paginada de até 1.000 execuções; cobertura limitada explicitada.
3. Memória até 50.000 observações com alerta a 80%; não há descarte silencioso.
4. Observação e persistência separadas, validação de artifacts, idempotência e push sem force.
5. Candidato limitado a duas fontes permitidas e um teste novo por revisão. SHA base e hashes do original obrigatórios.
6. Baseline, teste de regressão falhando por asserção e suíte do candidato passando em containers sem rede, tokens ou .git.
7. Publisher separado cria branch determinística e PR rascunho para LAB, sem executar o candidato e sem merge.
8. Resultados sanitizados persistidos e lidos no próximo experimento; evita repetir contexto já tentado nos 20 resultados recentes.
9. AGENTS.md e README atualizados para continuidade e replicação isolada.

## O que falta para ativação completa

- Configurar secret EXCLUSIVO AUTOEVOLUTION_API_KEY e variável AUTOEVOLUTION_MODEL, com modelo compatível com o adaptador OpenAI Chat Completions instalado.
- Configurar AUTOEVOLUTION_ENABLED=true para autorizar a chamada paga. Nenhuma chave dos blogs foi reutilizada.
- Confirmar permissão de Actions para criar PRs; fallback mantém branch/artifact se o GitHub bloquear a criação do PR.
- Realizar uma execução com o provedor real e avaliar o candidato resultante. O smoke já aprovado é sintético, não uma melhoria comercial.
- Não há cron global nem distribuição aos demais repositórios ativados. O LAB executa por push; habilitação por relógio exige dispatcher revisado na branch padrão.
- Promoção funcional exige revisão, regressões e QA por destino; passar testes não comprova qualidade visual, estoque, conversão ou efeito externo.

## Retomada

Ler AGENTS.md, README.md, este checkpoint, state.json e experiments/ antes de alterar. Consultar novamente os SHAs atuais. Não substituir a base por versões anteriores nem copiar credenciais/estado para outro blog. Não integrar a branch LAB inteira em main: ela contém histórico experimental de outras etapas. Promover somente alterações específicas revisadas.
