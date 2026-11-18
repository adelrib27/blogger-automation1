# C23 — Shopee App Secret rotacionado, autenticado e workflow temporário limpo (18/11/2026)

**Estado:** o proprietário confirmou que rotacionou o segredo no painel oficial Shopee e atualizou o **Environment secret** `V31_EDITORIAL_SHOPEE_APP_SECRET` no GitHub (sem informar valor).

- [Canário real 44302637196](https://github.com/adelrib27/blogger-automation1/actions/runs/44302637196): **SUCCESS**. Uma única consulta autenticada de **leitura** `productOfferV2`, com limite 1, usando `V31_EDITORIAL_SHOPEE_APP_ID` e o novo `V31_EDITORIAL_SHOPEE_APP_SECRET`. Log sanitizado **`V31_SHOPEE_API_PASS`**, seguido de `V31_C23_ROTATED_SECRET_AUTH_READONLY_SUCCESS`.
- **230/230 testes V31 offline PASS** na mesma execução. Nenhuma conversão de link, nenhuma publicação, nenhum envio de segredo em logs, nenhuma escrita no R2 e nenhuma criação de site.
- Workflow temporário `.github/workflows/v31_c23_shopee_rotated_secret_once.yml` e gatilho `C23_ROTATED_SECRET_ONCE_TRIGGER.txt` **removidos** após a prova. Nenhuma alteração na `main`, no Pinterest, nas páginas de loja ou nas flags de release.
- **[Issue #53](https://github.com/adelrib27/blogger-automation1/issues/53)** atualizada com os itens de rotação/validação marcados como concluídos.
- **Pendência administrativa ainda NÃO concluída:** definir restrição do GitHub Environment `v31-editorial-safe` para permitir apenas a branch `main`, revisar aprovação e permissões, e verificar se credenciais do mesmo aplicativo em outras rotinas independentes precisam de atualização. O canário C23 conseguiu acessar o Environment a partir de feature branch, logo a restrição ainda não está aplicada.
- **Próxima etapa após a proteção:** reconciliar PR #52 com `main`; validar gates e orçamento da API; converter progressivamente os **14 links reais** ainda necessários para reserva (Casa 5, Oficina 2, Radar 7) com persistência verificada; canário de publicação por site, rollback e ativação restrita. Não permitir publishing em review, nem inventar métricas de venda/comissão.

**Continuidade:** `V31-EDITORIAL-C23-SHOPEE-ROTATED-AUTH-PASS-230TESTS-20261118`. **PR #52 continua DRAFT sem merge**, aguardando ação manual de segurança.
