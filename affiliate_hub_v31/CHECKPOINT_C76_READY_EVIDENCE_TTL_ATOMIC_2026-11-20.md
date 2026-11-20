# C76 — binding atômico READY ↔ evidência exata/TTL por SKU (20/11/2026)

**PRÉVIA EM_ANDAMENTO salva na main ANTES de mudanças de código.**

## Diagnóstico após C75

- C74: D1 exclusivo V31 na conta R2 oficial com esquema e canários PASS; C75: [PR #100](https://github.com/adelrib27/blogger-automation1/pull/100) MERGED, [CI 505 testes](https://github.com/adelrib27/blogger-automation1/actions/runs/44761018643) SUCCESS, transporte HTTP isolado e read-only por padrão, sem writers.
- **Lacuna detectada em revisão SAFE:** `UniversalD1ReadyState.reserve_ready()` aceita `evidence_sha256` fornecido pelo chamador sem conferir na mesma instrução SQL a existência de pacote `v31_verified_evidence` do mesmo `site_key+campaign+product_key` com hash idêntico, `verified_epoch<=agora<expires_epoch`. `consume_one()` tampouco confere validade no momento de marcar USED.
- Impacto potencial se fosse ligado agora: um chamador com lease poderia criar READY com hash arbitrário ou consumir após expiração/rotação de evidência. **O risco não foi explorado em produção porque writers ainda estão DESLIGADOS do D1.**

## Plano SAFE

1. Tornar as duas verificações precondições SQL atômicas em `reserve_ready` e `consume_one`, mantendo lease/idempotência/buffer/cooldown. Não fazer SELECT seguido de INSERT/UPDATE, que abriria corrida.
2. Ajustar fixtures SQLite de testes C71 com evidência sintética por tenant e expiração realista; testar hash errado, SKU/campanha divergentes, TTL vencido, future-dated, troca de prova após READY e recusa de consumo.
3. PR/CI da suíte inteira, sem modificar schema/produtos/Cloudflare/R2/CMS/writers/crons. Nenhum LIVE e nenhum consumo Firecrawl.
4. Documentar o que foi validado e o que continua pendente (fact gate humano e URL/campanha real; HTTP D1 token e canário).

**Início:** nenhuma mutação Cloudflare/CMS. Trabalho somente GitHub em branch isolada.
