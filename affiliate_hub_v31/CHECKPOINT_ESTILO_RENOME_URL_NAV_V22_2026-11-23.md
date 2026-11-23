# V31 — Estilo no Dia a Dia e Acessórios: correção após mudança de URL
Data: 2026-11-23. Autoridade de verificação: Blogger API v3, blog ID `4830103887652146866`.

## Identidade real e estável
- Título na API: **Estilo no Dia a Dia e Acessórios**
- URL antiga: `https://estilo-no-dia-a-dia-0071220800-2.blogspot.com/`
- URL atual: `https://estilo-no-dia-a-dia-e-acessorios.blogspot.com/`
- Páginas existentes (ID preservado): LOJA `4843501559117111153`, Sobre `8773838001532016381`, Aviso de Afiliados `2697812152092116907`, Contato `2807837762943114164`, Privacidade `3558954602837840114`, Termos `98181324637432898`.
- Post vitrine Loja ID `3362829797679236320`, URL nova `https://estilo-no-dia-a-dia-e-acessorios.blogspot.com/2026/11/loja.html`.

## Alterações LIVE concluídas, API verificada
- **9 posts publicados** tiveram SOMENTE substituição do prefixo da URL interna antiga pelo novo domínio, com confirmação de HTML exato, status LIVE preservado e nenhum link de afiliado Shopee alterado:
  `2247439582611517548`, `5523832851018433598`, `3362829797679236320`, `2289040176282299378`, `7445696430893376472`, `3096686415183411115`, `4810921417416846727`, `5247907822209096210`, `888020488350877403`.
- A página LOJA `4843501559117111153` recebeu duas correções: botão e script de encaminhamento apontam ao post vitrine do novo domínio. Status LIVE e ID preservados.
- **Validação final independente:** `list_published_posts` (12 LIVE) e `list_pages` (6 LIVE) retornaram ZERO ocorrências da URL antiga no HTML, e os URLs LOJA agora existem na API.
- Backup PREALTERAÇÃO dos 9 posts + página LOJA, com conteúdo HTML integral e readback exato: https://docs.google.com/document/d/1e3t8Ugbt7Kz5oyYZ74iga9vVsj2k8T4niziaDW6WzmE/edit (não divulgar conteúdo em repo).
- Não alterados: título dos posts, suas URLs, os demais cinco pages, imagens, produtos, fotos, links de afiliados, workflows, automações, LIVE policy e outros blogs.

## Entrega de tema (ainda NÃO instalado)
- O XML **ESTILO_NO_DIA_A_DIA_TEMA_V22_LINKS_CORRIGIDOS.xml** foi gerado a partir do V21 enviado/instalado pelo proprietário e validado localmente como XML bem formado.
- No V21, 37 ocorrências do domínio antigo ainda persistiam no menu nativo, menus JS, rodapés e links institucionais.
- No V22, o `pageListJson` nativo recebe o domínio novo (1 ocorrência); as 36 referências estáticas/JS foram transformadas em caminhos relativos à raiz do blog, sem alterar funcionamento ou estilo.
- Contagem preservada no XML: 14 widgets, 9 seções, 148 includables e 19 scripts. Nenhuma mudança em tratamento de imagens ou CSS, nem em links Shopee.
- **Falta o proprietário instalar o V22** pelo Blogger Tema > Restaurar e testar visual e navegação no desktop e celular. A API atual não fornece uma operação administrativa autorizada de restauração desse tema para o blog.
- Não alegar teste HTTP público: verificador web do ChatGPT não conseguiu abrir as páginas Blogspot; existência/URL demonstradas pela Blogger API, não pela navegação real.

## SEO
A correção aqui é de **links internos** para o novo endereço. Isso não é a criação de um redirecionamento HTTP 301 da URL antiga de domínio Blogspot para o atual. Qualquer mecanismo cross-domain depende da plataforma e das propriedades dos domínios, não do XML do template. Verificar Search Console/índice conforme necessidade.

## Rota V31
A `affiliate_hub_v31/site_routes.json` já identifica o Blogger pelo ID imutável `4830103887652146866` com `site_key=blogger_estilo` e `publish_enabled=false`. Nenhuma alteração na rota é necessária por mudança de nome/domínio; NÃO ativar LIVE.
