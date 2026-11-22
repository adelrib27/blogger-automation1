# V31 C101 — Correção concluída: duas Lojas restauradas e Móveis publicado

**Data:** 22/11/2026 (America/Recife)  
**Repositório:** `adelrib27/blogger-automation1`, branch `main`.  
**Checkpoint anterior:** `affiliate_hub_v31/CHECKPOINT_C101_ROLLBACK_2_LOJAS_2026-11-22.md`.  
**Pedido do proprietário:** não mexer nas lojas já existentes Achados para Casa e Cozinha Sem Complicação; desfazer as alterações indevidas; criar somente a Loja de Móveis para Cada Canto.

## A. Restauração das duas lojas antigas — CONCLUÍDA
- **Achados para Casa** Blogger blog ID `1426630233929943394`, Page `3841238517239710135`: página restaurada com os **686 caracteres exatos** do backup `affiliate_hub_v31/backups/C100_ACHADOS_PARA_CASA_LOJA_BEFORE_LIVE_2026-11-22.html`. GET posterior LIVE e conteúdo idêntico. A Page voltou a redirecionar para `https://achadosparacasa2026.blogspot.com/2026/10/loja.html`, post Loja que permaneceu LIVE e contém 32 URLs Shopee distintas. Request ID: `v31-c100-correction-restore-achados-20261122-01`.
- **Cozinha Sem Complicação** Blogger blog ID `3552757910439359679`, Page `6913756651435112886`: página restaurada com os **694 caracteres exatos** de `affiliate_hub_v31/backups/C100_COZINHA_SEM_COMPLICACAO_LOJA_BEFORE_LIVE_2026-11-22.html`. GET LIVE exato, redireciona para `https://cozinha-sem-complicacao.blogspot.com/2026/10/loja.html`, post Loja original com 20 URLs Shopee distintas. Request ID: `v31-c100-correction-restore-cozinha-20261122-01`.
- Ambos os artigos Loja originais foram **preservados sem edição**. 0 botões com href placeholder nos posts verificados; isso não prova que a Shopee permite a navegação de todos os browsers (veja teste externo abaixo).
- Os exports C100 de 36/32 cards devem ser tratados **somente como histórico**, nunca como página atual desses blogs. **NÃO reaplicar**.

## B. Móveis para Cada Canto — PRIMEIRA LOJA PUBLICADA E VALIDADA
- Blog: `1439741542627895062`, Page `5105320514641154037`.
- URL FINAL: https://moveisparacadacanto.blogspot.com/p/loja.html
- Antes: única loja de produção verdadeiramente vazia, Page LIVE sem anúncios e sem redirecionamento.
- Backup original salvo ANTES do update: `affiliate_hub_v31/backups/C101_MOVEIS_PARA_CADA_CANTO_LOJA_ANTES_2026-11-22.html` (1186 caracteres).
- R2: 594 itens moderados/classificados no nicho `casa/moveis`; seleção de móveis completos, não ferragens/peças.
- Consulta 1 GitHub Actions [#45082936074](https://github.com/adelrib27/blogger-automation1/actions/runs/45082936074), job `137394938950`: 60 anúncios exatos, 14 aprovados, 8 chamadas API, 0 erros.
- Consulta 2 GitHub Actions [#45083038223](https://github.com/adelrib27/blogger-automation1/actions/runs/45083038223), job `137395263221`: faixa seguinte do catálogo sem repetir as primeiras ofertas, 54 candidatos verificados, 14 aprovados, 7 chamadas API, 0 erros.
- **28 anúncios distintos verificados** por shopId:itemId; um título promocional ambíguo excluído na revisão; **27 móveis publicados**, **23 vendedores**; **16 anúncios com sellerCommissionRate >=3%** na consulta (percentual não é ganho garantido). URL `offerLink` real da Shopee, `imageUrl` da mesma oferta, rating >=4 e histórico de >=10 vendas no instantâneo. Produtos de seis categorias. Quatro links internos para posts LIVE do próprio blog.
- Dados curados de origem, sem secretos: `affiliate_hub_v31/c101_moveis_curated_verified.json`.
- HTML final pronto antes da publicação: `affiliate_hub_v31/exports/C101_MOVEIS_CADA_CANTO_27_SHOPEE_VERIFICADOS_2026-11-22.html` (34884 caracteres). **27 cards, 27 imagens de altura controlada, 27 CTAs laranja #D83F00, 27 shortlinks distintos, 6 categorias, 4 guias**, sem scripts de redirecionamento nem alterações de tema.
- Atualizada **a Page existente uma só vez**, request ID `v31-c101-moveis-27-shopee-20261122-01`, updated_at `2026-11-22T20:27:10-03:00`.
- GET CMS posterior: `live`, permalink idêntico, HTML idêntico ao export, 27 cards, 27 fotos, 27 botões laranja e 27 shortlinks distintos.
- GET público Firecrawl `maxAge=0`: 27 cards, 27 CTAs, 27 shortlinks, headline nova presente. Inspeção no navegador remoto desktop 1280px: **27 cards efetivamente visíveis**, nenhum card com imagem gigante, 27 botões laranja com `target=_blank` e URL `https://s.shopee.com.br/...`.
- **ATENÇÃO — limite externo da Shopee:** testes com navegador automatizado nos links novos e em um antigo levaram à URL de verificação `shopee.com.br/verify/traffic/error?...next=...product/{shopId}/{itemId}&mmp_pid=an_18352820579`. Isso confirma que os shortlinks seguem para infraestrutura Shopee contendo identificação de afiliado e o SKU certo, **mas não comprova conclusão de navegação humana**; a tela de segurança é uma restrição/antibot do acesso automatizado e pode afetar visitantes conforme critérios externos da Shopee. Não afirmar que testes humanos foram concluídos nem remover link de afiliado sem validação.
- Links externos podem requerer autenticação ou verificação na Shopee; ofertas/estoque/frete/comissões podem mudar.

## C. Estado de encerramento
- **Correção completa:** 2 lojas antigas restauradas + 1 nova Loja de Móveis publicada.
- Todas as outras lojas preservadas.
- `V31_AUTOLIVE_ACTIVE` não alterado; sem nova automação LIVE, sem posts ou tema alterados, sem shortlink mutations, sem escrita D1/R2, sem Pinterest.
- Se a conversa expirar: ler primeiro este checkpoint, `affiliate_hub_v31/C100_ROLLOUT_MANIFEST.json`, `affiliate_hub_v31/CONTINUIDADE_ESTADO.json`, `V31_CONTINUAR_AQUI.md`. Verificar via GET os três IDs **antes de qualquer ação**. Não repetir publicação, não reintroduzir vitrines C100. Se houver relato de cliente de falha de Shopee, avaliar link e challenge a partir da experiência real do navegador, não substituir links em lote no escuro.

**C101 ENCERRADA — restore 2/2; Móveis 27 LIVE; QA CMS e pública confirmada; aviso de antibot externo mantido.**
