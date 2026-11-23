# V31 C137 — PREVIEW auditoria de cache de afiliados por campanha R2

**Data:** 2026-11-23. **Base:** `main` após C136, 653 testes PASS e monitor #45277246529 SUCCESS.
**Código:** `V31-C137-20261123-PREVIEW-R2-CAMPAIGN-CACHE-READONLY`.
**Objetivo:** preparar expansão universal de Blogger sem ativar site incompleto, sem repetir pesquisa Shopee nem converter URLs.

## Evidências existentes
- C136 implantou monitor read-only e verificou por GET/SELECT Blogger Móveis #4106024906916105222 e WP Casa #321 como DRAFT íntegros; Casa/Oficina crons ainda aguardam observação pós-hold; LIVE pendente.
- C135 recuperou shortlist C94 de 22/11 ([run #45063976401](https://github.com/adelrib27/blogger-automation1/actions/runs/45063976401)): quatro SKUs de catálogo para cada `blogger_cozinha_sem_complicacao`, `blogger_estilo`, `blogger_limpeza`, sem identificar cache real de URL afiliada por campanha.
- `affiliate_hub_v31/catalog.py` confirmou a tabela `affiliate_links(product_key,campaign,affiliate_url,verified_origin,updated_utc)`. Sua presença na campanha **não prova** que o shortlink ainda resolve para o SKU correto, nem valida fabricante/fatos ou imagem atual. `source_safe_for_use` e `moderation=eligible` são filtros anteriores à revisão factual, não provas finais.

## Plano SAFE
1. Reutilizar `R2State.restore_to` da conta/bucket V31 oficiais em arquivo temporário, verificar SHA256 da snapshot e integridade SQLite; reabrir SQLite `mode=ro`.
2. Selecionar até quatro SKUs por uma rota registrada usando taxonomia C94 (nicho, moderação e segurança de origem), consultar exclusivamente `affiliate_links` da **campanha exata daquela rota**. Emitir contagens e rótulos verificáveis (não links de afiliado) e timestamp de cache. Não converter, não chamar Shopee API, D1 ou CMS.
3. Validar por testes offline e Action one-shot GitHub, registrar checkpoint final e decidir qual site tem caminho de revisão factual independente mais próximo. Não criar profile/request nem declarar blog homologado sem fonte de fabricante e antirrepetição CMS.

**Proibido:** escrever R2/D1/CMS, alterar cotas, editar LIVE ou tocar projetos Pinterest/Mercado Livre.
