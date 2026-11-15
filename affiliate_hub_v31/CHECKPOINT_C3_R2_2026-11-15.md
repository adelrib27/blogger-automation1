# C3 — Cloudflare R2 privado criado (15/11/2026)

**Código de continuidade:** `V31-EDITORIAL-C3-R2-PRIVATE-20261115-CREATED`

## Escopo
Projeto **V31 Hub Editorial Shopee — Blogger & WordPress**, excluindo Pinterest. A implementação está isolada no PR draft [#52](https://github.com/adelrib27/blogger-automation1/pull/52), sem publicações LIVE.

## Fatos verificados pela API Cloudflare
- Conta Cloudflare selecionada pelo proprietário na captura da ativação R2 (a conta conectada ao projeto).
- Assinatura R2 ativada pela interface, com cobrança inicial de US$ 0; **excedentes podem ser cobrados**.
- Bucket `v31-editorial-shopee` **criado pela API**, operação com `success=true`.
- Releitura via API `GET /accounts/{account_id}/r2/buckets/{bucket_name}`: nome `v31-editorial-shopee`, classe **Standard**, região retornada `ENAM`, jurisdição `default`.
- Domínios personalizados: nenhum. Domínio público gerenciado `r2.dev`: **disabled**.
- Nenhum arquivo, snapshot ou produto foi carregado para esse bucket nesta etapa. Não confundir bucket criado com catálogo persistido.

## Próxima etapa obrigatória — credenciais de acesso S3 compatível

Criar no Cloudflare R2 um **API token de leitura e gravação de objetos**, com escopo **apenas para o bucket** `v31-editorial-shopee`:
1. Cloudflare Dashboard → Storage & databases → R2 → Overview → API Tokens → Manage → Create API token.
2. Permissão: `Object Read & Write`. Escopo: `Apply to specific buckets only` → `v31-editorial-shopee`.
3. Copiar os valores **uma única vez**, somente para o GitHub Environment `v31-editorial-safe`; **não colar no chat**, README, logs ou GitHub Issues:
   - Secret `V31_EDITORIAL_R2_ACCESS_KEY_ID`
   - Secret `V31_EDITORIAL_R2_SECRET_ACCESS_KEY`
4. Cadastrar também no mesmo Environment, como **variables** (não secrets):
   - `V31_EDITORIAL_R2_ACCOUNT_ID`: ID da conta Cloudflare exibido no painel (não gravar o ID público nos arquivos do repositório)
   - `V31_EDITORIAL_R2_BUCKET`: `v31-editorial-shopee`

Referência Cloudflare: https://developers.cloudflare.com/r2/get-started/s3/

## Limites e controles
- O projeto deve guardar catálogo, categorias, links convertidos e histórico de pautas; **não armazenar imagens da Shopee**.
- Planejamento para aproximadamente **50 blogs** com 1–2 artigos/dia; isso não implica 50 contas nem 50 buckets R2.
- A classe **Standard** possui franquia mensal e cobrança por excedentes. Uso efetivo e retenção de snapshots precisam ser monitorados para não gerar custos inesperados.
- Restringir o GitHub Environment `v31-editorial-safe` às branches revisadas, idealmente `main` no momento apropriado. Atualmente o PR permanece draft; não efetuar merge automaticamente.
- A chave App Secret Shopee anteriormente exibida em uma captura deve ser rotacionada, sem interromper os fluxos que a compartilhem.

## Validações que ainda NÃO ocorreram
- Nenhum acesso S3 compatível com credencial do GitHub Actions.
- Nenhuma gravação/leitura de snapshot ou restauração REAL.
- Nenhuma importação persistente dos dois feeds reais (a leitura temporária dos 110 mil foi aprovada no C2.1).
- Nenhuma conversão comercial REAL nem publicação Blogger/WordPress.
- Não existe garantia operacional de custo zero até confirmar uso e política de retenção.

## Próximo checkpoint
Após cadastro e validação do token restrito ao bucket, executar um teste **somente de escrita/leitura/remoção de um pequeno objeto de diagnóstico**, sem dados comerciais, e verificar permissões/integração GitHub Actions antes de ingerir os feeds. Depois: primeira importação do catálogo real, teste do conversor e integração dos adaptadores em modo SAFE.
