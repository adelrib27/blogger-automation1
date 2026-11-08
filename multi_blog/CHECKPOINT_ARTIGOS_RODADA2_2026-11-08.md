# Blogger Automation V31 — Rodada 2 de artigos (2026-11-08)

## Autorização e interpretação do escopo
- Após a primeira campanha de 25/25 artigos, o usuário pediu: "prossiga para os próximos". Interpretação operacional: iniciar **segunda rodada**, um novo artigo por blog, verificando antes de cada escrita.
- **Jardim e Horta na Prática, Blog ID `3644898524310766003` está sendo editado em outro chat. PROIBIDO EXCLUIR, EDITAR, PUBLICAR OU ALTERAR.** Ele não faz parte desta campanha.
- Inventário atual: 26 blogs na conta; escopo potencial de 25 blogs. Validar antes de cada post os títulos e URLs para evitar posts duplicados, inclusive por workflows paralelos.
- Usar oferta comercial real registrada na Loja específica do blog, previamente abastecida pela Shopee Affiliate API; nunca alegar sucesso de consulta nova à Shopee se houver falha GraphQL `10020`. Não inventar links, IDs, preços, estoque ou avaliações.
- Sequência por blog: list_blogs / get_blog, posts, Loja e página real, escolher pauta distinta, conferir item Shopee; rascunho → readback → LIVE → readback.
- Primeira campanha concluída em `multi_blog/CHECKPOINT_NOVOS_ARTIGOS_EM_SERIE_2026-11-08.md`. Não modificá-la nem contabilizar seus artigos como novos da rodada 2.
- Auditoria API valida publicação; teste HTTP público via navegação é adicional e não pode ser presumido por status `live`.

## Artigos confirmados LIVE nesta rodada
1. **Vida Pet Prática** — Blog ID `8052455848487624244`, Post ID `4801584793677919174`
   - *Comedouro de inox para cães e gatos: como escolher tamanho, base e higienização*
   - https://vida-pet-pratica.blogspot.com/2026/11/comedouro-de-inox-para-caes-e-gatos.html
   - Oferta Shopee da Loja: ID `22298882024` e link de afiliado `https://s.shopee.com.br/7Aep7Kl8ma`.
   - Blogger Bridge V2: LIVE, readback exato do post, HTML, link comercial, aviso de transparência.
2. **Mala Pronta e Viagem Prática** — Blog ID `4169782185971307909`, Post ID `9124026890007298181`
   - *Porta-passaporte e etiqueta de mala: como identificar bagagem sem expor dados pessoais*
   - https://mala-pronta-viagem-pratica.blogspot.com/2026/11/porta-passaporte-e-etiqueta-de-mala.html
   - Oferta Shopee da Loja: ID `22098437418` e link de afiliado `https://s.shopee.com.br/1Bmx5CzHG`.
   - Blogger Bridge V2: LIVE, readback exato do post, HTML, link comercial, aviso de transparência.
3. **Ateliê Criativo em Casa** — Blog ID `8888519348129960729`, Post ID `336082826373084324`
   - *Caneta permanente para artesanato: como testar em madeira, cerâmica e tecido*
   - https://atelie-criativo-em-casa.blogspot.com/2026/11/caneta-permanente-para-artesanato-como.html
   - Oferta Shopee da Loja: ID `18399335319` e link de afiliado `https://s.shopee.com.br/114K3wbcSj`.
   - Blogger Bridge V2: LIVE, readback exato do post, HTML, link comercial, aviso de transparência.

## Pendentes
- `4073458513010284301` Pedal Leve — Mobilidade e Ciclismo Urbano
- `4739187376492839837` Casa Leve e Funcional
- `1426630233929943394` Achados para Casa
- `8930870316690519385` Casa Prática Lab
- `8658632621591002634` Eletroportáteis na Cozinha
- `1637047917126642592` Achados da Rotina
- `6319734511998091378` Cabelos em Foco
- `4473989735719981382` Ventiladores em Foco
- `9113728635217260884` Air Fryers em Foco
- `7757953554206491487` Limpeza Inteligente
- `1719259388907013414` Conecta Achados
- `4830103887652146866` Estilo no Dia a Dia
- `4177382081459143374` Casa em Ordem
- `5151950717041967683` Escolha Certa Online
- `7527651041649593600` Achados que Valem
- `1453188702831337099` Guia de Achados &amp; Ofertas
- `9144338307944682868` Vitrine Prática
- `2858597309582499028` Moda e Ofertas
- `2562496977098748229` Achadinhos de Beleza
- `3552757910439359679` Cozinha Sem Complicação
- `5271798990390532475` Liquidificadores em Foco
- `7487888217273188851` Portal Radar Tech

## Observações
- A publicação editorial automática de alguns blogs, como Portal Radar Tech, pode ocorrer em paralelo. Não substituir código nem disputar workflows; fazer preflight dedicado antes de cada publicação.
- Este checkpoint só é atualizado após evidência real de escrita e leitura posterior.
