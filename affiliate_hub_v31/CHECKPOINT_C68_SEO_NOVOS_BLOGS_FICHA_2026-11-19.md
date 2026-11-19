# C68 — nova geração de blogs: SEO, links internos e ficha técnica (19/11/2026)

**STATUS FINAL: C68 CONCLUÍDA — norma SEO e biblioteca SAFE para NOVOS blogs implementadas/CI validado; nenhuma automação existente alterada.** Prévia anterior preservada abaixo.

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

## C68 — implementação entregue e homologação offline (19/11)

- [PR #95 MERGED](https://github.com/adelrib27/blogger-automation1/pull/95), commit `cfb54ad24fe688087f497713247dea6b52d51f9c`. [CI #44588998921](https://github.com/adelrib27/blogger-automation1/actions/runs/44588998921) **SUCCESS: 427 testes V31 +24 Casa +21 Oficina +15 Radar + cross-blog guard PASS**. Em relação à C67, **20 testes C68 novos**.
- Norma [ESTRATEGIA_NOVOS_BLOGS_SEO_SHOPEE_V1.md](ESTRATEGIA_NOVOS_BLOGS_SEO_SHOPEE_V1.md) salva com **11 seções e diretriz final da ficha**, SEO on-page, técnico, off-page, local quando verdadeiro, clusters, links internos, pesquisa de intenção, comissão positiva sem mínimo 3%, erro API `10000` separado de inelegibilidade, rotação documentada, isolamento e KPIs apenas com fontes.
- **Código offline novo** [future_blog_seo.py](future_blog_seo.py), sem API/CMS/R2: `plan_internal_links` prioriza pilar e páginas do mesmo cluster com posts realmente `publish/live` em mesmo hostname HTTPS; bloqueia drafts, links estrangeiros, query/fragment, duplicações e auto-link; cold-start registra explicitamente nenhum link em vez de inventar. `render_related_links` escapa HTML e aplica verificação de host; `audit_future_article` exige evidência externa datada da palavra-chave, headings/alt/aviso/com link `sponsored`, rejeita falsa marcação Review, solicita validação de schema Product e links publicados; sinaliza medições não acessíveis em código (`Core Web Vitals`, rastreamento, pesquisa de mercado, SKU de foto, atual oferta Shopee) sem inventá-las.
- [Teste novo test_c68_future_blog_seo.py](tests/test_c68_future_blog_seo.py) validou 20 casos SAFE: primeiro blog sem posts, pilar/satélite, links estrangeiros, posts não publicados, autopontuação, não preenchimento de 3 links, metadados, intenção/pesquisa, alt, sponsored e schema não verificado.
- [Template de onboarding](future_blog_onboarding.template.json) com campos `UNKNOWN` e `null`, fora dos cadastros reais, para exigir nicho, campanha, fonte de pesquisa, identidade técnica, isolamento secrets/quotas, clusters, CWV, SEO local apenas se negócio elegível e SAFE/LIVE. [Guia de cadastro sites.d](sites.d/README.md) agora aponta **o padrão obrigatório de revisão de próximos projetos**. Nenhuma rota/blog fake foi ativada.
- **SEM alterações nos escritores/agendamentos de Blogger ou WordPress existentes**, no catálogo R2, nos sistemas LIVE, nos posts ou nas credenciais. O código novo é biblioteca SAFE **para ser chamado pelo provisionador de cada novo blog real**; não afirmar que uma automação futura não criada já usa o código. Aplicar integração e auditoria CMS no onboarding específico, após o usuário indicar nicho/blog e fornecer fontes/conexões reais.

## Escopo das provas e pendências

**HOMOLOGADO AGORA:** extração técnica da ficha, documentação SEO universal future-only, teste automatizado de links internos e preflight editorial offline, 427 CI V31 e legados PASS. **NÃO EXECUTADO POR NÃO HAVER NOVO BLOG:** pesquisa de SERP para nicho escolhido, criação de repositório independente, conexão real Search Console, configuração de meta no WordPress plugin/Blogger, canonical/sitemap/robots/CWV num domínio novo, schema público, pesquisa de comissão atual, abertura de novo blog ou publicação. Esses requisitos não podem ser simulados pelo template.

**PENDÊNCIA ANTERIOR INALTERADA:** verificar 20/11/2026 10h10 America/Recife evento genuíno `event=schedule` dos 3 crons V31; a rotina de leitura C65 já existe. A C68 NÃO verificou nem resolveu o scheduler externo e não modificou esses workflows.

**Protocolo:** fechar `CONTINUIDADE_ESTADO.json` como `PRONTO_PARA_PROXIMA_ETAPA`, apontar `V31_CONTINUAR_AQUI.md` ao checkpoint C68, registrar PR/CI e preservar autorização LIVE específica C67 já cumprida.
