# Checkpoint C6 — Fallback CSV/R2 universal, expansível a novos blogs

**Data:** 16/11/2026  
**Código de continuidade:** `V31-EDITORIAL-C6-UNIVERSAL-FALLBACK-20261116-SAFE`  
**Repositório:** `adelrib27/blogger-automation1`  
**PR:** [#52](https://github.com/adelrib27/blogger-automation1/pull/52) — draft, sem merge  
**Branch:** `feature/v31-affiliate-hub-c1-safe-20261115`

## Objetivo confirmado pelo usuário

Os três WordPress já têm **automações próprias**; o V31 não deve criar novos geradores nem duplicar publicadores. É um serviço central de **obtenção de produtos**, que mantém a API Shopee como fonte prioritária e, quando a API registra **erro 1000**, usa o CSV persistido no R2 como alternativa segura. Não restringir a três WordPress: o serviço tem que atender Blogger, WordPress e novos blogs via cadastro declarativo.

## Módulos implementados nesta etapa

1. `routing.py` agora incorpora todos os manifests `*.json` em `affiliate_hub_v31/sites.d/`, além dos cadastros antigos de `site_routes.json`. **Sem número fixo de sites em código**. Todas as rotas precisam ser validadas; campanha e chave duplicadas falham fechadas; `publish_enabled` precisa permanecer `false` nesta etapa SAFE.
2. `sites.d/wordpress_oficina_garagem.json` adiciona **Oficina & Garagem** usando o mesmo padrão. Com isso, há **21 registros atuais** (18 Blogger, 3 WordPress) e espaço para novos, sem alterar Python. Registro de exemplo e instruções em `sites.d/README.md`.
3. `fallback_v23.py` consulta o SQLite restaurado do R2 em **modo somente leitura**, cruza a categoria/nicho autorizados, as palavras-chave de cada blog e as regras de intenção; **somente usa `affiliate_links` já convertidos para a campanha do blog**. Monta os mesmos arquivos de oportunidades que Casa/Oficina consomem: `ranking.json`, `ranking.csv`, `intent_report.json`, `search_signals.json` e `diversity_report.json`. Não inventa vendas, avaliações, preços, comissão ou performance e não converte URLs orgânicas em links afiliados.
4. `opportunity_router.py` preserva scanner Shopee legado e inspeciona as respostas GraphQL sem expor detalhes comerciais. **API com ofertas válidas é preferida**; na ausência de ofertas e com **erro 1000 confirmado**, chama fallback R2. Outros erros sem código 1000 não são silenciosamente encobertos. O router utiliza configuração, scripts e caminhos fornecidos por cada blog, sem nomes hardcoded.
5. Testes em `test_routing.py`, `test_fallback_v23.py` e `test_opportunity_router.py`: regressão de cache afiliado, domínios, campanha por blog, schema de arquivos v2.3, erro 1000, outros erros, e **60 blogs futuros simulados** registrados somente por JSON.
6. Foi testado o **scanner Casa real** `casa_decoracao/src/shopee_oportunidades_casa.py` com API/R2 simulados, confirmando que o router consegue acionar o adaptador sem substituir o scanner original.

## Segurança e limitações

- **NENHUM workflow de publicação existente foi alterado ou ativado nesta etapa.** Não houve post Blogger/WordPress, mutation Shopee ou operação comercial adicional no R2. O teste de erro 1000 foi **simulado**, não uma falha real.
- O catálogo R2 já foi importado e testado nas etapas anteriores. **Nem todas as campanhas dos blogs possuem links afiliados convertidos no cache.** A presença do produto no CSV não é suficiente para publicação. Sem link cacheado, a integração falha seguramente.
- Para operação autônoma: pré-converter lotes de produtos relevantes por campanha **enquanto a API Shopee estiver funcionando**; depois alimentar os workflows com o router. O CSV sozinho não cria links afiliados.
- O fluxo atual Radar Tech BR consome `fila_dia.json`/slots e não o contrato v2.3; precisa de um adaptador adicional de saída, reutilizando a infraestrutura central. Blogger pode ter outros formatos também.
- A possibilidade de reutilizar produtos é confirmada; porém alguns **publicadores legados ainda vetam produtos publicados anteriormente**, independentemente de assunto. Revisar esses gates para usar **pauta/título diferentes**, com testes dedicados, antes de modificar produção.
- Para registro de blog novo ainda são necessários **identificador/domínio real, campanha, nichos, config de palavras-chave e credenciais de publicação próprias**. Autodescoberta significa que o código não precisa ser editado, não que um site sem cadastro/credenciais possa publicar automaticamente.
- A proteção de branch do Environment `v31-editorial-safe` e rotação da App Secret exposta previamente seguem pendentes de confirmação.

## Próximo trabalho, sem acionar LIVE

1. Verificar produto/link cacheado para campanhas Casa e Oficina; implementar **pré-aquecimento de links** por campanha sem dependência do Windows e com limites de API.
2. Testar os wrappers de Casa/Oficina no contrato v2.3 com leitura do R2 real e API simulada; garantir que nenhum fluxo de publicação roda com `offerLink` inválido.
3. Criar adaptador de slots do Radar Tech BR, e equivalentes Blogger quando necessário, **sem substituir os publicadores**.
4. Conectar o router às etapas de descoberta dos workflows em branch de testes, mantendo condições de publicação `false`; só liberar depois de aprovação de segurança, rollback e validação real de ponta a ponta.
5. Adicionar novos sites via `sites.d/*.json`, validar URL/ID/credenciais e habilitar por ondas.

**Estado:** motor universal e testes offline concluídos; integração nos workflows de produção e fallback real ainda não habilitados.
