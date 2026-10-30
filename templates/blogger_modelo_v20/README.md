# BLOGGER_MODELO_V20 — TEMA MODELO FINAL E VALIDADO

Este pacote representa a baseline validada do blog de referência, mas **não copia posts**.

## O que faz parte do modelo

- Tema Emporio customizado V20 (`emporio-revisao-visual-20-modelo-final`)
- Home com destaque editorial e grade de 3 cards
- Cabeçalho e rodapé institucionais
- Sidebar `Postagens mais visitadas` em posts e páginas estáticas
- Página de contato com campos Nome, E-mail, Mensagem e Enviar
- Comentários/login removidos do layout aprovado
- Bloco `Artigos relacionados` abaixo dos posts
- Cinco páginas publicadas automaticamente pelo provisionamento:
  - Sobre
  - Aviso de Afiliados
  - Contato
  - Política de Privacidade
  - Termos de Uso

## O que NÃO faz parte do modelo

- Nenhum post do blog de referência
- Nenhum produto da Shopee
- Nenhum preço, imagem de produto ou link de afiliado do blog de referência
- Nenhuma URL/título fixo do blog de referência

## Arquivos

- `model_manifest.json`: contrato/validações do modelo
- `pages.json`: páginas institucionais parametrizadas por `{{BLOG_TITLE}}`
- `themes/blogger_modelo_v20/theme.xml.tpl`: snapshot limpo do tema final (gerado uma vez por `freeze_modelo_v20_theme.py`)

## Fluxo esperado para um NOVO blog

1. Criar o blog e obter o Blog ID.
2. Confirmar que o Blog ID é o alvo esperado.
3. Confirmar que o blog novo tem **zero posts**.
4. Configurar título, descrição, descrição de pesquisa e timezone.
5. Renderizar `theme.xml.tpl` com o título e URL do novo blog usando `render_modelo_v20_theme.py`.
6. Fazer backup do tema atual do novo blog.
7. Aplicar o tema renderizado e validar o marcador público V20.
8. Renderizar as páginas com `render_modelo_v20_pages.py`.
9. Publicar as cinco páginas via Blogger API/Bridge.
10. Validar que os cinco slugs estão live e que os links do menu/rodapé apontam para o novo blog.
11. Validar a página Contato: campos Nome, E-mail, Mensagem e Enviar visíveis e runtime do tema carregado.
12. Confirmar novamente que nenhum post do blog de referência foi copiado.

## Regra de segurança

O provisionamento limpo deve falhar se o blog-alvo já possuir posts, salvo autorização explícita para outro tipo de operação. O modelo nunca deve apagar posts automaticamente.

## Blog de referência

Blog ID `1453188702831337099` é somente referência histórica de validação. Ele não deve ser usado como fonte de posts no provisionamento.
