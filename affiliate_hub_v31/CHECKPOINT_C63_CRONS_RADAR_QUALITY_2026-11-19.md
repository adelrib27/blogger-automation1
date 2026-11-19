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

## Execução e evidências — C63

### C63.1 — Recuperação Radar com gate preservado
- [PR #85 MERGED](https://github.com/adelrib27/blogger-automation1/pull/85), merge commit `06998c96692a5345f911c36c6c883e7495b459f7`: corrigida a divergência entre prompt (35–60 caracteres) e parser/retry (anteriormente 35–65). Feedback da tentativa agora inclui erro anterior, quebra de linha real e faixa 35–60 consistente; continua máximo de 3 tentativas, sem fallback que burle o gate. Item/quarentena anteriores **não foram liberados nem publicados**.
- Novos testes offline: título curto seguido de válido; 3 curtos continuam bloqueados; 61 caracteres permanece proibido. O self-test Radar foi incorporado ao workflow CI e futuras mudanças em `radar_tech_br/src/**` passaram a disparar essa suíte.
- A causa confirmada da falha Radar anterior [#44447410967](https://github.com/adelrib27/blogger-automation1/actions/runs/44447410967) era título editorial curto (31 caracteres após 3 tentativas), **não** autenticação WordPress. Melhorias de recuperação **não são prova de cron LIVE novo**.

### C63.2 — Gate universal WordPress antes do POST
- Writer `affiliate_hub_v31/automatic_wordpress_drafts.py` agora invoca `validate_wordpress_paragraphs` para qualquer site WordPress V31 no processo `compose_article` **antes** de `create_draft`. Recusa textos fora do comprimento, repetição de parágrafos, HTML/URL comercial indevido, cópia integral de título comercial suficientemente específico e padrões conservadores de afirmação não sustentada (testes fictícios, efeito antibacteriano, promessas absolutas, benefícios funcionais, popularidade sem evidência). Falha fechada: erro e **0 POST**.
- Isso NÃO é fact-check completo nem autorização para LIVE. `articles:null`, no máximo 1 DRAFT/ciclo, anti-SKU, campanha, revisão R2 e imagens reais continuam como antes. Post WP #303 não foi editado ou recriado nesta C63.
- [CI final PR #85 #44546604810](https://github.com/adelrib27/blogger-automation1/actions/runs/44546604810) **SUCCESS: 383 testes V31 +24 Casa +21 Oficina +15 Radar + crossblog PASS**. Duas versões intermediárias falharam por expectativas de texto em teste legado C59; corrigidas antes do merge (não foi bug de produção).

### C63.3 — Estado independente dos destinos em 19/11/2026 às 14:43 UTC
- Blogger Móveis para Cada Canto, API conectada: **3 LIVE +1 DRAFT**, mesmo rascunho `3612281866616913629` da C61, sem alteração. Não houve nova publicação nesta execução.
- WordPress Casa e Decoração, API conectada: **43 LIVE +58 DRAFT**, mesmo 303 da C62. Nenhum novo WP POST foi enviado pela C63.
- GitHub Actions (últimos 100 runs lidos na abertura) não mostrou `schedule` dos dois workflows universais C55/C60 **depois da C61**. `v31_universal_blogger_autodraft_daily.yml` tem cron `18 12 * * *` (09:18 Recife) e `v31_universal_wordpress_autodraft_daily.yml` `41 12 * * *` (09:41 Recife). Essas janelas do dia **19/11** antecederam a alteração C61. Próxima data cron configurada: **20/11/2026**; nenhuma execução futura pode ser dada como sucesso antes de acontecer. WordPress C60 segue PREVIEW por padrão se flag não habilitada; Blogger no cron permite somente DRAFT.
- O verificador de continuidade [#44545373644](https://github.com/adelrib27/blogger-automation1/actions/runs/44545373644) falhou **transitoriamente** porque o JSON foi gravado apontando ao novo checkpoint um commit antes da criação do arquivo C63. Não ocorreu mutação externa. Verificação deve ser refeita após indexar C63 e finalizar JSON, sem ocultar o incidente.

## Encerramento técnico
**Status C63: implementação e suíte de testes CONCLUÍDAS; crons futuros A OBSERVAR.** Preservada a distinção entre PR/CI, crons configurados, DRAFT real e LIVE. Não criar mais rascunhos para revalidar o mesmo produto. Próximas ações: observar runs `schedule` de 20/11 e confirmar efeitos pelo Blogger/WordPress, ampliar auditoria editorial/factual conforme produtos reais sem liberar `REVIEW` em massa, investigar Radar caso novos títulos continuem insuficientes sem publicar por fora da quarentena. Nenhum segredo persistido.

### Validação final do protocolo de continuidade

- O incidente transitório de ponteiro C63 foi sanado após criar o checkpoint e atualizar o índice/JSON. [Continuity guard #44547021777](https://github.com/adelrib27/blogger-automation1/actions/runs/44547021777) **SUCCESS** na atualização do índice e [#44547095044](https://github.com/adelrib27/blogger-automation1/actions/runs/44547095044) **SUCCESS** após finalizar o estado JSON C63. Estado registrado como `PRONTO_PARA_PROXIMA_ETAPA`, sem mutação externa em andamento.
