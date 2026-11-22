# V31 C92 — Estado auditável após PR #129: canário E2E DRAFT de data única

**Horário do checkpoint:** 22/11/2026, após merge em `main` SHA `17dff4c3447aa349475e4833b167f71608421d57`.
**Status:** código e workflow programados, **sem afirmar ainda entrega de novo DRAFT**. V31 LIVE permanece desativado.

## Validações efetivamente concluídas
- PR #127 MERGED, CI #45056671904: 583 testes PASS, extração de identidade exata Buriti/Marabá 1.6/Viena/Master/Áurea, rejeição de descritor genérico, verificação de 6 portas + 4 gavetas em fabricante; não inventa material quando fonte não informa.
- PR #128 MERGED, CI #45057224963: 585 testes PASS. `site_request_queue.py` oferece modo de SKU único após leitura autenticada de histórico Blogger/WordPress, campanha e `V31_AUTODRAFT_ROLLOUT_SITE` corretas, reserva atômica na D1, gravação/R2 com readback, bloqueio de duplicatas, orçamento global Shopee 3/dia UTC.
- PR #129 MERGED, CI #45057541081: **588 testes PASS** e self-tests Casa 24/24, Oficina 21/21, Radar 15/15, cross-blog PASS.
- Workflow de data única instalado na `main`: `.github/workflows/v31_c92_buriti_one_time_e2e.yml` com cron `23 0 23 11 *` = 2026-11-23 **00h23 UTC** (2026-11-22 **21h23 Recife**). Gate de data UTC 2026-11-23 impede execução em outro ano/dia; exige `V31_AUTODRAFT_ACTIVE=true`, `ROLLOUT_SITE=blogger_moveis_para_cada_canto`, `V31_AUTOLIVE_ACTIVE!=true`, full rollout não habilitado. Apenas `shopee:1235923910:19299550912` Buriti, uma reserva Shopee, R2 readback, depois reusable DRAFT (histórico CMS, fabricante/Firecrawl, revisão HMAC/Ed25519, R2 envelope, D1 READY/USED, GET/replay). **NÃO contém release LIVE.**
- Canário anterior C89 #45055648381 provou histórico CMS e assinaturas, mas `NO_NEW_OFFER` porque três perfis com link já estavam no Blogger. 0 DRAFT novo, 0 LIVE.
- Auditoria read-only #45055951437: 9 posts/drafts Blogger na época, 10 perfis de fabricante, 3 com link já no CMS, 7 aguardavam conversão. Buriti SKU acima ainda não tinha URL convertida para campanha segundo R2.
- Workflow diário conversor #45056332000 já executou em 22/11: `converted=1`, `shopee_mutation_attempts=1`, `r2_snapshot_saved_and_verified=true`, `publication_calls=0`, e duas reservas negadas pela cota. A consulta direta D1 confirmou slots 1 Cadeira, 2 Ar Condicionado, 3 Móveis SKU `shopee:1235923910:18799312789` (Viena). **Não executar nova conversão Shopee antes do dia UTC seguinte**.
- As fontes oficiais acessíveis ao Buriti: `https://www.santosandira.com.br/produto/guarda-roupa-buriti-6-portas/`, título modelo e marca, 04 gavetas, 02 portas MDF ripadas como subconjunto de 06 portas; fotografia, metadados e produto exato ainda serão verificados pelo writer real antes de qualquer DRAFT.

## Gate do próximo run
1. Inspecionar se workflow `V31 C92 - converter Buriti uma vez e homologar DRAFT` foi disparado em 2026-11-23 UTC. O cron é administrado pelo GitHub e pode atrasar; a data do run não é comprovante de entrega.
2. Se job `exact-buriti-conversion` tiver `conversion_ready=true`, checar D1 tentativa SKU e R2 link exato, depois subjob `independently-verify-and-deliver-draft`, `independent-verifier` e `deliver-draft` por logs sem segredos.
3. Após DRAFT, confirmar post Blogger via GET ADMIN e HTML hash byte-identical em dois replays, idempotência, D1 USED. Exigir imagem real CSV, aviso de afiliado, link de campanha, link interno verificado, SEO e assinatura; NÃO confundir verde do Actions com artigo entregue.
4. Se o script falhar por `NO_NEW_OFFER`, cota, fonte exterior inconsistente, URL redirecionada ou link expirado, ficar fail-closed. Não inventar evidência, nunca repetir SKU usado.
5. Não promover `V31_AUTOLIVE_ACTIVE` para `true` nem ligar `all`. WordPress Casa ainda tem cron LIVE legado que requer reconciliação.

## Próximo plano de expansão
- Após **prova REAL de novo DRAFT** no Blogger, habilitar recorrência semanal/diária de reposição com prioridade SKUs verificáveis, com teto global D1 e proteção CMS; preservar outros blogs, Pinterest, Vida Pet e ARV.
- Em seguida, resolver o cron legado WordPress Casa antes de migração da sua rota DRAFT; homologar SEO/links internos/imagens e 1 novo DRAFT no WordPress.
- Só após observação e evidência 2 plataformas propor aprovação ÚNICA da política LIVE nova. O usuário não precisa aprovar artigo por artigo.

**Rollback operacional:** se ocorrer erro relevante, colocar Repository Variable `V31_AUTODRAFT_ACTIVE=false` e revalidar D1/CMS antes de qualquer retry; nunca apagar snapshots/rascunhos para “limpar fila”.

## Correção final de pré-homologação com Firecrawl real — PR #130
- Antes de usar cota Shopee adicional, executei uma pesquisa Firecrawl com a mesma consulta do verificador: `Santos Andirá Buriti guarda-roupa`; o resultado #1 foi a URL oficial `https://www.santosandira.com.br/produto/guarda-roupa-buriti-6-portas/`.
- O scrape Firecrawl real maxAge=0 retornou HTTP 200, metadata `title=Guarda-Roupa Buriti 6 Portas – Santos Andirá`, `url/sourceURL` exatas e conteúdo com título H2 após **11 imagens de galeria**. A seção do produto informa 04 gavetas, 02 portas MDF ripadas como subconjunto do modelo 06 portas, e demais características. Não houve publicação neste teste.
- Esse formato revelou defeito antes de gastar quota: o código anterior encontrava o primeiro token `buriti` dentro da URL de imagem e considerava as primeiras cinco linhas como heading, causando reprovação falsa. Corrigido em [PR #130 MERGED](https://github.com/adelrib27/blogger-automation1/pull/130), merge SHA `a9191a841dfaf21e166ca6a97204e5a17d6eb584`: remover links/imagens no Markdown, localizar H1/H2/H3 de produto exato, limitar o escopo ao artigo antes de rodapé, validar números a partir do heading real.
- [CI #45058125770](https://github.com/adelrib27/blogger-automation1/actions/runs/45058125770): **591 testes PASS**, regressões WordPress e cross-blog PASS. Testes adversariais recusam fatos tirados apenas da galeria/rodapé, sem tocar recursos remotos.
- O canário de data única do PR #129 continua configurado; utilizará automaticamente o código PR #130 porque foi integrado à `main` antes de 23/11 UTC. **A entrega do DRAFT ainda não está comprovada; somente o agendamento foi instalado e a pré-validação das fontes foi concluída.**
