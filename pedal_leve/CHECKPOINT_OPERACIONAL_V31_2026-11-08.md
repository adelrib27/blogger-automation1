# CHECKPOINT OPERACIONAL — Pedal Leve V31 — 08/11/2026
**Status:** blog real público, configuração SEO e Tema V31 validados, páginas e conteúdo publicados, Loja Shopee LIVE e primeira rotação real aprovadas. **Pendências isoladas:** Contato FormSubmit E2E; ciclos futuros por cron; publicação automática de novos artigos não configurada.

## Identidade (não reutilizar em outros blogs)
- Nome: **Pedal Leve — Mobilidade e Ciclismo Urbano**
- Blog ID: `4073458513010284301`
- URL: https://pedal-leve-mobilidade-urbana.blogspot.com/
- Idioma: pt-BR; fuso: America/Recife.
- Nicho: mobilidade por bicicleta, ciclismo urbano, manutenção básica e acessórios.
- Categorias da vitrine: Segurança e Visibilidade; Manutenção e Ferramentas; Bolsas e Transporte; Conforto e Acessórios.

## Criação / Tema / SEO
- Runner `provision_new_blog_v31`: `BLOGGER_NEW_BLOG_V31_CORE_PROVISIONED`, `settings_validated=true`, `theme_validated=true`; Blogger Bridge confirmou Blog ID, nome e URL.
- GitHub Actions SAFE `42456633745` confirmou HTTP 200, título e seletores do Tema V31 no HTML público.
- Runner `preflight_settings` read-only em 08/11: `SETTINGS_PREFLIGHT_OK`, visibilidade de pesquisa, HTTPS, lazy images, WebP e descrição de pesquisa ativos; fuso GMT-03 conforme planejado. Robots TXT e headers personalizados preservados desativados; nenhuma reconfiguração destrutiva.
- Tema V31 não foi reinstalado depois de provisionado.

## Páginas LIVE (readback Blogger Bridge, 8/8)
| Página | Page ID | URL |
|---|---|---|
| Sobre | `515777647427521897` | /p/sobre.html |
| Política de Privacidade | `6350622770346075437` | /p/politica-de-privacidade.html |
| Termos de Uso | `3519514486132220655` | /p/termos-de-uso.html |
| Política de Cookies | `6535541647107611760` | /p/politica-de-cookies.html |
| Aviso de Afiliados | `1834117404561300361` | /p/aviso-de-afiliados.html |
| Mensagem enviada | `8022921473820967967` | /p/mensagem-enviada.html |
| Contato | `5651764171349213719` | /p/contato.html |
| LOJA | `7331621701388164614` | /p/loja.html |

## Posts LIVE (7/7)
| Conteúdo | Post ID | URL |
|---|---|---|
| Pilar: Ciclismo urbano para iniciantes | `5142083525724697249` | /2026/11/ciclismo-urbano-para-iniciantes-guia.html |
| Pilar: Manutenção básica de bicicleta | `3314817259949611365` | /2026/11/manutencao-basica-de-bicicleta.html |
| Pilar: Como escolher acessórios | `7561400798523547232` | /2026/11/acessorios-para-bicicleta-como-escolher.html |
| Cluster: Farol e lanterna | `7967686109888995043` | /2026/11/farol-e-lanterna-para-bicicleta.html |
| Cluster: Kit básico de ferramentas | `5266886226266990609` | /2026/11/kit-basico-de-ferramentas-para.html |
| Cluster: Bolsas de quadro/selim/guidão | `1439744513556056915` | /2026/11/bolsa-de-quadro-selim-ou-guidao-como.html |
| Cluster: Luvas/manoplas/selim | `7942057534360202756` | /2026/11/luvas-manoplas-e-selim-de-bicicleta-o.html |

Pilares apontam para clusters; clusters retornam a pilares, com links contextuais e sem âncoras forçadas. Conteúdo original em pt-BR, sem simular testes próprios. Artigos comerciais com fotos obtidas da API Shopee e disclosure. `MAPA_EDITORIAL_V31.md` e `PLANO_AUTORIDADE_V31.md` documentam SEO, próximas pautas e backlinks legítimos **não garantidos**.

## Loja Shopee LIVE e rotação
- Page ID exclusivo: **`7331621701388164614`**, `/p/loja.html`.
- Fonte de catálogo: consulta **autenticada** à Shopee Affiliate API com `SHOPEE_APP_ID` e `SHOPEE_SECRET` protegidos no GitHub Actions; sem expor valores.
- 4 categorias × 4 produtos reais = **16 IDs únicos**; imagens e `offerLink` assinados validados por domínio, HTTPS, relevância semântica, sem repetição e `nofollow sponsored noopener`.
- Vitrine com 16 cards, 3 slides/carrossel, CSS escopado, marcadores `<!-- UNIVERSAL_V31_STORE_AUTO_START -->` e `<!-- UNIVERSAL_V31_STORE_AUTO_END -->`; atualização substitui somente a região automática e preserva shell; readback Blogger e HTTP públicos.
- LIVE primeira rotação GitHub Actions **`42458344928`** em 08/11/2026: `PEDAL_ROTATION_SELF_TEST_PASS`, `PUBLIC_VERIFY_PASS`, `LIVE_API_AND_PUBLIC_PASS`, **16 itens atualizados e 16 IDs alterados**.
- Readback Blogger independente após LIVE: 16 cards, 16 IDs únicos, 3 slides, CSS único, marcadores preservados, carimbo **08/11/2026 às 04:20 Recife (07:20 UTC)**.
- Workflow `.github/workflows/pedal_leve_rotation_v31.yml`: cron `0 9 * * *` (06:00 Recife), com guardas de Blog ID, Page ID, título, URL, marcadores, ETag/content, 16 produtos, SAFE em PR e LIVE em `main`.
- **Ainda não comprovados três eventos `schedule` futuros**. Não afirmar regularidade cron antecipadamente.
- O pipeline contínuo de publicação automática de **novos artigos** não foi ativado; já há sete artigos LIVE. Não assumir que rotação de vitrine equivale a geração editorial autônoma.

## Provas públicas
- Tema V31: run `42456633745` (PASS).
- Shopee catálogo SAFE após curadoria: run `42457321030` (PASS 16 ofertas sem escrita).
- Loja 16 cards HTML público: run `42457507079` (`PEDAL_STORE_PUBLIC_PASS`).
- Rotação PR SAFE: run `42457971087` (`SAFE_OK_NO_WRITE`, 16 ofertas).
- Auditoria HTML: run `42458240137` (`PEDAL_QA_PUBLIC_PASS`; homepage + 8 páginas + 7 posts, HTTP 200).
- Primeira rotação LIVE: run `42458344928` (`LIVE_API_AND_PUBLIC_PASS`, 16 IDs alterados).
- Teste Playwright de fotos / responsividade: run `42458480174` (`PEDAL_BROWSER_VISUAL_PASS`), 16/16 imagens carregadas na Loja em 1440px e 390px, imagem inicial do artigo também carregada, sem overflow horizontal.

## Contato: PROVA INSUFICIENTE (fail-closed)
- O formulário foi publicado na página `/p/contato.html` e o HTML público verificou campos, FormSubmit e `_next`.
- Teste **único** de envio por Playwright: run `42458795314`. Navegador permaneceu no host `formsubmit.co` sem retornar à página própria; status `CONTACT_E2E_NOT_CONFIRMED`. Nenhuma mensagem correspondente foi localizada na caixa Gmail conectada ao final do teste.
- O FormSubmit pode exigir verificação do usuário; **não presumir CAPTCHA como causa comprovada**, não contornar proteções ou repetir envios às cegas. O teste experimental PR #26 foi encerrado sem merge, preservando evidência. A publicação do formulário não prova entrega de e-mail. Retorno e entrega aguardam confirmação humana/E2E controlada.

## GitHub, isolamento e continuidade
- Repositório `adelrib27/blogger-automation1`, branch principal `main`; HEAD antes deste checkpoint: `e6768eba5f37e402835faa9f2cc943fc8c2f3e52` (reconsultar ao continuar).
- PR #24 (provisionamento de workflow exclusivo, curadoria Shopee, rotação, auditorias, mapa/autoridade) **MERGED** → commit `7debbf05600e03e2b225266ba5c6c86139905cd0`.
- PR #25 (QA visual Playwright) **MERGED** → commit `e6768eba5f37e402835faa9f2cc943fc8c2f3e52`.
- PR #26 (envio teste contato) **CLOSED, NOT MERGED**, não incorporar automatismo de envio.
- Outros blogs, temas, Page IDs e workflows não foram alterados intencionalmente; arquivos novos específicos `pedal_leve/` e workflows prefixados `pedal_leve_`.
- Estado real ao vivo > V31 validada > evidências/checkpoints > histórico. Sempre conferir `main`, Blogger API e estado público antes de qualquer escrita. Nunca publicar novos produtos, preços, imagens ou links imaginários. Sem manipular credenciais, cookies, tokens ou perfis Chrome.

**Próximas verificações:** (1) validar manualmente o FormSubmit e recepção real no Gmail; (2) observar pelo menos três execuções independentes `schedule` com `LIVE_API_AND_PUBLIC_PASS` e mudança de IDs; (3) se desejar artigos futuros autônomos, construir e validar pipeline editorial em LAB/SAFE antes de ativar em produção, preservando qualidade e deduplicação.

## Atualização de interface — 08/11/2026 (depois do checkpoint)
- Após observação direta do usuário, constatado que faltava botão visível de retorno à página inicial na página **Contato**.
- Editadas SOMENTE as páginas públicas do blog `4073458513010284301`: **Contato** Page ID `5651764171349213719` e **Mensagem enviada** Page ID `8022921473820967967`. Ambas receberam link destacado **“← Voltar ao blog”** com `href="/"`.
- Formulário FormSubmit, `action`, `_next`, campos e botão **Enviar mensagem** preservados.
- Blogger Bridge V2 `update_page` confirmou status `live` e identidade integral do HTML atualizado.
- Evidência pública externa: GitHub Actions `42492516107`, resultado `PEDAL_RETURN_BUTTON_PUBLIC_PASS`: botões presentes nas duas URLs, formulário preservado. Um HTTP 429 inicial foi contornado por nova leitura SAFE, sem escrita.
- A correção de navegação **NÃO comprova entrega de e-mail pelo FormSubmit** e não altera a limitação identificada no teste E2E `42458795314`; FormSubmit fora do blog não é controlável por edição da página do Blogger.

## Revalidação FormSubmit após ativação informada pelo usuário — 08/11/2026
- Usuário informou `ativado` para o formulário Pedal Leve; nenhum dado comprobatório da confirmação da ativação no backend FormSubmit foi fornecido.
- Reexecutado **somente uma vez** o job Playwright de teste de Contato via GitHub Actions `42458795314`, segunda tentativa (`job 128772063963`). Formulário carregado e único clique em Enviar executado, mas `returned_to_own_page=false`, `redirect_host=formsubmit.co`, `CONTACT_E2E_NOT_CONFIRMED`. Não houve CAPTCHA bypass, novos envios ou alterações em HTML público.
- Gmail conectado via plugin é conta diferente da destinatária configurada no `action`, portanto busca pelo plugin não permite verificar entrega. Leitura **somente de contexto da aba Gmail aberta pelo usuário** indicou assunto `Action Required: Activate FormSubmit on https://pedal-leve-mobilidade-urbana.blogspot.com/` ainda listado em inbox; isso não prova ativação nem desativação do serviço.
- Diagnóstico atual: envio/redirecionamento **NÃO VALIDADO E2E** após relato de ativação. A falha pode ser ativação ainda pendente, CAPTCHA antispam, bloqueio de navegador automatizado ou outro fluxo externo. Não assumir causa. Próximo passo seguro: envio manual em navegador convencional e verificar na conta destinatária recebimento e retorno (sem repetir envio automatizado até diagnosticar).
