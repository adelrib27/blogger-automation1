# Núcleo editorial universal V31

A arquitetura, as regras de negócio, o mapa de módulos e o roadmap oficial encontram-se exclusivamente em [SYSTEM_MASTER.md](../SYSTEM_MASTER.md).

Este pacote Python reúne catálogo SQLite, snapshots R2, taxonomia e índice universal, roteamento por site/campanha, conversão Shopee, evidência factual, revisão independente, envelope HTML privado, D1 READY/USED e adaptadores DRAFT Blogger/WordPress.

## Entradas operacionais

- [Estado](CONTINUIDADE_ESTADO.json) — atividade, bloqueios e próximo passo.
- [Escopo](EDITORIAL_ACTIVE_SCOPE_POLICY.json) — destinos aptos e sujeitos a onboarding.
- [Denylist](EDITORIAL_DELETED_BLOGGER_TOMBSTONES_C143.json) — identidades indisponíveis.
- [Rotas](site_routes.json) e `sites.d/` — site e campanha.
- `site_requests.d/` — pedidos reais de conteúdo.
- [Política LIVE](autonomous_live_policy.json) — liberação pública desativada.
- [Testes](tests/) e [workflows](../.github/workflows/) — evidências de regressão e operação.

**Contrato:** cada operação crítica é fail-closed e idempotente. O catálogo não autoriza publicação por si só. O sistema não deve publicar LIVE automaticamente enquanto a política final estiver pendente. A ausência de oferta exata, fonte independente, imagem real, credencial ou campanha verificada bloqueia mutações externas.

Os arquivos de configuração JSON e o conteúdo do GitHub não são substituídos por este README. Qualquer mudança de arquitetura deve constar no `SYSTEM_MASTER.md`.
