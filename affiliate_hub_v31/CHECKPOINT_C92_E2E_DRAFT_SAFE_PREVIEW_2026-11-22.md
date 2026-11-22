# V31 C92 — Prova ponta a ponta DRAFT após C89 (prévia)

Data: 2026-11-22. Status: CANÁRIO REAL DRAFT PENDENTE.

- V31 C89 PR#126 MERGED e CI579 PASS: fabricante/modelo verificado com R2 oficial 112 aprovados, 10 modelos potenciais, três links já convertidos.
- D1 oficial SELECT em 22/11: blogger_moveis_para_cada_canto USED=1, WP casa READY=1 USED=1; cotas SEARCH/HTTP **sem lançamentos no dia 22/11** até a leitura.
- D1 global v31_shopee_conversion_attempts de 22/11 já contém **duas reservas em outras campanhas** (arcondicionadosemduvidas e cadeiracertahomeoffice). Não realizar conversão exploratória; só há teto residual global, não necessariamente livre de concorrência.
- Os dois perfis manuais Blogger Toledo e B23 já estão em DRAFT autenticados; preservar 6 drafts do CMS, não duplicar.
- Canário GitHub Actions on-push **único** reusa `v31_independent_review_draft.yml`, com seleção fixa Blogger Móveis, verificando as mesmas chaves e guardas do ambiente `v31-editorial-safe`.
- Critério de homologação: novo DRAFT, leitura autenticada e mesmo ID/HTML em replay, R2 CAS, D1 USED, assinatura, SEO/links/imagem, sem release LIVE; o job SUCCESS ou NO_NEW_OFFER isolado não bastam.
- Se faltarem link ou fontes externas, retornar NO_NEW_OFFER; diagnosticar com contagens de candidaturas CMS sem reescrever links/ignorar a moderação.
- A etapa C92 não modifica rota WordPress Casa nem LIVE de blogs legados. Manter V31_AUTOLIVE_ACTIVE=false.
- Código do canário será removido após a primeira execução para evitar retomadas por push; checkpoint preservado.

Apenas prévia: nenhuma criação de post nem conversão Shopee executada por este documento.
