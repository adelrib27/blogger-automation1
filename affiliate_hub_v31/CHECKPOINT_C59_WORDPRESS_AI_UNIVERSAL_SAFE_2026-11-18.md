# V31 C59 — Workers AI UNIVERSAL WordPress: plano/CTA JSON e corpo HTML (checkpoint intermediário)

**Fase:** C59 EM_ANDAMENTO, atualização de 18/11/2026. **Não declarar LIVE testado nem migrado plenamente até resultado do canário em execução.**

## Continuidade da C58
- [C58 checkpoint](CHECKPOINT_C58_AUDITORIA_UNIVERSAL_ARTIGOS_WP_BLOGGER_2026-11-18.md), [PR #75](https://github.com/adelrib27/blogger-automation1/pull/75) MERGED: Python import, links internos de posts WP reais e permalinks WordPress/Blogspot corretos; [CI 347](https://github.com/adelrib27/blogger-automation1/actions/runs/44407154200) PASS.
- [R2/WordPress/AI C58 44407697822](https://github.com/adelrib27/blogger-automation1/actions/runs/44407697822) SUCCESS: 9/6/15 produtos aprovados com imagem real e link da campanha exata Casa/Oficina/Radar, piloto Casa 6 posts WP reais, 8 parágrafos originais/537 palavras, 2 links internos + foto+CTA, **0 posts, 0 conversões e 0 writes**.

## Entregas C59 no GitHub
- [PR #76](https://github.com/adelrib27/blogger-automation1/pull/76) **MERGED** commit `2f3c6b6afa888bfa5531bef68dde2de2d8d130fe`: cliente universal `affiliate_hub_v31/wordpress_ai.py` e migração dos 3 geradores WordPress Casa, Oficina e Radar para modelo Workers AI `@cf/meta/llama-3.3-70b-instruct-fp8-fast`; JSON schema para título/palavra-chave/plano e CTA; corpo HTML segue quality gate próprio de cada WP; preserva quarentena/limites da publicação. [CI #44408847744](https://github.com/adelrib27/blogger-automation1/actions/runs/44408847744) **353 V31 +24 Casa +21 Oficina +crossblog PASS**.
- [Canário real #44409264710](https://github.com/adelrib27/blogger-automation1/actions/runs/44409264710) **FAILED com segurança ANTES de qualquer POST**: Cloudflare devolveu um título de 22 caracteres, abaixo da faixa obrigatória 35–65; `make_plan` bloqueou como deveria.
- [PR #77](https://github.com/adelrib27/blogger-automation1/pull/77) **MERGED** commit `21bcd5a0c380be432d986450e844bbe2141323a9`: até 3 tentativas de planejamento JSON após erro de validação, com feedback, sem relaxar regra ou inventar título. `raw` explícito continua sem IA/retry. [CI #44409860381](https://github.com/adelrib27/blogger-automation1/actions/runs/44409860381) **356 V31 +24 Casa +21 Oficina +crossblog PASS**.
- [Segundo canário real C59 #44410047121](https://github.com/adelrib27/blogger-automation1/actions/runs/44410047121) **EM EXECUÇÃO no último registro**: seleciona SKU real Casa na campanha correta do R2, gera plano JSON, artigo HTML + CTA com cliente novo, verifica quality gate, 2 links internos, foto real/afiliação; **nenhum WordPress POST**. Inspecionar `fetch_workflow_run_jobs` e logs antes de fazer qualquer afirmação de conclusão.
- **Temporários ativos até decisão final:** `.github/workflows/v31_c59_wp_real_ai_safe_once.yml` e `affiliate_hub_v31/C59_WP_AI_REAL_ONCE_TRIGGER.txt`. Remover da `main` após PASS ou após registrar bloqueio/falha com causa.

## Próximas ações inequívocas
1. Verificar run **44410047121** até conclusão; se falhar, ler erro e corrigir sem liberar qualidade; reexecutar só teste SAFE.
2. Confirmar permissão de modelo e formato em Workers AI com exemplo real, e homologar verificações no WordPress. Nenhum post novo sem autorização separada.
3. Se PASS, remover workflow+trigger temporários; atualizar este documento e `CONTINUIDADE_ESTADO.json` para fase concluída e registrar estado dos 3 WordPress.
4. Próxima fase C60: fechar integração **qualquer WordPress futuro**, incluindo `site_requests.d`, credenciais/site reais e rascunho seguro, sem presunção de três sites fixos; observar próxima execução dos crons LIVE pré-existentes e detectar falhas sem desativar gates.
5. Runner tema #70 foi adiado pelo proprietário. Blogger Móveis 3/3 já LIVE, não criar quarto.

**Nenhum dado sensível ou token deve entrar em checkpoints e logs.** 


## C59 conclusão comprovada na MAIN (adendo)

- [x] [**Run C59 real 44410047121 — SUCCESS**](https://github.com/adelrib27/blogger-automation1/actions/runs/44410047121). WordPress piloto **Casa e Decoração**: produto autorizado R2, chamada REAL Llama com plano JSON estruturado, artigo HTML real original de **743 palavras**, `quality= DRAFT_READY`, imagem CSV HTTPS, link Shopee da campanha exata, CTA e 2 links internos reais de publicações WordPress; **0 WordPress posts, 0 Shopee mutations, 0 R2 writes**. A primeira falha de título curto do run #44409264710 foi corrigida pelo PR #77 sem relaxar quality gate.
- [x] Workflows temporários `v31_c59_wp_real_ai_safe_once.yml` e `C59_WP_AI_REAL_ONCE_TRIGGER.txt` **removidos** após SUCCESS.
- [x] Safe workflows originais disparados via kickoffs reais em `main`: primeira rodada Casa [44410470835](https://github.com/adelrib27/blogger-automation1/actions/runs/44410470835) e Oficina [44410482290](https://github.com/adelrib27/blogger-automation1/actions/runs/44410482290) falharam apenas na importação do núcleo universal em **`publish_generated.py`** depois de concluírem o gerador OFF. Radar [44410496620](https://github.com/adelrib27/blogger-automation1/actions/runs/44410496620) **SUCCESS**.
- [x] [**PR #78 MERGED**](https://github.com/adelrib27/blogger-automation1/pull/78) corrigiu imports em publicadores Casa/Oficina, mantendo status `LIVE_ENABLED=false` nos testes. [CI 44410794453](https://github.com/adelrib27/blogger-automation1/actions/runs/44410794453): **357 V31+24 Casa+21 Oficina+crossblog PASS**.
- [x] Repetição **REAL dos workflows SAFE existentes**: [Casa 44410965031](https://github.com/adelrib27/blogger-automation1/actions/runs/44410965031) **SUCCESS**, [Oficina 44410976595](https://github.com/adelrib27/blogger-automation1/actions/runs/44410976595) **SUCCESS**, [Radar 44410496620](https://github.com/adelrib27/blogger-automation1/actions/runs/44410496620) **SUCCESS**. Não publicaram artigos; isso valida os gates e imports do fluxo real em modo seguro.
- [x] Run de qualidade Radar LIVE anterior **foi QUARENTENA** por `alegacao_de_acessibilidade_nao_sustentada` — resultado protetivo esperado, não foi alterado nem forçado.

**C59 CONCLUÍDA** quanto à migração de IA WordPress, cliente universal, regressões, canário R2/AI/WordPress sem publicação e três workflows SAFE. Próxima fase **C60**: construir o caminho universal de rascunhos WordPress para QUALQUER site registrado, distinto dos três blogs legados com writers próprios. Para novos WordPress será indispensável identidade/credenciais reais da instalação; não inventar senhas ou domínios. Eventos futuros dos cron LIVE já existentes ainda necessitam observação posterior; o teste SAFE não equivale a autorização nem comprovação de nova publicação automática.
