# Cadastro ilimitado de blogs no Hub V31 (Blogger e WordPress)

O projeto **não tem uma lista fixa de três blogs**. `routing.sites()` combina os
registros de `site_routes.json` com **todos os arquivos `*.json` deste diretório**,
sem alteração de código Python. É um **cadastro declarativo**: um blog novo
precisa informar dados reais, mas não precisa de uma nova implementação do
catálogo, conversor ou fallback.

## C68 — novo blog exige estratégia SEO e linkagem contextual

Antes de cadastrar um novo site real em `sites.d`, leia a
[estratégia editorial e técnica C68](../ESTRATEGIA_NOVOS_BLOGS_SEO_SHOPEE_V1.md),
extraída da ficha técnica de 12/11/2026 e das regras SEO do proprietário.
Use a [ficha de onboarding NÃO executável](../future_blog_onboarding.template.json)
para coletar demandas reais, intenção de compra, prova da palavra-chave,
cluster pilar/satélites, comissão positiva verificável sem mínimo de 3%,
identidade/campanha/segredos separados e gates SAFE.

A biblioteca offline [future_blog_seo.py](../future_blog_seo.py) valida
links internos **somente de posts publicados no mesmo hostname** e audita
SEO por artigo **para futuros projetos**. Blog novo com zero posts não pode
inventar links: programa-se relink quando houver artigos correlatos reais.
Ela NÃO está ligada aos escritores legados e não publica nada, não acessa
rede nem valida Core Web Vitals ou comissões atuais. Preferir repositório
independente por blog, conforme ficha; preservar Hub V31 como motor
reutilizável e R2 central, sem copiar credenciais de um site para outro.
**Não instalar automaticamente em blogs existentes sem testes dedicados.**

## Novo blog — formato do arquivo

Exemplo `wordpress_novo_portal.json`:

```json
{
  "site_key": "wordpress_novo_portal",
  "platform": "wordpress",
  "identifier": "https://meu-blog-exemplo.com.br/",
  "campaign": "novoportal",
  "allowed_niches": ["tecnologia/gadgets", "casa/organizacao"],
  "publish_enabled": false
}
```

- `platform` aceita `wordpress` e `blogger`. Para Blogger, `identifier`
  é o ID numérico real do blog; para WordPress, é a URL HTTPS real.
- `site_key` e `campaign` precisam ser exclusivos; duplicatas falham
  fechadas. A campanha identifica o cache de links daquele blog.
- `allowed_niches` precisa usar nichos da taxonomia V31 existente. Novos
  nichos são adicionados na taxonomia versionada, não no código do fallback.
- `publish_enabled` permanece `false` na fase SAFE, e o cadastro
  **não concede permissão de publicar**.
- Registrar novos blogs reais em `sites.d/` não muda os workflows LIVE
  ou as credenciais dos outros sites.

## Fonte de produtos: API primeiro, CSV/R2 apenas no erro 1000

O `opportunity_router.py` aceita o mesmo scanner Shopee v2.3 já utilizado
por um blog. Quando há ofertas válidas pela API, conserva a saída normal.
Se ocorrer erro 1000 confirmado **e não houver ranking útil**, utiliza
o catálogo R2 e cria os arquivos `ranking.json`, `ranking.csv`,
`intent_report.json` e `search_signals.json` no formato esperado
pelas filas v2.3.

Exemplo **apenas de comando para futura integração** no mesmo job de
descoberta Casa e Decoração (não executa publicação):

```bash
python -m affiliate_hub_v31.opportunity_router \
  --site wordpress_casa_decoracao \
  --scanner casa_decoracao/src/shopee_oportunidades_casa.py \
  --config casa_decoracao/config/shopee_oportunidades.json \
  --rules casa_decoracao/config/shopee_intent_rules.json \
  --output casa_decoracao/data/shopee_oportunidades \
  --limit 32
```

Em execução GitHub Actions, a etapa deve dispor dos Secrets da API Shopee
já existentes e das credenciais R2 do Environment `v31-editorial-safe`.
As permissões e os gates de publicação do blog continuam nas suas próprias
automações. **Não ativar no `main` sem testes por plataforma.**

### Limite estrutural versus capacidade real

- O código não tem máximo de 3, 20 ou 50 blogs; um teste de cadastro
  registrou **60 novos blogs fictícios** sem alteração do motor.
- A quantidade de artigos/dia depende do cron de cada blog, da cota
  de geração, disponibilidade das plataformas e estoque de links verificados.
- O CSV contém produtos e imagens por URL, mas **não substitui a API de
  criação de links afiliados novos**: durante a falha 1000, a alternativa
  somente fornece produtos com `offerLink` já convertido para a campanha.
- Se uma campanha não possui links válidos, o fallback termina com erro
  seguro em vez de publicar um `productLink` sem rastreamento.
- Preparar um estoque de links cacheados por campanha enquanto a Shopee
  opera normalmente é uma etapa necessária antes de habilitar o fallback.
- O Radar Tech BR atual consome uma fila de slots própria, não os arquivos
  v2.3; precisará de adaptação específica **de saída**, reutilizando o mesmo
  seletor e registro universal.
- Os publicadores existentes ainda têm regras próprias de repetição de
  produtos; migrar para originalidade de **pautas e títulos** exige testes
  separados. Nenhum gate LIVE foi alterado neste PR.

**Atenção:** o fallback e o cadastro estão em branch SAFE, não conectados
automaticamente aos workflows de produção.
