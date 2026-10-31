# BLOGGER_MODELO_V20 — TEMA MODELO FINAL E VALIDADO

Este pacote representa a baseline validada do blog de referência, mas **não copia posts**. Em 2026-10-31 o V20 recebeu a extensão oficial de LOJA automatizada, aprovada visualmente no piloto Conecta Achados.

## O que faz parte do modelo

- Tema Emporio customizado V20 (`emporio-revisao-visual-20-modelo-final`)
- Extensão oficial da LOJA (`BLOGGER_MODELO_V20_STORE_EXTENSION`)
- Home com destaque editorial e grade de 3 cards
- Cabeçalho e rodapé institucionais
- Sidebar `Postagens mais visitadas` em posts e páginas estáticas, exceto na LOJA
- Página de contato com campos Nome, E-mail, Mensagem e Enviar
- Comentários/login removidos do layout aprovado
- Bloco `Artigos relacionados` abaixo dos posts
- Seis páginas previstas pelo provisionamento:
  - Sobre
  - Aviso de Afiliados
  - Contato
  - Política de Privacidade
  - Termos de Uso
  - LOJA
- Identidade visual própria por blog, sem alterar a estrutura validada

## LOJA automatizada — contrato V20

A LOJA usa `/p/loja.html` e aparece no menu global imediatamente depois de **Início**, com destaque visual próprio.

Layout aprovado:

- largura máxima de 1280 px no desktop;
- sidebar oculta **somente** na LOJA;
- 4 produtos por linha no desktop;
- 2 produtos por linha no tablet;
- 2 produtos por linha no celular, com cards compactos;
- demais páginas, posts, home, cabeçalho e rodapé permanecem no comportamento V20 normal.

O scaffold da LOJA não contém produtos fictícios. A região automática fica entre:

```html
<!-- BLOGGER_STORE_AUTO_START -->
<!-- BLOGGER_STORE_AUTO_END -->
```

A rotina de produtos deve trabalhar em modo fail-closed: só escrever quando houver exatamente **20 produtos reais válidos em 5 categorias**, preservar tudo fora dos marcadores e reler a página após a escrita. Cada card deve manter dados reais da seleção e links comerciais com `target="_blank"` e `rel="nofollow sponsored noopener"`.

## Identidade visual por blog

O modelo V20 separa **estrutura** de **identidade visual**.

Por padrão, `render_modelo_v20_theme.py` usa `--palette auto` e escolhe de forma determinística uma paleta a partir do título e URL do novo blog. Assim, blogs diferentes tendem a receber cabeçalho/acento/rodapé diferentes sem exigir configuração manual.

Paletas disponíveis:

- `blue`
- `emerald`
- `plum`
- `terracotta`
- `teal`
- `burgundy`
- `indigo`
- `amber`

Também é possível escolher uma paleta explicitamente ou sobrescrever cores individuais:

```text
--palette emerald
--primary-color "#0F8A5F"
--header-bg "#F2FBF7"
--footer-bg "#12372A"
```

## O que NÃO faz parte do modelo

- Nenhum post do blog de referência
- Nenhum produto fixo da Shopee
- Nenhum preço, imagem de produto ou link de afiliado do blog de referência
- Nenhuma URL/título fixo do blog de referência
- Nenhuma obrigação de repetir as mesmas cores do blog de referência

## Arquivos principais

- `model_manifest.json`: contrato/validações do modelo
- `pages.json`: seis páginas parametrizadas por `{{BLOG_TITLE}}`, incluindo scaffold da LOJA
- `themes/blogger_modelo_v20/theme.xml.tpl`: snapshot limpo do tema final mantido no ambiente local do runner
- `extend_modelo_v20_store.py`: aplica de forma idempotente o menu e o layout oficial da LOJA ao tema renderizado
- `install_modelo_v20_adoption.py`: renderiza, aplica a extensão da LOJA, faz backup e instala o V20

## Fluxo esperado para um NOVO blog

1. Criar o blog e obter o Blog ID.
2. Confirmar que o Blog ID é o alvo esperado.
3. Confirmar que o blog novo tem **zero posts**.
4. Configurar título, descrição, descrição de pesquisa e timezone.
5. Renderizar `theme.xml.tpl` com o título e URL do novo blog usando `render_modelo_v20_theme.py`.
6. Aplicar `extend_modelo_v20_store.py` ao tema renderizado.
7. Validar XML e os marcadores V20 + STORE antes do upload.
8. Fazer backup do tema atual do novo blog.
9. Aplicar o tema renderizado.
10. Renderizar/publicar as seis páginas.
11. Popular a LOJA com 20 produtos reais em 5 categorias e validar os 20 `data-item-id` após a escrita.
12. Validar menu, rodapé, contato, paleta e isolamento visual da LOJA.
13. Confirmar novamente que nenhum post do blog de referência foi copiado.

## Regra de segurança

O provisionamento limpo deve falhar se o blog-alvo já possuir posts, salvo autorização explícita para outro tipo de operação. O modelo nunca deve apagar posts automaticamente. A LOJA nunca deve receber publicação parcial nem dados inventados.

## Piloto visual aprovado

- Blog: **Conecta Achados**
- Blog ID: `1719259388907013414`
- Data de aprovação: `2026-10-31`
- Layout aprovado: **1280 px / sem sidebar na LOJA / 4 desktop / 2 tablet / 2 celular**

## Blog de referência histórico

Blog ID `1453188702831337099` permanece somente como referência histórica de validação. Ele não deve ser usado como fonte de posts no provisionamento.
