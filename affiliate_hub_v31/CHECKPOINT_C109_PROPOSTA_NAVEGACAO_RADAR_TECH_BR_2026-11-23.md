# V31 C109 — Proposta de menus e submenus Radar Tech BR (sem aplicação)
**Data:** 23/11/2026 • **Projeto:** https://radartechbr.com.br/ • **Solicitação:** planejar menus/submenus capazes de enriquecer o blog especializado em tecnologia.

## Auditoria real antes de recomendar
- WordPress conectado: 37 artigos `publish` e 8 páginas institucionais publicadas; **14 artigos pertencem à categoria Tecnologia (ID3)**, enquanto **23 pertencem a Guias de Compra (ID1), muitos fora do escopo**. A C106 removeu quatro categorias não tecnológicas, mas reatribuiu posts à ID1; portanto, o nome "Guias de Compra" atualmente não identifica apenas conteúdo tecnológico.
- FSE Twenty Twenty-Five, cabeçalho customizado DB ID66: atalhos secundários atuais **Loja / Tecnologia / Guias de compra**. Menu primário contém Loja, Guias, Sobre e Contato, além de pesquisa. Há repetição de Loja e Guias. HOME DB ID42 contém seção "Guias de tecnologia em destaque" C108.
- Páginas existentes: Loja /loja/, Sobre /sobre/, Contato /contato/, Política Editorial /politica-editorial/, Transparência e Afiliados /transparencia-e-afiliados/, Cookies, Termos, Privacidade.
- Temas dos 14 posts em Tecnologia: áudio Bluetooth (4 posts: 25,235,290,311), relógios inteligentes (2: 138,260), projetor/controle (1:278), iluminação RGB e LED (2:24,324), rádio comunicador (1:26), scanner OBD2 conectado (1:28), lanterna (1:27), ventilação USB e air cooler (2:29,256). Categorias de WP atuais apenas Tecnologia e Guias de Compra.

## Estrutura de navegação PROPOSTA (não criada)
**Barra primária ideal:** Início | Tecnologia ▾ | Guias de Compra ▾ | Loja | Sobre | Busca. Contato pode permanecer em área utilitária/rodapé, com link claro.
**Tecnologia dropdown (páginas HUB curadas, NÃO criar categorias vazias):**
1. Áudio e Bluetooth — já tem 4 posts tech. Primeira vertical apta a receber página/hub editorial com cartões reais.
2. Smartwatches e wearables — 2 posts tech. Recomendável hub só após 1–2 conteúdos adicionais diferenciados; por enquanto acesso direto aos artigos.
3. Projetores e acessórios — 1 post. Por enquanto link direto ao guia existente. Criar hub quando tiver diversidade suficiente.
4. Gadgets e conectividade — vários temas independentes; só virar hub próprio quando houver ângulo editorial coeso e 3–5 artigos; não usar categoria-coringa para absorver tudo.
**Guias de Compra dropdown (conteúdo precisa ser criado/curado sem autoafirmações):**
- Como escolher: tutoriais de critérios de compra de tecnologia (smartwatch, caixa de som).
- Compatibilidade: controle de projetor, scanner OBD2, conexões Bluetooth e rádios. Afirmar somente compatibilidades verificadas.
- Antes de comprar: checklists técnicos.
- Comparativos: ADIAR até existirem comparações reais, de fontes comprovadas; não dizer que produtos foram testados sem teste.
**Menu Loja:** apontar à página de loja atual; selecionar somente produtos de tecnologia e eletrônicos como política futura, cuidando para não apagar ou quebrar itens sem backup e revisão.
**Sobre:** preservar /sobre/; políticas no rodapé, não poluir a barra principal.

## Fases e critérios
- **Primeiro:** eliminar duplicidade Loja/Guias entre barras principal e secundária, sem remover Contact/Busca; melhorar acessibilidade mobile e teclado, o link principal do dropdown também deve ser clicável, e os filhos devem ter URL navegável `<a href>`.
- **Depois:** construir hub Áudio e Bluetooth com 4 links reais, breve introdução original e atualizações verificáveis. Acrescentar à navegação apenas quando a página existir e tiver conteúdo útil.
- **Futuro:** Smartwatches, Projetores, Casa Inteligente, Segurança/Redes, Computadores e Periféricos só quando existirem artigos suficientes e bem diferenciados. Não vincular nomes de menu a páginas vazias ou 404.
- **MUITO IMPORTANTE:** categoria atual `/category/guias-de-compra/` inclui 23 posts fora da área tecnológica. Não promovê-la como hub editorial puramente tech até curadoria / migração SEO segura (C106). Um novo HUB "Guias de Tecnologia" pode inicialmente aproveitar os 14 posts adequados sem modificar URLs antigas.
- Preservar C107 (menus corrigidos) e C108 (cards com fotos reais), não renomear slug ou excluir qualquer artigo. Unificar estrutura de navegação, reduzir profundidade (máximo 1 submenu), inserir links internos contextuais entre guias relacionados, breadcrumbs e posts relacionados quando aplicável.
- Não criar "Reviews", "Testamos", "As Melhores Ofertas de Hoje" sem testes, preço e vigência comprovados; nem etiquetas vazias que insinuem autoridade inexistente.
- Regras Google Search Central: links internos HTML rastreáveis e âncoras descritivas, arquitetura simples; docs https://developers.google.com/search/docs/crawling-indexing/links-crawlable e https://developers.google.com/search/docs/appearance/sitelinks.

## Situação atual
- **Apenas proposta C109 documentada. Zero mudanças no site/CMS, menus, categorias, artigos, Loja, tema, automações ou Cloudflare.**
- A C106–C108 já foram aplicadas e não devem ser revertidas sem auditoria.
- O objetivo primário é orientar leitores e construir clusters que realmente existam, não criar categorias apenas para preencher o cabeçalho.
