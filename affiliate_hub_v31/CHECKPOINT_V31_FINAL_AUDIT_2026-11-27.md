# V31 — Auditoria de homologação final (27/11/2026)
Código de continuidade: V31-FINAL-AUDIT-46058071209.
Base main: f5efb68e899fba739f7e4d771e6cf6ce13ac1a47. Branch de correção: fix/v31-final-audit-20261127.

## Evidência real antes da alteração
- Evento schedule 46058071209: sucesso, verificador READY e entrega DRAFT_VERIFIED #406, replay mesmo ID e SHA-256 68f5b60808d1b287fd909191f3cdedd9ddb6341469a96e44ebe8188dad062dc6. LIVE skipped.
- SELECT D1 oficial em 27/11: fingerprint 2d869a40a23547351c44cc6c9e796da795f47622d7b92811f8be16bdbc7b24f6 = USED. Inventário: Radar 5 USED, Móveis 2 USED, Casa 1 USED + 1 READY. Não repetir POST.
- DRAFT agendado Blogger 45639927141 / 5901505853451174265 conforme checkpoint C158. A comprovação independente do CMS nesta retomada não foi obtida: conectores WP retornaram resposta vazia; o GET/hash do escritor consta no log GitHub.
- Monitor C136 run 45945506302: auditoria dos legados PASS; auditoria D1 USED + CMS falhou fechada, exit 2. O workflow não injeta a ponte escopada de credenciais Radar já usada pelo writer e necessária quando JSON universal ausente. A falha exata ainda não foi diagnosticada por log sanitizado; ausência de configuração é defeito objetivo, não prova de causa única.
- Readiness offline run 46028580097: 8 destinos prioritários, 3 configurados, 4 sem perfil/pedido completo e 1 sem rota. Não confundir perfil com cobertura real.
- LIVE policy pending_policy_approval. Radar ainda não está no mapa LIVE. Ambiente dedicado criado, mas checkpoint anterior indica credenciais protegidas pendentes. A existência de migração/ledger não autoriza publicação.

## Prévia da intervenção
Corrigir exclusivamente as referências da ponte Radar no monitor GET/SELECT, sem alterar escritores, política, cron, cota, CMS, Shopee, D1 ou R2. Validar por CI e por novo run read-only; não mesclar sem evidência suficiente. Consolidar estado canônico e distinguir homologação de DRAFT da de LIVE.
## Próximos critérios
1. Monitor C136 green, confrontar todos os USED com GET/hash, reconciliar Casa READY sem duplicar #314.
2. Validar recorrência/alertas e separação por campanha, completar perfis e credenciais dos demais destinos individualmente. Vida Pet exige rota e campanha reais, não assumir autorização.
3. Homologar LIVE com política e hash específicos, ambiente protegido, autorização explícita, teste fail-closed e recibo de publicação; manter OFF até isso.
4. Verificar a fila comercial e refresh de catálogo recentes, Loja mensal se ainda exigida, antes de declarar escopo integral entregue.
Sem mutação operacional iniciada nesta retomada; edição GitHub somente. Nenhum dado privado ou segredo no checkpoint.

## Complemento: fila comercial, 27/11
- Run [46062938131](https://github.com/adelrib27/blogger-automation1/actions/runs/46062938131) terminou FAILURE. Dry-run PASS: 7 pedidos avaliados, 2 candidatos (cozinhasemcomp/oficinawp), 23 ready_review_jobs, 0 mutações. Execução retornou RequestQueueError (motivo detalhado não registrado).
- SELECT D1 atual: os três slots do dia UTC 27/11 estão ocupados por radarwp. Não aumentar cota, não reexecutar conversor e não inferir conversão de uma reserva. Diagnosticar a classe de erro por código sanitizado e reconciliar R2 antes de próximo ciclo.
- PR de correção C136: https://github.com/adelrib27/blogger-automation1/pull/192. Merge bloqueado por ausência de CI confirmado; nenhuma alteração da main por esta auditoria.
