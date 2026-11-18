# Checkpoint C7 — Fallback CSV/R2 comprovado nos 3 WordPress (16/11/2026)

**Código de continuidade:** `V31-EDITORIAL-C7-R2-3WP-FALLBACK-SAFE-20261116`

## Meta e decisão do usuário

O V31 Hub Editorial Shopee **não substitui as automações existentes de artigos**. O serviço compartilhado fornece produtos:
- API Shopee normalmente;
- em **erro 1000 confirmado**, usar o catálogo CSV no R2;
- somente fornecer produtos com `offerLink` afiliado previamente verificado e salvo na campanha correta;
- permitir novos blogs Blogger/WordPress sem lista fixa de apenas 3, usando `sites.d/*.json`.

A regra editorial é **permitir reutilizar produtos**, mas exigir **assunto, abordagem e título próprios com palavras-chave SEO preservadas**. Alguns sistemas legados ainda bloqueiam produtos repetidos; esse ajuste **não foi aplicado aos publicadores LIVE**.

## Evidências REAIS no GitHub Actions

| Prova | Run | Resultado |
|---|---|---|
| Casa e Decoração, 1 conversão Shopee real para `casaedecoracaowp`, snapshot no R2, construção com a fila Casa ORIGINAL em diretório temporário | [43878643279](https://github.com/adelrib27/blogger-automation1/actions/runs/43878643279) | SUCCESS |
| Oficina & Garagem, 1 conversão real para `oficinawp`, R2, fila Oficina ORIGINAL temporária | [43879142065](https://github.com/adelrib27/blogger-automation1/actions/runs/43879142065) | SUCCESS |
| Erro 1000 **SIMULADO em memória**, scanners originais Casa/Oficina, R2 REAL, 1 chamada simulada por site e saída v2.3 validada | [43879995986](https://github.com/adelrib27/blogger-automation1/actions/runs/43879995986) | SUCCESS, **89/89 testes offline PASS** |
| Radar Tech BR, 1 conversão real para `radarwp`, R2, 1 slot testado com o `prepare_slot.py` ORIGINAL em diretório temporário | [43880690866](https://github.com/adelrib27/blogger-automation1/actions/runs/43880690866) | SUCCESS, **89/89 testes offline PASS** |

Cada blog tinha **3 candidatos** identificados no teste de pré-aquecimento (limite de consulta de 3), com **0 links previamente cacheados para a campanha**. Agora foi salvo **1 link afiliado real por cada uma das três campanhas WordPress**, além do link anterior da campanha Blogger Air Fryers. A API `generateShortLink` retornou sucesso, sem interrupção. Resultados de links, imagens, títulos e IDs individuais não foram impressos nos relatórios.

## Mudanças no código

- `affiliate_hub_v31/link_warmup.py`: pré-aquecimento compartilhado por registro de site, categorias e palavras-chave, com teto **3 conversions por execução** e transação via snapshot R2, preservando links por campanha.
- `affiliate_hub_v31/tests/test_link_warmup.py`: teste de isolamento, elegibilidade e segundo produto não convertido.
- `affiliate_hub_v31/c7_casa_queue_probe.py` e `c7_legacy_queue_probe.py`: prova de contrato dos construtores originais Casa/Oficina em diretório temporário, sem escrita em filas de produção.
- `affiliate_hub_v31/opportunity_router.py`: **circuit breaker**: erro 1000 interrompe novas consultas do scanner, em vez de continuar gerando requisições durante a falha.
- `affiliate_hub_v31/c7_real_router_probe.py`: integração completa em ambiente SAFE, com API Shopee **inteiramente simulada** e R2 **real**. Não confundir simulação do erro com falha ocorrida de fato.
- `affiliate_hub_v31/c7_radar_slot_probe.py`: valida 1 produto em 1 slot original do Radar usando arquivo de fila **sintético e temporário**. Os outros quatro slots do teste são placeholders não publicáveis; **não** prova que a fila inteira de 5 categorias pode ser reconstruída para operação LIVE.
- Todos os workflows de execução única `v31_c7_casa_once.yml`, `v31_c7_oficina_once.yml`, `v31_c7_error1000_r2_once.yml` e `v31_c7_radar_once.yml` foram **removidos** da branch após SUCCESS. Os históricos de execução permaneceram como prova.

## Limitações e próximos gates

1. **Nenhum workflow comercial existente foi modificado ou ativado nesta fase.** O código está na branch SAFE, PR [#52](https://github.com/adelrib27/blogger-automation1/pull/52) draft. Nenhum artigo foi criado ou publicado nesta implantação.
2. O estoque de **1 link cacheado por campanha** só é suficiente para prova, não para a meta de 50+ blogs × 1–2 artigos/dia. Fazer pré-conversão limitada, contínua e monitorada por campanha **enquanto a API funcionar**. Não reutilizar link de campanha errada.
3. Casa/Oficina consomem o contrato Shopee v2.3, já validado. Radar exige uma fila diária com 5 categorias completas; a validação de um slot **não substitui a construção de fila completa**.
4. Adequar gate editorial de cada blog: produtos podem se repetir, mas a pauta, intenção de busca e título não. Preservar os gates de segurança e originalidade; não desativar controle de duplicidade sem substituição editorial comprovada.
5. Antes da produção, integrar o router com **feature flag desligada por padrão** nos workflows de descoberta e validar em shadow mode, sem alterá-los enquanto permanecem LIVE. Credenciais do R2 estão somente no Environment `v31-editorial-safe`, e os jobs comerciais antigos não o declaram. Evitar alterar o Environment dos publicadores em produção por acidente.
6. Confirmar restrição de branches e tags do Environment e rotação da Shopee App Secret anteriormente exposta; revisar rollback, limites de API e monitoramento de custos.
7. Novos blogs são declarados por `sites.d/*.json` e requerem domínio/ID real, campanha, nichos, regras, gerador/publicador próprio e credenciais — sem editar o motor central.

## Próximo marco

**C8 — Integração progressiva em shadow mode e ampliação do estoque por campanha**. Só depois conectar a execução nos workflows LIVE com rollback imediato e chaves revisadas.

**Estado:** infraestrutura e provas C7 aprovadas; **execução autônoma real em produção ainda NÃO ativada**.
