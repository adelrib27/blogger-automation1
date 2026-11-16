# CHECKPOINT C12 — Texto original obrigatório no reuso de produtos (16/11/2026)

**Código de continuidade:** `V31-EDITORIAL-C12-BODY-ORIGINALITY-126-PASS-20261116`  
**Branch:** `feature/v31-affiliate-hub-c1-safe-20261115`  
**PR:** [#52 — DRAFT](https://github.com/adelrib27/blogger-automation1/pull/52), sem merge.  
**STATUS:** C11/C12 implementadas e testadas em SAFE; não ativadas em LIVE.

## Decisões preservadas no projeto

O V31 é a camada **central e extensível** de produtos Shopee para blogs WordPress/Blogger. Os geradores Qwen3, SEO, publicadores e agendamentos existentes NÃO serão substituídos. A API Shopee é preferencial; em falha 1000 confirmada, o CSV/SQLite privado do R2 pode servir produtos com links já convertidos para a campanha. Reutilização de um mesmo produto deve produzir pautas, títulos e corpos realmente distintos.

**Hipótese futura, FORA DO ESCOPO até finalizar V31:** todos os blogs possuem páginas de loja atualizadas diariamente; essas consultas somadas às pesquisas editoriais podem concentrar chamadas e contribuir para falhas da Shopee, inclusive possíveis erros 1000. Não presumir que 1000 e 10030 sejam a mesma causa. Depois de concluído V31, medir as consultas/horários de TODAS as lojas e avaliar atualização mensal distribuída por blog, SEM desativar lojas antes. O runbook C10 registra essa decisão.

## C11 — implementação opt-in, já aprovada

- Reutilização editorial genérica `affiliate_hub_v31/reuse_policy.py`.
- `casa_decoracao/src/build_editorial_queue.py` e `oficina_garagem/src/build_editorial_queue.py`: candidatos repetidos por produto só se histórico confiável e `V31_EDITORIAL_PRODUCT_REUSE_ENABLED=true`, com os dois switches globais/por blog necessários. Outros IDs/fingerprints semelhantes continuam bloqueados; IDs novos evitam sobrescrever artigos anteriores.
- Os Qwen3 existentes recebem os títulos anteriores do mesmo produto e rejeitam novos planos com título semelhante antes da geração.
- Os publicadores existentes revalidam o histórico e permitem no máximo **duas matérias por produto no piloto**, diferenciando os registros por produto+título. URLs/slug WordPress e quality gates originais permanecem.
- Três interruptores obrigatórios simultâneos para habilitar o recurso: `V31_EDITORIAL_C9_RELEASE_ENABLED`, `V31_CASA_R2_FALLBACK_ENABLED` ou `V31_OFICINA_R2_FALLBACK_ENABLED`, e `V31_EDITORIAL_PRODUCT_REUSE_ENABLED`. Todos OFF por padrão.

## C12 — novidade: sem corpo anterior comparável, não há reuso

- `validate_prior_editorial_body` compara o **editorial_html** do novo artigo com o corpo histórico do mesmo produto e título publicado usando as métricas e thresholds do `src/editorial_cross_blog_guard.py`.
- Para evitar título novo com texto essencialmente repetido, o publisher **bloqueia antes de qualquer chamada WordPress** se o corpo é muito semelhante.
- Se o artigo anterior não possui um draft JSON comprovável em `data/generated`, o reuso é bloqueado — não se pode assegurar originalidade. Isso protege posts antigos sem backfill confiável.
- Guard é **no-op** quando o produto não está sendo reutilizado. Publicação normal mantém comportamento legado.
- Falhas na leitura de histórico/configuração também bloqueiam. Reutilizar produto é opt-in e não cria agendamento, scraper ou gerador adicional.

## Provas

- [Run de QA integrado C11](https://github.com/adelrib27/blogger-automation1/actions/runs/43910337180) — **SUCCESS**: 125/125 testes V31; 24/24 testes originais Casa, 21/21 Oficina, cross-blog guard PASS; sem API nem publicação.
- [Run de validação C12](https://github.com/adelrib27/blogger-automation1/actions/runs/43911094183) — **SUCCESS**: **126/126 testes V31** incluindo corpo igual, corpo diferente e ausência de texto histórico.
- Workflow de QA temporário eliminado após PASS. Nenhum secret, mutation Shopee, upload R2 ou publicação WordPress/Blogger neste marco.
- **NÃO foi testado com dados históricos privados reais da publicação de cada blog.** O teste é isolamento SAFE/offline, válido para provar comportamentos de código, não para autorizar LIVE.

## Pendências antes de encerrar V31 em produção

1. **Estoque cacheado por campanha**: último diagnóstico real **Casa 2/9, Oficina 2/6, Radar 6/15** para meta inicial 3 dias; total R2 **11 links**, incluindo Blogger Air Fryers. Metas ainda não cumpridas. Evitar disparar rajadas de API Shopee; usar prewarm com orçamento global baixo, após medir carga/conflitos de horários.
2. **Auditar históricos reais** de Casa/Oficina e comparar drafts antigos com posts para saber quais produtos podem ser reutilizados sem backfill; conferir idempotência, histórico de slug e quality gates.
3. **Radar**: a fila de 5 categorias, 5 lojas e 5 slots passou E2E com R2 real em C9, porém Radar ainda mantém seu próprio bloqueio de produto repetido; estender política editorial somente se necessário e após teste.
4. **Canário sem publicação:** validar fluxo dos workflows originais, suas condições, horários, artefatos e flags com histórico representativo; não ligar flags nem mesclar automaticamente.
5. **Expansão 50+ blogs:** cadastro declarativo existe, mas inclusão de cada blog real requer suas fontes/config/credenciais e adaptador de consumidor. A política de reuso é genérica; Casa e Oficina são implementações específicas nos publicadores existentes.
6. **Após o V31:** investigação separada sobre tráfego da API gerado pelas lojas e eventual rotação mensal por blog.

**Conclusão:** infraestrutura API→R2 testada; política editorial opt-in + comparação de texto anterior testadas; **a rede LIVE continua intocada e o PR em draft**, pendente reserva de links, histórico real e canário supervisionado.
