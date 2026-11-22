# V31 C81 — Preview de engenharia para implantação DRAFT gradual (22/11/2026)

**Estado:** em andamento, registrado antes do código. **Não é autorização para ligar publicadores, LIVE ou consumo adicional de cotas.**

## Problema comprovado no código existente
- `v31_autonomous_draft_scheduler.yml` aceita `vars.V31_AUTODRAFT_ACTIVE == 'true'` e faz rodízio por todos os perfis habilitados, sem limite de implantação de um único blog.
- `site_request_queue.autonomous_sites_for_writes()` retorna TODOS os perfis cadastrados quando a variável global é `true`; os writers legados Blogger e WordPress consultam essa mesma função para retirar blogs migrados de sua própria rotação.
- `v31_universal_blogger_autodraft_daily.yml` e `v31_universal_wordpress_autodraft_daily.yml` não possuem variável de rollout por rota. Portanto a ativação global pode alterar de imediato ambas as plataformas e dificultar diagnóstico de idempotência.
- Observações schedule #44924334792, #44953910353, #44998382196 foram PASS SOMENTE LEITURA; criação recorrente de novos DRAFTs permanece sem prova. A política LIVE nova está pendente. Há escritores LIVE legados independentes (Radar e Oficina) que precisam de trilhas de segurança próprias.

## Correção proposta, sem tocar secrets nem ativação
1. Introduzir `V31_AUTODRAFT_ROLLOUT_SITE` como opt-in de migração por blog. `V31_AUTODRAFT_ACTIVE=true` sem alvo válido **não libera qualquer rota nova**. A função de seleção deve retornar o conjunto apenas de sites registrados, habilitados e com perfil verificador.
2. Para expansão posterior, a opção literal `all` só poderá valer se `V31_AUTODRAFT_FULL_ROLLOUT_APPROVED=true` estiver **também** configurada. Sem isso, nenhuma transferência em massa.
3. O scheduler deve usar a mesma função de migração que os writers legados, e passar as variáveis aos dois workflows legados; não confundir o `workflow_dispatch` de teste explícito com ativação agendada. Em modo sem rota válida, manter observação read-only, não tentar escrita.
4. Provas em CI offline: sem flags, sem alvo, alvo inválido, um blog, ALL sem aprovação, ALL aprovado, preservação de writers legados não migrados e status LIVE bloqueado. Não chamar CMS, Cloudflare, Shopee, Firecrawl.
5. Quando o Work puder administrar GitHub Variables: ativar primeiro somente uma rota; GET CMS + título/HTML SHA + D1 USED + replay de mesmo ID; observar schedule real, depois outra rota. Não executar publicações LIVE até aprovação explícita de política.

**Estado inicial:** `main` no commit `b4e296a0336feff321f6fefd160b7ce639f9d372`. Preview documentado somente; primeiro PR/CI deve confirmar segurança antes de merge.

## PR #124 — implementação integrada e CI

- [PR #124 MERGED](https://github.com/adelrib27/blogger-automation1/pull/124) na `main`, merge `1cb0ea75e21dbe04664c1f6101f1f22e406487f3`. Nenhuma variável do GitHub ou publicação CMS foi ativada.
- [Actions #45028436487](https://github.com/adelrib27/blogger-automation1/actions/runs/45028436487) **SUCCESS**, `565 tests ... OK`, regressões Casa 24/24, Oficina 21/21, Radar 15/15, cross-blog PASS. 5 novos testes offline de rollout.
- `site_request_queue.autonomous_sites_for_writes` só retorna migração quando `V31_AUTODRAFT_ACTIVE=true` **E** `V31_AUTODRAFT_ROLLOUT_SITE=<site_key exato e habilitado>`. O literal `all` requer ainda `V31_AUTODRAFT_FULL_ROLLOUT_APPROVED=true`. Sem site, nenhuma migração.
- O cron novo em `v31_autonomous_draft_scheduler.yml` permanece em `observe-homologation` quando não existe alvo explícito válido; `choose-one` só escolhe as rotas permitidas pela função compartilhada. Disparo manual exige seleção explícita de um site registrado, sem habilitar cron global.
- Writers legados universais Blogger/WordPress recebem as mesmas variáveis de rollout e só excluem as rotas realmente migradas. O workflow reutilizável do verificador divide a trava `v31-editorial-catalog-single-writer` com os escritores universais para prevenir colisão na transição.
- A etapa de seleção `choose-one` agora instala explicitamente suas dependências Python; antes podia tentar importar `boto3` e `cryptography` em runner não preparado.
- **Limites conhecidos:** a evidência CI comprova código e regras de entrada, não uma execução agendada com a variável ativada nem DRAFT recorrente. A função migratória considera somente perfis configurados (atualmente Blogger Móveis e WordPress Casa), não torna outros blogs automaticamente homologados.
- **Gatilhos remotos NÃO alterados**: `V31_AUTODRAFT_ACTIVE` e `V31_AUTODRAFT_ROLLOUT_SITE` continuam sujeitos à administração GitHub/Work. `V31_AUTOLIVE_ACTIVE` não foi ligado.
- Antes do primeiro rollout, validar crédito Firecrawl, dia UTC da quota, histórico CMS e proteção de escritores legados. Verificar que somente `blogger_moveis_para_cada_canto` é migrado inicialmente, depois auditar schedule e novo DRAFT por GET/replay. Não habilitar `all` sem evidência e autorização apropriadas.

## Auditoria complementar do D1 oficial e colisão de CMS (22/11)

- Consulta somente leitura pela conexão Cloudflare oficial `adeiltonrib27@gmail.com` / D1 `v31-universal-ready-safe` confirmou 5 tabelas V31. Por `site_key+campaign+status`, há Blogger Móveis **USED=1**, WordPress Casa **USED=1**, **READY=1**. O READY adicional do WordPress não foi consumido e deve ser preservado.
- A consulta às cotas D1 com `day_utc >= '2026-11-21'` mostrou registros de 21/11 (Blogger HTTP 1/3, SEARCH 1/3; WordPress HTTP 3/3, SEARCH 3/3), e **nenhuma linha ainda para 22/11 no momento do SELECT**. Ausência de registro não é prova de que pesquisas ou conversões futuras foram executadas; reconsultar imediatamente antes do writer.
- Conversões registradas pelo D1 no dia 21/11: duas tentativas WordPress Casa e uma Blogger Móveis. Não repetir SKU/conversão por inferência.
- `.github/workflows/casa_editorial_generate_schedule.yml` está **agendado 3x/dia** e executa para `wordpress_casa_decoracao` com `CASA_WORDPRESS_STATUS=publish` e `CASA_LIVE_PUBLISH_ENABLED=true`, em grupo de concorrência `casa-decoracao-editorial-v3`, **diferente** da trava `v31-editorial-catalog-single-writer`. Portanto a migração da rota WordPress exige auditoria explícita de coexistência/reconciliação com o writer LEGADO LIVE; este PR não o desativa nem afirma ausência de LIVE legado.
- `radar_editorial_vnext_autonomous.yml` também possui LIVE legado habilitado, com falhas de QUARENTENA. Não alterar essa rota durante o rollout de Blogger Móveis.
- **Primeiro alvo recomendado** continua `blogger_moveis_para_cada_canto`. Caso a verificação no CMS mostre outro writer independente ativo para esse mesmo blog, abortar a transferência até corrigir o conflito.

## Verificação pós-merge da nova sintaxe do workflow

- A mudança da configuração do scheduler disparou o [run GitHub Actions #45028515776](https://github.com/adelrib27/blogger-automation1/actions/runs/45028515776), `event=push`, **SUCCESS** no novo código.
- O job `observe-homologation` confirmou novamente por GET e SELECT os mesmos IDs/hash dos dois DRAFTs, sem alterações remotas. Jobs `choose-one`, `draft`, `audit` e `release` ficaram **skipped**. Isto comprova que o workflow pós-merge é parseado/executa e continua em observação fail-closed; **não comprova criação de novo DRAFT recorrente**.
- [Diagnóstico de continuidade #45028879006](https://github.com/adelrib27/blogger-automation1/actions/runs/45028879006) **SUCCESS** após atualização do índice/estado.
