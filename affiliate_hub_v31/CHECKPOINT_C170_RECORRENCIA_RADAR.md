# C170 — recorrência editorial do Radar

Retomada `V31-C170-RADAR-RECORRENCIA`. Base C169 `9e3fb3e511d64710cc8ddb0c713729ca8c537dc4`.

A auditoria [45879847269](https://github.com/adelrib27/blogger-automation1/actions/runs/45879847269) confirmou `DAILY_CAP`, 2 jobs USED, zero READY e orçamento de busca esgotado em 26/11 UTC. Nenhuma nova entrega naquela janela. `V31_AUTODRAFT_ROLLOUT_SITE` aponta para Móveis para Cada Canto e esse destino já produz rascunhos agendados.

Preparar um horário próprio para um piloto explicitamente selecionado, pelo mesmo scheduler, sem substituir a rota existente. Ampliar perfis com SKU de catálogo e fonte do fabricante. Validar seleção, janelas D1, gates de revisão, teste de regressão e resultado real de `schedule`. LIVE continua fechado. Antes de qualquer rollback, conferir os recibos para preservar DRAFTs confirmados.

## Configuração e prova pendente

- Janela horária no minuto 42 pelo agendador universal. Ativação explícita com `V31_AUTODRAFT_PILOT_SITE=wordpress_radartechbr`. O alvo regular de Móveis para Cada Canto e o horário anterior ficam preservados. O evento piloto não aciona o job de LIVE.
- Foram cadastradas ofertas candidatas para o [Redragon M724](https://novo.redragon.com.br/produto/k1ng-1k) e o [Midea AI Ecomaster Frio de 18.000 BTU](https://www.midea.com.br/ar-condicionado-18000-btus-inverter-ai-ecomaster-frio-midea/p). O runtime ainda deve conferir oferta, variante, foto, campanha e evidência antes de permitir a entrega.
- O seletor ignora um SKU sem cache que já tenha tentativa histórica na mesma campanha. A reserva D1 continua atômica e limita a conversão. O escritor direto WordPress ignora destinos de categoria assinada na seleção automática.
- A comprovação de recorrência requer evento `schedule`, decisão D1 e, numa janela com oferta aprovada, recibo com ID/status/hash verificados por GET autenticado no WordPress. Registrar também o resultado de janela fechada. Para suspender a janela piloto, remover a variável exclusiva após conferir os recibos.
