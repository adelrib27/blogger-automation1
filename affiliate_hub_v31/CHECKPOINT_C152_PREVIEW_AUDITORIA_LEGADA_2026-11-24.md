# C152 — PREVIEW verificável, auditoria legada CMS (24/11/2026)

**Branch isolada:** `fix/v31-c152-legacy-cms-collision-20261124`
**Base HEAD `main`:** `e1a2fd180ce69e57f2ce3ee3e082c4618acaf8f9`; comparação GitHub `identical`, `ahead_by=0`, `behind_by=0` antes de criar a branch.
**Política LIVE lida na main:** `activation=pending_policy_approval`. **Radar request:** `enabled=false`.
**Escopo:** somente V31 Blogger/WordPress; não introduzir Pinterest ou writers Radar legados.

## Evidência de inventário READ-ONLY (WordPress Radar Tech BR)
- Identidade remota via WordPress conectado: `https://radartechbr.com.br` (name Radar Tech BR).
- `wp_count_posts`: **37 publish + 19 draft = 56**, sem pending/future/private; `wp_list_posts(statuses=[publish,draft], context=edit, per_page=100)` confirmou 56 itens.
- Leitura dos **56 conteúdos RAW** em `wp_list_posts(context=edit,raw_columns=true)` com paginação de 12: 56/56 corpos não vazios, aproximadamente 517.011 caracteres no total.
- Busca literal nos 56 corpos/títulos/slugs para os quatro itens C151: `22398817823`, `22192873783`, `22295181772`, `58267720942` — **zero coincidências literais**. Isso **NÃO** exclui colisão semântica, SKU com outra codificação, oferta em links abreviados ou duplicação em D1.
- Dois artigos publicados com sobreposição temática smartwatch: WordPress `#260` ("Smartwatch e frequência cardíaca: o que verificar") e `#138` ("Smartwatch com tela infinita: o que significa?"). Sobreposição genérica **não prova duplicata**; comparar modelo e ângulo antes de autorizar nova redação.
- Corpos legados contêm links Shopee; chaves `data-v31-product-key` ou formato `shopee:shop:item` aparecem explicitamente nos posts `#353/#354/#355/#324`, **não em correspondência literal aos quatro SKUs C151**.
- Esta auditoria não escreveu no CMS, Shopee, R2 ou D1. Nenhum POST ocorreu.

## Bloqueios preservados
1. Quatro candidatos C151 sem `radarwp` em cache e sem provas de fabricante/modelo/variante.
2. Não confundir ausência de SKU literal com ausência de artigo semanticamente equivalente.
3. Não repetir `campaign+SKU` das três tentativas históricas Radar; não converter sem evidência.
4. D1/R2 devem ser relidos antes de mutações; colisão Casa `READY` x post `#314` permanece.
5. Sem DRAFT Radar e sem LIVE até todos os gates.

## Execução planejada nesta branch
- Adicionar guarda de deduplicação **universal** de conteúdo CMS (títulos, slugs, SKU e links de SKU quando disponíveis) para posts publicados + rascunhos.
- Integrar no writer **revisado universal** antes do consumo de READY/POST; testes unitários de falsos positivos, variantes, plataformas e identidade.
- Rodar CI SAFE + 50 simulações e registrar resultados reais. Não afirmar homologação E2E sem recibos.
- Revisar mudanças via PR; só mesclar com evidência suficiente, atualizando `SYSTEM_MASTER.md`, `CONTINUIDADE_ESTADO.json` e `V31_CONTINUAR_AQUI.md` se necessário.

**Estado do preview:** C152 em andamento; segurança fail-closed. Nenhum artigo criado.
