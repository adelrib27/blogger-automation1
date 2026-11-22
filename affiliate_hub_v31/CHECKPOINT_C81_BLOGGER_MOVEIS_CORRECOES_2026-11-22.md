# V31 C81 — Correções reais do Blogger Móveis para Cada Canto (22/11/2026)

**Blog ID:** `1439741542627895062` · https://moveisparacadacanto.blogspot.com/  
**Execução:** leitura/escrita reais pela Blogger API v3 e Blogger Local Runner, 22/11/2026 (hora Recife ~11h46–11h51).  
**Preview anterior:** [auditoria pré-mutação](CHECKPOINT_C81_BLOGGER_MOVEIS_AUDITORIA_PRE_MUTACAO_2026-11-22.md).

## Diagnóstico inicial comprovado
- 3 artigos `live`: IDs `361914172841959603`, `3460803458877796795`, `5467343028388246916`.
- 6 artigos `draft`, inclusive canário assinado C81 `4106024906916105222` (**inalterado**).
- 0 páginas institucionais.
- Os três LIVE possuíam imagem do SKU, links Shopee, disclosure e `rel="sponsored nofollow ..."`, além de links internos. Nenhuma troca de SKU/campanha era necessária.
- Os 5 DRAFTs legados partilham estrutura de guias genéricos e demandam revisão de originalidade antes de qualquer publicação; não foram modificados.
- O Blogger Local Runner preflight confirmou visibilidade para busca, redirecionamento HTTPS, lazy loading/WebP, descrição de pesquisa ativada, e fuso horário São Paulo; robots customizados OFF.

## Mudanças realmente realizadas
1. **Configuração SEO no Blogger:** `configure_settings` status `SETTINGS_PROFILE_VALIDATED`; descrição longa editorial mantida e meta descrição curta definida: “Guias para escolher sofás, guarda-roupas, mesas e móveis para cada ambiente, com medidas, materiais, organização e dicas de compra consciente.” Foram preservados HTTPS, indexação, lazy images, WebP, timezone e robots customizados.
2. **Novas páginas publicadas via Blogger API e verificadas por GET individual:**
   - `880296422528540850` [Sobre o blog](https://moveisparacadacanto.blogspot.com/p/sobre-o-moveis-para-cada-canto.html)
   - `4353966172029848498` [Transparência comercial e links de afiliados](https://moveisparacadacanto.blogspot.com/p/transparencia-comercial-e-links-de.html)
   - `5725767004918622546` [Política de Privacidade](https://moveisparacadacanto.blogspot.com/p/politica-de-privacidade.html)
   - Novo `list_pages`: 3/3 status `live`. Não foram criados novos **artigos** LIVE.
3. **Navegação institucional adicionada aos três artigos LIVE já existentes**, preservando todo o HTML original e anexando uma seção com links às três páginas. Atualização via `update_post` e GET posterior confirmou `data-v31-institutional-nav="20261122"`, três URLs institucionais e status `live` nos três IDs, sem remoção dos links de afiliados ou imagens. Links comerciais permanecem `rel="sponsored nofollow ..."`.
4. **Não houve alteração dos seis rascunhos.** GET do canário assinado `4106024906916105222` confirma `status=draft`, `data-v31-evidence-revision`, e a data de atualização anterior. Contagem após alterações: **3 LIVE / 6 DRAFT / 3 páginas LIVE**.

## GitHub scheduler — pendência de execução ainda não comprovada
- No momento da auditoria, coleção Actions retornou #44998382196 como o último `event=schedule` do workflow `V31 - fila editorial autônoma DRAFT`, iniciado em 22/11 07:28 UTC (antes da configuração visível do proprietário). #45028515776 é `push`, não escrita agendada.
- A captura do proprietário indica Repository Variables `V31_AUTODRAFT_ACTIVE=true`, `V31_AUTODRAFT_ROLLOUT_SITE=blogger_moveis_para_cada_canto`, `V31_AUTOLIVE_ACTIVE=false`. O conector deste chat não pode reler/escrever variables administrativas.
- O cron no YAML é `47 */4 * * *` UTC. O próximo horário nominal após a captura (~13:59 UTC) é **16:47 UTC / 13:47 Recife** em 22/11, com possível atraso do GitHub. **Não afirmar que essa execução já aconteceu.**
- Próxima validação: `event=schedule` efetivo após a ativação; job `choose-one` seleciona só Blogger Móveis; `release` skipped; `draft` gera novo ID com SKU elegível ou falha de modo explícito `NO_NEW_OFFER`/quota/source; cruzar D1, Blogger GET, HMAC, hash de HTML e idempotência. Não forçar publicação ou conversão para “fazer passar”.

## Pendências que permanecem (não simular conclusão)
- **Navegação de homepage:** verificar se o tema possui gadget `Páginas/PageList` ativo e se mostra as 3 páginas; nenhuma ferramenta conectada aqui edita a aba Layout do Blogger. Links foram adicionados aos 3 artigos públicos para assegurar descoberta dentro do conteúdo.
- **Contato e solicitações de privacidade:** não inventar e-mail/dados pessoais; canal oficial depende de informação fornecida pelo proprietário e validação jurídica/operacional.
- **Cinco rascunhos legados** exigem revisão editorial/originalidade/checagem de produto e fontes antes de qualquer publicação; preservar assinaturas, histórico e os 6 DRAFTs.
- **Recorrência C81:** ainda exige nova execução schedule real pós-ativação, com GET e D1; não considerar CI PASS nem push PASS como prova de produção.
- **LIVE automático V31:** `false` e não autorizado. Nenhum `publish_post` foi chamado nesta execução.
- A política de privacidade é descritiva e geral; confirmar posteriormente quais serviços de analytics/anúncios/cookies são usados antes de tratá-la como texto jurídico final.

## Integridade e isolamento
- 3 páginas novas e 3 posts LIVE existentes atualizados; 0 novos artigos LIVE, 0 exclusões, 0 alterações em DRAFT, D1, R2, Shopee, GitHub Variables ou outros blogs.
- Nenhum tema foi instalado; o Runner restringe adoção V31 a outros blogs/laboratórios, logo não se forçou a instalação para Móveis.
- Se houver discrepância, use os IDs exatos acima para GET antes de qualquer retry. Não recriar páginas ou posts já existentes.
