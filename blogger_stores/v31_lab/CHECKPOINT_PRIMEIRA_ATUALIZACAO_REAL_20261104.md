# Checkpoint — primeira atualização real Shopee V23 → Loja Universal V31 R1 (LAB)

**Escopo:** somente LAB `blog teste tema worpress` (`blog_id=4739187376492839837`, `page_id=2446067640331732447`).

**Origem:** Shopee Affiliate API, scanner V23, seleção fresh em `SAFE_READY` às `2026-11-04T01:03:25Z`. Quatro categorias, 16 produtos únicos, 16 URLs de foto Shopee e 16 links afiliados gerados/validados; nenhuma reutilização de itens do LAB.

**Gates:**
- Scanner SAFE: run https://github.com/adelrib27/blogger-automation1/actions/runs/41751202914 — sucesso, artifact `13286500833`, selection SHA256 `46ef8a293875720f036d90430d1e57c862277b42bde966fbf34b15f9d2cb6c0c`.
- Preflight Blogger GET read-only: run https://github.com/adelrib27/blogger-automation1/actions/runs/41752570577 — sucesso. Original SHA256 `69936bbba975c45ef4aa35f3aeac09cd20eb7fa11ffb5e19117f81a9f1fecb76`; HTML candidato SHA256 `6f3810a364fe2114865b96fa5f118c10495bfe39943406624710ac9aaf25f450`.
- Backup persistente da página antes da publicação: `lab_backups/v31r1/loja_page_2446067640331732447_pre_first_shopee_live_20261104.html` nesta branch; conteúdo conferido igual ao snapshot de preflight. Há também backups temporários nos artefatos Actions.
- Primeira publicação controlada via GitHub Actions: run https://github.com/adelrib27/blogger-automation1/actions/runs/41753180692, em 2026-11-04 UTC (2026-11-03 America/Recife).

**Publicação Blogger observada:** página atualizada em `2026-11-03T22:19:09-03:00` pela API. Blogger Bridge GET confirmou 16 cards, 16 IDs únicos, 16 URLs de fotos Shopee, 16 URLs afiliadas e os marcadores V31 intactos. Novo primeiro item `20042293295` e antigo primeiro `52207212755` ausente. Runner permanece `0.8-v31r1-lab`, auditoria `AUDIT_OK`.

**Verificação pública independente:** Firecrawl `maxAge:0` retornou HTTP 200 e HTML com Tema V31 R1, um par de marcadores, 16 IDs de produto e 16 links afiliados *exatamente* iguais aos da seleção aprovada, 16 tags `<img>` com URL da Shopee e categorias preservadas. A exibição de cada foto em navegador ainda deve ser aceita visualmente; URLs HTML não garantem carregamento de todas as imagens.

**ALERTA IMPORTANTE:** o job de publicação terminou com **`failure`** após a gravação, porque o verificador HTTP público originado do GitHub Actions recebeu `HTTP 429 Too Many Requests` em 6 tentativas. A atualização real ocorreu; o estado de verificação *in-process* ficou inconclusivo. NÃO rerodar o workflow de escrita nem aplicar rollback automático. Próxima tarefa é validar e implementar uma rota de verificação pública confiável, separada da mutação, mantendo estado `PUBLISHED_PENDING_AUTONOMOUS_VERIFIER` até prova de sucessos por essa rota.

**Não ativado:** schedule de atualização diária da LOJA; provisionamento universal V31 em novos blogs. Ambas flags do Runner continuam `false`. Nenhum blog de produção, branch main ou workflow produtivo foi modificado.

**Conclusão rigorosa:** primeira publicação real = comprovada na API e no HTML público por fonte independente; automação integral diária = NÃO VALIDADA. Não promover para produção nem iniciar cron até validar verificação pública automática e persistência da rotação somente após sucesso.