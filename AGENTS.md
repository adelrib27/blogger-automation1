# Agentes — V31 Hub Editorial Shopee

A referência arquitetural única é [SYSTEM_MASTER.md](SYSTEM_MASTER.md). Antes de executar, leia o documento mestre, [CONTINUIDADE_ESTADO.json](affiliate_hub_v31/CONTINUIDADE_ESTADO.json), [política de escopo](affiliate_hub_v31/EDITORIAL_ACTIVE_SCOPE_POLICY.json), [tombstones](affiliate_hub_v31/EDITORIAL_DELETED_BLOGGER_TOMBSTONES_C143.json) e [política LIVE](affiliate_hub_v31/autonomous_live_policy.json). Confirme as fontes vivas e o SHA atual de `main`.

## Contrato operacional

- Biblioteca Shopee cumulativa, universal e independente de blog futuro. Nenhum blog, nicho ou campanha é presumido.
- Só escrever no CMS com identidade real autenticada, rota registrada, campanha legítima, SKU/variante/foto exatos e verificação de fatos/SEO/links internos/afiliado.
- Os 24 IDs presentes na denylist são inalteravelmente inelegíveis. Não reativar, criar rota, cron, artigos ou Loja. Ar-Condicionado sem Dúvidas permanece excluído sem ordem de exclusão de CMS.
- Vida Pet Prática é um CMS Blogger real e ativo, mas não recebe writer V31 antes de verificar rota e campanha.
- Conversão e DRAFT são operações independentes; não fazer retries cegos após resultado remoto ambíguo. Confrontar histórico CMS, D1 READY e cache R2 antes de consumir novamente.
- Executar 50 simulações offline antes de ciclos críticos; simulação bem-sucedida não confirma publicação. Blogger `isDraft=True`; WordPress `status="draft"`. Verificar readback.
- `articles:null` significa continuidade sem teto vitalício. Preservar limites diários por site e deduplicação editorial.
- LIVE automático permanece `pending_policy_approval`. Não ativar sem homologação E2E e autorização final expressa.
- Não expor segredos ou dados de campanha em logs ou arquivos. Não alterar R2, D1, Shopee ou CMS para saneamento documental.
- Para mudanças: branch isolada, revisão dos riscos, CI verde, merge com SHA protegido e registro no estado JSON. Sem renomear caminhos existentes nem reescrever Git history.

Este arquivo define somente instruções aos agentes. Políticas detalhadas e arquitetura ficam em `SYSTEM_MASTER.md`; os JSON de configuração e as APIs autenticadas governam os estados executáveis.
