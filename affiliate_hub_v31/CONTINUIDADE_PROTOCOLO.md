# Contrato de continuidade operacional V31

**Autoridade documental:** [SYSTEM_MASTER.md](../SYSTEM_MASTER.md). O arquivo `CONTINUIDADE_ESTADO.json` registra a atividade atual e os próximos passos. O código da `main` e os serviços autenticados confirmam fatos mutáveis.

1. Antes de qualquer tarefa longa, conferir GitHub, Actions, CMS e filas relevantes. Registrar a atividade no JSON sem segredos nem alegações não comprovadas.
2. Trabalhar em branch isolada; executar verificações offline e CI; distinguir `PASS` de teste, `SUCCESS` do job, `DRAFT_VERIFIED` e publicação LIVE.
3. Persistir cada resultado verificável com commit, execução ou ID remoto e definir o próximo passo seguro.
4. Antes de repetir operações que possam ter sido enviadas, realizar GET/SELECT e reconciliar estado remoto para impedir duplicação.
5. Manter os bloqueios de blog, isolamento por campanha, orçamento por serviço, limites por site e política `activation=pending_policy_approval`.
6. Após a entrega, conferir a `main` e atualizar `CONTINUIDADE_ESTADO.json` e o índice `V31_CONTINUAR_AQUI.md`. Mudanças nas regras ou na arquitetura atualizam `SYSTEM_MASTER.md`.

**Segurança:** nenhuma atualização documental autoriza escrita em Shopee, Blogger, WordPress, R2 ou D1. O documento mestre é a entrada principal; este protocolo e o JSON são controles operacionais complementares, não fontes arquiteturais concorrentes.
