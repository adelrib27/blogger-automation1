# C171 — cota diária opcional de DRAFT

Retomada `V31-C171-COTA-DRAFT-OPCIONAL`. Base C170 `3c884688af87e3bd3ad748afa5a8c2ccb0c7164a`.

A auditoria C169 mostrou que dois DRAFTs já consumidos impediam novos testes do Radar durante o mesmo dia. Remover a cota editorial arbitrária do Radar no agendador, no verificador e na reserva atômica do D1. Intervalo do piloto, deduplicação, evidência, assinatura, orçamento externo e LIVE conservam seus contratos. Outros destinos mantêm os limites configurados. Verificar com regressão, CI e auditoria real da janela.

## Configuração e critérios de aceite

- `max_drafts_per_day: null` desativa o teto apenas no perfil Radar. O agendador, a revisão e o UPDATE atômico de READY para USED usam o mesmo significado. Valores numéricos continuam funcionando nos demais perfis.
- Verificar no mesmo UTC que jobs USED anteriores não bloqueiam a entrega de um READY novo e que intervalo, lease, validade da evidência e replay idempotente continuam exigidos.
- A auditoria de capacidade deve mostrar a decisão real da janela. Se faltar evidência ou orçamento de pesquisa, registrar essa causa separadamente. LIVE continua desativado.
