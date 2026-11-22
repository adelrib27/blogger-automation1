# C100 — CORREÇÃO CRÍTICA DO INVENTÁRIO: Lojas com redirecionamento para posts

**Data:** 22/11/2026 (America/Recife).
**Status:** DIAGNÓSTICO AUDITADO — SUBSTITUI A INTERPRETAÇÃO DE “19 LOJAS VAZIAS” do primeiro inventário C100.

## Falha de classificação e causa
A inspeção inicial limitou-se à Blogger Page `/p/loja.html`. Em 18 blogs o HTML dessa página não tinha imagens/links, pois era **apenas um redirecionamento JavaScript** via `window.location.replace` para um **post Blogger com título "Loja"**, de URL `/2026/10/loja.html` ou `/2026/11/loja.html`. A API `list_pages` e `get_page` não expõe automaticamente o conteúdo do post de destino. Logo, dizer que essas 18 lojas não continham produtos foi **incorreto**.

## Evidência API: 18 lojas efetivamente preenchidas por posts
Todos os posts abaixo foram encontrados via `Blogger_Bridge_V2.search_posts_by_title(match=exact, status=live)` e lidos com `get_post`. Contagem de URL Shopee afiliada distinta dentro do conteúdo do post:

| Site key | Blog ID | Blogger Page ID | Post "Loja" ID | Shortlinks distintos no post |
|---|---|---|---|---:|
| liquidificadores | `5271798990390532475` | `5473313787015756722` | `8867555367475283866` | 20 |
| portal_radar_tech | `7487888217273188851` | `6887385207246667244` | `906894044295273477` | 20 |
| achadinhos_beleza | `2562496977098748229` | `455853998448723529` | `7650631557624373238` | 20 |
| moda_ofertas | `2858597309582499028` | `1341310014099438949` | `4871366557503134389` | 20 |
| vitrine_pratica | `9144338307944682868` | `8344701886444887322` | `115613719594316807` | 20 |
| guia_achados | `1453188702831337099` | `9156313162825773745` | `3858461075334539445` | 20 |
| achados_valem | `7527651041649593600` | `2615453333851618808` | `953731363427123084` | 20 |
| escolha_certa | `5151950717041967683` | `3334029815604129982` | `5474604520207119855` | 20 |
| casa_em_ordem | `4177382081459143374` | `4031853959690608178` | `5566188787681469799` | 20 |
| estilo_dia | `4830103887652146866` | `4843501559117111153` | `3362829797679236320` | 20 |
| conecta_achados | `1719259388907013414` | `2386698852540729057` | `259394788951394758` | 20 |
| limpeza | `7757953554206491487` | `4457645831148890823` | `6383277011247909539` | 20 |
| ventiladores | `4473989735719981382` | `8010344677278545283` | `1410775502611365606` | 20 |
| eletroportateis | `8658632621591002634` | `2989554269967771834` | `2599179962359747947` | 20 |
| cabelos | `6319734511998091378` | `3590970839633701768` | `2897872370214992246` | 20 |
| air_fryers | `9113728635217260884` | `6090919827060846509` | `5189023277801568424` | 20 |
| achados_casa | `1426630233929943394` | `3841238517239710135` | `854861801599328533` | 32 |
| cozinha_sem_complicacao | `3552757910439359679` | `6913756651435112886` | `7888042807715084117` | 20 |

- **16** posts na lista acima têm 20 shortlinks distintos; **Achados para Casa** tem **32** e **Cozinha Sem Complicação** tem **20**. Esses 18 blogs já possuíam lojas comerciais funcionando antes da C100.
- Os posts "Loja" consultados continham fotos (tipicamente 32 imagens por HTML) e links afiliados, independentemente de a Page ser redirecionadora.
- **Móveis para Cada Canto** (`blog_id=1439741542627895062`, Page Loja `5105320514641154037`) é a **ÚNICA** página que não contém anúncios E não redireciona para um post "Loja"; `search_posts_by_title("Loja", exact)` retornou ZERO. Esse é o alvo realmente vazio no inventário de 19.
- Os outros **11 Blogger** que tinham produtos diretamente nas Pages continuam preservados; 1 LAB Casa Prática Lab e 1 blog de astronomia não lançado excluídos. Os 3 WordPress também possuem lojas preenchidas no HTML público.
- Portanto, entre os 32 blogs Blogger da conta: **29 lojas comerciais já tinham ofertas antes de C100**, **1 Loja comercial realmente sem produtos** (Móveis), **1 LAB** (possui ofertas) e **1 não lançado**.

## Intervenções C100 já executadas — não duplicar e não reverter cegamente
1. **Achados para Casa**: `/p/loja.html` antes redirecionava a POST antigo `/2026/10/loja.html` com 32 links. C100 substituiu a Page por uma vitrine nova de **36 ofertas** verificadas, URL https://achadosparacasa2026.blogspot.com/p/loja.html. **Post antigo permanece LIVE e intacto**; ele tem outra URL e conteúdo comercial também. Essa operação deve ser classificada como **AMPLIAÇÃO de uma vitrine existente, não criação de loja vazia**. Novo HTML e backup nos checkpoints já existentes. Nenhum artigo antigo foi apagado ou modificado.
2. **Cozinha Sem Complicação**: `/p/loja.html` antes redirecionava a POST `/2026/10/loja.html` com **20** links. C100 substituiu a Page por nova vitrine de **32 ofertas**, URL https://cozinha-sem-complicacao.blogspot.com/p/loja.html. **Post antigo LIVE e intacto**, também constitui ampliação, não inauguração.
3. Manter ambos os destinos ativos por ora: não redirecionar/excluir os posts legados sem auditoria de SEO, links de navegação e backup. **Duas URLs comerciais podem implicar risco de conteúdo concorrente, embora os produtos não sejam conjuntos idênticos.** Registrar para auditoria específica futura; não confundir com duplicação interna DOM do tema (que também existe).
4. **Casa em Ordem:** o erro Shopee API `10030` na tentativa de ampliar a loja NÃO significa loja vazia ou inoperante. A PAGE continua redirecionando para post "Loja" com **20 ofertas**. Preservar. Existe uma shortlist de 29 ofertas distintas em logs de três execuções anteriores do mesmo dia, mas não publicar automaticamente se a meta é apenas encher lojas realmente vazias.

## Estado corrigido e política de retomada
- **NENHUMA nova Loja ficou vazia devido ao 10030.**
- **NÃO** prosseguir com as outras 16 edições da lista de 19 como "lojas vazias": já têm produtos (20 links cada) no post de destino. Preservá-las. Qualquer decisão futura de **ampliar/modernizar vitrines já existentes** é escopo diferente e deve partir do estado real, com backup da Page E do post de origem, plano para URLs/SEO, curadoria por nicho e QA pós-publicação.
- No escopo estrito "blogs que estão sem produtos", priorizar **somente Móveis para Cada Canto**. Alvo Page existente `5105320514641154037`, sem post de destino, e somente atualizar se houver pelo menos 24 URLs/itens novos realmente verificados em Shopee Affiliate API; como `10030` sinalizou rate-limit, não insistir em chamadas hoje.
- C100 manifest, `V31_CONTINUAR_AQUI.md` e `CONTINUIDADE_ESTADO.json` precisam referir esta **correção mais recente**, prevalecendo sobre inventário preliminar.

**Diagnóstico atualizado: 1 Loja comercial realmente vazia; 18 anteriormente confundidas eram redirecionadores; 2 Page upgrades já feitos e confirmados; nenhuma outra atualização autorizada por suposto vazio.**
