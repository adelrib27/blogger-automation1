# V31 C81 — autorização de ativação DRAFT de um blog (22/11/2026)

**Estado atual:** código do rollout por blog integrado à `main` no [PR #124](https://github.com/adelrib27/blogger-automation1/pull/124), [CI #45028436487](https://github.com/adelrib27/blogger-automation1/actions/runs/45028436487) `565 tests OK`; **a ativação administrativa não foi executada por este chat.** Novo LIVE automático desativado. Nunca confundir os fluxos legados LIVE com a política nova.

## Mudança administrativa mínima — somente REPOSITORY VARIABLES

O GitHub App disponível neste chat não possui `Actions variables: write`. O proprietário pode ir a:
`https://github.com/adelrib27/blogger-automation1/settings/variables/actions`
e, na aba **Repository variables**, cadastrar ou editar:

| Variável | Valor no PRIMEIRO rollout | Efeito |
|---|---|---|
| `V31_AUTODRAFT_ROLLOUT_SITE` | `blogger_moveis_para_cada_canto` | Exatamente um blog migra para o verificador automático |
| `V31_AUTODRAFT_ACTIVE` | `true` | Habilita o escritor recorrente no scheduler novo |
| `V31_AUTODRAFT_FULL_ROLLOUT_APPROVED` | **não definir** ou `false` | Impede seleção `all` |
| `V31_AUTOLIVE_ACTIVE` | **não definir** ou `false` | Bloqueia LIVE automático novo |

**Ordem:** conferir nome/valor dos gatilhos existentes; definir `ROLLOUT_SITE` antes de ativar `ACTIVE=true`. Essas flags precisam estar no nível do **repositório**, porque o job `choose-one` não tem `environment:`; armazená-las somente em `v31-editorial-safe` pode produzir divergência entre jobs. Se houver homônimos no Environment, reconciliar para NÃO haver conflito de escopo. Não tocar Secrets HMAC/Ed25519/R2/D1/Shopee.

## O que esperar do próximo schedule

- Agendamento atual `v31_autonomous_draft_scheduler.yml`: `47 */4 * * *` (UTC), com atraso possível do GitHub Actions. Quando ativo, `choose-one` só pode escolher a rota explícita, `draft` executa a revisão factual/autenticação e entrega DRAFT, `release` deve ficar `skipped` porque LIVE não foi autorizado.
- O escritor universal antigo Blogger passa a pular **somente** essa rota migrada; rotas não migradas continuam sob o comportamento anterior. Grupo de concorrência compartilhado evita dois workflows V31 tentando escrever ao mesmo tempo.
- Antes de avaliar o resultado, consultar o D1 oficial em leitura e as tentativas/conversões Shopee do **dia UTC correto**, o crédito Firecrawl e o histórico autenticado dos CMS.
- Passagem de gate: **um NOVO DRAFT** de SKU inédito, com ID, status draft, título/HTML SHA exato conferidos via GET, foto real e campanha correta, link interno válido, D1 USED com evidência e assinatura; replay conserva o mesmo ID. O workflow `success` com jobs `skipped` não comprova isso.
- Como a lista atual de perfis verificadores cobre dois blogs e poucos produtos, não assumir criação contínua ilimitada sem expansão da cobertura factual/catálogo. Falta de fonte ou oferta segura deve recusar ou pular, nunca publicar conteúdo inventado.

## Como interromper imediatamente a tentativa de novos DRAFTs

1. Em Repository variables, alterar `V31_AUTODRAFT_ACTIVE` para `false` (ou remover). Isso interrompe futuros schedules novos sem apagar posts existentes, D1 ou R2.
2. Se uma execução estiver em andamento, inspecionar o run antes de cancelar: checar estado D1 e CMS para evitar retry duplicado/POST ambíguo. Manter LIVE inativo.
3. Não apagar nem republicar Blogger ID `4106024906916105222` ou WordPress ID `321`. Preservar hashes, evidência e histórico.

## Expandir somente depois da prova real

- Próxima etapa: **antes de mover** `V31_AUTODRAFT_ROLLOUT_SITE` para `wordpress_casa_decoracao`, auditar e resolver coexistência com o workflow legado `casa_editorial_generate_schedule.yml`: esse cron 3x/dia está configurado com `CASA_LIVE_PUBLISH_ENABLED=true`, `CASA_WORDPRESS_STATUS=publish` e usa grupo de concorrência diferente. Não se pode declarar migração WordPress isolada enquanto existir conflito de publicadores. Depois de corrigido/homologado, migrar a segunda rota isoladamente, nunca `all` de início.
- Usar `all` apenas após autorização explícita para expansão e `V31_AUTODRAFT_FULL_ROLLOUT_APPROVED=true`, políticas de fontes por site e provas independentes por plataforma.
- LIVE requer política aprovada e específica, não faz parte deste procedimento.

## Evidências anteriores

- [Três observações schedule por GET+SELECT](CHECKPOINT_C81_OBSERVACAO_AGENDADA_2026-11-22.md)
- [PR #124 com rollout fail-closed](https://github.com/adelrib27/blogger-automation1/pull/124)
- [CI 565 testes PASS](https://github.com/adelrib27/blogger-automation1/actions/runs/45028436487)
- [C81 DRAFTs reais](CHECKPOINT_C81_RETOMADA_DRAFT_2026-11-21.md)

**Intervenção do proprietário ou Work necessária:** alterar estas Repository Variables. O conector GitHub instalado neste chat não expõe essa mutação. **Nenhuma configuração remota foi alterada neste checkpoint.**
