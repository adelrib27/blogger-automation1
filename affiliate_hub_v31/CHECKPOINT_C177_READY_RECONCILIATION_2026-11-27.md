# C177 — Conciliação READY/CMS universal
Código: V31-C177-READY-20261127. Base main 0cc75b292b760e5141f3e5d6598885b164a08483.
C176 concluída em main: PR 193, CI 46064125327: 959 testes PASS, 50 simulações PASS, WP 24/24,21/21,15/15. Migração D1 atômica executada após CI; 22/22 reservas byte-a-byte nos campos ordenados, 3 NULL/NULL preservadas, 3 slots hoje, CHECK 1..20. Código global 10, fila regular 8, fallback editorial 1 por artigo. Nenhuma conversão Shopee ou CMS write executada na migração. Monitor C136 run 46063857102: 8/8 DRAFTs verificados.
Próxima etapa: ajustar ponte Radar escopada no auditor C135, já usada pelo monitor C136, sem alterar o writer. O push na main executa exclusivamente GET/SELECT Casa e verifica o READY remanescente com o histórico CMS. Se existir colisão com #314, não consumir o job nem editar o artigo; exigir prova para conciliação. Não habilitar LIVE. Conversão real C176 ainda não comprovada; o conector GitHub não possui dispatch. Se necessário, Work para disparar a fila existente após merge e confirmar recibo R2.

## Resultado final desta retomada
- PR [194](https://github.com/adelrib27/blogger-automation1/pull/194) merged após CI 46064344980 PASS, SHA 27792e84f77b452a5e71ab70fa45662ab9985429.
- C135 [46064408922](https://github.com/adelrib27/blogger-automation1/actions/runs/46064408922) PASS: 15 testes, um READY Casa confrontado com CMS #314, CONFLICTING_DRAFT_HTML. Não converter em USED, não editar nem repetir POST.
- C148 [46064247485](https://github.com/adelrib27/blogger-automation1/actions/runs/46064247485) job remoto: R2/D1 PASS, 6/7 CMS GET; Oficina BLOCKED_CMS_SITE_CREDENTIALS_UNAVAILABLE. Cache por campanha Radar 20, Móveis 15, Casa 16, Oficina 6; Cozinha, Estilo e Limpeza 0. Não inferir conversão bem-sucedida do cache ou reserva. R2 CURRENT GET: snapshot criado 27/11 19:39:57 UTC. Fila comercial read-only do canário estava em andamento na última leitura.
- C176 em produção: 10/dia, fila regular até 8 por ciclo, schema 20; 22 reservas preservadas e 3 anônimas mantidas. Conversão real pós-deploy ainda não comprovada. Não disparar writer antigo.
- Bloqueio operacional: usar Work para novo workflow_dispatch da fila comercial e configuração de acesso Oficina; não expor secrets. LIVE OFF e tombstones preservados. Nenhuma mutação Shopee/CMS nesta retomada.

## Retomada C178 — fila comercial comprovada e acesso Oficina pendente

Código de continuidade `V31-C178-COMERCIAL-46071220811`.

- A execução [46071057260](https://github.com/adelrib27/blogger-automation1/actions/runs/46071057260) foi pulada pelo guard de confirmação, com zero tentativas.
- A execução única de conversão real [46071220811](https://github.com/adelrib27/blogger-automation1/actions/runs/46071220811) concluiu com sete conversões em seis campanhas, uma reserva negada pelo limite e zero chamadas de publicação. SELECT direto no D1 confirmou os slots 1 a 10 em 27/11 UTC, com sete novas reservas nos slots 4 a 10. GET direto no R2 confirmou CURRENT atualizado em 21h38 UTC e SHA-256 `9f384ecdbf5a1b19170b50290a0ebed7d5417c2208339b7f232bcb72dfcb28a9`. O log confirma snapshot salvo e verificado.
- O conector da Oficina respondeu com a URL registrada. O runner C148 estava sem `V31_WORDPRESS_SITE_CREDENTIALS_JSON` e a inspeção do ambiente protegido confirmou a ausência. A [PR 195](https://github.com/adelrib27/blogger-automation1/pull/195) preserva a credencial de Casa restrita à própria rota quando o JSON só contém Oficina. Mesclada em `c3f2c2e455775f0de369acd123e09fe4193ae99b` após [960 testes e 50 simulações](https://github.com/adelrib27/blogger-automation1/actions/runs/46071402276).
- Próximo passo após cadastro manual da senha de aplicação da Oficina no ambiente `v31-editorial-safe`: disparar o C148 na main e exigir GET na rota correta e 7/7 CMS. Seguir com a homologação DRAFT por rota e perfis restantes. O READY Casa em conflito com #314 segue bloqueado e a política LIVE está em `pending_policy_approval`.
