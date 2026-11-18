# C24 — SHOPEE_SECRET legado atualizado e autenticado (18/11/2026)

**Confirmação do proprietário:** `SHOPEE_SECRET` (Repository secret) foi substituído pela nova chave rotacionada da mesma aplicação Shopee. A confirmação C23 de `V31_EDITORIAL_SHOPEE_APP_SECRET` (Environment secret) permanece válida.

## Prova efetiva

- [Canário C24 — run 44303901286](https://github.com/adelrib27/blogger-automation1/actions/runs/44303901286): job `verify-legacy-credential` **SUCCESS**. Executou uma única consulta GraphQL autenticada `productOfferV2`, somente leitura, usando `SHOPEE_APP_ID` + `SHOPEE_SECRET` do repositório. Recebeu `V31_SHOPEE_API_PASS` e `V31_C24_LEGACY_SECRET_AUTH_READONLY_SUCCESS`.
- Nenhum link convertido, nenhum armazenamento R2, nenhuma publicação e nenhuma criação de blog. Nenhum valor secreto registrado nos logs.
- O workflow temporário `.github/workflows/v31_c24_legacy_shopee_secret_once.yml` e o gatilho `affiliate_hub_v31/C24_LEGACY_SHOPEE_SECRET_ONCE_TRIGGER.txt` foram **excluídos** depois da prova. Apenas a branch `feature/v31-affiliate-hub-c1-safe-20261115` foi alterada; `main` e Pinterest não foram tocados.
- [Issue #53](https://github.com/adelrib27/blogger-automation1/issues/53) atualizada. **Ainda pendente:** proprietário restringir `Settings → Environments → v31-editorial-safe → Deployment branches and tags` para `main` e revisar regras de aprovação/permite ações.
- `PR #52` **DRAFT** permanece sem merge; todas as flags LIVE OFF. Depois da proteção, faltam 14 ofertas afiliadas convertidas para estoque alvo de reserva: Casa 5, Oficina 2, Radar 7, sob gate de origem, nicho, campanha e cotas.
- A falta de métricas de vendas/comissões não impede as etapas técnicas. Não confundir o PASS read-only com uma prova de mutações ou liberação de produção.

**Continuidade:** `V31-EDITORIAL-C24-LEGACY-SHOPEE-SECRET-AUTH-PASS-20261118`.
