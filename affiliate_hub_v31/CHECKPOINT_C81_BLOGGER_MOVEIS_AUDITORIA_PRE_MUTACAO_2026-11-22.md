# V31 C81 — Blogger Móveis para Cada Canto — auditoria pré-mutação (22/11/2026)

## Identidade e escopo
- Blog ID: `1439741542627895062`; URL: https://moveisparacadacanto.blogspot.com/
- Repo: `adelrib27/blogger-automation1`; branch `main`.
- Esta revisão se restringe ao blog Móveis para Cada Canto; não alterará sites WordPress, ARV/Pinterest, contas Cloudflare, D1, R2 nem política LIVE.

## Constatações por API Blogger autenticada (22/11/2026 ~14:46 UTC)
- LIVE: 3 artigos, previamente autorizados e enriquecidos. Imagens Shopee, CTA, rel sponsored e links internos presentes no HTML lido.
- DRAFT: 6 artigos; um é o canário assinado C81 ID `4106024906916105222`. **Não alterar nem publicar esse DRAFT, pois o HTML é vinculado a hash/assinatura.**
- Páginas institucionais: 0.
- Outros 5 DRAFTs legados: títulos de guias de compra, conteúdo semelhante; manter DRAFT e revisar editorialmente antes de qualquer LIVE.
- Preflight do Blogger Local Runner: indexação, HTTPS redirect, imagens lazy/WebP e descrição de pesquisa habilitadas; timezone America/Sao_Paulo. A ferramenta NÃO leu o texto atual da meta description, apenas a presença de configuração.

## GitHub / scheduler
- `V31_AUTODRAFT_ACTIVE=true`, `V31_AUTODRAFT_ROLLOUT_SITE=blogger_moveis_para_cada_canto`, `V31_AUTOLIVE_ACTIVE=false` aparecem em captura registrada pelo proprietário no checkpoint C81; não há leitura administrativa independente destas variables.
- Consulta REST à coleção Actions em 22/11/2026 (~14:47 UTC): último run `event=schedule` do workflow `V31 - fila editorial autônoma DRAFT` = #44998382196 de 07:28 UTC, antes da captura/ativação. #45028515776 foi `push` e só observação; portanto **cron escritor pós-ativação ainda não homologado**.
- CI prévio #45028436487 aprovou 565 testes; não repetir conversão, D1 ou publicação manual para simular cron.

## Plano de correção limitada
1. Preservar invariantes DRAFT / LIVE; não mudar o artigo canário nem os três LIVE comerciais.
2. Aplicar SEO seguro por Blog ID via Runner (descrição editorial já existente, nova descrição curta de pesquisa, HTTPS/indexação e horário; não editar robots personalizados).
3. Criar páginas institucionais úteis (Sobre, Transparência de afiliados, Política de Privacidade) apenas com informações verificáveis, nenhum contato pessoal inventado; verificar via GET. **Páginas não são novos artigos LIVE comerciais; nunca usar publish_post.**
4. Conferir configuração Blogger após a escrita e estado de novos DRAFTs sem recriar nada.
5. Manter como pendência externa de homologação uma execução `event=schedule` após ativação, com inspeção real do job, GET do Blogger, D1 e assinatura.

## Guardrails
- Nenhum `publish_post` de artigos, nenhuma ativação LIVE, nenhuma mudança de produto, link ou conteúdo assinado.
- Sem mudança de secrets, promoção de SKU, consumo de cotas, delete de posts/páginas, mudança de tema, ou writes em Cloudflare.
- Se uma edição falhar, registrar explicitamente o estado parcial e não repetir cegamente.
