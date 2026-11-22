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
