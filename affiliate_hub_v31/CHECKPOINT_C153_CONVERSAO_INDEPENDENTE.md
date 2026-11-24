# C153 — Conversão independente da homologação editorial

24/11/2026. Base main 730e2753353b2c5565d26cdd92a345455979d6e5. Autorização do proprietário: corrigir confusão e permitir operação independente.

Causa confirmada: site_request_queue.py descartava todo o conjunto aprovado para sites migrados quando não existia perfil de fabricante/GTIN. site_launch_plan.py também descartava SKU comercial sem template editorial. Corrigir seleção comercial sem remover gates dos escritores ou recuperação pontual protegida. Prioridade factual opcional, nunca pré-requisito da fila regular. Manter cota D1, campanha, moderação, origem, escopo, cache R2 e single writer. Não alterar LIVE, flags de sites ou crons aposentados.

Estado: PREVIEW, sem mutações Shopee/CMS/D1/R2. CI e merge pendentes. C152 histórico preservado; sua regra de bloqueio de conversão por revisão editorial fica superada para fila comercial regular após validação da correção.
