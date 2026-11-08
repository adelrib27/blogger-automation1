# Checkpoint operacional V31 — Jardim e Horta na Prática — 08/11/2026

> **Hierarquia de confiança**: estado real ao vivo > arquitetura V31 vigente > checkpoints > histórico. Documento de continuidade, não substitui prova de execução. **Não executar o Blogger Local Runner para recriar/provisionar o blog ou reinstalar o tema manual**. Edição de tema exige inspeção pontual e autorização própria. Sem credenciais, cookies ou e-mails privados.

## Identidade auditada
- **Blog ID:** `3644898524310766003` (string).
- **URL:** https://jardim-e-horta-na-pratica.blogspot.com/
- **Título:** Jardim e Horta na Prática.
- **Tema:** instalado manualmente pelo usuário; preservado integralmente nesta execução. Firecrawl público HTTP 200, título correto, marcadores `ub-header` e `ub-footer` e navegação com Início/Sobre/Loja/Contato. **Não afirmar equivalência byte a byte com XML oficial R52** sem leitura de tema.
- **SEO público da home:** `<title>` correto, meta description própria do nicho, link canonical para homepage, viewport e JSON-LD encontrados em HTML público (HTTP 200).
- **Runner:** não utilizado para provisionar, configurar ou aplicar tema; operação exclusivamente Blogger Bridge V2, GitHub, consulta Shopee em Actions SAFE e leitura pública.

## Etapas e evidências
1. Criação + SEO e instalação manual do tema: estados anteriores preservados; blog ID/URL/nome conferidos via Blogger Bridge V2.
2. **Etapa 5, institucionais:** 7 páginas preexistentes LIVE: Sobre `4574444738342874846`, Contato `4125652355333889293`, Mensagem enviada `3997662167983852294`, Privacidade `3478834712691603419`, Termos `4668993262553159592`, Cookies `7376358284014475222`, Aviso de Afiliados `8612144418692401548`. Teste E2E do envio real de mensagem NÃO comprovado.
3. **Etapa 6, três artigos Shopee:** três artigos originais publicados e confirmados via API e por HTTP público 200, dois `img` dos anúncios Shopee e dois CTAs diretos com `nofollow sponsored noopener noreferrer` em cada. Avisos de afiliados, alt e fontes editoriais Embrapa/RHS.
   - `4113098260539608076` — [Horta em vasos em pequenos espaços](https://jardim-e-horta-na-pratica.blogspot.com/2026/11/horta-em-vasos-em-pequenos-espacos-como.html).
   - `8593080993371659532` — [Como regar uma horta em vasos sem encharcar](https://jardim-e-horta-na-pratica.blogspot.com/2026/11/como-regar-uma-horta-em-vasos-sem.html).
   - `8966541792778071469` — [Ferramentas de jardinagem para horta em vasos](https://jardim-e-horta-na-pratica.blogspot.com/2026/11/ferramentas-de-jardinagem-para-horta-em.html).
4. **Etapa 7, Loja:** Página `3065510801940114231`, https://jardim-e-horta-na-pratica.blogspot.com/p/loja.html, LIVE. Quatro categorias × quatro produtos = **16 IDs diferentes, 16 imagens HTML, 16 links Shopee**. Dados de anúncios reais em consulta Shopee Affiliate API validada por GitHub SAFE runs `42507560643` e `42507264005`; itens inadequados (planta artificial, brinquedos, objetos de bolo) excluídos da vitrine. Timestamp comercial refere-se à consulta de 08/11/2026, não à atualização contínua. CSS `adr-store-v31-css` e marcadores `UNIVERSAL_V31_STORE_AUTO_START/END` presentes. Firecrawl público móvel HTTP 200 e 16 IDs/links únicos no HTML.
5. **Etapa 11 parcial, links internos:** os três posts foram atualizados com links contextuais entre si e para `/p/loja.html`; verificação exata por API Blogger PASS. Não afirmar pilares/clusters adicionais publicados.
6. **Validação pública de home, Loja e 3 artigos:** HTTP 200, título correto, URL e conteúdo de cada página, 2 CTAs Shopee por post, presença das imagens e disclosure no HTML. Capture mobile da Loja obtida; verificação independente de `naturalWidth`/carregamento de todas as imagens e inspeção visual detalhada por dispositivos ainda NÃO concluída.

## Pendência crítica — Contato no tema manual
- A API Blogger para página Contato `4125652355333889293` armazena `<form action="https://formsubmit.co/...">` com `_subject`, `_next=https://jardim-e-horta-na-pratica.blogspot.com/p/mensagem-enviada.html` e `_honey`.
- **HTML público é DIFERENTE:** o tema renderiza `<form class="ub-contact-form" method="post" action="https://formsubmit.co/...">` com campos name/email/message, porém **sem `_next` e `_subject`**. A página de retorno existe e contém retorno ao início, mas não há evidência de que o formulário público redirecione até ela.
- **Não marcar E2E como PASS**. Necessária inspeção pontual do template ativo, correção apenas do bloco público do formulário para incluir `<input type="hidden" name="_next" value="https://jardim-e-horta-na-pratica.blogspot.com/p/mensagem-enviada.html">`, preservando o resto do tema, seguida de readback público e envio/recebimento de mensagem de teste autorizado. Não reinstalar tema nem presumir que editar apenas o corpo da página resolverá, pois o tema já entrega outro formulário.

## GitHub e automação
- PR #33 `https://github.com/adelrib27/blogger-automation1/pull/33`: catálogo Shopee de consulta SAFE e teste público do tema, **rascunho não integrado**. A consulta SAFE de 16 produtos passou; o teste do tema sofreu falso negativo inicial (string esperada errada) e depois HTTP 429 do agente GitHub. Consulta independente Firecrawl HTTP 200 confirmou identificação do tema em público.
- Atenção: o selecionador inicial do catálogo ainda classificou anúncio de ferramentas na categoria de vasos em uma execução; revisar regras antes de reutilizar como rotação autônoma.
- **Sem workflow de rotação diária para este blog no main até esta auditoria.** Não há Page ID em latches de produção registrados antes da publicação da Loja. Criar e testar fluxo isolado em SAFE, sem afetar outros blogs; só ativar com validação e autorização.
- Automação de novos artigos também não foi configurada/ativada nesta execução. Posts editoriais adicionais (pilares/clusters) NÃO publicados.

## Próximos gates
1. Corrigir formulário **do tema público** sem reinstalação; testar `_next`, entrega e retorno.
2. Auditar carregamento efetivo e visual mobile/desktop das imagens, header, artigos e grid da Loja.
3. Validar regras da categorização Shopee e preparar rotador diário isolado pelo Blog ID `3644898524310766003` e Loja Page ID `3065510801940114231`; SAFE + concurrency guards + readback e public QA antes de LIVE.
4. Planejar e publicar conteúdos-pilar e clusters da etapa 8–12 com qualidade e links, sem extrapolar os três artigos solicitados nesta execução.
5. Só considerar ativação/finalização após as verificações pendentes. Não inventar backlinks, testes de recebimento ou periodicidade de schedule.

**Estado:** 8 páginas LIVE, 3 posts LIVE, Loja 16×1, tema manual preservado; auditoria pública principal PASS, Contato E2E/auto-rotação/visual de imagens ainda pendentes.
