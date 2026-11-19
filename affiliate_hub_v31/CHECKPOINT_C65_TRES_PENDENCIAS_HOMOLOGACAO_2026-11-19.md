# V31 C65 — três pendências de homologação (19/11/2026)

**PRÉVIA DURÁVEL — EM_ANDAMENTO.** Criada no início da C65, antes de alterar workflows/geradores e de qualquer efeito externo. Ref: [V31_CONTINUAR_AQUI.md](../V31_CONTINUAR_AQUI.md) e [estado JSON](CONTINUIDADE_ESTADO.json).

## Evidência de partida
- C64: [#44551595546](https://github.com/adelrib27/blogger-automation1/actions/runs/44551595546) SUCCESS Shopee 3 conversões reais e R2 restaurado/verificado, 0 posts; [#44552501661](https://github.com/adelrib27/blogger-automation1/actions/runs/44552501661) SUCCESS 1 DRAFT Blogger ID 2990403416970116294, 0 LIVE; [PR #86](https://github.com/adelrib27/blogger-automation1/pull/86) MERGED e CI 384 PASS.
- C62: WordPress Casa publicou somente DRAFT ID 303, sem LIVE. APIs C65 retomada: Blogger Móveis 3 LIVE+2 DRAFT, Casa WordPress 43 LIVE+58 DRAFT.
- Não existia `schedule` C55/C60 confirmado após C61 nos últimos 100 runs. Próximos crons permanentes 20/11 09:18/09:41 Recife; NÃO aguardar para testes funcionais.
- WordPress universal não possui pedido persistente habilitado (somente Blogger Móveis). A credencial WordPress Casa no C62 existiu como segredo legado do ambiente seguro, mas a disponibilidade do segredo multi-site universal no cron é desconhecida.
- Publicação automática LIVE universal NÃO foi aprovada em massa. A autorização anterior foi pontual aos 3 LIVE Blogger; drafts gerados por IA estão sob revisão. Não executar `publish_post`/WordPress publish para conteúdo não revisado.

## Plano C65
1. Adicionar canário TEMP **somente prévia** ao schedule dos workflows PERMANENTES para 19/11, em horário UTC próximo, com branch, domínio e jobs protegidos; distinguir `event=schedule` real de `push`. Remover canário após evidências; se não ocorrer por atrasos do GitHub, manter status não comprovado.
2. Resolver abastecimento contínuo real por campanha sem teto global de 3 artigos: calendário da fila Shopee antes dos writers, rodízio entre pedidos existentes, integridade/persistência R2, anti-duplicata e gates de curadoria. Não criar campanhas nem pedidos hipotéticos; registrar lacuna WordPress real.
3. Projeto de publicação LIVE: fluxo explícito de aprovação de conteúdo por post + URL da rota + canal + hashes/identidade; prévia, aprovação e publish separados; testar em simuladores/sem publicar; um LIVE real somente após aprovação explícita de post concreto e revisão factual.
4. CI, PR, merge, leitura independente dos blogs, limpeza de temporários e atualização do índice+JSON na main. Não repetir os posts 2990403416970116294 e 303.

## Status
- **FEITO**: JSON C65 prévia antes dos trabalhos.
- **PENDENTE**: cron programado, auditoria multi-site, gate LIVE, CI/PR, fechamento.
