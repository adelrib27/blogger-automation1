# Checkpoint J.A.R.V.I.S. V31 — 13/11/2026

## Decisão vigente

Continuar somente sem gastos adicionais de API. Não reativar chamadas OpenAI ou outro modelo pago. A chave e as variáveis previamente cadastradas não são consumidas pelos workflows offline. Esta decisão substitui a configuração paga descrita nos checkpoints antigos.

## Implementação e validação

- Implementação offline: commit `83e3a7b2483f774714819fd0d49e781b437f23e7`.
- Primeira receita: `strict-affiliate-verification-v1`, exigindo `True` booleano para confirmação externa da origem afiliada. Preserva comissão positiva sem mínimo; não substitui autenticação do gateway.
- Primeiro ciclo: https://github.com/adelrib27/blogger-automation1/actions/runs/43322137584 — sucesso. Baseline de 182 testes, regressão nova reproduzida no original, suíte corrigida aprovada em sandbox sem rede.
- Branch candidata criada automaticamente: `lab/jarvis-candidate-3cc15c93768ff75312ad`.
- O GitHub bloqueou a abertura de PR pelo bot; o PR foi aberto pela integração e revisado antes da integração somente no LAB: https://github.com/adelrib27/blogger-automation1/pull/41 . Não alegar abertura automática de PR validada.
- Merge LAB: `b4b0cd67c64c31e6a3f72e0d15d5c995f2f0fd3b`.
- Ciclo após integração: https://github.com/adelrib27/blogger-automation1/actions/runs/43322420170 — sucesso; **185 testes aprovados**, `OFFLINE_NO_APPLICABLE_RECIPE`, `paid_api_calls: 0`, `production_writes: false`.
- A receita deixou de se aplicar ao código corrigido: nenhuma nova branch candidata foi publicada. Sandbox e publicação foram corretamente pulados nesse ciclo sem candidato.
- Feedback persistido: `experiments/43322420170-1.json`.
- Observador após integração: https://github.com/adelrib27/blogger-automation1/actions/runs/43322420220 — sucesso.

## Escopo e custos

O modo ativo observa execuções, acumula evidências e propõe mudanças apenas por receitas determinísticas revisadas. Não é retreinamento do ChatGPT nem geração livre de código por IA. Novas capacidades exigem novas receitas e testes revisados.

Os dois workflows usam runners padrão em repositório público, bloqueiam execução privada e não armazenam artifacts/caches. Não chamam modelos externos. Isso não altera faturamento de outros workflows ou serviços; artifacts históricos continuam sujeitos à retenção existente. O uso conversacional permanece sujeito às cotas do plano ChatGPT.

Nenhuma alteração desta implantação foi feita na main ou em blogs de produção. Não há cron global nem replicação em outros repositórios. Ciclos são acionados por pushes pertinentes no LAB ou disparo manual. A promoção para produção continua dependente de revisão e validação por destino.

## Retomada

Ler `AGENTS.md`, `README.md`, código atual e evidências recentes antes de agir. Preservar o modo sem API paga. Não solicitar nem expor secrets. Consultar resultados reais; não confundir classificação de falhas com diagnóstico de causa. Novos repositórios devem ter memória, configurações e testes próprios, sem copiar credenciais.
