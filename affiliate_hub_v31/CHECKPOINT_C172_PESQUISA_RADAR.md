# C172 — pesquisa do Radar sem cota diária interna

Retomada `V31-C172-PESQUISA-RADAR`. Base C171 `7fe7d80aa457434f3bd7ec539c645d28ad09fa9c`.

A auditoria [45895258709](https://github.com/adelrib27/blogger-automation1/actions/runs/45895258709) mostrou `RESEARCH_BUDGET` com saldo Firecrawl disponível e zero READY no Radar. Tornar a cota diária de pesquisa opcional e usar `null` no Radar. O D1 continua contabilizando tentativas e respeitando lease e HTTP 429. Testar a transição com o contador já esgotado, entregar um DRAFT real pelo workflow universal e conferir o WordPress. LIVE segue desativado.
