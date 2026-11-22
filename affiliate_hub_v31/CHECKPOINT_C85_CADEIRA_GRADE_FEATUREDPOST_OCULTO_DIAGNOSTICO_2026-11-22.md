# V31 C85 — Cadeira Certa: Office Arco ausente na grade (diagnóstico, 22/11/2026)

## Contexto
- Blog https://cadeira-certa-home-office.blogspot.com/, ID Blogger `7163624325768776034`.
- Usuário confirmou por captura que Office Arco aparece como primeiro slide do carrossel, mas não como cartão na grade de "Postagens".
- C84 corrigido **pelo proprietário** no editor do Blogger antes deste diagnóstico: o HTML público atual contém `var cards = document.querySelectorAll('#FeaturedPost1 .post-wrapper, #Blog1 .post-wrapper');`. Não alterar essa linha.
- Blogger API: 6 artigos LIVE, todos com URLs próprias; feed RSS/Atom público `/feeds/posts/default?alt=json&max-results=20` declara `openSearch$totalResults=6` e contém Office Arco como artigo mais recente.
- Configurações do Blogger lidas pela aba autenticada (somente leitura): `Máximo de postagens mostradas na página principal: 7 postagens`. **Não é problema de limite.**

## Causa observada na renderização (evidência muito forte)
- HTML `#FeaturedPost1` inclui `post-6656620121237912250` Office Arco.
- HTML `#Blog1` tem somente os cinco outros IDs `3691939235338797956,5233454304666317388,8648967166394388356,7516498952063951593,4636680511643933177`.
- Inspeção do DOM e estilos calculados via navegador público Firecrawl Interact encontrou:
  - `div#featured_post.featured-post.section`: **computed display:none, dimensões 0x0**;
  - `#FeaturedPost1`: display:block, mas herdou ocultação de ancestral `.featured-post`;
  - `#Blog1 .blog-posts`: computed display:grid, 1200px largura, com cinco cartões visíveis.
  - CSS explícita do tema: `.centered-top-container, .centered-top-placeholder, .sidebar-container, .featured-post, .vertical-ad-container, #footer.footer { display: none !important; }`.
- O tema mantém um widget Blogger FeaturedPost ativo **mas o esconde via CSS**, enquanto o `Blog1` apresenta uma lista filtrada que exclui o artigo selecionado pelo widget. Nos temas responsivos Blogger 2017, isso costuma ser feito por `data:posts filter (p => p.id not in (data:widgets.FeaturedPost map (w => w.postId)))`; esta expressão exata **não foi inspecionada no XML privado atual** (não alegar que seja exatamente a mesma). Fontes externas confirmam esse padrão: `https://blogger.fineshop.app/docs/theme-xml/widget-types/featured-post` e `https://blogger.fineshop.app/docs/theme-xml/widget-types/blog`.

## Correção limpa e reversível recomendada
O carrossel próprio `#ub-v21-featured` não precisa do gadget `FeaturedPost1`, e o seletor corrigido C84 já aceita candidatos `#Blog1` mesmo sem o FeaturedPost.

Acessar **Blogger → Layout → Postagem em destaque (Featured Post) → Editar → DESATIVAR "Mostrar este widget/gadget" → Salvar → Salvar organização**. Ao tornar o gadget invisível também **para o mecanismo de widgets do Blogger**, `data:widgets.FeaturedPost` em temas responsivos deixa de selecionar aquele post e `Blog1` deve passar a renderizar os seis. Isso mantém o XML do tema, posts, SEO, permalinks e CTA inalterados; o ajuste é reversível ativando novamente a opção.

- **Não** resolver editando CSS para mostrar `.featured-post`: isso geraria um segundo destaque fora da grade, não um cartão padrão.
- **Não** duplicar Office Arco, mudar data de publicação, adicionar scripts de clonagem, fazer `display:contents`, reiniciar automações nem instalar outro tema.
- Se desativar o gadget não liberar Office Arco na grade, reativar ou manter cópia das configurações, e auditar o includable `Blog1/main` no XML do tema; remover **somente** eventual filtro que exclui `data:widgets.FeaturedPost` em visualização de homepage, depois testar. Não alterar a lógica sem abrir o XML exato.

## Gate de verificação após operação do proprietário/Work
1. Homepage HTTP 200, seletor `#Blog1 .post-wrapper` com **seis IDs únicos** e Office Arco em primeiro.
2. `#ub-v21-featured` mantém **cinco slides**, Office Arco e Tok Boxbit, com imagens e links corretos; Anterior/Próximo funcionam.
3. Não existe widget destacado oculto que retire postagem da grade.
4. As páginas internas, feed, CTA afiliado exato Shopee Office Arco `https://s.shopee.com.br/9fMfOM4016` e Tok permanecem.
5. Responsividade, menu, aviso de cookies e mobile intactos.
6. Status blogger: 6 LIVE, 0 DRAFT; LIVE V31 automático continua OFF.

## Permissões e estado
Os conectores do chat Blogger Bridge V2 suportam páginas/postagens, não Layout/Template; Browser acessa abas em leitura; Blogger Local Runner autoriza instalação de tema apenas em outros IDs, nunca este blog. **Nenhuma configuração Layout foi alterada nesta execução. A correção está identificada, mas aplicação e verificação pós-alteração permanecem PENDENTES**, para proprietário em Layout ou ChatGPT Work com navegador autenticado. Evitar afirmar que seis cartões já aparecem.

Links de continuidade: [C84](CHECKPOINT_C84_CADEIRA_TEMA_CARROSSEL_DIAGNOSTICO_2026-11-22.md), [C83](CHECKPOINT_C83_CADEIRA_CERTA_CONVERSAO_PUBLICACAO_CARROSSEL_2026-11-22.md).
