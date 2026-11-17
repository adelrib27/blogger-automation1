# Checkpoint C20 — Fila de curadoria e consulta para blogs futuros (17/11/2026)

**Continuidade:** `V31-EDITORIAL-C20-R2-INTAKE-203649-17LINKS-203TESTS-20261117`

**Repositório:** `adelrib27/blogger-automation1`  
**Branch de desenvolvimento:** `feature/v31-affiliate-hub-c1-safe-20261115`  
**PR:** [#52 DRAFT](https://github.com/adelrib27/blogger-automation1/pull/52), sem merge.  
**Escopo:** Blogger e WordPress. **Pinterest fica fora.**

## Ponto inicial confirmado — C19
- Snapshot privado Cloudflare R2: **203.649 produtos**, **203.649 entradas FTS5**, **17 links afiliados reais** separados por campanha.
- Taxonomia/categorização não implica publicação: **8.685 elegíveis** pelos gates anteriores, **194.964 em revisão** no checkpoint C19.
- Estado de produção da main e switches LIVE não foram alterados. Nada do C20 publica posts, cria blogs ou converte links.

## Implementação C20 em branch isolada
1. `product_discovery.py`: `discover(..., include_review=True, review_only=True)` devolve apenas candidatos sob revisão, nunca candidatos aprovados misturados; `review_only` sem `include_review` falha fechado. Relevância, bloqueios de raiz protegida, conflito entre feeds, limite por loja, separação por campanha e `can_publish=False` permanecem.
2. `future_site_intake.py`: `preview_future_site(catalog, topic, platform, campaign, ...)` integra sugestão de categorias oficiais + pool previamente aprovado + fila de pendências com razões controladas (raiz protegida, falta de faceta oficial, moderação ou taxonomia não aprovada). **Tema só é recebido quando o futuro blog for solicitado**. Nenhum nicho/URL/identidade de blog futuro é fabricado.
3. `summarize_preview` e CLI `python -m affiliate_hub_v31.future_site_intake --mode r2 --topic "Air Fryer" --platform blogger` imprimem **somente métricas agregadas**, nunca IDs, títulos, nomes de campanhas, links comerciais nem URL assinada. Modo R2 restaura snapshot em pasta temporária e **não chama save_from**.
4. `tests/test_future_site_intake.py` valida campanha explícita, segregação revisão/aprovados, bloqueios, FTS equivalente, ausência de alterações no estado e falha segura para parâmetros inválidos.

## Provas independentes no GitHub
- [CI do código C20 — run 44185865913](https://github.com/adelrib27/blogger-automation1/actions/runs/44185865913): **203 testes offline PASS**, incluindo 7 testes da interface futura e regressões dos módulos antigos. [CI da PR 44185876298](https://github.com/adelrib27/blogger-automation1/actions/runs/44185876298): **SUCCESS**.
- [Canário R2 REAL 44186244836](https://github.com/adelrib27/blogger-automation1/actions/runs/44186244836): **SUCCESS**, 203 testes PASS; restaurou snapshot R2 privado com leitura e fez consultas temáticas reais, sem qualquer publicação.
- Produtos **203.649 = linhas FTS5 203.649**, URLs afiliadas antigas **17 intactas**.
- Temas sem campanha: `Air Fryer` (Blogger), `Guarda Roupa` (WordPress), `Freio` (sem plataforma). Em cada exemplo, **12 candidatos aprovados** e **12 pendentes para revisão**, `affiliate_url=None` para todos por não haver campanha explicitamente selecionada; relatórios agregados identificaram caminhos de categoria e possíveis raízes protegidas sem fornecer dados sensíveis. São amostras da busca, não aprovação nova dos 194.964 pendentes.
- Métricas do canário: `affiliate_conversion_calls=0`, `publication_calls=0`, `site_creation_calls=0`, `r2_writes=0`, `can_publish=False`. **Sem chamada Shopee** e sem escritor de WordPress/Blogger.
- Workflow transitório C20 de teste deve ser removido após o resultado, como feito com canários anteriores. Guardar o run permanente como evidência.

## Limites e próximos passos
1. **Não promover automaticamente os 194.964 pendentes**: criar mecanismo de revisão segura/regras comerciais por segmento com falsos positivos avaliados; categorias Shopee servem à descoberta e não à autorização.
2. Integrar o `preview_future_site` a um orquestrador existente de criação de blogs em **modo consulta sem publicação**, preservando tema/site quando a demanda do usuário for explícita, com teste de contrato por Blogger e WordPress.
3. Só quando a campanha do novo blog for real e autorizada, usar conversor Shopee existente para os produtos escolhidos; **nunca** transferir URL afiliada de campanha diferente. Observar cotas reais, cooldown e erros.
4. O programa de criação/redação/publicação precisa continuar aplicando SEO, originalidade, integridade comercial, validação de produto, credenciais por destino e confirmação/rollback. **C20 não é release LIVE**.
5. Antes de mesclar PR #52: revisar conflito/estado com main atual, todos os interruptores LIVE OFF, regressões de consumidores legados e gate por blog; não alterar cron das lojas, websites, WordPress ou Pinterest agora.

**Estado C20:** implementação de interface de consulta e fila SAFE aprovada em testes offline e R2 real, sem persistência adicional ou publicação. PR permanece DRAFT; main e os 17 links existentes preservados.
