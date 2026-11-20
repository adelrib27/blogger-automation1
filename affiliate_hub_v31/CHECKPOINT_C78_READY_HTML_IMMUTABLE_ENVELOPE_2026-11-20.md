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

## C78.1 — PR e CI
- [PR #103 MERGED](https://github.com/adelrib27/blogger-automation1/pull/103), merge SHA `fecbf066b04c985c9b0ddd3c6ddf8e3077670b97`. Somente `affiliate_hub_v31/private_ready_envelope.py`, `tests/test_c78_private_ready_envelope.py`, e `C78_ENVELOPE_PRIVADO_R2_CONTRATO.md` foram acrescentados.
- [CI #44772815507 SUCCESS](https://github.com/adelrib27/blogger-automation1/actions/runs/44772815507): `Ran 527 tests in 14.778s` / `OK` (9 testes novos C78), Casa 24/24, Oficina 21/21, Radar15/15, cross-blog PASS.
- API privada ABSTRATA: chaves namespaced por site+campanha+hash; objeto HTML exato + manifesto C77 assinado; backend futuro precisa `put_if_absent` atômico, read-after-write byte idêntico, falha se já existe conteúdo diferente; load revalida hash, assinatura e JSON canônico. Não há R2 real nesta prova.
- Os testes incluem replay idempotente, conteúdo adulterado, mudança de review sob o mesmo SHA, recusa de outra campanha/tenant/path traversal, assinatura ausente ou errada e CAS inválido.

## C78.2 — escopo concluído e pendências
- **C78 SAFE CONCLUÍDA.** Nenhum token GitHub D1, nenhum backend R2 real, nenhum POST/CMS, nenhum Firecrawl search, nenhum Worker ou cron alterado; 0 LIVE e 0 DRAFT atribuíveis à C78.
- Conta Cloudflare oficial segue `adeiltonrib27@gmail.com`; ambiente GitHub `v31-editorial-safe` com R2 account MATCH, `V31_D1_API_TOKEN` ainda AUSENTE conforme canário C77; não improvisar token.
- Antes de E2E: conectar adapter de escrita condicional R2 na conta oficial (com prova CAS), configurar D1 token de escopo mínimo, fluxos de revisão HMAC independente e evidências reais, implementar reconciliação R2 envelope -> D1 READY -> writer e revalidação de HTML/comercial/SEO, canário CMS DRAFT, publicação LIVE somente por autorização individual.
- `articles:null` permanece geração contínua e `min_ready=3` apenas buffer de trabalhos simultâneos.

**Fechamento:** `active_work.status=PRONTO_PARA_PROXIMA_ETAPA`, nenhuma mutação remota em andamento ou rollback pendente. Próxima C79 integra um backend R2 de prova CAS ou verifica a autorização de credenciais mínimas; não habilitar escritores automaticamente.

## C78.3 — conferência independente final após PR #103

- Cloudflare conectado à conta oficial `ebb8d5b4cf9a2cb850c6d8051bd2661f`: GET nome exato `v31-universal-ready-safe`; SQL somente SELECT retornou `leases=0, jobs=0, evidence=0, budgets=0`. Nenhum escritor novo habilitado, nenhuma gravação de conteúdo no D1/R2 real e 0 posts por C78.
- Estado JSON e índice permanente de continuidade atualizados para C78; workflow TEMP C77 já excluído. Próxima fase C79 deve começar por este checkpoint e auditar o estado vivo.
