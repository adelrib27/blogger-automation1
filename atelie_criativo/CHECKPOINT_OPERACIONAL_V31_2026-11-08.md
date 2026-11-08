# CHECKPOINT OPERACIONAL V31 — Ateliê Criativo em Casa — 08/11/2026

**Escopo:** blog real de produção; documento de continuidade, NÃO uma etapa de backup. A sequência oficial continua com 15 etapas; reler estado vivo antes de toda próxima alteração. Evidência API não equivale a renderização visual ou E2E.

## Identidade e implementação V31

- **Blog:** Ateliê Criativo em Casa
- **Blog ID:** 8888519348129960729
- **URL:** https://atelie-criativo-em-casa.blogspot.com/
- **Página LOJA:** ID 2731790842719271847; https://atelie-criativo-em-casa.blogspot.com/p/loja.html
- **Runner:** provision_new_blog_v31 devolveu BLOGGER_NEW_BLOG_V31_CORE_PROVISIONED, settings_validated=true, theme_validated=true.
- **SEO técnico:** preflight de leitura confirmou descrição e descrição de pesquisa, indexação, HTTPS, lazy-load, WebP e fuso GMT-03. Tema V31 declarado validado pelo Runner, mas sem aprovação visual independente desktop/mobile.
- **Estado independente Blogger Bridge V2 em 08/11/2026:** 8 posts LIVE, 8 páginas LIVE. Preservados outros blogs da conta.

## Etapas oficiais e evidências

| Etapa | Estado comprovado | Limite da prova |
| --- | --- | --- |
| 1. Planejamento | Nicho de papelaria, costura, crochê e organização do ateliê; identidade distinta | Planejado |
| 2. Criação pelo Python | Runner e Blogger API confirmaram ID, URL e título | Produção |
| 3. Configurações/SEO | Runner aplicou e releu SEO técnico antes do tema | Validação Runner |
| 4. Tema V31 | Runner confirmou theme_validated=true | Visual independente pendente |
| 5. Institucionais | 7 páginas publicadas, leitura de retorno API | Contato sem E2E de recebimento |
| 6. 3 artigos Shopee | 3 artigos comerciais LIVE com 3 fotos Shopee cada e links afiliados | Renderização visual das fotos pendente |
| 7. Loja Shopee | 16 produtos, 4 categorias, 3 slides, faixa de atualização | API + prova HTTP pública da rotação |
| 8. Mapa editorial | MAPA_EDITORIAL_V31.md publicado no GitHub | Documento |
| 9. Conteúdo-pilar | Guia de organização do ateliê LIVE | API Blogger |
| 10. 4 clusters | Quatro artigos complementares LIVE | API Blogger |
| 11. SEO on-page/links | P1 aponta aos quatro clusters, clusters retornam a P1; zero URLs internas ausentes na lista API | Metadescrição individual no painel não verificada |
| 12. Autoridade/backlinks | PLANO_AUTORIDADE_V31.md publicado no GitHub | Nenhum backlink externo declarado conquistado |
| 13. Automação | PR SAFE aprovado, primeiro LIVE push com prova pública; cron diário em main | Nenhum evento schedule diário ainda comprovado |
| 14. Verificação pública | Rotação prova HTTP 200, 16 cards, 3 slides e carimbo exato | QA visual desktop/mobile via CI recebeu HTTP 429 |
| 15. Ativação | Blog com 8 posts, 8 páginas e Loja LIVE; workflow diário configurado | Não declarar E2E total até pendências verificadas |

## Páginas publicadas (8)

- Sobre — 7579005080133412781 — /p/sobre.html
- Política de Privacidade — 2751170593712027766 — /p/politica-de-privacidade.html
- Termos de Uso — 410568476856480107 — /p/termos-de-uso.html
- Política de Cookies — 1247035994381626127 — /p/politica-de-cookies.html
- Transparência e Afiliados — 2590837417274955670 — /p/transparencia-e-afiliados.html
- Mensagem enviada — 4769157187464956078 — /p/mensagem-enviada.html
- Contato — 4036081139847183731 — /p/contato.html
- LOJA — 2731790842719271847 — /p/loja.html

**Contato:** formulário FormSubmit configurado com nome/e-mail/mensagem e redirecionamento _next para a página Mensagem enviada; entrega real ainda NÃO testada neste blog.

## Artigos publicados (8)

**Três comerciais Shopee, etapa 6 — cada um com 3 imagens de anúncios:**

1. Papelaria criativa para iniciantes: como escolher canetas e marcadores sem desperdício — 6772995545259963458 — /2026/11/papelaria-criativa-para-iniciantes-como.html
2. Costura à mão para iniciantes: como escolher agulhas e passadores de linha — 5644899493099819814 — /2026/11/costura-mao-para-iniciantes-como.html
3. Crochê para iniciantes: como escolher agulhas, kits e marcadores de pontos — 5046891376282671630 — /2026/11/croche-para-iniciantes-como-escolher.html

**Pilar e quatro clusters, etapas 9–10 — cada um com 1 imagem ilustrativa de anúncio:**

- P1: Ateliê de artesanato em casa: guia completo para planejar, organizar e começar — 75799334179381404 — /2026/11/atelie-de-artesanato-em-casa-guia.html
- C1: Como organizar papelaria criativa em pouco espaço — 7375212170065313731 — /2026/11/como-organizar-papelaria-criativa-em.html
- C2: Como guardar agulhas, linhas e materiais de costura com segurança — 7720396551251101010 — /2026/11/como-guardar-agulhas-linhas-e-materiais.html
- C3: Como organizar fios de crochê, agulhas e projetos em andamento — 2862603623628875693 — /2026/11/como-organizar-fios-de-croche-agulhas-e.html
- C4: Como montar uma bancada de artesanato com iluminação e espaço funcional — 2321412906672219031 — /2026/11/como-montar-uma-bancada-de-artesanato.html

**SEO interno:** o pilar aponta aos quatro clusters; estes retornam ao pilar e incluem links editoriais úteis a guias comerciais. Checagem de destinos internos com URLs canônicas da API Blogger não identificou links ausentes. A presença da tag IMG não garante que a foto carregue visualmente.

## Loja, API e rotação diária

- Loja Page ID 2731790842719271847. Marcadores UNIVERSAL_V31_STORE_AUTO_START e UNIVERSAL_V31_STORE_AUTO_END; CSS adr-store-v31-css; classes ub-product-card, ac-store-slide, ub-store-status.
- 16 produtos únicos, quatro cada nas categorias Papelaria Criativa, Costura e Bordado, Crochê e Tricô, Organização do Ateliê. Três slides incluídos na região rotativa. Fotos e links de produto Shopee; preços são referência datada, NÃO cotações em tempo real.
- Busca de costura trazia vestuário inadequado; filtro semântico SAFE passou a recusar peças íntimas/roupas e exigir materiais de artesanato. NÃO reverter essa curadoria.
- **Último banner confirmado pela API:** 08/11/2026 às 02:46 (Recife), 16 produtos, 3 slides.
- Repo: adelrib27/blogger-automation1, branch main; HEAD observado 59001c00922359e6c10d869c024442e61aa971b5 (revalidar sempre).
- Script: atelie_criativo/rotation_v31.py
- Workflow: .github/workflows/atelie_criativo_rotation_v31.yml
- Cron: 0 9 * * * (UTC), correspondente a 06:00 America/Recife, sujeito a atrasos do GitHub Actions. Isolado pelo Blog ID 8888519348129960729 e página ID 2731790842719271847; secrets por GitHub Actions, nunca em código.
- PR #19 merged; PR SAFE run 42452007584: SELF_TEST_PASS e SAFE_OK_NO_WRITE, 16 produtos, changed_ids=16.
- Primeiro LIVE push run 42452070382: PUBLIC_VERIFY_PASS e LIVE_API_AND_PUBLIC_PASS, 16 produtos, changed_ids=16, 3 slides; propagação pública demorou alguns retries. Blogger Bridge confirmou posteriormente. **Não alegar periodicidade diária comprovada até observar evento schedule real.**
- A rotação de 20 minutos do Achados da Rotina é separada e não foi modificada.

## QA público e pendências

- PR #20 é somente diagnóstico de Playwright visual, NÃO mesclado. Primeiro run 42452266738 falhou por dependência do navegador em Ubuntu 26.04. Segundo run 42452322398 inicializou Chromium no contêiner oficial, mas o Blogger respondeu HTTP 429 em visualizações desktop/mobile e páginas consultadas. HTTP 429 do robô NÃO prova indisponibilidade ao público, mas inviabiliza declarar imagens visualmente validadas.
- Browser conectado mostrou Loja, categorias e links, porém seu snapshot pode ser anterior à última rotação; não usar como readback da execução mais recente.
- PR #16 da curadoria SAFE de catálogo também permaneceu sem merge.
- **Pendências reais:** (a) inspeção visual desktop/mobile em Chrome confiável, fotos carregadas, 3 slides e ausência de overflow; (b) teste de envio e recebimento FormSubmit e redirecionamento; (c) primeira execução originada por schedule diário e próximas repetições; (d) SEO/metadescrição individual no painel quando possível.
- NÃO fazer múltiplas tentativas automatizadas que agravem 429; inspecionar o Blogger/API com moderação ou usar Chrome local.
- Outro blog Jardim e Horta na Prática, ID 3644898524310766003, pertence a fluxo paralelo; tema pendente em outra conversa, não modificar por engano.

## Retomada segura

Primeiro leia estado REAL de blog ID, URL, tema, títulos, HTML, páginas e posts, GitHub HEAD, branches, PRs, cron e logs; compare antes de escrever. Qualquer divergência ou alteração paralela interrompe a execução. Usar o contrato V31, sem migrar para V20, sem alterar blogs diferentes e sem afirmar validações ausentes. A ordem oficial é 15 etapas: planejamento → criação Python → SEO → tema V31 → institucionais → 3 artigos Shopee → Loja → mapa editorial → pilar → clusters → SEO/interlinks → autoridade → automação → QA público → ativação. Nenhuma etapa de backup foi adicionada.
