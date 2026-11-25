# C153 — Conversão independente da homologação editorial

24/11/2026. Base main 730e2753353b2c5565d26cdd92a345455979d6e5. Autorização do proprietário: corrigir confusão e permitir operação independente.

Causa confirmada: site_request_queue.py descartava todo o conjunto aprovado para sites migrados quando não existia perfil de fabricante/GTIN. site_launch_plan.py também descartava SKU comercial sem template editorial. Corrigir seleção comercial sem remover gates dos escritores ou recuperação pontual protegida. Prioridade factual opcional, nunca pré-requisito da fila regular. Manter cota D1, campanha, moderação, origem, escopo, cache R2 e single writer. Não alterar LIVE, flags de sites ou crons aposentados.

Estado: PREVIEW, sem mutações Shopee/CMS/D1/R2. CI e merge pendentes. C152 histórico preservado; sua regra de bloqueio de conversão por revisão editorial fica superada para fila comercial regular após validação da correção.

## Resultado verificado

C153: fila comercial regular não depende de fonte factual, template ou revisão de artigo. Perfil factual é prioridade opcional, não veto. Mantêm-se moderação, origem, campanha real, escopo, cache, reserva D1 na fila diária e single writer; a recuperação pontual editorial continua restrita. LIVE e flags de DRAFT inalterados. PR #160 mesclada em 60db4b0eda1c216a6ed34e028d5e264d904807ef; CI 45448688104: 922 testes e 50 simulações PASS. Sem nova conversão real confirmada; dispatch indisponível no conector GitHub atual. A próxima execução regular deve ser auditada antes de qualquer retry.
