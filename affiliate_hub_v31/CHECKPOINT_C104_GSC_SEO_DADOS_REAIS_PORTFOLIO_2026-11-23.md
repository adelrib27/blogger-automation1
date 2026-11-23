# V31 C104 — Search Console conectado: 1ª auditoria REAL de desempenho e indexação
**Data:** 23/11/2026 (America/Recife). **Somente leitura de Search Console**, sem exclusões/publicações/alteração de sites.
**Provedor:** OpenSEO, projeto `a4655e65-afb6-44e0-a54e-89c31e165d7f`, Google conectado `comercebem@gmail.com` (não registrar IDs de sessão ou tokens). 
**Contexto:** Plano estratégico C103 sugeria 10 projetos comerciais a manter e 23 Blogger a congelar/descontinuar por sobreposição de nichos. C104 acrescenta DADOS reais; não confundir recomendação de portfólio com comprovação de zero tráfego/vendas.

## Cobertura de propriedades
- OpenSEO confirmou conexão Google Search Console operacional, `requiresReconnect=false`, `apiDisabled=false`.
- API listou 15 propriedades cadastradas nesta conta; **5 sites distintos correspondentes ao V31 estão com verificação siteOwner**: `sc-domain:achadosparacasa2026.blogspot.com`, `https://ar-condicionado-sem-duvidas.blogspot.com/`, `sc-domain:radartechbr.com.br`, `https://oficina.radartechbr.com.br/`, `sc-domain:casaedecoracao.radartechbr.com.br` (também versão URL específica `https://casaedecoracao.radartechbr.com.br/`).
- **Demais blogs do V31 não constam como propriedades verificadas nesta conexão.** Ausência de dados de GSC NÃO é prova de zero tráfego ou zero indexação. Há outras propriedades não relacionadas com estado `siteUnverifiedUser`, não considerá-las V31.
- A propriedade de domínio `sc-domain:radartechbr.com.br` inclui subdomínios; agrupar URLs por hostname ao apresentar métricas para evitar dupla contagem com propriedade da Oficina.

## Desempenho orgânico verificado: busca Web, dados FINAL (Pacífico), 20/08 a 20/11/2026 (93 dias)
| Site distinto | Impressões reportadas por PÁGINAS | Cliques | URLs com dados | Estado |
|---|---:|---:|---:|---|
| **Radar Tech BR** — SOMENTE hostname `radartechbr.com.br` | **546** | **3** | **28** | Tráfego orgânico inicial e URLs indexadas |
| **Oficina & Garagem** — SOMENTE `oficina.radartechbr.com.br` | **79** | **0** | **12** | URLs indexadas; visibilidade inicial |
| **Achados para Casa** | **5** | **0** | **1** | Visibilidade mínima; investigar erro de redirecionamento da home |
| **Casa e Decoração WP** | **0** | **0** | **0** | Precisa investigar descoberta/indexação de URLs; não afirmar penalização |
| **Ar-Condicionado sem Dúvidas** | **0** | **0** | **0** | Página detectada, ainda não indexada no instantâneo |
| **TOTAL sem dupla contagem** | **630** | **3** | **41** | Não representa outros 30 blogs não verificados |

**Observação importante:** relatório de consultas (queries) pode omitir consultas anonimizadas, portanto não somar linhas de consultas como total do site; utilizar métricas por página e distinção de host. A janela termina em 20/11 para evitar dados incompletos dos ~3 dias recentes.

## Últimos 28 dias completos: 24/10 a 20/11/2026
- Radar Tech hostname principal: **472 impressões, 2 cliques, 27 URLs**.
- Oficina hostname próprio: **78 impressões, 0 cliques, 11 URLs**.
- Achados para Casa: **5 impressões, 0 cliques, 1 URL**.
- Casa e Decoração e Ar-Condicionado: nenhum resultado por página no período anterior.
- Esses valores são muito pequenos para avaliar lucratividade; todos os sites são relativamente novos e GSC não atribui vendas Shopee.

## Indexação de URL (amostra, API de inspeção do Search Console)
### Radar Tech — confirmação POSITIVA
- `https://radartechbr.com.br/` — `Enviada e indexada`, crawled 13/11/2026, canonical do Google = declarado, robots ALLOWED, fetched SUCCESSFUL.
- `https://radartechbr.com.br/arctic-air-cooler-portatil-o-que-conferir-antes-de-comprar/` — `Enviada e indexada`, crawled 13/11, canonical correto.

### Oficina & Garagem — confirmação POSITIVA
- `https://oficina.radartechbr.com.br/` — `Enviada e indexada`, crawled 20/10.
- `https://oficina.radartechbr.com.br/como-escolher-o-jogo-de-chaves-ideal-para-seu-carro/` — `Enviada e indexada`, crawled 13/11.
- `https://oficina.radartechbr.com.br/como-escolher-o-melhor-pano-de-microfibra-para-limpeza/` — `Enviada e indexada`, crawled 22/11.
- Uma página tem 33 impressões e outra 26 (no período de 93 dias), embora 0 cliques. Não descartar esse domínio com base em cliques zerados.

### Casa e Decoração WP — ALERTA INVESTIGAR, NÃO CONCLUIR FALHA AUTOMATICAMENTE
- `https://casaedecoracao.radartechbr.com.br/`, `/organizando-o-banheiro-com-prateleiras/`, `/organizando-o-espaco-com-varal-de-chao/`: as 3 inspeções retornaram `O Google não reconhece o URL` e `verdict NEUTRAL`. Não há lastCrawlTime, robots nem fetch registrados nessas amostras. Possível descoberta/indexação ainda pendente, sitemap/canonical/robots/visibilidade; requer auditoria técnica. **Não declarar que todas as 51 páginas estão desindexadas** com base só em 3 inspeções.

### Ar-Condicionado sem Dúvidas — PREPARAR SAÍDA, SEM APAGAR
- Home e artigo `/2026/11/antes-de-instalar-ar-condicionado-split.html` retornaram `Detectada, mas não indexada no momento`. 0 impressões/clicks. O artigo é de 23/11 e não poderia ter tempo para maturar até o corte de métricas 20/11. Não inferir baixa qualidade por isso; estratégia de juntar ar-condicionado no hub Casa WP continua plausível.

### Achados para Casa — PRIORIDADE CORREÇÃO
- Homepage `https://achadosparacasa2026.blogspot.com/`: inspeção GSC indica `Erro de redirecionamento` com `pageFetchState REDIRECT_ERROR`, robots ALLOWED, última tentativa rastreada 10/10/2026. **É o último estado conhecido pelo Google naquela data, NÃO prova de que o redirecionamento ainda falha hoje**.
- Um artigo `/2026/10/como-escolher-o-tamanho-certo-de.html`: `Rastreada, mas não indexada no momento`; crawl 30/10/2026, fetch SUCCESSFUL, canonical reconhecido, citado em sitemap, 5 impressões GSC; dados de busca e inspeção podem variar de data/estado. Ação: investigar homepage e cobertura/sitemap, não excluir acervo de 85 posts precipitadamente.

## Revisão executiva de C103
1. **MANTER — prioridade confirmada por indexação:** Radar Tech BR, Oficina & Garagem. Não confundir 0 cliques da Oficina com ausência de indexação (3 URLs inspecionadas indexadas).
2. **MANTER, MAS DIAGNOSTICAR URGENTEMENTE:** Casa e Decoração (51 posts, 3 URLs não reconhecidas) e Achados para Casa (85 posts, home com último erro de redirect). A decisão de mantê-los é estratégica; não se comprovou tráfego correspondente.
3. **AR-CONDICIONADO EM PAUSA/CONSOLIDAÇÃO:** Sem impressão e sem indexação nas 2 URLs amostradas, mas conteúdo recente; seguir plano de não ampliar o site e avaliar migração ao núcleo Casa.
4. **Outros Blogger:** falta de propriedade Search Console verificada impede qualquer classificação empírica de tráfego. Plano C103 de congelamento por SOBREPOSIÇÃO continua como hipótese editorial; **não realizar exclusões físicas nem migrações automáticas**.
5. **AÇÃO DE PRIORIDADE:** resolver descoberta/indexação e errados de redirecionamento de sites que já produzimos antes de publicar em escala. Conectar/verificar GSC de blogs potencialmente eliminados e medir cliques/comissões de afiliados antes da destruição definitiva.
6. Monitorar por 60–90 dias após correções, com métricas e custos por site (impressões, cliques, CTR, consultas, indexação, conversão afiliada e comissão líquida). Rankings não são garantidos.

## Segurança e continuidade
- Operações: `OpenSEO.list_projects`, `list_search_console_sites`, `set_search_console_site` alternando propriedade do projeto para consultas e `get_search_console_performance` / `inspect_urls`. Última propriedade selecionada no projeto ao registrar este checkpoint: `sc-domain:radartechbr.com.br`. A seleção de propriedade no OpenSEO mudou para leitura; **nenhum blog/CMS/tema/cron foi alterado**.
- Nenhum novo artigo, nenhuma exclusão, nenhum redirecionamento, nenhuma escrita R2/D1/Pinterest, nenhuma ativação de LIVE automática.
- **O relatório C103 de recomendação 10/23 NÃO foi implantado**: permanece decisão condicionada a dados adicionais e plano técnico reversível.
- Próximo chat: ler C104 antes de C103; NÃO confundir propriedade de domínio Radar com URLs/subdomínio Oficina e não extrapolar amostra de indexação como site inteiro.

**STATUS C104: Search Console integrado e 5 propriedades V31 consultadas; prioridades de indexação definidas, deletar 0 sites.**
