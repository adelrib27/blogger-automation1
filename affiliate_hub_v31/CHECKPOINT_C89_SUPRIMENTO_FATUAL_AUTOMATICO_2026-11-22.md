# V31 C89 — Reabastecimento automático de ofertas com prova de fabricante (22/11/2026)

**Estado:** ENGENHARIA INTEGRADA E CI APROVADO. Execução agendada de criação recorrente de um NOVO DRAFT com o novo algoritmo AINDA NÃO HOMOLOGADA.
**Objetivo:** retirar a dependência de dois perfis estáticos por blog e de GTIN/EAN no CSV, sem alterar autorizações LIVE, cotas pagas ou regras de fidelidade do produto.

## Diagnóstico de causa raiz — provas
- [Cron V31 #45044961421](https://github.com/adelrib27/blogger-automation1/actions/runs/45044961421) confirmou o primeiro schedule writer após V31_AUTODRAFT_ACTIVE=true, site Blogger Móveis; verificou histórico/autorização, mas `independent-verifier` devolveu NO_NEW_OFFER/no_new_offer_with_trusted_source; deliver-draft e LIVE release SKIPPED.
- [C89 probe original #45051513196](https://github.com/adelrib27/blogger-automation1/actions/runs/45051513196): catálogo R2 oficial, Blogger Móveis: 112 SKUs aprovados na amostra, 11 com URL afiliada da campanha, zero GTIN válido, dois perfis estáticos com URL da campanha. As duas ofertas estáticas já figuram em rascunhos Blogger autenticados: Toledo ID 4106024906916105222 e Briz B23 ID 1333713426144675487. Fila não deve duplicar.
- C81 Writer DRAFT atua sob `v31-editorial-safe`; LIVE V31 separado e desligado (Repository variable V31_AUTOLIVE_ACTIVE=false segundo captura do proprietário). WordPress Casa ainda tem writer LIVE legado que deve ser auditado antes de migração.

## Alterações C89 — PR #126 integrado
- [PR #126 MERGED](https://github.com/adelrib27/blogger-automation1/pull/126), merge SHA `f2c01fe811417d59b75c747be2addcb74859b557`.
- [CI #45052979760](https://github.com/adelrib27/blogger-automation1/actions/runs/45052979760): **579 testes PASS** + regressões de Casa, Oficina, Radar e cross-blog. O primeiro CI do PR detectou ciclo de imports; foi corrigido com import GTIN tardio. Um teste exigiu isolar variantes de portas/gavetas para não aceitar uma ficha silenciosa; corrigido e CI final PASS. Nenhum código falho dessa etapa foi integrado em main.
- `affiliate_hub_v31/manufacturer_review.py`: permite busca por marca+modelo+tipo em hosts oficiais preaprovados; exige página de produto específica, URL canônica, metadados, material comprovado e portas/gavetas iguais às do título comercial quando explicitadas. Rejeita fontes/redirects arbitrários e material/variantes ambíguos.
- `affiliate_hub_v31/verified_supply.py`: amplia seleção de SKUs aprovados por nichos oficiais além do top24; produtos sem GTIN podem ter perfil verificável por modelo fabricante, sempre com rota, moderação, faceta e campanha exatas.
- `affiliate_hub_v31/autonomous_review.py`: integra verificação externa Firecrawl limitada por SEARCH/HTTP no D1 ao caminho por fabricante, conserva assinatura HMAC/Ed25519, armazenamento privado R2, D1, deduplicação CMS e no LIVE. Em fonte ausente/excesso de budget retorna NO_NEW_OFFER seguro, não inventa fatos.
- `affiliate_hub_v31/site_request_queue.py` e `.github/workflows/v31_universal_request_queue_daily.yml`: para blog já migrado, prioriza conversão de potenciais ofertas comprováveis; blogs legados não migrados conservam comportamento anterior; teto 3 tentativas Shopee/dia UTC permanece.
- `affiliate_hub_v31/trusted_manufacturer_sources.json`: catálogo extensível de hosts oficiais por marca e blog, sem permitir aprovação de domínio por resposta de IA ou do vendedor.
- `affiliate_hub_v31/supply_probe.py`: medição quantitativa read-only dos modelos extraíveis, sem expor títulos/URLs/segredos.

## Auditoria oficial após o merge
- [C89 probe ampliado #45053078645](https://github.com/adelrib27/blogger-automation1/actions/runs/45053078645) **SUCCESS** e zero mutações: dentre 112 SKUs aprovados amostrados, 10 possuem identificação potencial por modelo de fabricante previamente confiável; 3 desses 10 já possuem link convertido para a campanha do Blogger Móveis. Zero GTIN no pool, sem novas pesquisas pagas nesta auditoria.
- A prova de modelo **não é ainda prova de fonte externa do SKU**. O verificador fará consulta independente, recusará URL/produto/atributos inconsistentes e nunca liberará LIVE por isso.
- A execução recorrente real após PR #126 ainda não foi comprovada. Não declarar segundo DRAFT criado sem GET autenticado do Blogger, SHA HTML, idempotência e USED D1.

## Operação automática daqui em diante
1. Preservar variáveis atuais: `V31_AUTODRAFT_ACTIVE=true`, `V31_AUTODRAFT_ROLLOUT_SITE=blogger_moveis_para_cada_canto`, `V31_AUTOLIVE_ACTIVE=false`; `V31_AUTODRAFT_FULL_ROLLOUT_APPROVED` ausente/false. Não abrir rollout `all` ou WordPress.
2. No próximo ciclo do scheduler `.github/workflows/v31_autonomous_draft_scheduler.yml`, conferir `choose-one`, `authenticated-history`, `independent-verifier`, `deliver-draft` e `release=skipped`. Se DRAFT novo, validar GET, SKU/URL/imagem/campanha, HTML SHA, D1 READY→USED, replay do mesmo ID. Não reexecutar piloto Toledo/B23.
3. O conversor `.github/workflows/v31_universal_request_queue_daily.yml` executa manhã por horário GitHub, respeita cota compartilhada D1 Shopee (3/dia UTC). Após converter produto de fabricante viável, writer poderá tentar verificação externa em ciclo seguinte.
4. `NO_NEW_OFFER` legítimo deve permanecer com zero POST e zero LIVE; não é possível garantir artigo diário quando nenhum produto disponível tem URL afiliada e prova externa objetiva. Amplie fontes confiáveis por marcas oficiais quando comprovadas, sem converter resultado de pesquisa diretamente em autoridade.
5. Auditar convivência WordPress Casa LIVE legado antes de mudar rota ou habilitar `all`. Preservar projetos C82–C88/Cadeira Certa/Ar Condicionado, Pinterest, ARV e Vida Pet.
6. Não atualizar estado JSON concorrente C88 sem conciliação: este documento é fonte C89 específica e índice de continuidade pode apontar para ele.

**Rollback:** para desativar futuras tentativas de DRAFT, alterar somente Repository variable `V31_AUTODRAFT_ACTIVE=false`; não apagar D1/R2 ou rascunhos CMS. LIVE novo continua desligado.