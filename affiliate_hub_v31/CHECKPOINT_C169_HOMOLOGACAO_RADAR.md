# C169 — recibo de homologação Radar Tech BR

26/11/2026. Retomada `V31-C169-RADAR-HOMOLOGACAO`. Base `dc985f08a1ca95a203217b70482851ae95a4d32d`. Acompanhar [execução C168](https://github.com/adelrib27/blogger-automation1/actions/runs/45879376367), validar GET autenticado do segundo artigo e conciliar jobs D1 e orçamento. A prova de cadência deve registrar a decisão real sem produzir novo DRAFT fora da cota. LIVE OFF.

## Entregas com confirmação externa

| Rascunho Radar | Taxonomia CMS | Oferta | SHA-256 do HTML | Prova |
| --- | --- | --- | --- | --- |
| #401 Soundcore Select 4 Go | Tecnologia 3 | shopee:1051446617:50211608450 | 273416baeb45c96d8d243e582c251bc44738d049e5f696da32ce8dd95a11acc8 | [C164](https://github.com/adelrib27/blogger-automation1/actions/runs/45877249628) |
| #403 Samsung WindFree AI Pro 12.000 BTU | Ar-condicionado 20, parent 3 | shopee:1009975506:47114871036 | ad7bfe2896cc0ed888474286c80a1ecebf8dbc99881515c5f3cfc99a32c80493 | [C168](https://github.com/adelrib27/blogger-automation1/actions/runs/45879376367) |

- Os dois DRAFTs passaram por verificação de oferta, catálogo, fonte, foto, SEO, assinatura e GET/replay, com os mesmos IDs e hashes. Leitura WordPress independente confirmou imagem no corpo, CTA afiliado patrocinado, aviso de afiliação e link interno público. Nenhuma imagem destacada foi configurada. O SEO do #401 foi completado diretamente no AIOSEO após observar o fallback. No #403, o próprio writer gravou metadescrição assinada v3 e validou excerpt nativo, campo do plugin e descrição do head.
- D1 Radar: 2 USED, 0 READY. Samsung: uma tentativa Shopee histórica no ciclo. Retomadas somente com cache da campanha; alvo exato comprovado na [auditoria C166](https://github.com/adelrib27/blogger-automation1/actions/runs/45878468830).
- Desvio e correção: C165 não encontrou uma página elegível no SEARCH. C167 recuperou a fonte canônica e esbarrou no slug incorreto do post interno #29. C168 corrigiu o slug valendo-se do GET público, antecipou o gate da URL e usou uma reserva adicional de pesquisa datada e atômica. Busca ficou 4/4 e HTTP 3/3 naquele UTC; operações Shopee mantiveram a regra original.
- Ferramentas e capacidade: Firecrawl do runtime 301/1.000 créditos no momento da auditoria C166. R2 snapshot medido em 1.686.626.304 bytes; restore/GET do afiliado em 21 s. GitHub Actions tem mínimo declarado de 5 min, com fila variável. WP/AIOSEO aceitaram dois DRAFTs e metadados; limite de hospedagem e cota oficial da conta Shopee não foram identificados. Três conversões por dia é controle do V31. A cadência em minutos ou horas verifica janela, READY, orçamento e teto no D1 antes de R2; a frequência curta é opt-in.
- Aceite: E2E DRAFT Radar comprovado nas duas categorias. O rollout recorrente do Radar ficou staged e sua regularidade precisa de ciclos observados. Expandir o cadastro por fonte exata e verificar oportunidades frescas antes de armar recorrência. Catálogo comercial independente, demais blogs fora desta expansão e LIVE em `pending_policy_approval`.
