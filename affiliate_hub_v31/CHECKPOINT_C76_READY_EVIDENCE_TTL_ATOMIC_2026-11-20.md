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

## C76.1 — PR e CI homologados em SAFE

- [PR #101 MERGED](https://github.com/adelrib27/blogger-automation1/pull/101), merge SHA `d7d8676437f150884d23d91f74459ae861bcb6f5`. Alteradas somente `affiliate_hub_v31/d1_universal_ready.py` e `tests/test_c71_d1_universal_ready.py`.
- [CI #44761871702 SUCCESS](https://github.com/adelrib27/blogger-automation1/actions/runs/44761871702): **508 testes V31 / OK**, Casa 24/24, Oficina 21/21, Radar 15/15, crossblog PASS. C75 tinha 505 testes; C76 adicionou 3 regressões.
- Contrato `reserve_ready`: agora só reserva se `v31_verified_evidence` contém **mesmo site, campanha, SKU, SHA e janela temporal `verified_epoch <= now < expires_epoch`**, e tudo é checado no **MESMO INSERT SQL**.
- Contrato `consume_one`: o UPDATE `READY → USED` exige que a **mesma prova** continue atual, sem hash modificado nem vencimento; mantém lease válido e controle de repetição, sem CMS.
- Fixtures SQL de teste simulam prova; provas reais continuam exigindo `cache_verified_evidence`/whitelist C69 e gate factual HTML C71. Nem SQL match nem 508 testes demonstram fonte externa genuína/credencial Firecrawl.

## C76.2 — leitura independente do D1 oficial após integração GitHub

- GET na conta Cloudflare **`adeiltonrib27@gmail.com`**, account `ebb8d5b4cf9a2cb850c6d8051bd2661f`, conferiu banco exato `v31-universal-ready-safe`, UUID `9bfce7a4-6167-4bfc-a65e-a74c1a34f064`.
- POST /query somente SELECT confirmou contagens **leases=0, jobs=0, evidence=0, budgets=0** no banco novo. Nenhum dado de produto/tenant REAL migrado, nenhuma fixture restante; C76 não escreveu no D1.
- Outros D1/contas/Workers/R2/CMS/Firecrawl não foram tocados. Sem credencial GitHub D1, sem integração de READY aos writers, sem novos DRAFTs ou LIVE por C75/C76.

## Fechamento e continuidade

**C75 + C76 = SAFE concluídos, código em main, CI 508 PASS.** `active_work` deve ficar `PRONTO_PARA_PROXIMA_ETAPA`, mutação remota pendente = false. Próximo passo real: auditar variável `V31_EDITORIAL_R2_ACCOUNT_ID` do GitHub e credencial de privilégio mínimo (sem expor valores); smoke test do novo HTTP runner contra D1 com SELECT-only e sem posts, seguido de prova concorrente multi-executor isolada. Somente depois Evidence/HTML/SEO R2 e canário DRAFT por blog; LIVE sempre aprovação individual.
