# C94 — Rodada sequencial de um artigo por blog V31 sem nova publicação em 22/11/2026

Pedido do usuário: após implementar C93, percorrer blogs que NÃO receberam artigo novo hoje, UM POR VEZ até o último, criar e publicar um novo artigo editorial para cada blog elegível. Data editorial: 22/11/2026 (America/Recife).

## Auditoria e restrições operacionais
- INVENTÁRIO Blogger API autenticado: 31 blogs na conta; V31 roteia apenas subconjunto via site_routes.json/sites.d. Respeitar roteamento, não publicar em LAB, blogs não homologados ou conteúdo sem nicho verificado apenas para aumentar contador.
- Ar-Condicionado sem Dúvidas já tem 2 posts Midea novos em 22/11; Cadeira Certa publicou Office Arco em 22/11. PULAR para evitar duplicação diária. Móveis para Cada Canto tem 3 LIVE, todos de 18/11, e 6 drafts. NÃO alterar draft assinado C81 id 4106024906916105222 (evidência HMAC).
- WP Radar Tech BR: último post publicado em 20/11; Casa e Decoração: 21/11; Oficina & Garagem: 21/11 na checagem inicial. Conferir novamente antes de publicar devido aos crons independentes.
- Shopee D1 em 22/11 já usou 3/3 conversões globais, portanto NÃO executar generateShortLink ou furar limite para esta rodada. Aproveitar apenas links já existentes validados da campanha específica ou offerLink da API da mesma conta, distinguindo falta de SubID. NÃO inventar links, produtos ou fotos.
- Política C92/C93: anúncio esgotado não é banimento do modelo; procurar vendedores alternativos; não prometer estoque. Um post educativo de qualidade pode ser publicado sem CTA comercial quando não houver oferta confiável, mas nunca inventar afiliado.
- Publicação de cada artigo requer GET prévio do draft e confirmação pós-publicação, SEO original, fonte verificável, links internos, imagem da oferta real e aviso de afiliação se tiver CTA.
- AUTO LIVE V31 continua OFF; esta é execução editorial MANUAL explicitamente solicitada, não autorização para liberar cron LIVE.

## Passos e diário de operações
Registros de artigos serão acrescentados a cada publicação verificada. Evitar transformar um draft já publicado em item duplicado; preservar títulos/permalinks. Este arquivo é checkpoint antes das primeiras mudanças da C94.

## Publicações C94 confirmadas em 22/11/2026
1. **Móveis para Cada Canto**, Blogger `1439741542627895062`: `Mesa de escritório em L Miguel 150 × 150 cm: medidas, circulação e montagem`, novo post `337705191680257250`, publicado em 22/11/2026 16:54 Recife, URL https://moveisparacadacanto.blogspot.com/2026/11/mesa-de-escritorio-em-l-miguel-150-150_01046554637.html . Oferta original de rascunho com foto e afiliado `https://s.shopee.com.br/BVVXTVVPH`; o antigo draft `6093702465101600335` permaneceu **draft** para preservar histórico e evitar dupla publicação. Draft C81 HMAC `4106024906916105222` preservado.
2. **Oficina & Garagem**, WP `https://oficina.radartechbr.com.br/`: `Kit de ferramentas Vonder anunciado com 163 peças: checklist para conferir antes de comprar`, WP post `129`, publicado em 22/11, URL https://oficina.radartechbr.com.br/kit-ferramentas-vonder-163-pecas-o-que-conferir/ . Imagem real do R2 e link afiliado da campanha `oficinawp`, `https://s.shopee.com.br/6Amf3nQkbv`, item `shopee:1363787561:23193413258`. Draft criado 22/11, conteúdo verificado via WP REST `context=edit`, publicação individual.
3. **Radar Tech BR**, WP `https://radartechbr.com.br/`: `Luminária de mesa LED USB tipo cristal: 8 cuidados antes de escolher`, WP post `324`, publicado em 22/11, URL https://radartechbr.com.br/luminaria-de-mesa-led-usb-cristal-como-escolher/ . Oferta cadastrada R2 para `radarwp` `shopee:1579483292:22694332797`, foto correspondente e afiliado `https://s.shopee.com.br/6L66qruBZV`. Draft confirmado WP REST e publicado individualmente.
4. **Air Fryers em Foco**, Blogger `9113728635217260884`: `Air Fryer Oven Britânia BFR2100P 12 litros: espaço, acessórios e consumo`, post `6889292539057925311`, novo draft criado em 22/11, publicado às 16:59 Recife, URL https://air-fryers-em-foco.blogspot.com/2026/11/air-fryer-oven-britania-bfr2100p-12.html . Produto R2 `shopee:1042011939:22798683574`, imagem correspondente e afiliado da campanha `airfryers` `https://s.shopee.com.br/6fixSVnm8t`, sem nova conversão.

**Blogs pulados por já terem artigo novo hoje:** Ar-Condicionado sem Dúvidas (2 Midea), Cadeira Certa no Home Office (Office Arco), WordPress Casa e Decoração (cron criou post `330`, `Organizando o Banheiro com Prateleiras`, 22/11 16:50:55). O cron WP estava em andamento durante a auditoria: rechecamos antes de evitar duplicação.

**Inventário R2 C94 read-only:** workflow [#45063501588](https://github.com/adelrib27/blogger-automation1/actions/runs/45063501588) SUCCESS. Campanhas com affiliate_links armazenados: `airfryers=3`, `casaedecoracaowp=14`, `moveisparacadacanto=12`, `oficinawp=6`, `radarwp=15`; demais campanhas V31 sem links cached. Limite global D1 de 3 conversões Shopee de 22/11 já esgotado. **Não inventar URLs para demais blogs**. Próxima etapa exige consultar API exata `productOfferV2(itemId)` para obter `offerLink` oficial da mesma conta (sem SubID específico) ou publicar apenas conteúdo sem CTA quando válido editorialmente. Este checkpoint NÃO afirma que todos os blogs foram concluídos.

## Etapa concluída — totalidade das 24 rotas V31 cadastradas
Todas as 24 rotas editoriais atualmente cadastradas no V31 (21 Blogger + 3 WordPress) foram verificadas. **21 receberam nova publicação individual neste ciclo**, **3 foram puladas** porque já tinham publicação de 22/11, inclusive o post 330 de Casa e Decoração publicado por seu cron.
Artigos adicionais à primeira etapa, todos Blogger LIVE `published_at=2026-11-22` com foto do anúncio e offerLink de conta Shopee API:
- Cabelos em Foco: `7433909958670615634`, https://cabelos-em-foco.blogspot.com/2026/11/modelador-de-cachos-de-cetim-sem-calor.html
- Eletroportáteis na Cozinha: `4918040711433599634`, https://eletroportateis-na-cozinha.blogspot.com/2026/11/sanduicheira-grill-oliverhome-750-w.html
- Achados para Casa: `6572219156134379728`, https://achadosparacasa2026.blogspot.com/2026/11/cortina-blackout-280-230-m-como-medir.html
- Ventiladores em Foco: `7711287992526425292`, https://ventiladores-em-foco.blogspot.com/2026/11/ventilador-de-teto-com-lampada-e27-8.html
- Limpeza Inteligente: `178485226582513429`, https://limpeza-inteligente.blogspot.com/2026/11/mop-com-esponja-pva-quando-vale-pena-e.html
- Conecta Achados: `1053423153113471831`, https://conectaachados.blogspot.com/2026/11/sapateira-de-nove-andares-como-planejar.html
- Estilo no Dia a Dia: `5523832851018433598`, https://estilo-no-dia-a-dia-0071220800-2.blogspot.com/2026/11/sandalia-de-amarrar-no-tornozelo.html
- Casa em Ordem: `1450278586926534219`, https://casa-em-ordem-pratica.blogspot.com/2026/11/porta-talheres-de-bambu-com-5.html
- Escolha Certa Online: `6713641579459420246`, https://escolha-certa-online.blogspot.com/2026/11/pulseira-de-smartwatch-22-mm.html
- Achados que Valem: `6153898693607741422`, https://achados-que-valem.blogspot.com/2026/11/kit-de-caixas-organizadoras-de-40-l-o.html
- Guia de Achados & Ofertas: `6210479350725590904`, https://guia-de-achados-e-ofertas.blogspot.com/2026/11/organizador-de-maquiagem-com-tampa.html
- Vitrine Prática: `2903591004267019099`, https://vitrine-pratica.blogspot.com/2026/11/caixa-organizadora-de-40-litros-para.html
- Moda e Ofertas: `7593866043388843685`, https://moda-ofertas.blogspot.com/2026/11/kit-de-calcas-jeans-skinny-com-elastano.html
- Achadinhos de Beleza: `538506346193721537`, https://canal-attitude.blogspot.com/2026/11/secador-taiff-easy-1700-w-voltagem.html
- Portal Radar Tech Blogger: `2924800419526696880`, https://portalradartechbr.blogspot.com/2026/11/smartwatch-w99-anunciado-com-amoled-e.html
- Cozinha Sem Complicação: `1080965947069489990`, https://cozinha-sem-complicacao.blogspot.com/2026/11/formas-de-silicone-para-bolo-e-air.html
- Liquidificadores em Foco: `1403911035321641048`, https://liquidificadores-em-foco.blogspot.com/2026/11/liquidificador-philco-ph900-1200-w-copo.html

Foram criados e conferidos todos como DRAFTs novos com data atual, e publicados individualmente; cada API Blogger retornou `status=live` e URL real. A oferta e imagem referem-se ao MESMO SKU; os links dos 17 anúncios foram confirmados na [Actions #45064120898](https://github.com/adelrib27/blogger-automation1/actions/runs/45064120898), SUCCESS, com retorno `offerLink` autenticado da conta. Esses `offerLink` podem não carregar SubID de campanha. V31 AUTO LIVE segue OFF; não houve nova conversão D1.

### Continuação de escopo — blogs conectados, mas não roteados no V31
A conta Blogger tem 31 blogs, dos quais **10 adicionais** não são blog V31 cadastrado (e 21 são roteados). O inventário inclui blogs legítimos de café, violão, ciclismo, casa, achados, ateliê, viagem, pet e jardim; há também LAB e um blog astronomia sem posts/páginas. Antes de publicar em blog NÃO roteado, conferir se o usuário incluiu a operação ao solicitar até o último blog, evitar LAB/placeholder e ter produto real com offerLink da conta, sem inventar campanha/SubID. A nova etapa ainda não é concluída neste checkpoint.

## Segunda etapa: nove blogs adicionais não roteados, todos publicados manualmente em 22/11

A auditoria final `Blogger_Bridge_V2__list_blogs` identificou **32 blogs Blogger**, dos quais 21 estão no cadastro V31 e **11 fora dele**. Os 3 WordPress V31 completam 35 sites conectados. Nove blogs Blogger fora da rota são editoriais reais, com posts anteriores, e receberam um novo artigo em resposta ao pedido do usuário `até o último blog`; **não foram criadas rotas, campanhas, agendas ou LIVE automáticos** para eles.

Antes de publicar foram realizadas duas ações somente de leitura, ambas **SUCCESS**:
- [Actions #45065462143](https://github.com/adelrib27/blogger-automation1/actions/runs/45065462143): selecionou imagens e SKUs existentes no snapshot R2 para nichos café, violão, ciclismo, organização, cozinha, artesanato, viagem, pets e jardim; descartados produtos inadequados.
- [Actions #45065563243](https://github.com/adelrib27/blogger-automation1/actions/runs/45065563243): validou por `productOfferV2(itemId)` **9/9** SKUs e respectivos `shopId`, origem, imagem e `offerLink` afiliado da conta, sem mutation nem SubID específico.
Artigos criados como **novos rascunhos com data 22/11**, verificados individualmente por GET e publicados manualmente após revisão. GET de listagem final confirmou nove LIVE hoje.

| Blog | Artigo publicado 22/11/2026 | Blogger post ID | SKU Shopee / URL de afiliado da conta |
|---|---|---|---|
| Café na Medida | [Cafeteira italiana de inox: 200 ou 300 ml, moagem e uso em fogão de indução](https://cafe-na-medida.blogspot.com/2026/11/cafeteira-italiana-de-inox-200-ou-300.html) | `5908389765438644073` | `1046470373:23898564808` / `https://s.shopee.com.br/7pv1UpUa9A` |
| Violão do Começo | [Violão Giannini Start NF-14 CEQ de nylon: o que avaliar na primeira compra](https://violao-do-comeco-acordes.blogspot.com/2026/11/violao-giannini-start-nf-14-ceq-de.html) | `4274247247044362464` | `1209673900:22593119903` / `https://s.shopee.com.br/5LDgWEe6Df` |
| Pedal Leve | [Bicicleta Premier aro 26 ou 29: como conferir marchas, freios e tamanho do quadro](https://pedal-leve-mobilidade-urbana.blogspot.com/2026/11/bicicleta-premier-aro-26-ou-29-como.html) | `7856819199581769482` | `1499062997:22499049227` / `https://s.shopee.com.br/5q9x79cbnA` |
| Casa Leve e Funcional | [Cabideiro de canto com sapateira: organização vertical sem bloquear a circulação](https://casa-leve-e-funcional.blogspot.com/2026/11/cabideiro-de-canto-com-sapateira.html) | `2118945138766105008` | `1348601027:58204233539` / `https://s.shopee.com.br/2BGekPv2GY` |
| Achados da Rotina | [Dispenser de detergente de 550 ml: como organizar a bancada da pia](https://achados-da-rotina.blogspot.com/2026/11/dispenser-de-detergente-de-550-ml-como.html) | `2706202619683032977` | `1615607650:58204902136` / `https://s.shopee.com.br/3Vm2Krpp22` |
| Ateliê Criativo em Casa | [Luminária USB de haste flexível para artesanato: posicionamento e iluminação](https://atelie-criativo-em-casa.blogspot.com/2026/11/luminaria-usb-de-haste-flexivel-para.html) | `7160135978538488548` | `497708428:58251675489` / `https://s.shopee.com.br/40iIvmnzHP` |
| Mala Pronta e Viagem Prática | [Mala de viagem grande anunciada para 23 kg: dimensões, rodas e cuidados](https://mala-pronta-viagem-pratica.blogspot.com/2026/11/mala-de-viagem-grande-anunciada-para-23.html) | `859677851654531331` | `1783832671:58209674695` / `https://s.shopee.com.br/70LuVIgtiC` |
| Vida Pet Prática | [Arranhador com toca para gatos: como conferir tamanho, estabilidade e material](https://vida-pet-pratica.blogspot.com/2026/11/arranhador-com-toca-para-gatos-como.html) | `4479490813115979404` | `631619886:20572876042` / `https://s.shopee.com.br/8KrI5kbxXE` |
| Jardim e Horta na Prática | [Musgo sphagnum de 10 litros: umidade, drenagem e cuidados na jardinagem](https://jardim-e-horta-na-pratica.blogspot.com/2026/11/musgo-sphagnum-de-10-litros-umidade.html) | `143842189592844804` | `410010723:22997556744` / `https://s.shopee.com.br/6L6Di4jVKK` |

### Sites fora da publicação, por razões verificáveis
- **Casa Prática Lab**, Blogger `8930870316690519385`: **LAB/testes**, deliberadamente excluído de publicações comerciais por não ser blog de produção.
- **Meu Céu Noturno — Astronomia para Iniciantes**, Blogger `9156820142401099679`: **0 artigos e 0 páginas**, sem implantação editorial prévia ou cadastro de nicho/campanha V31. Mantido como blog ainda não lançado, sem publicação isolada que ignore a preparação necessária.
Não confundir essas duas exceções justificadas com falha de publicação. Os 9 blogs editoriais adicionais ativos foram concluídos.

## Homologação final do ciclo 22/11/2026
- **35 sites conectados**: 32 Blogger e 3 WordPress.
- **30 novos artigos manuais LIVE nesta execução**: 28 Blogger (19 V31 + 9 adicionais) e 2 WordPress.
- **3 sites já tinham artigos novos hoje**: Ar-Condicionado sem Dúvidas, Cadeira Certa no Home Office e Casa e Decoração WordPress; sem posts clonados por esta rodada.
- **2 sites não publicados justificadamente**: LAB e astronomia não lançado.
- **Todas as 28 publicações Blogger reconfirmadas** em `list_published_posts` com `id`, `status=live`, `published_at=2026-11-22` e URL; WP Oficina id `129` e WP Radar id `324` rechecados `status=publish`, date 22/11. Cron Casa & Decoração post `330` verificado.
- Total 17 novos links da Shopee API em V31 + 9 links adicionais API, e alguns links R2 cached; URLs exatas da mesma oferta e imagens preservadas.
- O estoque em tempo real não foi confirmado; artigos orientam conferir variantes e valores no checkout. Produtos esgotados podem voltar e podem existir vendedores alternativos, conforme política C92.
- `offerLink` da conta não equivale necessariamente a URL com SubID individual do blog; não houve mutation de geração de shortlink. A inexistência de uma campanha individual para sites não roteados foi explicitada nos seus artigos, sem inventar rastreabilidade.
- **Nenhuma alteração nos gatilhos LIVE automáticos**; `V31_AUTOLIVE_ACTIVE` segue OFF. Não tocar no sistema Pinterest, DRAFT HMAC C81, R2/D1 ou configurações de outros plugins.
- O inventário preliminar deste checkpoint que falava em 31 Blogger/10 adicionais foi corrigido nesta auditoria final para **32 Blogger/11 adicionais**.

**Estado C94: CONCLUÍDO PARA TODOS OS BLOGS EDITORIAIS ATIVOS**, preservando duas exclusões justificadas. Recheck de entrega pública e SEO fino pode ser executado separadamente sem republicar posts, principalmente se o tema exibir widgets antigos.
