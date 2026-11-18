# Instruções de continuidade — V31 e rede Blogger legada

**Este repositório contém dois históricos operacionais diferentes.** A rede Blogger legada usa `CHECKPOINT_ATUAL.md` (2/11/2026); o **V31 Hub Editorial Shopee — Blogger & WordPress** usa o índice próprio [`V31_CONTINUAR_AQUI.md`](V31_CONTINUAR_AQUI.md). Não substituir nem misturar essas fontes.

## Para qualquer solicitação relativa ao V31

1. **ANTES de programar ou executar**, ler da `main`: `V31_CONTINUAR_AQUI.md` → `affiliate_hub_v31/CONTINUIDADE_ESTADO.json` → arquivo `checkpoint_detail` → [issue #54](https://github.com/adelrib27/blogger-automation1/issues/54).
2. Se `continuity_status` ou `active_work.status` for `EM_ANDAMENTO`, retomar pelo `latest_verified_step` e inspecionar as mutações existentes para não repetir Blogger POST/Shopee/R2.
3. Salvar **prévia em commit** no `CONTINUIDADE_ESTADO.json` antes de trabalho longo, atualizar durante cada marco e registrar fechamento; seguir [`CONTINUIDADE_PROTOCOLO.md`](affiliate_hub_v31/CONTINUIDADE_PROTOCOLO.md).
4. Usar evidência verificável por repositório, API, Workflow e R2. Se um teste for offline ou somente preview, **não afirmar** que postagem, deploy, cron ou conversão real ocorreu.
5. Manter o V31 **UNIVERSAL**: os dois CSVs constituem biblioteca de todos os nichos, independente de blogs presentes/futuros; só selecionar produto por tema/campanha real quando o proprietário definir o blog. Respeitar revisão e veto por origem.
6. Cada artigo afiliado comercial deve associar o SKU correto, imagem REAL do CSV/R2, link da campanha correta, palavra-chave, CTA Shopee, transparência, links internos existentes e conteúdo original. Nunca inventar preço/venda/estoque.
7. Não ativar LIVE, Pinterest ou publicar artigos adicionais sem autorização. Em particular, o blog `blogger_moveis_para_cada_canto` recebeu pedido **de três artigos** e já possui três LIVE; o quarto exige pedido novo. Criação de rascunhos não é autorização automática de publicação.
8. Mudança de tema do Blogger Local Runner foi adiada pelo proprietário; PR #69 é laboratório não implantado no Windows.

**Para a rede legada**, seguir o `CHECKPOINT_ATUAL.md` do Blogger e seu guard; esta instrução V31 não altera os 18 blogs legados.

**Limitação real:** um agente novo não recebe automaticamente o conteúdo desta conversa. É necessário efetivamente abrir os arquivos do GitHub; este arquivo facilita a descoberta por agentes que leem a raiz do repositório.
