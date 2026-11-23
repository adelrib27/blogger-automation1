# V31 C140 — PREVIEW: 50 simulações e unificação definitiva da referência Vida Pet

**Data:** 2026-11-23 America/Recife. **Base:** main `f0ad07716633c7cb176fc9bf127212b4210b6186`, C139 diretriz de todos os blogs ativos, exceto Ar-Condicionado sem Dúvidas.

## Correções explícitas do proprietário
1. Cada ciclo crítico de validação da automação deve executar **entre 10 e 50 simulações verificáveis**; padrão adotado **50 simulações offline independentes por ciclo**, com identificação de cenário, observabilidade e falha fechada se alguma rejeição indevida ocorrer. Testes simulados não substituem prova remota E2E.
2. `Vida Pet Prática` é **referência arquitetural**, NÃO um motor/pipeline/projeto independente nem um blog privilegiado no V31. A metodologia foi incorporada genericamente na C69: Evidence Engine, identidade exata SKU/modelo, whitelist, cache TTL sete dias sem renovação em leitura, duas evidências exatas e fonte externa quando aplicável, Candidate Failover, Evergreen, cooldown por SKU/ângulo, SearchBudget, anti-duplicações e buffer READY. Tudo por `site_key+campaign` universal. **Não modificar os writers legados próprios do antigo Vida Pet nem migrar seus dados como projeto separado.** Como blog acessível ao CMS, sua identidade é só mais uma possível entrada do inventário comum, exigindo registro/campanha como qualquer outro site; não criar fluxo especial.
3. Escopo C139 mantém todos os blogs ativos da conta conectada Blogger e os três WP existentes, excluindo Ar-Condicionado do novo V31 sem apagar o blog. Instantâneo não equivale a teto fixo; novos blogs exigem inventário CMS e campanha verificável antes de inclusão.

## Evidência de fonte histórica
O relatório mestre V31 C80 anexado ao projeto, seção 4.4, confirma que a fusão C69 foi universal e explícita, não específica para pets. Não confundir referência de métodos com autorização de usar o projeto/blog de origem como piloto isolado.

## Plano de execução SAFE
1. Atualizar `EDITORIAL_ACTIVE_SCOPE_POLICY.json` para registrar a metodologia **universal**, sem `vida_pet` especial ou exceção por nicho; deixar intactos inventário factual e a falta de rota/campanha verificada para qualquer alvo sem registro. Configurar `simulation_gate`: mínimo 10, padrão 50, máximo 50.
2. Criar módulo genérico de checagem de escopo e simulação de qualidade/regras. Matriz reproduzível **10 identidades × 5 condições**: sete alvos com rota confirmada, um alvo atual sem rota, um explicitamente excluído, um blog histórico não verificado; para cada um testar baseline, falta de link afiliado, falta de fonte independente, duplicidade CMS, solicitação LIVE.
3. Executar **50 cenários** em código sem CMS/D1/R2/Shopee writes; validar em CI, e aplicar o mesmo preflight antes de escrita nos workflows universais prioritários (conversor, DRAFT Blogger, DRAFT WP, scheduler/verificador). Guard operacional de escopo deve impedir Ar-Condicionado e rotas não ativas; não ativar os sites que ainda não possuem perfil/request.
4. Registrar preview antes da mudança, trabalhar em branch/PR, exigir CI verde e run remoto do gate, salvar checkpoint+JSON+índice.

**Proibições:** nenhuma ativação LIVE, publicação, renovação de cota, dispatch de escritor, criação de campanha fictícia, onboarding exclusivo de Vida Pet ou alteração do projeto Pinterest.
