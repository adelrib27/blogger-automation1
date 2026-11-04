# Ledger V31 — idempotência e persistência segura

Componente **puro e reutilizável**, parametrizado por Blog ID e Page ID. Não usa credenciais, não faz rede, não publica e não possui caminhos fixos de computador.

Estados de uma atualização: `PLAN` → `PUBLISHED_PENDING_PUBLIC` → `PUBLIC_VERIFIED` → `PERSISTED`. Uma nova seleção fica bloqueada enquanto outra estiver ativa. `mark_readback` exige SHA-256 exato do HTML publicado. `mark_public_verified` exige relatório da auditoria pública com catálogo exato; o orquestrador é responsável por autenticar a origem dessa prova e validar o sucesso real do workflow. `history_commit` anexa no máximo uma entrada por operação e somente depois da prova pública.

**Status no LAB em 2026-11-03:** os 16 produtos da primeira seleção Shopee estão públicos e foram confirmados pelo Blogger Bridge e por auditoria independente, porém o workflow de publicação terminou `failure` após um HTTP 429 na verificação interna. Até concluir a auditoria pública automatizada, **não gravar rotação como `PERSISTED` nem ligar cron**.

O módulo possui 14 testes unitários locais (nenhuma rede). Sua integração transacional com GitHub/Actions e persistência atômica (`If-Match`/compare-and-swap) permanece futura: **não tratar este módulo isoladamente como motor diário completo**.