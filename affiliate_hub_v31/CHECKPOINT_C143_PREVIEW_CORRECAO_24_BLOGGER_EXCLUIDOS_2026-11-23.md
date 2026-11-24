# V31 C143 — PREVIEW: exclusão definitiva de 24 blogs históricos do escopo operacional

**Data local:** 23/11/2026 (America/Recife). **Último verificado:** checkpoint C142.
**Origem de verdade:** proprietário esclareceu: **"os 24 blogs Blogger históricos"** referidos na C141 foram **EXCLUÍDOS por ele**. Essa informação substitui a hipótese anterior `PENDING_ACCOUNT_AUTHENTICATION` e NÃO depende de tentar reautenticar contas excluídas.

## Contrato corretivo
- Atual V31 editorial: **4 Blogger conectados** (Móveis para Cada Canto, Limpeza Inteligente, Estilo no Dia a Dia e Acessórios, Cozinha Sem Complicação) e **3 WordPress** (Casa, Oficina, Radar). Não criar teto universal de sete para novos blogs futuros; somente estes são alvos de agora.
- **24 Blogger apagados pelo usuário**: marcar `DELETED_BY_OWNER`, `eligible=false`, bloqueá-los por **ID Blogger + site_key de rota antiga**. NUNCA descrevê-los como "24 pendentes", "28 Blogger ativos", "8 sem rota" ou recomendá-los para recuperação/publicação. Somente um tombstone mínimo por ID para impedir reintrodução acidental, não carregar antigos produtos/posts/URLs na seleção.
- `Ar-Condicionado sem Dúvidas` existe no conector, mas foi **EXPRESSAMENTE EXCLUÍDO DO V31**, ainda não foi apagado automaticamente; nunca apagá-lo.
- `Vida Pet Prática` é referência metodológica e CMS existente, **não um projeto/etapa de onboarding/editoria especial do V31**, nem foi declarado parte dos 24 apagados.
- Nova auditoria: inventário vivo dos **6 Blogger** nos conectores (4 alvos + Ar excluído + Vida referência), em vez de C102/C141 obsoletos. Três WP conectados. Preservar a biblioteca R2 de produtos, links históricos e checkpoints de evidência, mas tirar os manifests antigos dos pontos operacionais.
- Auditoria de todos os workflows com `schedule` ligados a IDs apagados. Fail-closed: **nenhum cron escritor de blog apagado deve executar nem acionar APIs**; preservar código em histórico Git, não recriar workflows nem tocar CMS do Blogger. Não alterar writer de blog ativo ou do WP. Consistência do auditor estático e testes.
- Reinventariar as 50 simulações por ciclo usando **4 Blogger+3 WP atuais**, ataques de reintrodução de 24 IDs excluídos, blog Ar excluído, referência e futuro novo blog. 10–50 por ciclo, alvo 50, não escrever nem consumir cota.
- Registrar nova política/versionamento e checkpoint antes de continuar C144; reposicionar `V31_CONTINUAR_AQUI.md`, `CONTINUIDADE_ESTADO.json` e C141 JSON antigo como **SUPERSEDED**, sem reescrever Git history.

## Proibições
- Não apagar blogs do Blogger (já excluídos pelo proprietário), não restaurar ou tentar logar antigos IDs.
- Não excluir lojas/postagens remotas nem D1/R2/URLs que ainda possam ter evidência contábil; deixar registros históricos antigos **fora da seleção/continuidade ativa**.
- Não ligar LIVE automático; `pending_policy_approval` até autorização expressa final.
