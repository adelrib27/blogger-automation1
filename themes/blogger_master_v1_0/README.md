# Tema Mestre Blogger v1.0

Base editorial/comercial reutilizável para novos blogs de produto do projeto `blogger-automation1`.

## Estado

**LAB_ONLY**. Não aplicar em blogs reais até concluir validação no blog de laboratório:

- Blog ID: `99449222854490000`
- Nome: `TESTE BOG Tema editorial — XML v1.0`

A aplicação futura deve sempre fazer **backup do tema atual antes de qualquer escrita**.

## Objetivos da v1.0

- layout responsivo sem dependências externas;
- identidade visual centralizada em variáveis CSS;
- navegação por páginas;
- slot próprio para oferta/CTA afiliado;
- área principal de posts;
- sidebar para tópicos e posts populares;
- footer com aviso de afiliados;
- baseline de SEO técnico e Open Graph;
- microdados `WebSite`;
- acessibilidade básica, skip-link e suporte a `prefers-reduced-motion`;
- nenhum secret, token ou link afiliado fixo dentro do tema.

## Arquivos

- `theme.xml` — tema Blogger.
- `theme_profile.json` — contrato de automação e segurança.
- `validate_master_theme.py` — validação estática local.

## Slots estáveis para automação

| Finalidade | Section ID |
| --- | --- |
| Menu principal | `topnav` |
| Oferta afiliada | `offerSection` |
| Postagens | `main` |
| Sidebar | `sidebar` |
| Links do footer | `footerlinks` |

Esses IDs são parte do contrato do Tema Mestre. Mudanças futuras devem gerar nova versão.

## Personalização por blog

Na v1.0, a identidade é alterada prioritariamente nas variáveis CSS em `:root`:

- `--tm-bg`
- `--tm-surface`
- `--tm-surface-soft`
- `--tm-text`
- `--tm-muted`
- `--tm-border`
- `--tm-accent`
- `--tm-accent-strong`

O nome do blog é lido diretamente do Blogger por `data:blog.title`.

Links Shopee, preço, imagem do produto e CTA **não pertencem ao XML mestre**. Eles entram depois pelo conteúdo ou pelo slot `offerSection`.

## SEO e schema

O tema inclui baseline global de SEO/Open Graph e microdados `WebSite`.

Schemas específicos de `Article` e `Product` dependem dos dados reais de cada postagem/produto e, portanto, devem ser gerados pela automação de conteúdo. Isso evita dados falsos ou desatualizados no tema global.

## Validação local

Execute:

```bat
python themes\blogger_master_v1_0\validate_master_theme.py
```

Resultado esperado:

```text
THEME_MASTER_V1_STATIC_VALIDATION_OK
```

## Ordem segura de implantação futura

1. backup do tema atual;
2. validar Blog ID;
3. preflight somente leitura;
4. aplicar no blog de laboratório;
5. validar home, post, página e responsividade;
6. testar Layout e widgets;
7. validar URL pública;
8. somente depois liberar para blogs reais.

## Não fazer

- não inserir tokens/secrets no XML;
- não hardcodar link curto Shopee;
- não carregar JavaScript externo na v1.0;
- não aplicar diretamente em blog real;
- não alterar robots por causa do tema;
- não considerar a importação bem-sucedida sem validar a URL pública.
