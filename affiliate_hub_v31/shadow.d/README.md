# Monitoramento e reposição por blog — shadow.d/

O C8 opera por configuração, sem codificar os 3 WordPress iniciais no
motor. Um novo blog pode consumir o catálogo central quando tiver:

1. Registro real `site_key`/plataforma/domínio ou ID/campanha/nichos em
   `../sites.d/<site_key>.json` (ou cadastro legado `site_routes.json`).
2. Config de produtos por categoria/keyword e arquivo de regras semânticas
   versionados no repositório do blog.
3. `<site_key>.json` neste diretório descrevendo os arquivos e a
   quantidade de slots da automação **já existente**.

Formato:

```json
{
  "site_key": "wordpress_exemplo",
  "config": "meu_projeto/config/shopee_oportunidades.json",
  "rules": "meu_projeto/config/shopee_intent_rules.json",
  "daily_slots": 2,
  "reserve_days": 3,
  "required_source_categories": []
}
```

Os campos `config` e `rules` são caminhos relativos à raiz do
repositório, existentes, sem `..` ou links simbólicos. Não use URLs
públicas nem chaves nesses arquivos. `required_source_categories`
precisa conter exatamente rótulos presentes na seção `categories`
do config. Para o Radar, as cinco categorias são obrigatórias para
comprovar a montagem diária dos cinco slots; isso NÃO valida
automaticamente a publicação.

### Modos e limites

- `python -m affiliate_hub_v31.shadow_audit --site all` **somente lê**
  o catálogo privado R2 e publica apenas contagens nos logs.
- `python -m affiliate_hub_v31.cache_replenish --site all --budget 3`
  é dry-run, sem chamadas Shopee; mostra planejamento.
- `python -m affiliate_hub_v31.cache_replenish --site all --budget 3 --execute`
  exige credenciais S3 R2 e Shopee do Environment em runtime, faz
  **no máximo 3 mutations por execução** e grava **um snapshot**.
- `--site wordpress_exemplo` permite focar um blog registrado; a
  regra de limite máximo 3 por execução permanece.
- Rodízio usa data e lista de perfis configurados, não depende de nome
  ou quantidade fixa de blogs.
- As duas automações `v31_c8_*_safe.yml` possuem cron **desligado por
  padrão**; habilitação exige revisão/merge e Variables de opt-in.
- Nenhuma dessas rotinas chama WordPress, Blogger, gerador editorial ou
  API de publicação; resultado `SHADOW_READY` é apenas condição
  necessária, **não suficiente**, para ativar LIVE.

A meta de 50+ blogs requer adicionar as rotas reais, ampliar nichos e
palavras-chave quando necessário, dimensionar orçamento/cotas da Shopee
antes de elevar o limite global de 3, revisar gates de originalidade
editorial e testar cada integração sem duplicar os publicadores.
