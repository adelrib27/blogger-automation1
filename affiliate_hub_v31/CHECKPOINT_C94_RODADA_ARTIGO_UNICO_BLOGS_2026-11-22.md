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
