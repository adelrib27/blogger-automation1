# C69 — fusão da engenharia experimental Vida Pet ao V31 UNIVERSAL (19/11/2026)

**STATUS: EM_ANDAMENTO — checkpoint prévio antes de alterações de código ou estado.**

## Solicitação e escopo exatos
O usuário enviou `RELATORIO_MESTRE_VIDA_PET_PRATICA_CONTINUIDADE_2026-11-19.md` e PDF homônimo e solicitou **incorporar a engenharia do laboratório à evolução do V31 UNIVERSAL** para quaisquer blogs Blogger/WordPress, **não criar um subsistema focado em Vida Pet**. O usuário autorizou prosseguir nas tarefas independentes da observação dos crons GitHub de 20/11. Isso **não autoriza** implantar writer no WordPress.com privado Vida Pet, editar seus dados D1, criar novo cron, migrar host, alterar outros posts LIVE ou gastar créditos de pesquisa sem medição de quota.

## Contexto vivo consultado hoje no GitHub
- Entrada principal [V31_CONTINUAR_AQUI.md](../V31_CONTINUAR_AQUI.md), JSON C68 `PRONTO_PARA_PROXIMA_ETAPA` e [checkpoint C68](CHECKPOINT_C68_SEO_NOVOS_BLOGS_FICHA_2026-11-19.md); última edição V31: [PR #95](https://github.com/adelrib27/blogger-automation1/pull/95), CI **427 V31** + regressões legadas, SAFE, SEO/links futuros.
- O LAB Vida Pet **já está no MESMO repo**, sob `vida_pet_pratica/`, não precisa copiar história a outro projeto. Workflow `.github/workflows/vida_pet_pratica_persistence_lab.yml` continua `workflow_dispatch` e trigger de kickoff, **sem cron e sem publicador**; `permissions: contents:read`. `vida_pet_pratica/wordpress_write.flag` **AUSENTE**.
- `vida_pet_pratica/config/automation_policy.json` atual (sha `2f2ab8bbd9cec15e80e63ce155ef7673bb97c642`): `wordpress.writes_enabled=false`, `min_ready=3`, `candidate_attempt_limit=20`, `rotation.product_cooldown_days=30`, `anti_duplicate.max_similarity=.72`, Evergreen e Candidate Failover ativos. `evidence_reuse_policy.json` sha `c1df499af02168a867561bc7c36431574a4229ef`: TTL 7d, mínimo 1 fonte externa autorizada e 2 evidências exatas, sem renovar TTL ao ler cache, fail-closed.
- Último run especificamente comprovado do LAB: [R28 #42503073705](https://github.com/adelrib27/blogger-automation1/actions/runs/42503073705), `completed/success` 08/11; nenhuma execução R29 foi comprovada. Métricas R27/R28 do D1, READY 3/3 e saldo Firecrawl apresentados no RELATÓRIO são **históricos**, não SQL direto atual em 19/11. Falta cache miss real e READY refill <3 de forma controlada; **não alegar realizados**.
- `vida_pet_pratica/src/evidence_engine.py`, `evidence_engine_persistent_v13.py`, `firecrawl_quota_guard.py`, `firecrawl_telemetry.py` e `d1_persistence_v2.py` conferidos. O budget R28 limita LAB a 2 buscas/3 HTTP, bloqueia 429/contador inválido; NÃO mede custos monetários por si só.
- V31 já possui catálogo universal CSV/R2, `Catalog.for_conversion`, `article_commerce._single_verified_offer` para foto e campanha exata, seleção de nichos/links site-specific, dedup por SKU e writers Blogger/WordPress DRAFT-only. **Não sobrescrever nem enfraquecer tais gates**.

## Arquitetura de fusão aprovada
- Converter o **padrão de engenharia** de Evidence Engine (identidade `EXACT_PRODUCT` vs `MATCHED_MODEL` vs `SIMILAR_PRODUCT`), fatos autorizados, cache TTL 7d, histórico/anti-dup, Evergreen por ângulo real+cooldown, Candidate Failover, buffer READY e orçamento de buscas em **módulo reutilizável** `affiliate_hub_v31/`, com escopo lógico por `site_key+campaign`, não por pets.
- Preferir reutilizar validação comercial real `Catalog.for_conversion` e foto+campanha exatas, e interligar futuramente à norma SEO C68 antes de emissão READY. Não copiar SKUs/policies de pets nem os IDs/URLs/segredos/D1 específicos. Recursos de pets (alegações veterinárias) ficam restritos à taxonomia/política temática do nicho quando aplicável.
- Nesta fase criar **núcleo SAFE offline, persistência adaptável demonstrada com SQLite em testes, integração por interface com catálogo e SEO, política parametrizável e regressões**; separar **código integrado/testado** de **implantação em D1/R2/jobs de produção** ainda pendente. Nenhum novo writer LIVE, cron ou banco D1 criado automaticamente.
- Demanda V31 por artigos ilimitados permanece `articles:null`: `min_ready=3` define uma **reserva operacional**, NÃO teto de 3 artigos nem teto de blogs.

## Plano imediato C69
1. Salvar este checkpoint em `main` **antes** de qualquer código; marcar continuidade C69 `EM_ANDAMENTO`.
2. Implementar núcleo V31 universal SAFE e adaptador de produto aprovado/campanha real, segurança de evidências e anti-dup por site, budget Search/HTTP/429, fila READY com persistência e testes offline. Idealmente teste de integração com o `future_blog_seo.py` da C68, sem alterar escritores legados.
3. PR + CI e comprovação de não regressão (Blogger/WordPress e LAB). Sem chamadas Firecrawl/Groq/D1 mutáveis ou WordPress nesta fase.
4. Documentar fronteiras LIVE, caminho futuro de deploy D1/site_keys e migração por canário, registrar checkpoint/JSON/índice para novo chat.
5. Verificação independente 20/11 de `event=schedule` permanece pendente e não é pré-requisito para C69.

## Limitações
O PDF e o MD são duas representações do mesmo relatório; conteúdo de tabelas, figuras e riscos considerado pelo arquivo Markdown recebido. Vida Pet WordPress.com Simple é privado/não lançado e **fora do escopo de escrita**. Status lab R28 ≠ implantação editorial V31 de produção. Não inferir crédito Firecrawl ou declarar teste de cache miss real sem evidência.

## C69.1 — primeiro núcleo universal aprovado, independente de cron
- [PR #96 MERGED](https://github.com/adelrib27/blogger-automation1/pull/96), merge `7c6bfde9e31eea515f7567ad4d5b7cfe0784cc0d`. [CI #44598058674](https://github.com/adelrib27/blogger-automation1/actions/runs/44598058674) **SUCCESS**: **459 testes V31** (32 novos C69) + Casa 24/24 + Oficina 21/21 + Radar 15/15 + crossblog PASS. Nenhum writer/cron/R2/D1/LAB existente editado.
- Módulo `universal_evidence_ready.py` valida catálogo real injetado `Catalog` (moderação, foto, campanha exata), SEO real C68 de fixture, pacote de evidência exato/autorizado/TTL, failover, anti-dup, cooldown30, READY min3/por site e SearchBudget 2/3 com 429 em simulador; **0 publicação, 0 rede**.
- [Guia de arquitetura](UNIVERSAL_EVIDENCE_READY_ARQUITETURA_C69.md) e template C68 com Evidence/READY documentados; `vida_pet_pratica/` mantém R28 sem escrita ou cron.
- **Nova evidência externa relevante ao scheduler:** em 19/11 foram observadas execuções `event=schedule` **de workflows legados** (Radar Tech BR fila #44593351294 SUCCESS, sombra V31 C8 #44595622511 SKIPPED conforme configuração, Radar Editorial #44597661599 FAILURE). Logo GitHub **consegue entregar alguns schedules do repo**; isso não demonstra os três crons novos V31, cuja homologação específica segue para 20/11. Não declarar problema global de scheduler como causa conclusiva.
- **Extensão SAFE C69.2 ainda por implementar:** persistência local de cache de evidência com reuso entre sessões e TTL que não é renovado ao ler, mais testes; nenhuma obrigação de API/conta real nesta fase.
