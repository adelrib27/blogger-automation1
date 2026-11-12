# J.A.R.V.I.S. V31 — modo OFFLINE, sem API paga

**Decisão do responsável em 12/11/2026:** continuar apenas sem gastos adicionais de API.
O fluxo ativo usa receitas determinísticas revisadas, testes, memória e GitHub. Não chama
OpenAI, não usa modelos externos e não precisa recarregar créditos. Não é uma IA aprendendo
a gerar código livremente, nem retreinamento do ChatGPT.

## O que funciona

1. Observer consulta metadados de Actions do próprio repo e mantém memória por execução/tentativa.
2. `offline.py` verifica receitas de manutenção previamente revisadas. Uma receita só pode
   alterar o padrão exato para o qual foi escrita. Implementação desconhecida vira no-op.
3. Candidato inclui SHA base, hash do conteúdo original e teste de regressão novo.
4. Sandbox sem rede, secrets ou `.git` exige baseline aprovada, falha por asserção no original
   e suíte inteira aprovada após a mudança.
5. Publisher em outro job revalida hashes e cria branch/PR para LAB. Nunca mergeia em main.
6. Feedback fica no git e evita repetir candidato já publicado para a mesma receita/fonte.
7. Se não houver receita aplicável, registra isso honestamente e não inventa melhoria.

Receita inicial: `strict-affiliate-verification-v1` exige `True` booleano como confirmação
externa de origem afiliada. Strings como `"false"`, números e coleções deixam de servir como
confirmação. Comissão positiva verificável continua aceita sem percentual mínimo.
Esse flag não substitui autenticação real: o gateway continua responsável pela origem.

## Custos e limites

- Repositório verificado como público: `adelrib27/blogger-automation1`.
- Jobs usam somente `ubuntu-latest`, runner padrão gratuito para repositórios públicos.
- O job inicial e o registro de resultados bloqueiam execução se o repo virar privado.
- Estes dois workflows não usam upload/download de artifacts, caches nem modelos externos.
- Pacotes pequenos passam por job outputs; estado e resultados ficam no git. Logs e summaries
  não consomem armazenamento de artifacts, conforme documentação GitHub.
- Os artifacts antigos de execuções anteriores permanecem sujeitos à retenção já definida.
  Esta mudança não altera faturamento de outros projetos, workflows ou serviços da conta.
- O trabalho conversacional continua sujeito às cotas do plano ChatGPT existente.
- Não há scheduler global nem polling de IA ativo: eventos de push no LAB iniciam os ciclos.

Referência: https://docs.github.com/en/billing/concepts/product-billing/github-actions

## Proteções

Os candidatos só podem alterar `store_stock_commission_safe.py`, `shopee_r2_safe.py` e um
novo teste `test_autoevolution_candidate_<sha-base-12>.py`. Não podem alterar seus próprios
controles, workflows, testes existentes, credenciais, temas ou blogs. O publisher aceita
somente a procedência `DETERMINISTIC_REVIEWED_RECIPE` neste modo.

O observador tem job de testes read-only separado do job de persistência. A persistência
usa a revisão atual do LAB somente se todo o código for igual ao que foi testado; mudanças
concorrentes de código bloqueiam o ciclo. Mudanças apenas de evidências podem ser incorporadas.
Tokens GitHub são usados somente para leitura/escrita do repo autorizado; não há token de
serviço comercial nos jobs. Push sem force nunca sobrescreve trabalho concorrente.

`propose.py` é código histórico da opção paga, **fora dos workflows ativos**. As variáveis
AUTOEVOLUTION_ENABLED/MODEL e o secret antes cadastrados não ativam esse modo offline.
Reativação paga requer nova decisão explícita e alteração revisada do workflow.

## Aprendizado e continuidade

A memória mantém tentativas anteriores e a última conclusão de cada execução. A janela
consultada é de até 1.000 execuções, não todo o histórico; pode haver lacunas entre ciclos
muito distantes. Estado tem limite de 50.000 observações com alerta a 80%, sem descarte
silencioso. O arquivo de resultados identifica receita, contexto e gates executados.

Novas capacidades exigem adicionar receitas revisadas e seus testes. Não criar consertos
aleatórios a partir do nome de um workflow que falhou. PASS não comprova estoque, conversões,
qualidade visual ou efeitos em Blogger/WordPress; promoção exige QA pertinente por destino.

## Replicar em outro blog

Copiar engenharia e testes, não credenciais nem memória de outro blog. Atualizar allowlist
de repositório/branch/fontes e guards dos workflows. Iniciar com estado vazio e testes próprios.
Para repositório privado, este perfil não executa: avaliar alternativa local antes de ativar
qualquer serviço que possa ser cobrado. Não tornar outro repositório público automaticamente.

## Verificar localmente

`python -m unittest discover -s v31_master/tests -v`

`python v31_master/autoevolution/offline.py`

Com Docker e um commit contendo o pacote:
`python v31_master/autoevolution/verify_candidate.py`

Nunca executar o conteúdo de um candidato fora do sandbox. Nenhum comando dessas verificações
chama modelos ou utiliza a chave OpenAI. Resultados sintéticos permanecem identificados como
sintéticos e não devem ser publicados como melhorias reais.
