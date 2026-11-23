# V31 Radar Tech BR — C116: primeira reescrita publicada e conferida

**Data:** 2026-11-23 (America/Recife). **Fase:** execução da Etapa 4, 1º dos 10 posts do manifest C115.  
**Identidade:** WordPress post ID **260**, URL permanente **https://radartechbr.com.br/smartwatch-com-monitor-de-frequencia-cardiaca/**, slug **inalterado**.

## Backup obrigatório anterior à edição
Arquivo completo versionado antes de qualquer alteração: `affiliate_hub_v31/backups/C116_RADAR_WP_POST_260_BEFORE_REWRITE_2026-11-23.json`, commit `45359abbff8152e3b573f366a73dfaeb1b7c8a30`. Contém HTML integral original, excerpt, título, status, categorias, tags, imagem, datas, metadados AIOSEO, permalink, termos e links afiliados. Antes da gravação, foi feita verificação atômica de que `modified=2026-10-31T12:57:46`, conteúdo, título, excerpt, status, categoria e featured_media coincidiam com o backup; **todas as condições passaram**.

## Oferta e fontes
- Link comercial preservado, sem reconversão: `https://s.shopee.com.br/5AtgvXX3jj`.
- Redirecionamento obtido via Firecrawl com maxAge=0 confirmou o produto `/product/1158053430/22499056874` e parâmetro `mmp_pid=an_18352820579` da campanha afiliada. A Shopee exigiu login e exibiu checagem de tráfego: **não** considerar estoque, preço, rating ou especificação confirmados em tempo real. A busca pública pela Shopee também recuperou anúncio de mesmo título com ID `22499056874`.
- Fotografia original preservada: `https://cf.shopee.com.br/file/br-11134207-81z1k-mg4sqr0e5nggcd`. Imagem destacada do WP permanece attachment **261**.
- Fontes explicativas no artigo: University of Iowa Health Care (`https://uihc.org/health-topics/are-wearable-health-and-fitness-data-trackers-reliable`) e Mount Sinai (`https://health.mountsinai.org/blog/can-wearables-really-monitor-your-heart-health/`). Estas descrevem limitações gerais de sensores vestíveis e **não validam o modelo Shopee individualmente**.

## Prévia e publicação
- Fonte revisada em `affiliate_hub_v31/previews/C116_RADAR_WP_POST_260_REWRITE_CANDIDATE_2026-11-23.json`, commit de ajuste `71ab459b5e151db4789991eed1da6b699c08fb64`.
- Novo título: **Smartwatch e frequência cardíaca: o que verificar** (49 caracteres); **mesmo ID e slug**.
- Metadescrição e excerpt atualizados: **147 caracteres**. Palavra-chave foco AIOSEO: `smartwatch com frequência cardíaca`.
- HTML revisado: **10.094 caracteres / 1.207 palavras aproximadas / 7 H2 / 1 cartão Shopee / 2 âncoras afiliadas da mesma campanha / 1 imagem inline original / 1 disclosure / 2 links internos** para o hub Smartwatches e artigo #138. Dois links externos para as fontes.
- WordPress `wp_update_post(post_id=260,title,content,excerpt)` executado às **15:03:59**, mantendo `status=publish`, categoria Tecnologia ID 3, mídia destacada ID 261, permalink original e data original do post. É uma **edição manual autorizada** de post já publicado, não ativação de LIVE automático.
- AIOSEO `seo-data-update` confirmou novo title, description, focus_keyphrase e **robots noindex=false**. SEO score permaneceu 0, o que não representa performance de Google.

## Dupla verificação posterior
1. `wp_get_post_full(context=edit)` encontrou conteúdo HTML **byte a byte idêntico** à prévia GitHub, título e excerpt iguais ao esperado, categoria ID 3, featured_media 261, status `publish`, slug original e `modified=2026-11-23T15:03:59`; zero vazamento `O leitor`.
2. `wp_ability_aioseo_posts_seo_data_get(postId=260)` devolveu title, description e focus keyword novos, canonical default, `noindex=false`.
3. Firecrawl live público `maxAge=0` retornou title novo, **1 único bloco comercial** na página, o link afiliado original presente, fonte acadêmica presente, nenhum texto antigo “O leitor busca um smartwatch...” e nenhum noindex visível.

## Próximos passos
- Continua a Etapa 4 com próximo candidato **#314 Ventilador**, mas **cada post precisa do seu próprio backup, conferência de link e validação antes de editar**.
- O post #260 NÃO deve ser reeditado se o mesmo checkpoint for lido em novo chat, salvo nova solicitação expressa. Conferir seu `modified` antes de ações.
- Outros nove candidatos do C115 continuam pendentes neste checkpoint. Categoria Ar-condicionado ID 20 ainda tinha zero artigos na última auditoria.
- LIVE automático do legado continua desligado e V31 universal mantém oito testes antigos pendentes. Não reativar workflows.

**Código de retomada:** `V31-RADAR-C116-20261123-POST260-LIVE-EDIT-VERIFIED`.
