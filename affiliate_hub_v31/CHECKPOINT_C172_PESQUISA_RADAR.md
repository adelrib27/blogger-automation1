# C172 — pesquisa do Radar sem cota diária interna

Retomada `V31-C172-PESQUISA-RADAR`. Base C171 `7fe7d80aa457434f3bd7ec539c645d28ad09fa9c`.

A auditoria [45895258709](https://github.com/adelrib27/blogger-automation1/actions/runs/45895258709) mostrou `RESEARCH_BUDGET` com saldo Firecrawl disponível e zero READY no Radar. Tornar a cota diária de pesquisa opcional e usar `null` no Radar. O D1 continua contabilizando tentativas e respeitando lease e HTTP 429. Testar a transição com o contador já esgotado, entregar um DRAFT real pelo workflow universal e conferir o WordPress. LIVE segue desativado.

## Aceite

A política sem cota é explícita por perfil. O teste de regressão precisa manter o histórico D1 e comprovar que a resposta HTTP 429 ainda impede novas chamadas durante o bloqueio. O teste real deve usar o agendador universal com alvo Radar e confirmar o ID e status DRAFT no WordPress. A execução manual comprova a entrega. A recorrência automática requer um evento schedule separado.

## Recibo real

- [Execução 45897356609](https://github.com/adelrib27/blogger-automation1/actions/runs/45897356609) via workflow_dispatch do agendador universal na main. Revisão, entrega e auditoria concluíram com sucesso; release foi ignorado.
- O contador SEARCH no D1 passou de 4 a 5 no mesmo dia UTC, sem reinicialização. O WordPress confirmou o status draft, categoria 20 e o título “Midea AI Ecomaster Frio 18.000 BTU: o que conferir antes de comprar” no post 404.
- O recibo do writer foi DRAFT_VERIFIED com SHA-256 7718165e8a6b73b1a738fc5eba2769da3e29852b63b9c5426a6aa0d1a5631bbf.
- A entrega de ponta a ponta está comprovada. Até a verificação das 18h23 de Brasília, a lista de eventos schedule ainda não mostrava disparo posterior à implantação do piloto. A checagem do disparo automático permanece pendente.
