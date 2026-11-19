# C68 — nova geração de blogs: SEO, links internos e ficha técnica (19/11/2026)

**STATUS: EM_ANDAMENTO — checkpoint prévio registrado antes de desenvolver.**

## Solicitação do proprietário
Aplicar **aos próximos blogs** (Blogger e WordPress) as diretrizes de SEO on-page, técnico, autoridade/off-page e local quando houver pertinência, além de obter **o máximo da ficha técnica anexada**: `FICHA TÉCNICA — NOVA ESTRATÉGIA DE BLOGS AUTOMATIZADOS COM SHOPEE`, v1.0 datada **12/11/2026**, aprovada para planejamento e desenvolvimento. A ficha se aplica a **novos projetos**, não é autorização para editar LIVE antigos ou criar blogs futuros fictícios. Usuário não selecionou nicho, nome, domínio ou novos dados de conexão nesta solicitação. Projeto continua universal.

## Fonte técnica e interpretação sem inventar fatos
Fonte primária: texto anexado nesta conversa, 11 seções + diretriz final. Prioridades: demanda/compra planejada/necessidade do consumidor → pauta SEO de decisão → SKU Shopee de campanha comprovada. Categorias da tabela são **exemplos** e não limitam nichos futuros. Comissão **positiva e verificável**, sem mínimo 3%, sem exigir extra do vendedor; valor em reais estimado é apenas indicador e só quando preço e comissão real foram comprovados. A API comercial e o catálogo R2 têm papéis separados: erros 10000 tratados como erros de API, não como ausência de elegibilidade; nenhuma revisão em lote aprovada por inferência.
- A ficha pede preferencialmente repositório **independente por blog**, CI e cron/secrets/histórico por destino; preservar o V31 como biblioteca/motor universal compartilhável por configuração, **não copiar segredos** nem credenciais entre projetos e não criar novos repos sem um blog real e sua autorização.
- Gatilhos LIVE: somente após SAFE, revisão editorial/comercial, consentimento individual; não alterar crons/publicações existentes. Credenciais Shopee em repositórios distintos **não implicam cotas independentes** se app for a mesma.

## Conteúdos novos solicitados
- SEO on-page: intenção comercial real, clusters (pilar/satélites), palavra-chave principal/cauda longa comprovada, H1/título, meta description, introdução que responde à dúvida, comparação honesta, FAQ textual quando pertinente, imagens do próprio SKU (alt específico, dimensões e carga otimizadas), links de afiliado com `rel=sponsored nofollow`, reviews/testes nunca simulados.
- Links internos: apenas URLs HTTPS **existentes e publicadas no MESMO blog**, âncoras descritivas, pertinência do assunto e links **pilar ↔ cluster**; não preencher quantidade artificial quando novo blog não tem histórico. Detectar órfãs, quebrados, externos indevidos e duplicatas. Não ligar entre campanhas/sites apenas por compartilhar acervo.
- Técnico: responsividade/móvel, Core Web Vitals LCP/INP/CLS, HTTPS, canonical, sitemap XML, robots/indexação, slugs legíveis quando possível, schema `Article`/`BlogPosting` e `BreadcrumbList` apenas com fatos verdadeiros; **não** gerar `Review`/ratings/`Product` como se o blog fosse lojista ou tivesse avaliado produto sem elegibilidade/fatos. Validar por plataforma (tema/plugins).
- Off-page: processos editoriais verificáveis (autoria, transparência, fontes, menções e outreach legítimo); backlinks não podem ser prometidos/gerados artificialmente. SEO local **somente** com empresa local/atendimento real, NAP comprovado; blogs afiliados nacionais comuns **não** precisam de perfil de empresa fictício.

## Plano de implementação C68
1. Registrar esta prévia e estado JSON `EM_ANDAMENTO` na main antes de mudanças.
2. Criar **norma canônica v1.0** com extração máxima da ficha, contratos de dados, critérios de aceitação SAFE, status `AVAILABLE / UNKNOWN / NOT_APPLICABLE`, scorecards e checklist por Blogger/WordPress. Guardar fontes oficiais Google Search Central sem inventar ranking.
3. Criar **módulo puro, offline** reutilizável para próximos blogs: brief/validação SEO e seleção de links internos publicados, pertinentes, mesmo domínio; disponibilizar contrato de saída auditável, sem writes/publish. Incluir testes de cold-start, links estrangeiros, posts DRAFT, duplicidade, anchor text e SEO de produto sem Schema fictício.
4. Integrar ao **intake de FUTUROS sites SAFE** somente se compatível, sem mudar geradores/crons/WordPress e Blogger atuais, sem forçar novos projetos ou travar os artigos existentes. Preparar template de configuração do novo projeto e instruções de adoção.
5. Abrir PR, rodar CI, merge somente com sucesso, consolidar checkpoint e estado/index GitHub. **Cron event=schedule em 20/11 ainda PENDENTE**, independente desta entrega.

## Situação de partida verificável
- `main` C67 `PRONTO_PARA_PROXIMA_ETAPA`: WordPress Casa #305 LIVE confirmado #44583376909; 44 LIVE/58 DRAFT; Blogger Móveis 3 LIVE/2 DRAFT; nenhuma mudança nesses blogs prevista aqui.
- Não há blog novo especificado; não executar integração LIVE, gerar conteúdo ou escolher nicho por conta própria.
