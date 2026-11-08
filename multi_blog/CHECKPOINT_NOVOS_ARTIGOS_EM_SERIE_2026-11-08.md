# Checkpoint V31 — Novos artigos em série (08/11/2026)

## Escopo autorizado
- Usuário autorizou criar **um artigo novo por vez em cada blog da conta**, seguindo o respectivo nicho, com oferta e link de afiliado verdadeiros obtidos de sua Shopee Affiliate API.
- Usuário informou que **Jardim e Horta na Prática**, Blog ID `3644898524310766003`, será excluído por ele. **EXCLUIR O BLOG DO ESCOPO E NÃO APAGAR OU ALTERAR.**
- Inventário realizado: 26 blogs; 25 no escopo; cada blog deve receber apenas um artigo **novo** adicional nesta campanha. Não confundir com os 26 artigos que já existiam antes.
- Preflight por blog: ID/nome/URL, posts existentes (evitar pauta duplicada), Loja e produto verdadeiro, link afiliado, políticas; criar rascunho, readback, publicar, readback; validar público quando acesso permitir.
- Nova consulta Shopee realizada via GitHub PR #31 (fechado sem merge), run `42504307962`: GraphQL `10020` em três consultas de produtos pet, fail-closed. Para os cinco posts abaixo, reutilizou-se **produto real previamente obtido pela Shopee Affiliate API e já validado na página LOJA do próprio blog**, sem inventar produto, link, imagem ou preço atual.
- Auditoria HTTP de Vida Pet run `42504723298`, PR #32 (fechado sem merge), recebeu HTTP 429 repetidamente. Não é prova de falha de publicação. Blogger Bridge V2 confirmou cada post LIVE e conteúdo com afiliado. Evitar novos loops agressivos de GET públicos.

## Concluídos com Blogger API live e readback
1. **Vida Pet Prática**, Blog ID `8052455848487624244`
   - Post ID `6337576020500368620`
   - Título: *Bola interativa automática para pets: como avaliar tamanho, bateria e segurança*
   - https://vida-pet-pratica.blogspot.com/2026/11/bola-interativa-automatica-para-pets.html
   - Produto Shopee da Loja: ID `58254297432`, `https://s.shopee.com.br/1qdIlZR2zB`. Imagem real CDN Shopee; links internos e disclosure.
   - Estado: LIVE/API_READBACK_PASS; HTTP público externo 429, não comprovado por GET.
2. **Mala Pronta e Viagem Prática**, Blog ID `4169782185971307909`
   - Post ID `370469501121677066`
   - Título: *Saco a vácuo na mala de viagem: quando economiza espaço e o que conferir*
   - https://mala-pronta-viagem-pratica.blogspot.com/2026/11/saco-vacuo-na-mala-de-viagem-quando.html
   - Produto Shopee da Loja após rotação: ID `20997980466`, `https://s.shopee.com.br/4VeCI8MZN6`.
   - Estado: LIVE/API_READBACK_PASS.
3. **Ateliê Criativo em Casa**, Blog ID `8888519348129960729`
   - Post ID `1739297681837646357`
   - Título: *Organizador de miçangas para artesanato: como separar cores, tamanhos e projetos*
   - https://atelie-criativo-em-casa.blogspot.com/2026/11/organizador-de-micangas-para-artesanato.html
   - Produto Shopee da Loja: ID `21699888784`, `https://s.shopee.com.br/1W0aerviLF`.
   - Estado: LIVE/API_READBACK_PASS.

4. **Portal Radar Tech**, Blog ID `7487888217273188851`
   - Post ID `8180014042421101273`
   - Título: *Caixa de som Bluetooth portátil: como comparar conexões, bateria e potência anunciada*
   - https://portalradartechbr.blogspot.com/2026/11/caixa-de-som-bluetooth-portatil-como.html
   - Produto real do post Loja redirecionado: ID `20997608223`, afiliado `https://s.shopee.com.br/2LZglP61P4`.
   - Estado: LIVE/API_READBACK_PASS. O blog ainda requer revisão de páginas institucionais ausentes.
5. **Liquidificadores em Foco**, Blog ID `5271798990390532475`
   - Post ID `8365046370075588694`
   - Título: *Mini liquidificador portátil USB: o que conferir em capacidade, recarga e limpeza*
   - https://liquidificadores-em-foco.blogspot.com/2026/11/mini-liquidificador-portatil-usb-o-que.html
   - Produto real do post Loja: ID `58255874292`, `https://s.shopee.com.br/7fbElOrTmx`.
   - Antes de publicar foi corrigido no rascunho um link interno de `/2026/11/` para o slug real em `/2026/10/` após conferência API.
   - Estado: LIVE/API_READBACK_PASS.


## Continuação em 08/11/2026 — Novo chat, Jardim preservado
- Usuário especificou: **Jardim e Horta na Prática NÃO deve ser excluído** e deve ficar de fora de todas as operações de hoje, pois está sendo editado em outro chat. Apenas excluir do ESCOPO da campanha; preservar integralmente.
- Mais cinco artigos publicados sequencialmente, status LIVE e HTML/readback pela Blogger Bridge V2, com produto e link já presentes em Loja da Shopee Affiliate API:
6. **Cozinha Sem Complicação** — Blog ID `3552757910439359679`, Post ID `5283119069759760117`
   - *Porta-temperos giratório: como avaliar espaço, potes e uso diário na cozinha*
   - https://cozinha-sem-complicacao.blogspot.com/2026/11/porta-temperos-giratorio-como-avaliar.html
   - Oferta Shopee ID `58216601427`, link `https://s.shopee.com.br/W7xcDnEPb`.
   - Estado: LIVE/API_READBACK_PASS. Não presumir teste HTTP público se não executado.
7. **Achadinhos de Beleza** — Blog ID `2562496977098748229`, Post ID `1228052396044811809`
   - *Máscara de cílios marrom e delineador: como combinar acabamento e remoção sem irritar os olhos*
   - https://canal-attitude.blogspot.com/2026/11/mascara-de-cilios-marrom-e-delineador.html
   - Oferta Shopee ID `58254271380`, link `https://s.shopee.com.br/3g54TLtZFr`.
   - Estado: LIVE/API_READBACK_PASS. Não presumir teste HTTP público se não executado.
8. **Moda e Ofertas** — Blog ID `2858597309582499028`, Post ID `5075103736629337907`
   - *Cinto elástico sem fivela: quando ajuda no jeans e como conferir o ajuste*
   - https://moda-ofertas.blogspot.com/2026/11/cinto-elastico-sem-fivela-quando-ajuda.html
   - Oferta Shopee ID `53707116674`, link `https://s.shopee.com.br/114JHqEjpo`.
   - Estado: LIVE/API_READBACK_PASS. Não presumir teste HTTP público se não executado.
9. **Vitrine Prática** — Blog ID `9144338307944682868`, Post ID `8224723807403374087`
   - *Sapateira de aço compacta: o que medir antes de organizar tênis e sapatos*
   - https://vitrine-pratica.blogspot.com/2026/11/sapateira-de-aco-compacta-o-que-medir.html
   - Oferta Shopee ID `23793687166`, link `https://s.shopee.com.br/5LDJx3pvif`.
   - Estado: LIVE/API_READBACK_PASS. Não presumir teste HTTP público se não executado.
10. **Guia de Achados & Ofertas** — Blog ID `1453188702831337099`, Post ID `8790716739654760829`
   - *Mini batedor elétrico para café e leite: o que conferir na recarga e na limpeza*
   - https://guia-de-achados-e-ofertas.blogspot.com/2026/11/mini-batedor-eletrico-para-cafe-e-leite.html
   - Oferta Shopee ID `23593232547`, link `https://s.shopee.com.br/6q24hzKYoy`.
   - Estado: LIVE/API_READBACK_PASS. Não presumir teste HTTP público se não executado.

## Pendentes — não criar duplicatas
- `7527651041649593600` Achados que Valem
- `5151950717041967683` Escolha Certa Online
- `4177382081459143374` Casa em Ordem
- `4830103887652146866` Estilo no Dia a Dia
- `1719259388907013414` Conecta Achados
- `7757953554206491487` Limpeza Inteligente
- `9113728635217260884` Air Fryers em Foco
- `4473989735719981382` Ventiladores em Foco
- `6319734511998091378` Cabelos em Foco
- `1637047917126642592` Achados da Rotina
- `8658632621591002634` Eletroportáteis na Cozinha
- `8930870316690519385` Casa Prática Lab
- `1426630233929943394` Achados para Casa
- `4739187376492839837` Casa Leve e Funcional
- `4073458513010284301` Pedal Leve — Mobilidade e Ciclismo Urbano

**IMPORTANTE:** Estado real > checkpoint. Antes de cada novo artigo, reconsultar o inventário e posts; outro executor pode ter publicado durante a pausa. A Loja serve somente como fonte de oferta previamente validada pela API; a API nova está reportando 10020. Não afirmar consulta atual bem-sucedida. Não modificar Jardim e Horta. Não realizar exclusão.
