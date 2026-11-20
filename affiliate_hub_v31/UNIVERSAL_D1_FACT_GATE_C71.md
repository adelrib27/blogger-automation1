# C71 — D1 READY + Fact Gate pós-IA: contrato SAFE UNIVERSAL

**Escopo:** código reutilizável para qualquer blog REAL Blogger/WordPress, sem tocar em `vida_pet_pratica/`, D1 existente, R2, publicadores ou agendamentos. **NÃO É DEPLOY DE PRODUÇÃO.**

## 1. O que está implementado

- `final_fact_gate.py`: usa `evidence_whitelist` da C69 com produto/SKU exato, fontes aprovadas, TTL e hash do texto. Cada fato material atribuído a evidência é um `<span data-v31-fact-id="...">texto exato da fonte</span>`. O texto do span deve corresponder **literalmente** à afirmação aprovada, não basta citar uma ID. Rejeita alegações mudadas, origem similar, fonte vencida, id inexistente/duplicada, tags de script/form e links inseguros. O restante da redação exige hash de bloco aprovado **por revisor independente, nunca pela IA**; se não houver, falha fechada `unreviewed_editorial_text`. Um PASS não dispensa verificação editorial externa ou consentimento LIVE.
- `migrations/c71_universal_ready_d1.sql`: tabelas **novas e isoladas** para leases, READY/USED, cache de fontes, orçamento diário e circuit breaker. Índices por `site_key+campaign`; não migra Pet/CSV nem duplica os 203k SKUs.
- `d1_universal_ready.py`: adaptador SQL por `query(sql,params)->list[dict]` injetado, preparado para query REST/Worker D1 explicitamente autenticada. Todos os mutadores usam **UMA** declaração SQL atômica com `RETURNING`, evitam check-then-write e não se baseiam em `meta.changes` cumulativo. Lease por `site_key+campaign+tipo` com nonce, vencimento e compare-and-swap; buffer até min_ready por site, consumo `READY→USED` sem CMS; cache validado TTL7 sem refresco de leitura; orçamento SEARCH/HTTP por site/dia com breaker 429. **Nenhum token, client HTTP, banco, Worker, CMS ou Firecrawl real configurado**.
- Testes `test_c71_final_fact_gate.py` e `test_c71_d1_universal_ready.py`: integridade HTML, fonte exata, TTL, anti-XSS básico, ausência de revisão, corrida com duas conexões SQLite no mesmo arquivo, idempotência, ausência de lease, separação por site/campanha, cooldown implícito apenas após C69, budgets e 429.

## 2. Fronteiras de segurança
- Hash editorial não é um atestado automático: `trusted_reviewed_text_hashes` deve vir de revisão externa concreta e imutável (nunca do JSON da IA). O verificador **não infere semanticamente** que toda afirmação livre foi detectada; por isso exige aprovação independente de blocos não factuais.
- `data-v31-fact-id` é uma referência estruturada ao *mesmo produto*, não autorização para publicidade ou publicação. A whitelist depende de autorização confiável a montante, não da saída do crawler/modelo.
- O runner SQL não é instalado em nenhum cron. `RETURNING` precisa ser suportado/validado pelo backend D1 real e migrations aplicadas somente após backup e autorização de DB **V31 dedicado**. Testes de SQLite não substituem teste Cloudflare, read-after-write nem observabilidade de concorrência real.
- Toda chamada SEARCH paga depende da **mesma** credencial Firecrawl do GitHub com saldo/quota verificado e custo medido; orçamento local e tabela D1 controlam tentativas, **não garantem créditos nem custo monetário**.
- `min_ready=3` é buffer simultâneo, **não teto de artigos**; `articles:null` e a biblioteca universal de qualquer nicho continuam.
- O controle LIVE C67 permanece separado com aprovação por post+hash e autorização explícita do proprietário. Nada neste PR cria, publica, ou revisa automaticamente os blogs existentes.

## 3. Próximas fases reais de homologação

1. Provisionar **após revisão** um banco D1 V31 independente do Vida Pet com ambiente/secret seguro, aplicar migração reversível e validar SQL/locks com execução real, isolamento e readback (sem posts).
2. Construir um runner Cloudflare D1 autenticado com segredo isolado e parâmetros preparados, mais telemetria sem SKU/URL/segredos; conectar somente a uma fila SAFE sem write em CMS.
3. Confirmar quota/saldo da **mesma chave GitHub Firecrawl** e executar no máximo **1 cache miss real** com custo/429/TTL medidos, ou registrar bloqueio até haver saldo. Não executar pesquisa real no escuro.
4. Integrar Evidence/READY aos writers Blogger e WordPress **somente depois** de validar fact gate, SEO C68, foto/link/campanha R2, quota por site e prova DRAFT segura. Conduzir canários DRAFT independentes, zerar LIVE.
5. Reforçar revisão humana para textos de IA fora da whitelist, proteção contra mudança de HTML pós-revisão e dedup distribuído, além de observar `event=schedule` de 20/11 (19/11 já comprovou os writers).
6. Depois de homologação total, ativar rotinas SAFE graduais por blog real. Publicação LIVE somente em aprovação individual; nunca genérica.

**Referências oficiais:** [D1 query API](https://developers.cloudflare.com/api/resources/d1/subresources/database/methods/query/index.md) e [D1 Worker API](https://developers.cloudflare.com/d1/worker-api/d1-database/index.md).

O contrato C71 oferece código/SQL testável e evita fingir que D1, Firecrawl, fontes, QA semântico ou produção estão ligados.
