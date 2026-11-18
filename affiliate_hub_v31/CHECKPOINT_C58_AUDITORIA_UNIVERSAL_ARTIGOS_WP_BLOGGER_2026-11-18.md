# C58 — Auditoria e teste universal de artigos Blogger/WordPress (em andamento)

**Estado atual:** EM_ANDAMENTO — início salvo antes de operações no [CONTINUIDADE_ESTADO.json](CONTINUIDADE_ESTADO.json), commit `199bdee0fd16884b68f4fd10455dacf59a03c6d6`.

## Missão e escopo

Testar e concluir o fluxo de artigo com produto REAL do catálogo universal R2 e 2 CSVs Shopee: curadoria -> seleção por tema/site -> foto real do SKU -> link convertido na campanha **exata** -> texto original -> links internos reais -> CTA -> rascunho -> publicação apenas quando autorizada. Não restringir o sistema aos três WordPress ou publicar novos posts sem solicitação explícita. Pilotar **Casa e Decoração** (WordPress com automação editorial já instalada), aplicar correção universal também a Oficina & Garagem, Radar Tech BR e Blogger.

## Verificações iniciais em serviços REAIS (18/11/2026)

- GitHub workflows agendados ativos no código: `casa_editorial_generate_schedule.yml`, `oficina_editorial_autonomous.yml`, `radar_editorial_vnext_autonomous.yml`, e Blogger universal `v31_universal_blogger_autodraft_daily.yml`.
- [Casa run 44393128512](https://github.com/adelrib27/blogger-automation1/actions/runs/44393128512) **FAIL** na criação da fila; traceback `ModuleNotFoundError: No module named 'affiliate_hub_v31'` ao iniciar `casa_decoracao/src/build_editorial_queue.py` sem raiz do repo no PYTHONPATH. O workflow tem descoberta V31 R2 opcional desativada nessa execução; precisa corrigir a invocação, sem alterar o catálogo.
- [Oficina run 44390826656](https://github.com/adelrib27/blogger-automation1/actions/runs/44390826656) **FAIL** na mesma etapa e pela mesma causa.
- [Radar run 44401956211](https://github.com/adelrib27/blogger-automation1/actions/runs/44401956211) **FAIL/QUARENTENA por qualidade**: `alegacao_de_acessibilidade_nao_sustentada`. Não é falha de importação, nem justifica remover o gate. A publicação não ocorreu, e o contrato deliberadamente exigiu confirmação LIVE, mantendo a proteção.
- Leitura diretamente dos três WordPress conectados: Casa **43 posts publish**, Oficina **12**, Radar **32** (contagens retornadas em 18/11; não afirmam quantas foram produzidas por qual mecanismo). Últimos exemplos lidos: Casa post 298 (15/11), Oficina post 112 (14/11), Radar post 311 (17/11). Cada um tinha imagem destacada e URLs Shopee no conteúdo; **nenhum desses três exemplos tinha href para outra postagem do próprio domínio**. Os geradores antigos inserem link de /category/ genérico, mas não links de posts específicos.
- Geradores antigos Casa/Oficina/Radar ainda usam `@cf/qwen/qwen3-30b-a3b-fp8` no default e workflows; C56 já validou modelo Llama 3.3 JSON mode no Blogger, mas isso **não atualizou automaticamente os publicadores WordPress**.
- O núcleo `affiliate_hub_v31/article_commerce.py` C54 constrói imagens/CTA e internos, mas a função `related_articles_html` exige permalink terminado em `.html` (Blogger), rejeitando URLs típicas WP com `/slug/`. Precisará generalizar com segurança e testes antes de chamar fluxo UNIVERSAL.
- Os três jobs antigos são pipelines separados; R2 só entra opcionalmente por workflow de descoberta com flags condicionais. Não declarar que o pipeline WP LIVE inteiro já consome todos os componentes C54.

## Marcos de execução

- [x] C58 prévia no GitHub antes de alterações nos scripts.
- [x] Três runs reais analisados; causas e quarentena diferenciadas.
- [x] Leitura API WordPress para piloto Casa e duas regressões adicionais, zero alterações nos posts.
- [ ] Corrigir PYTHONPATH e testar os três pipelines sem publicar.
- [ ] Tornar links internos universais para URLs WP e Blogger, com posts verificados.
- [ ] Testar piloto WordPress R2 → renderização de artigo → imagem/CTA/links internos; preferir dry-run.
- [ ] Resolver modelo IA descontinuando sem soltar gates de qualidade.
- [ ] CI regressiva + canário seguro real; atualizar estados e encerrar de maneira verificável.

**Regra:** nenhum novo LIVE nem alteração da revisão de produtos; mutações de código GitHub passam por CI, e qualquer canário de publicação deve ser segregado e controlado.

## C58 — Implementação + validação concluídas (complemento)

- [x] [**PR #75 MERGED**](https://github.com/adelrib27/blogger-automation1/pull/75) em `main`: importação de `affiliate_hub_v31` corrigida em scripts de fila Casa/Oficina e em workflows; Radar mantido protegido, com PYTHONPATH também apropriado.
- [x] `related_articles_html` C54 agora aceita URLs Blogger `/2026/11/x.html` **e** WordPress `/slug/` sob o MESMO host, com proteção contra caminhos externos/encodados/redirects.
- [x] `wordpress_related_posts.py` é o seletor universal de até dois artigos internos anteriormente confirmados pela API WordPress no histórico local; usado pelos geradores Casa, Oficina e Radar. Não inventa URLs e não toca em produtos/links Shopee.
- [x] [**CI PR #75 44407154200 SUCCESS**](https://github.com/adelrib27/blogger-automation1/actions/runs/44407154200) — **347 testes V31**, 24 Casa, 21 Oficina + crossblog PASS.
- [x] [**Canário R2 + WordPress + Workers AI REAL C58 44407697822 SUCCESS**](https://github.com/adelrib27/blogger-automation1/actions/runs/44407697822). Campanhas/site exatos e estoque de fotos:
  - `wordpress_casa_decoracao`: **9** produtos aprovados com imagem real e link convertido nesta campanha.
  - `wordpress_oficina_garagem`: **6**.
  - `wordpress_radartechbr`: **15**.
  - Piloto Casa: API WordPress REST pública devolveu **6 posts reais válidos para links internos**; montada em memória prévia HTML com **8 parágrafos originais / 537 palavras**, foto Shopee via CSV/R2, keyword/CTA da campanha exata e **2 links para posts do próprio WordPress**. **0 posts WordPress, 0 links novos Shopee, 0 writes R2**. A geração da IA foi chamada de fato; não é um mock.
- [x] Workflow/gatilho C58 temporários deletados da main após canário PASS.

**Limites de evidência:** a correção dos geradores está em main e a prévia REAL de artigo foi validada. A CI e a prévia não demonstram que o próximo cron Casa/Oficina já rodou depois do patch, nem que um novo post WordPress foi publicado; Radar continuou bloqueando alegação não comprovada corretamente. Geradores LIVE antigos ainda usam modelo Qwen3 perto da descontinuação e não foram migrados na C58.

**Próxima fase sugerida C59:** migrar o modelo dos três geradores WordPress para modelo Workers AI sustentado (com teste HTML/JSON por formato), validar o próximo ciclo em modo seguro, observabilidade de falhas e publicação LIVE só pelo próprio gate existente. Depois trabalhar rota universal WordPress de novos blogs e publicação com liberação própria, sem criar blog/ID fictício.
