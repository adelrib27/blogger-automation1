# Blogger Automation V31 — Checkpoint inicial: Violão do Começo

**Registro:** 2026-11-08. **Natureza:** estado vivo comprovado, com criação parcialmente concluída e bloqueio fail-closed da etapa 4. **Não reiniciar o provisionamento.**

## Identidade e anticlonagem

- **Blog ID exato**: `370856880185231084` (string).
- **Título**: Violão do Começo — Acordes e Cuidados.
- **URL**: https://violao-do-comeco-acordes.blogspot.com/
- **Nicho**: educação introdutória para violão, afinação, conservação, cordas, organização de instrumentos e acessórios comerciais, excluindo cursos musicais clonados.
- **Inventário prévio**: Blogger Bridge V2 listou **26 blogs** antes da criação; nenhum projeto diretamente equivalente de violão nesse inventário. Foram avaliados também camping/trilhas e astronomia amadora como oportunidades distintas.
- **Diferença entre projetos**: reutilizar engenharia V31, jamais texto, produtos, temas específicos, blogs IDs, Page IDs ou workflows de blogs anteriores.

## Estado real das etapas

1. **Planejamento:** concluído, nicho diferenciado com categorias propostas abaixo. Não há promessa de demanda/lucro comprovada.
2. **Criação:** Runner `provision_new_blog_v31` foi chamado uma vez com confirmação literal `PROVISION BLOG V31`. Retornou `safe_automation_error`, mas criou o blog antes de parar. Blogger Bridge V2 e inventário da conta confirmaram o Blog ID exato, URL e descrição. **Nunca repetir provisionamento/criação para este endereço**.
3. **SEO/Blogger:** Runner `configure_settings` com `APPLY SETTINGS` retornou `SETTINGS_PROFILE_VALIDATED`; readback `preflight_settings` confirmou visibilidade de busca, HTTPS redirect, lazy-load, WebP, descrição de pesquisa habilitada e timezone `(GMT-03:00) Horário Padrão de Brasília – São Paulo`. Robots personalizados permaneceram intocados. Descrição:
   > Violão do Começo é um guia para quem está começando a tocar violão. Reúne orientações de afinação, escolha do instrumento, troca e cuidado com cordas, postura, armazenamento e acessórios úteis, com explicações acessíveis e recomendações comerciais transparentes quando houver links de afiliados.
   
   Descrição de pesquisa:
   > Violão para iniciantes: escolha do instrumento, afinação, cordas, cuidados, suporte, capotraste e acessórios explicados de forma prática.
4. **Tema V31 R52:** **BLOQUEADO / NÃO INSTALADO**. Chamada `adopt_model_v31_exact({expected_blog_id:"370856880185231084",blog_title:"Violão do Começo — Acordes e Cuidados",blog_url:"https://violao-do-comeco-acordes.blogspot.com/",confirm:"INSTALL MODEL V31"})` retornou `target_not_authorized` / `Blog ID, nome e URL sem autorizacao exata.`. `health` do Runner mostrou `v31_enabled_for_new_blogs:true`, mas a lista `universal_v31_allowed_blog_ids` continha somente `4739187376492839837`, `1625257710858445955`, `8476663092477971560` (sem o novo ID). Não tentar contornar allowlist; requer autorização exata pela configuração oficial do serviço local antes da instalação.
5. **Páginas institucionais:** não iniciadas. Blogger API: 0 páginas.
6. **Três artigos iniciais reais Shopee:** não iniciados. Blogger API: 0 posts.
7-15. **Loja, pilares, clusters, SEO editorial, autoridade, automações, QA público e finalização:** não iniciados por bloqueio da etapa 4.

## Auditoria pública do estado após bloqueio

- Firecrawl retornou **HTTP 200**, título e descrição coerentes com a criação.
- HTML público **sem** marcadores V31 `ub-header` e `ub-footer`: indica que o tema universal não foi instalado.
- Não confundir site público com tema V31 aplicado; não declarar sucesso apenas porque a página inicial responde HTTP 200.

## Próxima ação segura — obrigatória

1. Autorizar o **destino exato** (Blog ID, título e URL acima) no mecanismo oficial de autorização do Blogger Local Runner, sem remover guardas de segurança nem liberar outros blogs.
2. Verificar `health` e a autorização resultante; executar **apenas** `adopt_model_v31_exact` para o blog existente, nunca `provision_new_blog_v31` de novo.
3. Confirmar sucesso no Runner e ler HTML público da homepage até ver a identidade V31, `ub-header` e `ub-footer`; registrar evidências. Se FAIL, parar.
4. Prosseguir às páginas institucionais, com formulário realmente público, FormSubmit, `_next`, Mensagem enviada e botão Voltar ao blog. Envio real e recebimento são validações separadas.
5. Consultar a Shopee Affiliate API autenticada; selecionar somente ofertas reais, relevantes e permitidas pelo policy guard; **publicar exatamente três artigos iniciais originais com imagens do anúncio e CTA Shopee** antes da Loja.
6. Depois criar Loja com 16 IDs distintos em quatro categorias, HTML marcadores protegidos, linkagem e data real; seguir etapas 8–15 com SAFE e isolamento de workflows.
   
## Planejamento editorial — apenas hipótese, sem publicações

- **Três pautas iniciais propostas:** escolher violão para iniciantes (comparar modelos, tamanho e cordas); afinar com afinador digital (uso e cuidados); primeiros acessórios (palhetas, capotraste, capa e suporte).
- **Categorias comerciais propostas**: cordas e manutenção; afinadores e metrônomos; capotrastes e palhetas; capas e suportes. Revalidar disponibilidade via API Shopee antes de qualquer publicação.
- **Pilares futuros**: escolha e manutenção do primeiro instrumento; afinação e preparação para estudar; acessórios e organização de prática.
- **Rotação:** diária somente para este blog após o Page ID real da Loja, SAFE, readback e primeiro LIVE aprovado; não reutilizar workflows nem URLs de outros blogs.

**Segurança:** nenhum token/segredo registrado; não editar blogs existentes, não contornar allowlist, não mascarar um erro do Runner, não assumir trabalho paralelo inalterado sem readback. Checkpoint doc-only, sem alterações em tema nem produção por GitHub.
