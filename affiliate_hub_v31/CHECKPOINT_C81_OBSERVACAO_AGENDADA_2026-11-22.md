# V31 C81 — Observação agendada de DRAFTs e próximo gate de ativação (22/11/2026)

**Status: SAFE / checkpoint de continuidade.** Esta atualização documenta evidências externas e **não** aciona conversor, pesquisa, CMS, R2 ou D1 em escrita; tampouco altera cron, segredos ou os gatilhos da publicação. A fase editorial C81 ainda não equivale a uma fila DRAFT produtiva.

## 1. Base verificada

- Repositório `adelrib27/blogger-automation1`, branch `main`, HEAD antes deste checkpoint `0131f0d12bef396c52f01070290d990ce07ae402`.
- [C81 de 21/11](CHECKPOINT_C81_RETOMADA_DRAFT_2026-11-21.md) confirmou por GET autenticado e replay: Blogger `blogger_moveis_para_cada_canto` DRAFT `4106024906916105222`, SHA HTML `acf054f9eb4b65196aa46544c8402e7d603144d781604e006042059ba263569c`; WordPress `wordpress_casa_decoracao` DRAFT `321`, SHA HTML `81303c4a8d9590a0f4490afa8d92c8f845e5add267195535b7de5a2d300e6877`. Preservar os dois IDs, sem reconversão e sem segundo POST.
- A observação do workflow `.github/workflows/v31_autonomous_draft_scheduler.yml` é agendada a cada 4h em minuto 47 UTC. A observação somente leitura executa enquanto `vars.V31_AUTODRAFT_ACTIVE != 'true'`; o writer recorrente depende explicitamente da variável `V31_AUTODRAFT_ACTIVE == 'true'`. `V31_AUTOLIVE_ACTIVE == 'true'` é gate adicional somente para LIVE, cuja política `autonomous_live_policy.json` segue `pending_policy_approval`.

## 2. Prova de recorrência SOMENTE DE OBSERVAÇÃO

Três jobs `observe-homologation` invocados por `event=schedule` confirmaram **SUCCESS**, executando testes e `python -m affiliate_hub_v31.audit_draft_pilots` com GET dos dois CMS e SELECT D1:

| Run GitHub | Criado em UTC | Evidência |
|---|---|---|
| [#44924334792](https://github.com/adelrib27/blogger-automation1/actions/runs/44924334792) | 21/11 16:23 | Blogger status=draft ID 4106024906916105222, hash exato; WordPress status=draft ID 321, hash exato |
| [#44953910353](https://github.com/adelrib27/blogger-automation1/actions/runs/44953910353) | 21/11 21:54 | Mesmos IDs, hash e status |
| [#44998382196](https://github.com/adelrib27/blogger-automation1/actions/runs/44998382196) | 22/11 07:28 | Mesmos IDs, hash e status |

- **Nessas três execuções**, os jobs `choose-one`, `draft`, `release` e `audit` ficaram **skipped**. A conclusão `SUCCESS` do workflow **NÃO** é prova de criação recorrente de artigos novos, apenas de observação read-only e integridade preservada.
- Registro de monitoramento do dia 22/11 às 10h Brasília não pode ser inferido a partir do run de 07:28 UTC; revalidar GitHub antes de declarar janela de 10h concluída.
- Os logs mostram `SyntaxWarning` de escape em `universal_evidence_ready.py` (aviso não bloqueante) e deprecação Node.js de ações GitHub (higiene futura, sem invalidar a prova).

## 3. Falhas externas identificadas: não confundir com C81

- [Radar Tech BR #44972828996](https://github.com/adelrib27/blogger-automation1/actions/runs/44972828996) `schedule` **FAILURE**: tentativa legada ficou em `QUARENTENA` depois de 3 tentativas, motivo `título editorial fora da faixa: 34`; verificação `Confirmar publicação do slot` falhou. **Atenção: no workflow legado o log registra `RADAR_LIVE_PUBLISH_ENABLED=true` e `RADAR_WORDPRESS_STATUS=publish`**. Portanto, afirmar `LIVE globalmente desativado` seria incorreto: somente **a política LIVE do novo fluxo V31 autônomo C81** está desativada. Antes de migrar/expandir o V31, auditar autonomia e isolamento de writers legados para evitar duas rotas LIVE em paralelo.
- [V31 LAB #44961954195](https://github.com/adelrib27/blogger-automation1/actions/runs/44961954195) **FAILURE** em uma rotina LAB isolada de varredura Shopee SAFE: API retornou intermitente 10000 e terminou com `Sem oferta segura para Decoração / quadro decorativo`. Não habilitar publicação para contornar falha de fonte; preservar LAB isolado.
- Não repetir jobs de conversão/POST que já tiveram sucesso. Não misturar Pinterest/ARV/Vida Pet/contas Cloudflare externas.

## 4. Próximos passos para Work (ordem de segurança)

1. **Antes de qualquer novo disparo:** reler os workflows e runs de `schedule` após este checkpoint, verificar no GitHub os valores de habilitação (sem segredos), crédito Firecrawl e cotas D1/Shopee do dia UTC. Confirmar ausência de canários em andamento e manter idempotência por `site_key+campaign+SKU+HTML`.
2. Auditar escopo da fila `V31_AUTODRAFT_ACTIVE`, lista de sites ativados e quantidade por blog, além de conflitos com schedulers legados Blogger/WordPress. Validar que nenhum LIVE será acionado, inclusive por automação antiga quando migrar as rotas.
3. **Canário de recorrência de escrita DRAFT de forma limitada**: um site primeiro, um SKU inédito e orçamento disponível, usando workflow existente e sem reexecutar pilotos usados. Confirmação por GET do CMS, HTML SHA exato, ID estável em replay, campanhas e links corretos, D1 READY→USED e nenhuma publicação LIVE. Só depois ampliar ao segundo site e observar múltiplos ciclos reais.
4. Se a variável `V31_AUTODRAFT_ACTIVE` ainda for falsa/ausente, a ativação depende de configuração autorizada no GitHub/Work (conector GitHub deste chat não gerencia Variables de Actions). **Não contornar o opt-in alterando a condição do código ou ativar LIVE**.
5. Corrigir falhas de agendamento de Radar Tech BR e LAB **por trilhas separadas**, com os dados e política próprios de cada projeto, sem desviar da C81; investigar a razão de LIVE legado já ativo.
6. Registrar CI, resultados de canário, rollback e próximo checkpoint em `main`. Política LIVE do novo sistema somente após homologação e autorização única do proprietário para versão exata.

**Resultado deste checkpoint:** observação agendada de integridade passou em três ciclos; criação DRAFT recorrente ainda NÃO homologada; nenhuma mutação CMS/Cloudflare/Shoppe efetuada por esta atualização.
