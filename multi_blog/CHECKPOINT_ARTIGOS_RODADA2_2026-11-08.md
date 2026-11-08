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
_Nenhum ainda._

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
- `8888519348129960729` Ateliê Criativo em Casa
- `4169782185971307909` Mala Pronta e Viagem Prática
- `8052455848487624244` Vida Pet Prática

## Observações
- A publicação editorial automática de alguns blogs, como Portal Radar Tech, pode ocorrer em paralelo. Não substituir código nem disputar workflows; fazer preflight dedicado antes de cada publicação.
- Este checkpoint só é atualizado após evidência real de escrita e leitura posterior.
