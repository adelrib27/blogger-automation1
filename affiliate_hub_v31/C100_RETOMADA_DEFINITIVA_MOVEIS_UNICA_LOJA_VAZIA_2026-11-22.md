# V31 C100 — PONTO DE RETOMADA DEFINITIVO — APÓS AUDITORIA DE REDIRECIONAMENTOS

**Data:** 22/11/2026 (America/Recife). **Branch:** `main`. **Repositório:** `adelrib27/blogger-automation1`.

## PRIORIDADE ZERO: não repetir o erro de inventário
O primeiro C100 contou 19 Blogger Pages `/p/loja.html` sem produtos e as chamou de Lojas vazias. **A contagem estava INCORRETA.** Das 19, **18 redirecionavam por JavaScript** a um post `Loja` que já continha 20 links Shopee afiliados (Achados para Casa: 32). Essa conclusão foi comprovada com `list_pages`, `get_page`, `search_posts_by_title` e `get_post` autenticados para os 18 blogs. [Auditoria retificadora](CHECKPOINT_C100_CORRECAO_REDIRECIONAMENTOS_LOJAS_2026-11-22.md) é fonte prioritária sobre documentos anteriores.

## Estado FINAL efetivo na C100
- **32 Blogger**: 29 com produtos comerciais antes de C100 (18 via post/redirecionamento; 11 via página), 1 LAB com produtos excluído, 1 blog não lançado excluído, **1 Loja de produção de fato sem produtos**.
- **3 WordPress** com páginas Loja já preenchidas: Radar Tech, Casa e Decoração, Oficina & Garagem, não tocadas.
- **2 PAGES comerciais foram AMPLIADAS antes da descoberta:** Achados para Casa de redirecionamento a post de 32 links para uma página nova de 36 produtos; Cozinha Sem Complicação de redirecionamento a post de 20 links para página nova de 32 produtos. Ambas LIVE, GET CMS exato e URLs públicas verificadas, artigos Loja antigos preservados, não duplicar update nem apagar posts.
- **16** redirecionamentos restantes para post Loja com 20 ofertas cada: preservados intactos; não há justificativa para abastecer por “vazio”.
- Uma tentativa de ampliação opcional de Casa em Ordem consultou 19 ofertas até a Shopee retornar `10030`; a Loja existente COM 20 links continua operacional. Não assumir bloqueio comercial.
- **ÚNICA Loja comercial verdadeiramente vazia:**
  - Nome: **Móveis para Cada Canto**
  - Blog ID: `1439741542627895062`
  - Page ID: `5105320514641154037`
  - URL: https://moveisparacadacanto.blogspot.com/p/loja.html
  - `Blogger_Bridge_V2.get_page`: página LIVE com texto de apoio, 0 `<img>` e 0 `s.shopee.com.br`; **não há redirect para Loja post**.
  - `search_posts_by_title(title="Loja", match="exact", status="live")` retornou **nenhum post Loja**.
  - R2: 594 produtos classificados em `casa/moveis` (não são automaticamente ofertas aptas nem links convertidos).
  - Último estado da Shopee Affiliate API foi `10030` no outro blog; nenhuma nova chamada realizada depois desse bloqueio nesta fase.

## Código de execução pronto para retomada
- Manifesto anti-duplicação: `affiliate_hub_v31/C100_ROLLOUT_MANIFEST.json` já retificado: **16 EXISTING_STORE_POST_PRESERVED, 2 PAGE_UPGRADED_EXISTING_STORE_POST_PRESERVED, 1 PENDING_TRUE_EMPTY_STORE**.
- Estado geral `affiliate_hub_v31/CONTINUIDADE_ESTADO.json` também retificado: `c100_store_expansion.pending_shops=1`.
- Candidato de Móveis pela biblioteca R2 sem mutação: `affiliate_hub_v31/c100_r2_exact_readonly.py --sites moveis`; exige ambiente `v31-editorial-safe`, credenciais Shopee e R2, executar no GitHub Actions em período de API disponível, **sem gerar shortlinks, não escrever em R2, D1 nem CMS**. A revisão do guard de produtos principais, inclusive exclusão de ferragens/peças de móveis, foi implantada após a detecção de falsos positivos.
- Renderizador HTML `affiliate_hub_v31/c100_shop_renderer.py --input <JSON> --site moveis --guides <JSON> --output <HTML>`, exige **24 ou mais** anúncios distintos com `shopId:itemId`, `imageUrl`, `offerLink` reais, rating e categorias; layout C98 grade única + botão C99 `#D83F00`.
- **Teste offline de guardas:** [GitHub Actions #45080445023](https://github.com/adelrib27/blogger-automation1/actions/runs/45080445023) executou 6 testes unitários em PASS, com casos de air fryers, liquidificadores, ventiladores, móveis reais vs peças e outros nichos. Nenhuma chamada externa Shopee/CMS nesses testes.

## Guias internos reais do blog Móveis (confirmados por API)
1. [Mesa de escritório em L Miguel 150x150 cm](https://moveisparacadacanto.blogspot.com/2026/11/mesa-de-escritorio-em-l-miguel-150-150_01046554637.html)
2. [Sofá para sala pequena](https://moveisparacadacanto.blogspot.com/2026/11/sofa-para-sala-pequena-como-escolher.html)
3. [Guarda-roupa para quarto](https://moveisparacadacanto.blogspot.com/2026/11/guarda-roupa-para-quarto-portas-medidas.html)
4. [Home office confortável: mesa e cadeira](https://moveisparacadacanto.blogspot.com/2026/11/home-office-confortavel-como-escolher.html)

## Protocolo para próxima sessão
1. Ler **primeiro** este arquivo, `V31_CONTINUAR_AQUI.md`, `C100_ROLLOUT_MANIFEST.json`, `CONTINUIDADE_ESTADO.json` e checkpoint da retificação, não só o inventário C100 preliminar.
2. Revalidar por API Blogger se a Page Móveis ainda existe e continua sem anúncios. Não criar outra página.
3. Só consultar a Shopee quando a cota permitir, em READ ONLY. Em caso de `10030` ou menos de 24 ofertas confirmadas, registrar bloqueio e preservar a Page.
4. Quando houver >=24 anúncios elegíveis, priorizar móveis completos e variantes coerentes, vendedor diverso, comissão do vendedor, reputação e demanda sem prometer estoque. Validar manualmente riscos de peças de reposição e identidade produto-imagem-link. Usar 4 guias reais.
5. **Antes de qualquer update:** salvar HTML atual em `affiliate_hub_v31/backups` via GitHub e conferir bytes/ID. Criar export completo em `affiliate_hub_v31/exports`; testar invariantes 1 card=1 foto=1 oferta, 24+, CTA sponsored laranja `#D83F00`, links internos verificados. Então uma única atualização da Page existente com request_id exclusivo.
6. GET autenticado confirmando HTML idêntico e status live; verificar público desktop e mobile, se possível, e tema não exibe clones visíveis.
7. Atualizar manifest + checkpoint + `CONTINUIDADE_ESTADO.json` + `V31_CONTINUAR_AQUI.md`. Não repetir lojas já concluídas.
8. **NÃO alterar** o LIVE automático de artigos, C81 HMAC/DRAFT, outras lojas, posts legados, Pinterest, R2 ou D1. Não prometer continuação em segundo plano sem agendamento autorizado e efetivo.

## Nota sobre dois upgrades e SEO
As novas Blogger Pages Achados e Cozinha não substituíram fisicamente os antigos POSTS “Loja”; ambos continuam públicos em endereços `/2026/.../loja.html`. Isso não é necessariamente conteúdo idêntico, mas pode gerar competição de SEO e navegação ambígua. Um projeto futuro pode avaliar `canonical`, links internos, sitemap e eventual atualização das URLs antigas, **após backup e autorização específica**. Não executar remoção automática.

**Resultado presente:** documentos, fonte, testes e estado de continuidade salvos. **1 Loja realmente vazia PENDENTE por validação de 24+ anúncios após recuperação da API.** Não atribuir qualquer escrita futura já realizada.
