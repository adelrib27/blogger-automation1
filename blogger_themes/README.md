# Tema Mestre Blogger — Shopee V3.0

Este é o tema-base oficial para novos blogs de conteúdo/afiliados no Blogger.

## O que o mestre resolve

- A página inicial monta os cards a partir dos posts reais publicados no Blogger.
- Cada card usa o permalink e o título do próprio post; não há URLs de artigos escritas manualmente no XML.
- A página individual mostra `data:post.title` e `data:post.body`, portanto o conteúdo vem do post publicado.
- Páginas institucionais também usam o conteúdo cadastrado no Blogger, sem texto legal preso ao tema.
- Inclui paginação para blogs que ultrapassem o número de posts exibidos por página.
- Usa o título e a descrição do próprio blog; não contém nome de produto, marca ou link de afiliado específico.

## Instalação padrão para cada novo blog

1. Criar o blog no Blogger.
2. Definir o título e a descrição do blog (a descrição aparece na área de abertura da página inicial).
3. Antes de publicar os artigos, abrir **Blogger → Tema → Restaurar/Enviar tema** e enviar este XML.
4. Criar as páginas institucionais com estes slugs padrão:
   - `/p/sobre.html`
   - `/p/aviso-de-afiliados.html`
   - `/p/politica-de-privacidade.html`
   - `/p/termos-de-uso.html`
5. Criar/publicar o artigo principal e os artigos relacionados. O tema os lista automaticamente; não editar o XML para adicionar títulos ou URLs.
6. Validar a página inicial e abrir ao menos um permalink individual para confirmar título e corpo do artigo.

**Limitação importante:** a Blogger API v3 não oferece um recurso oficial de tema/template para enviar o XML. Portanto, a instalação do arquivo continua sendo feita pela interface do Blogger. O fluxo de conteúdo via API pode criar posts e páginas, mas não deve declarar um tema instalado sem confirmação pela interface.

## Checklist de aceite

- [ ] Página inicial mostra os posts publicados em cards clicáveis.
- [ ] O link de cada card abre o permalink correto.
- [ ] O artigo individual mostra título e corpo completo.
- [ ] As páginas institucionais mostram o conteúdo salvo no Blogger.
- [ ] Não há nome de produto, URL de post ou link de afiliado específico hardcoded no tema.
- [ ] A lista continua navegável quando há mais posts do que a página atual exibe.
- [ ] O layout é utilizável em desktop e celular.

## Regra de manutenção

Este arquivo é a fonte canônica. Não criar uma nova versão de tema para cada blog. Mudanças estruturais devem ser feitas aqui, validadas pelo teste automatizado e só depois distribuídas para novos blogs. Personalização de cada blog deve ficar no título, descrição, páginas e conteúdo dos posts.
