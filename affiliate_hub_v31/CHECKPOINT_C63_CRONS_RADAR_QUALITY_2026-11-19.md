# V31 C63 — crons universais, recuperação Radar e qualidade do writer WordPress (19/11/2026)

**PRÉVIA DURÁVEL — EM_ANDAMENTO.** Criada antes de mudanças de código e de mutações externas. Não autoriza LIVE, novo POST WordPress ou rerun de Radar.

## Missão universal preservada
Biblioteca dos dois CSV Shopee em R2, independente de nichos e blogs antecipados; após pedido e rota real, só SKUs aprovados com imagem real, link da campanha exata, conteúdo original, CTA/disclosure e posts internos reais. Blogger/WordPress compartilham contratos com gates separados de publicação.

## Evidências confirmadas na retomada
- `main` HEAD na abertura: `2fc36141bcd8c315b66cfc360e8729f1c207d455`. [C62](CHECKPOINT_C62_WORDPRESS_REAL_DRAFT_ONCE_2026-11-19.md) terminou: [PR #84](https://github.com/adelrib27/blogger-automation1/pull/84) MERGED, [CI 44543354220](https://github.com/adelrib27/blogger-automation1/actions/runs/44543354220) SUCCESS, 1 DRAFT WordPress real ID 303 preservado; nenhuma publicação LIVE V31.
- GitHub Actions últimos 100 registros na abertura: não foi encontrada ocorrência `schedule` dos workflows permanentes `v31_universal_blogger_autodraft_daily.yml` ou `v31_universal_wordpress_autodraft_daily.yml` após C61. Isso **não equivale** a prova de que jamais rodaram; revisar filtros pelo endpoint de workflow e período.
- [Radar #44447410967](https://github.com/adelrib27/blogger-automation1/actions/runs/44447410967) FAILURE na confirmação do slot porque planejamento editorial voltou título de **31 caracteres** mesmo após 3 tentativas; slot QUARENTENA, 0 publicações naquela execução. Não desabilitar quality gates.
- Regras de `articles:null` da C61 continuam: sem teto total; no máximo 1 DRAFT por ciclo, SKU/campanha isolados. Nenhuma autorização para LIVE automático irrestrito.

## Plano C63
1. Ler workflows permanentes Blogger/WordPress, resultados por workflow/evento, e estado seguro de crons recentes (distinguir agendamento de sucesso e rascunho criado).
2. Radar: corrigir qualidade da tentativa de reparação do **plano editorial** inválido com prompt consistente e erros precisos, sem reduzir 35–65 caracteres, sem soltar itens QUARENTENA nem disparar publicação LIVE.
3. WordPress: endurecer pré-POST com gate semântico conservador e testes de regressão para frases não comprovadas, conservando aprovação R2, imagem real, CTA, link da campanha, dois links internos quando disponíveis. Nunca alterar o rascunho #303 sem plano explícito e readback.
4. PR + CI com testes V31 e legados; verificar merge; documentar resultado e limpar artefatos temporários; atualizar início e JSON na `main`.
5. Não reexecutar workflow de publicação Radar; validar correções por testes e prévia sem publicação.

## Marcos
- **FEITO:** prévia C63 no estado JSON e este checkpoint.
- **PENDENTE:** diagnóstico e implementação, CI/PR, encerramento.
