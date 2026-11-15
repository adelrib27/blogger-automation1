# Resultado SAFE — 27 blogs Blogger / Shopee Affiliate — 2026-11-09

**Operação:** consulta autenticada e análise de candidatos comerciais, sem publicações.
**Escopo:** 27 Blogs IDs presentes no inventário; **excluído** Meu Céu Noturno — Astronomia para Iniciantes (ID `9156820142401099679`).
**Fuso editorial:** America/Recife. **AppID esperado:** `18352820579`. **Segredos:** nenhum registrado.

## Execução e evidências
- [Run SAFE completo #42696609460](https://github.com/adelrib27/blogger-automation1/actions/runs/42696609460) concluído com sucesso como *diagnóstico*, não como liberação de publicação.
- Artefato: `editorial-v31-shopee-candidates-safe-8` (JSON com retorno real de `itemId`, `imageUrl` e `offerLink` dos candidatos). Reporta 27 blogs, sendo 17 com candidato e 10 bloqueados.
- **57 consultas autenticadas** em 27 buscas, **40 respostas GraphQL `10000`**, **17 respostas que produziram candidatos**; os 10 restantes pararam após três tentativas.
- Retries com nova assinatura, intervalos de 3/7 segundos, no máximo três requisições por busca; não tenta repetir outros códigos arbitrariamente.
- O workflow do PR retornou ao preflight amostral de três pautas **após** o scan completo, para evitar repetição automática de 27 consultas por mudança de código.
- Somente PR [#38](https://github.com/adelrib27/blogger-automation1/pull/38) em DRAFT. **`main`/Blogger/Lojas/temas/cron não alterados.**

## Curadoria manual obrigatória

### 12 candidatos diretamente pertinentes, mas ainda SEM autorização de artigo
- Achados para Casa — suporte cabide/organizador de porta, item `58268517628`
- Portal Radar Tech — suporte ajustável com ventilação para notebook, item `58210968568`
- Pedal Leve — adaptador para válvula Presta/Schrader, item `18299211081`
- Casa Leve e Funcional — prateleira adesiva de banheiro, item `22099046331`
- Achados da Rotina — passa-fio de mesa, item `57953953678`
- Ventiladores em Foco — ventilador de coluna, item `23193886166`
- Air Fryers em Foco — papel perfurado para air fryer, item `58214653026`
- Estilo no Dia a Dia — mochila casual para trabalho, item `58200598766`
- Casa em Ordem — organizador sob a pia, item `58109766285`
- Escolha Certa Online — cabides de veludo, item `58202019742`
- Mala Pronta e Viagem Prática — balança de bagagem, item `58207904854`
- Vida Pet Prática — fonte de água para gatos, item `58212387087`

### 2 candidatos somente contextuais
- Violão do Começo — flanela de limpeza, item `22392664941`: não substitui regulagem profissional por luthier; usar apenas se a pauta incluir cuidado preventivo relacionado.
- Jardim e Horta na Prática — casca de arroz carbonizada, item `53311613162`: insumo de drenagem/substrato, não mistura completa.

### 3 candidatos rejeitados como semanticamente inadequados
- Casa Prática Lab — item `58261999569`: apoio de tampa e colher na bancada não responde à organização de tampas no armário.
- Eletroportáteis na Cozinha — item `22995159446`: processador **manual**, inadequado a artigo sobre eletroportáteis.
- Guia de Achados & Ofertas — item `23098514649`: cafeteira com timer interno, inadequada a texto sobre temporizador digital avulso.

Os três casos acima foram incorporados à checagem de nicho do script SAFE do PR. Não copiar nem publicar esses anúncios para preencher lacunas.

### 10 bloqueios da consulta GraphQL 10000
- Cabelos em Foco — `6319734511998091378`
- Limpeza Inteligente — `7757953554206491487`
- Conecta Achados — `1719259388907013414`
- Achados que Valem — `7527651041649593600`
- Vitrine Prática — `9144338307944682868`
- Moda e Ofertas — `2858597309582499028`
- Achadinhos de Beleza — `2562496977098748229`
- Cozinha Sem Complicação — `3552757910439359679`
- Liquidificadores em Foco — `5271798990390532475`
- Ateliê Criativo em Casa — `8888519348129960729`

## Gates de publicação (NÃO PASSADOS)
1. Uma chamada GraphQL com produto é apenas prova comercial **para aquele anúncio e momento**, não liberação da rodada.
2. Faltam curadoria por pauta, redação original completa, fontes técnicas, link interno verdadeiro, HTML seguro, transparência comercial, inspeção de duplicação imediatamente antes de escrever, draft/readback, API LIVE e HTML público.
3. Em 09/11 o inventário anterior confirmou 27 blogs sem artigo nesse dia, mas a fila deverá ser **reconferida ao vivo** antes de qualquer criação; rascunhos antigos não devem ser publicados por engano.
4. **Mudanças Blogger nesta execução: 0**; **novos rascunhos: 0**; **novos artigos LIVE: 0**.

**Estado formal:** `SAFE_CATALOG_PARTIAL_12_DIRECT_2_CONTEXT_3_REJECT_10_GRAPHQL_BLOCKED`.
