# C78 — envelope HTML imutável/privado R2 entre READY D1 e CMS (20/11/2026)

**PRÉVIA EM_ANDAMENTO — salva na main antes de código.**

## Ponto inicial
- C77 [PR #102 MERGED](https://github.com/adelrib27/blogger-automation1/pull/102), [CI #44771203643](https://github.com/adelrib27/blogger-automation1/actions/runs/44771203643) 518 testes V31 PASS, adapter de preflight SEO/fatos/revisão independente/READY SQL sintetizado.
- R2 oficial `v31-editorial-shopee` e D1 oficial `v31-universal-ready-safe` pertencem à conta Cloudflare correta `adeiltonrib27@gmail.com`; D1 continua vazio após leitura C77.
- Auditoria no ambiente GitHub protegido `v31-editorial-safe` confirmou account ID R2 MATCH e novo D1 secret ausente. Não configurar segredos por inferência.
- Lacuna concreta: D1 guarda `html_sha256` na tabela READY, mas não possui armazenamento/releitura dos bytes do HTML aprovado. Regenerar com IA na hora do POST poderia alterar conteúdo pós-revisão.

## Plano estritamente SAFE
1. Criar biblioteca de envelope privado por `site_key/campaign/SHA256`, JSON canônico com HTML exato e assinatura editorial já aprovada, sem duplicar produtos/catálogo CSV. Backend de objetos injetado e **compare-and-set atômico put-if-absent**, nunca `GET` seguido de `PUT` em produção.
2. Read-after-write de bytes e hash, isolamento de tenant, recusas de mutação/sobrescrita, replay de outra campanha, URL falsa, HTML corrompido ou assinatura divergente, sem ler ou escrever R2 real nesta fase.
3. Especificar ordem segura: preflight C77 → gravação privada imutável → D1 READY com hash exato → writer somente após confirmar D1 USED + readback e HTML hash; órfãos não são aprovados para publicação e exigem GC controlado.
4. Testes offline com backend simulado e CI PR, preservar legado, cron, CMS, D1 e Cloudflare; nenhum POST/LIVE.

**Nenhuma mutação remota por esta prévia.**
