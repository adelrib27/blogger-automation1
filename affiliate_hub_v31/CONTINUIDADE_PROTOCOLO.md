# Protocolo V31 de continuidade entre chats, tarefas e GitHub Actions

**Versão:** 1 · **Ativado a partir da C57** · **Autoridade:** apenas fatos conferidos e artefatos `main` verificáveis.

## Ponto único de entrada

1. [`/V31_CONTINUAR_AQUI.md`](../V31_CONTINUAR_AQUI.md) — visão humana de início, meio e fim.
2. [`CONTINUIDADE_ESTADO.json`](CONTINUIDADE_ESTADO.json) — estado curto, legível por máquina e atualizado **antes** de tarefas longas.
3. `checkpoint_detail` indicado pelo JSON — provas de implementação, PR, Actions, Blogger, R2 e decisões.
4. [Issue #54](https://github.com/adelrib27/blogger-automation1/issues/54) — backlog e decisões técnicas; conferir os itens antigos porque a issue conserva histórico.
5. README e código da `main`; só o que está **implantado e verificado** pode ser afirmado em produção.

**Não sobrescrever `CHECKPOINT_ATUAL.md` (rede Blogger legada de 02/11/2026)**. É outro escopo.

## Contrato de execução resumível (três momentos)

### 0 — PRÉVIA OBRIGATÓRIA antes das primeiras mutações

Salvar `active_work` em `CONTINUIDADE_ESTADO.json` com:

- fase exclusiva (p. ex. C57/C58), objetivo exato e resultados esperados;
- `continuity_status=EM_ANDAMENTO`;
- arquivos/branches/PRs envolvidos, ponto de partida `main` e evidências já verificadas;
- próximo passo **executável** e dependências que ainda faltam;
- `mutation_in_progress`, `remote_operation_in_progress`, `rollback_needed` como flags reais, nunca suposições;
- proibição de segredo, token, URL assinada, e-mail privado ou conteúdo sensível no checkpoint.

**Publicar commit dessa prévia no GitHub antes da tarefa longa**. Um resumo apenas na conversa não basta.

### 1 — DURANTE: checkpoints incrementais, não esperar o final

Após cada marco verificável, como commit/PR, CI, alteração no R2, conversão Shopee, edição Blogger/WordPress, ou bloqueio:

- atualizar o JSON com **`latest_verified_step`**, link/ID do resultado e `next_safe_step`;
- registrar no `checkpoint_detail` (arquivo Markdown) a trilha: premissa → ação → resultado observado → impacto em produção → pendência;
- marcar etapas explicitamente `FEITO`, `NÃO FEITO`, `EM TESTE` ou `FALHOU`;
- para operação com efeito remoto, guardar IDs/links públicos de verificação e verificar read-after-write;
- uma vez que uma mutação foi enviada, **nunca a repetir cegamente após interrupção**; consultar o destino primeiro.

A prévia enviada ao usuário deve conter fatos estáveis já comprovados, não somente “estou trabalhando”.

### 2 — ENCERRAMENTO: estado conclusivo, sem fingir completude

- `continuity_status=PRONTO_PARA_PROXIMA_ETAPA`, `BLOQUEADO` ou `EM_ANDAMENTO` se algo ficou incompleto;
- atualizar `last_checkpoint_phase` e `checkpoint_detail` para a fase de fato encerrada;
- separar melhorias aplicadas em `main` de mudanças apenas em branch/PR e testes que não chegaram a produção;
- conferir links e caminhos no GitHub, incluir últimas evidências CI reais;
- atualizar `V31_CONTINUAR_AQUI.md` para apontar a fase recente e a próxima ação;
- registrar se existe ajuste pendente no Runner Windows, Blogger, WP, R2 ou deploy e por quê.

Um chat pode expirar em qualquer momento; nesse caso, **o estado publicado antes da interrupção** permite retomar sem atribuir sucesso a ações não concluídas.

## Abertura de um novo chat no projeto

Roteiro curto que o assistente deve executar, não só prometer:

1. Abrir com o conector GitHub **a `main` atual**, não presumir que caminhos ou SHA antigos continuam válidos.
2. Ler `V31_CONTINUAR_AQUI.md`, depois o JSON, checkpoint apontado e Issue #54.
3. Se `active_work.status` estiver `EM_ANDAMENTO`, identificar a última mutação/commit/Action real, inspecionar antes de continuar ou reexecutar.
4. Para qualquer alegação mutável (contador R2, posts LIVE, estado cron, resultado de PR/deploy), confirmar na fonte adequada.
5. Respeitar a missão de biblioteca universal e a separação por campanha/SKU, os gates de produto e a ausência de autorização para publicação LIVE irrestrita.
6. Registrar novo `active_work` e salvar outra **prévia** antes das próximas alterações.

## Automatização de detecção e limites

O job `.github/workflows/v31_continuity_guard.yml` validará a coerência mínima do índice/JSON no push da `main` e pode exibir o resumo do estado na aba Actions. Isso é um **alarme documental**, não ferramenta que conhece o estado da sessão do ChatGPT ou consulta R2/Blogger automaticamente. O conteúdo factual do JSON deve continuar sendo atualizado em cada execução e conferido em suas fontes. Sem abrir os arquivos em um novo chat, a continuidade NÃO é garantida pelo produto.

O verificador não deve escrever no catálogo, converter links, publicar artigos, editar o Runner, alterar variáveis do GitHub ou expor segredos.

## Regras de segurança e escopo

- Nunca revelar segredos, chaves, cookies, URLs privadas de campanha, conteúdo confidencial de env/outputs.
- Preservar os dois CSVs e o histórico do R2. Produtos `REVIEW` e pistas de taxonomia não podem virar publicidade automaticamente.
- Um novo site exige ID e campanha reais; não misturar links de diferentes campanhas, nem imagens de produtos diferentes.
- `isDraft=True` nos jobs Blogger V31 e `status=draft` no escritor WordPress V31. Desde C61, `articles:null` autoriza rascunhos contínuos SEM teto total, mas nunca mais de um por execução; pedidos com total numérico exigem ampliação autorizada quando esgotados. LIVE exige gate e autorização separados.
- Publicação LIVE apenas com autorização explícita e controle de qualidade.
- Citar evidências (PR, run, post) **somente quando realmente vistas**.
- Mudanças de tema do Blogger Local Runner ficam para quando o proprietário retomar esse assunto.
