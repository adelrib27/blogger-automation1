# V31 — Expansão comercial autorizada (27/11/2026)
Código: V31-BUDGET10-20261127. Base main 9fbee8c281b020f5a3512d6e9fefc838d351f587; PR 192 merged após CI 46063495908 success.
Proprietário autorizou ampliar 3 para 10 ou 20 tentativas/dia. Decisão: cap operacional 10, fila regular até 8, 2 slots disponíveis para fallback editorial; teto estrutural SQL 20 para evolução posterior controlada. Sem elevar cotas externas ou garantir conversões.
D1 SELECT: 22 reservas históricas, 3 legadas com ambos campos NULL; máximo slot 3. SQL real CHECK 1..3. As reservas anônimas não podem ser convertidas em pares inventados; preservá-las e contabilizá-las no dia, ignorar somente na lista de pares identificados. O erro histórico do conversor rejeita essas linhas. Não repetir par conhecido.
Plano: migração SQL atômica preservando histórico e constraints; código global 10; fila 8; conversor manual usa mesma reserva D1; testes de limite, slots históricos e duplicação. CI antes de deploy/migração; não alterar CMS, LIVE ou cadência editorial. Monitor C136 pós-merge run 46063857102 em andamento. 

## Resultado verificado
- CI [46064125327](https://github.com/adelrib27/blogger-automation1/actions/runs/46064125327): 959/959 testes, 50/50 simulações, três regressões WordPress PASS. PR [193](https://github.com/adelrib27/blogger-automation1/pull/193) merged, SHA 0cc75b292b760e5141f3e5d6598885b164a08483.
- D1 batch: CREATE, INSERT 22, DROP, RENAME, quatro statements success. SELECT ordenado antes/depois confirmou 22/22 linhas idênticas, três reservas anônimas preservadas, PK e unique preservadas, CHECK 1..20. Nenhuma tentativa nova. Dia UTC 27/11: 3 reservas, 7 slots restantes no código global 10.
- Monitor C136 real [46063857102](https://github.com/adelrib27/blogger-automation1/actions/runs/46063857102): 8/8 DRAFTs verificados.
- Estado: DEPLOYED_SCHEMA_VERIFIED_RUNTIME_PENDING. Nenhuma chamada Shopee para teste nesta etapa; aguardar novo cron ou dispatch pelo Work para comprovar novo cache R2.
