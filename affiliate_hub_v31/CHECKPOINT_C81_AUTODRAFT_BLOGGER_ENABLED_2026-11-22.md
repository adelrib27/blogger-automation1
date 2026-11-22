# V31 C81 — Ativação DRAFT do primeiro blog (22/11/2026)

**Fonte da confirmação:** captura da tela de GitHub Settings → Actions → Variables enviada pelo proprietário. Essa confirmação é visual; o conector GitHub desta sessão não expõe leitura administrativa de Repository Variables. **Não confundir com execução bem-sucedida do escritor.**

## Configuração que aparece na captura

Na seção **Repository variables** de `adelrib27/blogger-automation1`:
- `V31_AUTODRAFT_ACTIVE=true`
- `V31_AUTODRAFT_ROLLOUT_SITE=blogger_moveis_para_cada_canto`
- `V31_AUTOLIVE_ACTIVE=false`
- `V31_AUTODRAFT_FULL_ROLLOUT_APPROVED` não aparece cadastrado.
- Outras variables `AUTOEVOLUTION_*` foram preservadas.

Trata-se de ativação limitada à **migração DRAFT do Blogger Móveis para Cada Canto**. O novo sistema V31 LIVE continua inativo. Não mexer nas flags antigas de Casa, Radar ou Oficina sem auditoria própria.

## Evidências técnicas anteriores

- [PR #124 MERGED](https://github.com/adelrib27/blogger-automation1/pull/124): migração de writer por site exato, controle `all` duplo, concorrência com writers universais antigos e dependências do scheduler.
- [CI SAFE 565 testes PASS](https://github.com/adelrib27/blogger-automation1/actions/runs/45028436487).
- [Pós-merge observação GET+SELECT PASS](https://github.com/adelrib27/blogger-automation1/actions/runs/45028515776): Blogger DRAFT `4106024906916105222` e WordPress DRAFT `321` intactos. Jobs `choose-one/draft/release/audit` skipped porque era evento push.
- O último `event=schedule` visto **antes da ativação** foi [#44998382196](https://github.com/adelrib27/blogger-automation1/actions/runs/44998382196), executado ainda em modo observação. Até o momento da captura e da inspeção subsequente, **não foi comprovada nenhuma execução `event=schedule` do writer após a nova configuração.**

## Próxima validação operacional

1. Reconsultar as execuções GitHub Actions do workflow `v31_autonomous_draft_scheduler.yml`, filtrando `event=schedule` **posteriores à configuração acima**.
2. Expectativa: `choose-one` deve selecionar exclusivamente `blogger_moveis_para_cada_canto`. `release` deve continuar `skipped` com `V31_AUTOLIVE_ACTIVE=false`.
3. Não considerar `workflow SUCCESS` como prova de um artigo novo: examinar `independent-verifier`, `deliver-draft`, os logs sem segredos, D1 e GET autenticado do Blogger.
4. Se houver nova oferta segura: comprovar SKU inédito, link da campanha, imagem, aviso afiliado, link interno, assinatura, HTML SHA, D1 READY→USED, ID de DRAFT e replay idempotente.
5. Se sair `NO_NEW_OFFER`, `quota` ou fonte insuficiente, **não forçar** conversão, inventar evidência, repetir SKU piloto, nem desligar o fail-closed. Catálogo atual tem apenas dois perfis específicos por site; pode não existir produto adicional pronto.
6. Em falha importante do novo writer ou risco de duplicação, primeiro verificar CMS/D1; para impedir futuros ciclos alterar somente `V31_AUTODRAFT_ACTIVE=false` no repositório.
7. Depois de homologar nova recorrência no Blogger, resolver coexistência com cron LIVE legado Casa antes de qualquer rollout WordPress. Nunca ligar `V31_AUTOLIVE_ACTIVE` sem autorização da política.

Nenhuma mutação D1/R2/CMS/Shopee e nenhum teste manual de publicação foi realizado para salvar este documento.
