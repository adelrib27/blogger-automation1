# Checkpoint — Casa Prática Lab — E2E visual final

Data: 2026-11-02
Status: PASS

## Alvo

- Blog ID: `8930870316690519385`
- Home: `https://casa-pratica-lab-20261102.blogspot.com/`
- Page LOJA ID: `7110845449177208439`
- Page LOJA pública: `https://casa-pratica-lab-20261102.blogspot.com/p/loja.html`
- Store Post técnico ID: `7691087355641688975`
- Store Post técnico: `https://casa-pratica-lab-20261102.blogspot.com/2026/11/loja.html`
- Shopee AppID obrigatório: `18352820579`

## Arquitetura canônica aprovada para este blog novo

1. A superfície pública da loja é a Page `/p/loja.html`.
2. A Page recebe o HTML maduro da vitrine com exatamente 20 cards de Store + 12 cards de Hero.
3. O Store Post é apenas staging técnico e deve permanecer em `DRAFT`, fora da home.
4. A Page recebe patch de superfície ampla para reproduzir o layout maduro: sidebar/PopularPosts/título externo removidos somente nessa superfície, conteúdo centralizado e largura de até 1440 px.
5. O controlador legado do carousel baseado em `document.getElementById('blsSlider')` é removido da versão Page.
6. O carousel da Page usa delegação global de eventos + `MutationObserver` + estado global `currentIndex`, sincronizado entre as cópias de DOM que o Blogger cria para Pages estáticas.
7. O carousel mantém 3 slides, exatamente 1 visível, 3 dots, setas anterior/próximo e rotação automática de 6 s em produção.
8. A home deve conter apenas os 3 posts editoriais e nunca renderizar o Store Post técnico no FeaturedPost nem na grade normal.

## Causa raiz corrigida

O primeiro E2E considerava apenas contagens 20+12 e Policy Guard. Isso permitia PASS mesmo com comportamento visual diferente dos blogs maduros. Em Page estática, o Blogger duplica/recria o conteúdo no DOM. O JavaScript herdado do Store Post ligava eventos à cópia errada/obsoleta e o hero podia ficar empilhado ou o clique não persistir. Além disso, manter o Store Post LIVE poluía o FeaturedPost e depois a grade normal da home.

A solução final preserva o Store Post em DRAFT e torna a própria Page visualmente equivalente ao layout maduro, com controlador clone-safe.

## Prova final em navegador real

GitHub Actions run: `41494351547`
Job: `125445256366`
Conclusão: `SUCCESS`

Métricas finais em Chrome headless real, viewport 1440 px:

- largura pública `.bls-page`: `1392 / 1440`
- cópias Blogger detectadas: `2`
- slides: `3`
- slides visíveis: `1`
- dots: `3`
- controlador delegado: PASS
- controlador legado: ausente
- clique manual: `0 -> 1`
- índice após 700 ms: `1`
- índice após 2 s: `1`
- título externo `LOJA`: oculto
- `prefers-reduced-motion: reduce` usado apenas no teste para isolar o clique manual da rotação automática de 6 s

Mensagem final da prova:

`CASA_PRATICA_LAB_BROWSER_VISUAL_PASS: width=1392/1440; pages=2; slides=3 visible=1; dots=3; next=0->1; persisted_2s=PASS; delegated_state_sync=PASS; auto_rotation_isolated=PASS`

## Gates públicos finais

- `/p/loja.html`: HTTP 200
- Store: 20/20
- Hero: 12/12
- Policy Guard: PASS
- links afiliados patrocinados: >= 32
- layout amplo: PASS
- carousel delegado: PASS
- Store Post técnico fora da home: PASS
- 3/3 artigos editoriais presentes: PASS
- 3/3 artigos com imagem editorial: PASS

Mensagem E2E pública:

`CASA_PRATICA_LAB_PUBLIC_E2E_PAGE_MATURE_PASS`

## Automação permanente

Writer canônico:

`.github/workflows/casa_pratica_lab_store_page_autonomous.yml`

- `workflow_dispatch`
- schedule: `10:20` em `America/Recife`
- SAFE Shopee
- regressão semântica
- Policy Guard
- staging técnico
- sincronização Page madura
- Store Post novamente DRAFT
- aceitação pública
- persistência de rotação somente após PASS

Auditor permanente:

`.github/workflows/casa_pratica_lab_acceptance_audit.yml`

O auditor deve rejeitar regressões em 20+12, Policy Guard, superfície ampla, controlador delegado, controlador legado, home editorial e imagens dos artigos.

## Estado editorial esperado

Posts LIVE permitidos:

- `7732798999877296654` — Como organizar uma cozinha pequena sem gastar muito
- `5391626968548073797` — Air fryer: 7 pontos para conferir antes de comprar
- `1671345332688351619` — Ventilador ou climatizador: qual faz mais sentido para cada ambiente?

Store Post técnico esperado em DRAFT:

- `7691087355641688975` — Loja

## Higiene do repositório

Após PASS foram removidos os workflows temporários de migração, diagnóstico e provas visuais, além do helper abandonado do experimento Store Post LIVE. Devem permanecer apenas os componentes permanentes do caminho canônico.

## Regra para próximos blogs novos

Nunca declarar criação E2E como concluída apenas por HTTP 200, número de cards ou Policy Guard. A aceitação deve validar também o contrato visual/comportamental público, incluindo largura, quantidade de slides visíveis, controles do carousel, clique real, ausência de conteúdo técnico na home e estabilidade diante da duplicação/recriação de DOM do Blogger.

## Rede existente

Este contrato foi aplicado ao Casa Prática Lab como caminho de blog novo. Não usar este checkpoint como autorização para migrar automaticamente a arquitetura dos 18 blogs existentes.
