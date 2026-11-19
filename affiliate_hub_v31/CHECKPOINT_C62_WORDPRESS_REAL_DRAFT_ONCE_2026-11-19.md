# V31 C62 — canário WordPress REAL em DRAFT: Casa e Decoração (19/11/2026)

**PRÉVIA DURÁVEL. Estado: EM_ANDAMENTO. Nenhum WordPress POST neste ponto.**

## Autorização / propósito
O proprietário pediu o teste das automações de artigos e remover o teto de três. C61 já criou um Blogger DRAFT real e removeu o teto. C62 verifica a pendência C60 de **primeiro WordPress DRAFT real** no Casa e Decoração (instalação e campanha reais), sem LIVE e sem alterar os cron legados.

## Contrato seguro
- Testar primeiro autenticação REST e histórico de posts WordPress via credenciais existentes do **próprio Casa**, acessíveis somente no Environment GitHub. Não registrar tokens.
- R2 da campanha `wordpress_casa_decoracao`, apenas SKU `eligible` com foto real e link exato convertido, não reutilizado nos posts e com pauta derivada de título de produto realmente disponível.
- Um pedido temporário e explícito de TESTE, **1 rascunho total**, será criado apenas no runtime da Action (não registrado em `site_requests.d` da main), para evitar cron novo não autorizado. O writer C60 será usado com `status=draft`, originalidade de IA, CTA, disclosure, internos e read-after-write. O teste não autentica credenciais de futuros sites; isso continua exigindo secret por instalação.
- Em erro de identidade, permissão, conteúdo, campanha, R2 ou qualidade: **0 POST**; se a escrita tiver sido tentada e resposta inconclusiva, verificar posts WordPress antes de qualquer repetição.
- Workflow temporário, disparo por arquivo de controle; primeiro `preview` sem escrita. Após prova/impedimento, remover temporários e registrar evidências.

## Base confirmada
- C61 PR #81 e #82 MERGED; Blogger Móveis 3 LIVE+1 DRAFT real com foto e 2 links internos após correção.
- C60 #44412775615 WP Casa preview R2+43 posts, 0 POST; ainda não foi confirmado POST real.
- GitHub Casa cron #44451960384 SUCCESS; nomes de credenciais protegidas existentes nos workflows Casa. Isso não comprova acesso do writer C60 ao endpoint `settings` do WordPress.

## Próximos passos
1. Auth/read-only real com logs apenas de contagens e booleanos.
2. Se identidade e candidatos passam, geração original IA com worker e 1 único POST draft, nunca LIVE.
3. Confirmar draft REST e portal, registrar PR/CI e remover workflow temporário.

**Não usar Blogger/WordPress conectores como fonte de segredos; não alterar Runner/Pinterest/Worker v1.0.**

## C62 marco — autenticação WP e histórico

- [Teste #44538164537](https://github.com/adelrib27/blogger-automation1/actions/runs/44538164537) **FALHOU fechado antes de POST**: credenciais Casa disponíveis, `site_settings()` foi aceito; `list_posts(include_unpublished=True)` retornou `wordpress_http_HTTPError` ao consultar múltiplos status no mesmo filtro REST. 0 WordPress writes, 0 Shopee/R2 writes.
- Próximo passo: diagnóstico GET somente com variantes de status (`any`, `publish`, `draft` e lista), expondo apenas códigos HTTP; corrigir contrato REST com teste fake se necessário antes de POST.


## C62 atualização — paginação corrigida e prévia autenticada

- [Diagnóstico #44538971324](https://github.com/adelrib27/blogger-automation1/actions/runs/44538971324): API WordPress Casa respondeu 200 para filtros e revelou **43 publicados + 57 rascunhos = 100 posts**, header `X-WP-TotalPages=1`. O C60 anterior tratava página cheia como paginação adicional e falhava no GET página 2, sem POST.
- [PR #83 MERGED](https://github.com/adelrib27/blogger-automation1/pull/83) corrige `list_posts` para respeitar X-WP-TotalPages, inclusive 100 posts exatos, várias páginas e histórico inconsistente, CI [#44539480674](https://github.com/adelrib27/blogger-automation1/actions/runs/44539480674) PASS.
- [Canário WP PREVIEW autenticado #44539669937](https://github.com/adelrib27/blogger-automation1/actions/runs/44539669937) **SUCCESS**: identidade via `/wp-json/wp/v2/settings`, **100 posts lidos com permissão**, SKU novo aprovado da campanha Casa, foto/link exatos R2, `V31_C62_R2_CASA_READY`, **0 POST, 0 Shopee/R2 writes**. Próximo passo: execução única `execute_draft` sob esses mesmos gates, confirmar status draft e evitar repetição caso resposta inconclusiva.

## C62 — retomada do chat, pré-POST durável (19/11/2026)

- **VERIFICADO:** `main` HEAD `904417e740e0ed5b97237c12b806c01421f90eab` antes das mudanças desta retomada, mode file `C62_WP_TEST_MODE.txt=preview`, nenhum Action C62 `execute_draft` encontrado nas execuções recentes; [preview autenticado #44539669937](https://github.com/adelrib27/blogger-automation1/actions/runs/44539669937) SUCCESS e [PR #83](https://github.com/adelrib27/blogger-automation1/pull/83) MERGED.
- **AUTORIZAÇÃO JÁ EXISTENTE:** pedido de testar as automações em rascunho, sem LIVE e sem teto total de três; teste de Casa limitado a um único novo rascunho pelo runner temporário. Não criar demanda permanente WordPress `site_requests.d`.
- **ANTES DO POST:** JSON C62 atualizado em `main` com estado `EM_ANDAMENTO` e sinalização de potencial operação remota. Se ocorrer interrupção, procurar o Action C62 e consultar o WordPress **antes de reexecutar**. Bloquear qualquer repetição cega e preservar gates comerciais.
- **PRÓXIMO PASSO:** alterar `C62_WP_TEST_MODE.txt` de `preview` para `execute_draft` uma única vez; registrar ID da execução, verificar `DRAFT_CREATED`/status REST e ausência de LIVE; se falha ambígua, conferir rascunhos do site sem reenviar POST.

## C62 — Action disparada, aguardando resultado autenticado

- **FEITO:** alteração única de `C62_WP_TEST_MODE.txt` de `preview` para `execute_draft` no commit [`c22b1a7`](https://github.com/adelrib27/blogger-automation1/commit/c22b1a7fa6525455a140905c4be3e4d301d49e9b).
- **EM ANDAMENTO:** [Action C62 #44542052615](https://github.com/adelrib27/blogger-automation1/actions/runs/44542052615), job `wp-real-once` ID `135622693623`; instalação e regressões passaram e a etapa autenticada WP está em andamento. WordPress Casa independente ainda mostrava **43 publicados + 57 rascunhos** no último GET.
- **REGRA CRÍTICA:** enquanto o job estiver em execução, não executar outra vez; se falhar, checar primeiro o estado de posts no destino, em especial o slug exclusivo `v31-*`, antes de qualquer novo POST.
- **DIAGNÓSTICO PARALELO:** Radar cron [#44447410967](https://github.com/adelrib27/blogger-automation1/actions/runs/44447410967) terminou `failure` porque o slot `19:00` ficou `QUARENTENA` após três tentativas de plano com `título editorial fora da faixa: 31`; `Publicações confirmadas nesta execução: 0`. Quality gates funcionaram; não é falha de token WP e não cabe bypass de gate.
