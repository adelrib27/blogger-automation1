# V31 C45 — Curadoria universal contínua e índice resiliente (18/11/2026)

**Objetivo imutável:** feeds CSV Shopee → catálogo cumulativo R2 → categoria/nicho/facetas de todo o acervo (inclusive REVIEW) → seleção por tema só quando um novo blog for solicitado → campanha real daquele blog → conversão → gerador e publicador autorizados. Nunca limitar a biblioteca a três WordPress ou antecipar nichos/lojas/campanhas.

## Base real

- [C42 auditoria real](https://github.com/adelrib27/blogger-automation1/actions/runs/44350542388): 594 candidatos históricos com evidência dupla após ampliar regras de móveis; sem aprovação automática pela faceta oficial isolada.
- [C43](https://github.com/adelrib27/blogger-automation1/actions/runs/44351103492): 10 reclassificações, R2 salvo e verificado, índice universal atualizado, 0 posts, links anteriores preservados.
- [C44 — run 44352445875](https://github.com/adelrib27/blogger-automation1/actions/runs/44352445875): mais **584 reclassificações históricas**, em seis lotes até 100, cada um com snapshot e índice R2 restaurados/verificados; último ciclo 84. Total C43+C44 **594**, resta **194.370 REVIEW** no catálogo de **203.649 SKUs**. O sidecar final C44 marcou **8.997** como `approved`, **282** antigos aprovados mas bloqueados por origem e **194.370** em revisão; nenhum produto `POLICY_REVIEW` foi promovido. 0 publicações/0 conversões durante a curadoria.
- Workflow e gatilho temporários C44 removidos da `main` depois do sucesso para não repetir lotes por engano.

## C45 — operação permanente, sem previsão de blogs

- Novo módulo `universal_maintenance.py` chama a reclassificação histórica C39 estritamente até **100 SKUs por execução**, só para motivo de revisão `taxonomy_*` previamente existente e com título+L1/L2+origem+política concordantes. Retorna aprovação apenas quando `safe_reclassification` gravou e restaurou R2; nunca aceita métricas inventadas, posts ou mutation Shopee.
- Confere manifests `CURRENT.json` (catálogo principal) e `UNIVERSAL_INDEX_CURRENT.json` (sidecar); se o catálogo avançou, o produto total mudou, o índice faltou, ou a reclassificação aprovou novos SKUs, reconstrói **sidecar inteiro e verifica restauro**. Se a escrita do catálogo foi bem-sucedida e o sidecar falhou, a execução falha e o próximo ciclo restaura a coerência sem duplicar aprovações. Se nada mudou, **0 writes** ao R2.
- Novo workflow `.github/workflows/v31_universal_safe_maintenance_weekly.yml` roda na `main` às quartas ~09h13 Recife, após o refresh semanal dos dois feeds na terça ~07h23, **independente de blogs cadastrados**. Há disparo manual com confirmação explícita e opção de reparo forçado. Compartilha `concurrency: v31-editorial-catalog-single-writer`, usa Environment `v31-editorial-safe` restrito à `main`, apenas credenciais R2; não recebe chaves Shopee ou tokens WordPress/Blogger.
- Regressão CI [run 44368472242](https://github.com/adelrib27/blogger-automation1/actions/runs/44368472242) **SUCCESS**: **298 testes V31**, **24 Casa**, **21 Oficina**, cross-blog originality PASS. Testes novos cobrem relógios timezone, sidecar inexistente/antigo, reparo após falha parcial, no-op sem escritas, confirmação de invariantes e gate em erro.
- **O cron configurado não comprova execução futura**: só uma execução real após merge, seguida de auditoria, poderá validar o comportamento com a versão vigente do R2.

## O que continua pendente do objetivo integral

- O acervo completo é pesquisável no sidecar, mas os **194.370 em revisão não foram todos aprovados**; especialmente os **88.239 sem faceta oficial** e itens sob política. Não converter/publicar itens sem evidência segura.
- Expandir regras de título+fonte com base nos dados reais por categorias adicionais, preferindo evidência conservadora. Não inventar nichos futuros; se não houver dados suficientes, manter revisão e permitir busca.
- Um blog **novo** ainda depende de identidade real Blogger/WordPress, campanha Shopee própria e tema/quantidade solicitados pelo proprietário no momento da criação. Os adapters C36–C41 não provam criação e publicação de blog inexistente; cadastro e OAuth não podem ser inventados. Manter os publicadores atuais intactos.
- A ausência de dados de vendas/comissão **não bloqueia** indexação, conversão, seleção ou testes técnicos.
