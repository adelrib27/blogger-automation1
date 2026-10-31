# Checkpoint — rollout Blogger Multi Store

Data: 2026-10-31

## Objetivo

Implantar loja Shopee nos blogs da conta Blogger que ainda não possuíam loja, usando como referência funcional a loja do Liquidificador Philips Walita RI2242 e as regras do kit mestre de loja validado.

## Auditoria inicial

```text
18 blogs na conta
1 loja completa pré-existente: Philips Walita RI2242
17 blogs sem post LIVE Loja e sem página LIVE Loja
```

## Estado confirmado após as primeiras implantações

### PASS completo — post Loja + página estável /p/loja.html

1. Liquidificador Philips Walita RI2242 — pré-existente
   - Blog ID: `5271798990390532475`
   - Post Loja: `8867555367475283866`
   - Página Loja: `5473313787015756722`

2. Cozinha Sem Complicação
   - Blog ID: `3552757910439359679`
   - Post Loja: `7888042807715084117`
   - Post URL: `https://cozinha-sem-complicacao.blogspot.com/2026/10/loja.html`
   - Página Loja: `6913756651435112886`
   - Página URL: `https://cozinha-sem-complicacao.blogspot.com/p/loja.html`

3. Achados para Casa
   - Blog ID: `1426630233929943394`
   - Post Loja: `854861801599328533`
   - Post URL: `https://achadosparacasa2026.blogspot.com/2026/10/loja.html`
   - Página Loja: `3841238517239710135`
   - Página URL: `https://achadosparacasa2026.blogspot.com/p/loja.html`

4. Moda e Ofertas
   - Blog ID: `2858597309582499028`
   - Post Loja: `4871366557503134389`
   - Post URL: `https://moda-ofertas.blogspot.com/2026/10/loja.html`
   - Página Loja: `1341310014099438949`
   - Página URL: `https://moda-ofertas.blogspot.com/p/loja.html`

5. Radar Tech BR
   - Blog ID: `7487888217273188851`
   - Post Loja: `906894044295273477`
   - Post URL: `https://portalradartechbr.blogspot.com/2026/10/loja.html`
   - Página Loja: `6887385207246667244`
   - Página URL: `https://portalradartechbr.blogspot.com/p/loja.html`
   - Conteúdo pós-publicação revalidado: marcador multi-store, produtos reais, imagens reais e links `nofollow sponsored noopener` PASS.

### PARCIAL — post Loja criado, página estável ainda pendente

6. Achadinhos de Beleza
   - Blog ID: `2562496977098748229`
   - Post Loja: `7650631557624373238`
   - Post URL: `https://canal-attitude.blogspot.com/2026/10/loja.html`
   - Página `/p/loja.html`: PENDENTE devido a rate limit de escrita.

### Ainda sem implantação

- Robô Aspirador WAP Robot W90 — `7757953554206491487`
- Air Fryer Elgin Cube Fry 4,2 L — `9113728635217260884`
- Ventilador Mondial Super Power VSP-40-B 40cm — `4473989735719981382`
- Tá Na Moda | Morte Súbita Lola 450g — `6319734511998091378`
- Liquidificador Britânia BLQ1300P — `8658632621591002634`
- Guia de Achados & Ofertas — `1453188702831337099`
- Conecta Achados — `1719259388907013414`
- Vitrine Prática — `9144338307944682868`
- Achados que Valem — `7527651041649593600`
- Escolha Certa Online — `5151950717041967683`
- Casa em Ordem — `4177382081459143374`
- Estilo no Dia a Dia — `4830103887652146866`

## Quota / bloqueio observado

Após várias escritas, a Blogger API passou a devolver:

```text
HTTP 429
rateLimitExceeded
Resource has been exhausted (e.g. check quota)
```

O bloqueio ocorreu tanto no Blogger Bridge V2 quanto no OAuth usado pelo GitHub Actions, confirmando que não era defeito de um conector específico.

A última janela observada permitiu nova escrita depois de aproximadamente seis minutos. Não fazer rajadas de escrita.

## Workflow e código de retomada

- `blogger_multi_store/config/bootstrap_missing_stores.json`
- `blogger_multi_store/src/bootstrap_missing_stores.py`
- `.github/workflows/blogger_multi_store_bootstrap.yml`
- `blogger_multi_store/README.md`

O bootstrap é idempotente: relê post/página `Loja` antes de qualquer criação, portanto pode ser retomado sem duplicar objetos.

Commits centrais:

```text
d31925eb30b0b578285a21bbad966a5f130d584b  config de lojas/produtos-semente
aeb8f1cae02f91b26e88ecdd917f68afddca21b0  bootstrap inicial
dd7ba16d8c6a4f7a93a136123acdb175bc35b0e0  workflow bootstrap
3a39f1b61ba2faa2d1b8daa1d3591331dbbb7e64  backoff de quota Blogger
64ea4893c1aba044d743b16da67035419252ddda  documentação multi-store
```

## Runs GitHub Actions

- Run `41199266816`: falhou na criação da página Radar por HTTP 429; o post Radar já havia sido criado.
- Run `41199348749`: retomou Radar, criou a página e validou PASS; depois falhou ao tentar criar Achadinhos após todos os backoffs, ainda por HTTP 429.
- Após a janela de quota, o post Achadinhos foi criado isoladamente e validado LIVE.

## Regra de retomada

Antes de qualquer nova escrita:

1. buscar título exato `Loja` LIVE no blog alvo;
2. listar páginas LIVE e procurar título exato `Loja`;
3. criar somente o objeto ausente;
4. fazer no máximo uma escrita por janela de quota;
5. revalidar por leitura antes de passar ao próximo objeto;
6. nunca excluir ou recriar uma Loja já encontrada.

## Definition of Done final

Somente declarar rollout completo quando os 18 blogs tiverem loja validada. Para os blogs novos desta camada, o alvo preferencial continua sendo:

```text
post LIVE Loja
página LIVE Loja em /p/loja.html
links de afiliado seguros
produtos reais
sem duplicata
validação independente posterior
```
