# CHECKPOINT ATUAL — BLOGGER AUTOMATION

**Estado canônico:** 2026-11-02 — após conclusão de Moda e Ofertas  
**Projeto:** Blogger Automation sem ChatGPT Work  
**Progresso:** **15/18 lojas Blogger modernas concluídas**

## LEIA PRIMEIRO

Antes de qualquer nova operação Blogger neste projeto, leia nesta ordem:

1. `CHECKPOINT_ATUAL.md`
2. `blogger_multi_store/data/NETWORK_STORE_INVENTORY_2026-11-02.json`
3. `blogger_multi_store/config/network_store_rollout_2026-11-01.json`
4. `CHECKPOINT_UPDATE_2026-11-01_POLICY_EDITORIAL_COOKIES.md`
5. `BACKUP_MANIFEST_BLOGGER_AUTOMATION_2026-11-02_R4.json`
6. `CHECKPOINT_UPDATE_2026-10-30_LAB_CANONICAL_V20.md`
7. `CHECKPOINT_BLOGGER_AUTOMATION_MASTER_2026-10-30.md`
8. `infrastructure/README.md`

Este arquivo prevalece para o estado operacional. Checkpoints anteriores são histórico/base de recuperação.

---

# 1. ESTADO OPERACIONAL VALIDADO

- Rede: **18 blogs Blogger**.
- **18/18** possuem Page LIVE `/p/loja.html`.
- **18/18** possuem Store Post LIVE `Loja`.
- **15/18** possuem automação moderna protegida pelo Blogger Policy Guard.
- **3/18** permanecem com scaffold e ainda precisam de automação Blogger 20x12.
- Não recriar Page/Post Loja; preservar sempre os IDs existentes.
- TEMA MODELO V20 permanece como base canônica.
- Blogger Local Runner v0.8 e Blogger_Bridge_V2 continuam válidos.
- Rollout global permanece desabilitado. Trabalhar **um blog por vez**.

## Lojas modernas concluídas — 15/18

1. Eletroportáteis na Cozinha
2. Cabelos em Foco
3. Ventiladores em Foco
4. Air Fryers em Foco
5. Limpeza Inteligente
6. Liquidificadores em Foco
7. Vitrine Prática
8. Achados para Casa
9. Conecta Achados
10. Estilo no Dia a Dia
11. Casa em Ordem
12. Escolha Certa Online
13. Achados que Valem
14. Guia de Achados & Ofertas
15. **Moda e Ofertas**

Inventário atual:

- `modern_blogger_auto_policy_guard: 15`
- `modern_blogger_auto_20x12_needs_policy_guard_upgrade: 0`
- `store_scaffold_needs_auto_rotation: 3`
- `duplicate_writer_risks: 0`

Fonte atual: `blogger_multi_store/data/NETWORK_STORE_INVENTORY_2026-11-02.json`.

---

# 2. ARQUITETURA CANÔNICA

```text
Shopee API
→ Policy Guard
→ filtro semântico específico do blog
→ deduplicação / rotação
→ SAFE
→ Policy Guard pré-LIVE
→ dry-runs de identidade / Store / hero
→ LIVE no Store Post existente
→ hero 12
→ identidade/layout
→ validação pública HTTP 200
→ contrato público 20 produtos + 12 hero
→ Policy Guard no HTML público
→ persistência de estado somente após PASS
→ schedule
```

Contrato obrigatório:

- 20 produtos;
- 12 mini-cards no hero;
- Page Loja existente preservada;
- Store Post existente preservado;
- filtros semânticos específicos por blog;
- links afiliados com `rel="nofollow sponsored noopener"`;
- disclosure de afiliado;
- fail-closed;
- nenhum item semanticamente inválido usado apenas para completar quantidade;
- HTTP público 200 obrigatório; 429 deve receber retry;
- persistência somente após PASS público;
- config, seleção e histórico de rotação independentes por blog;
- writer automático único por blog.

---

# 3. POLICY GUARD E AUDITOR PERMANENTE

Arquivos centrais:

- `POLICY_BASELINE_BLOGGER_GOOGLE_2026.md`
- `config/blogger_policy_guard.json`
- `src/blogger_policy_guard.py`
- `src/blogger_policy_guard_self_test.py`
- `src/blogger_policy_repo_audit.py`
- `.github/workflows/blogger_policy_repo_audit.yml`

O auditor cobre **15 SAFE/LIVE modernos**, writers legados, proteção de cookies e schedules finais. Após Moda e Ofertas, o auditor também protege:

- Casa em Ordem — 08:05
- Escolha Certa Online — 08:20
- Achados que Valem — 09:50
- Guia de Achados & Ofertas — 10:05
- **Moda e Ofertas — 10:20**

Prova da promoção de Moda:

- commit do writer agendado: `4dd7113dc4f5ebcef2161dfa3aac466eb5b7be56`
- commit do reforço do auditor: `ec940860dbedd49b7d63e5cde02ecf53b293f1d9`
- auditor run `41477761596` — **SUCCESS**
- job `125387734042`
- `BLOGGER_POLICY_REPO_AUDIT_PASS`
- `SAFE/LIVE 15/15 protegidos`

O writer de Moda não possui mais gatilho `push`; fica em `workflow_dispatch` + schedule diário `20 10 * * *`, timezone `America/Recife`.

---

# 4. MODA E OFERTAS — 15ª LOJA MODERNA — CONCLUÍDA

## Alvo preservado

- Blog ID `2858597309582499028`
- Blog `https://moda-ofertas.blogspot.com/`
- Page LOJA ID `1341310014099438949`
- Page `https://moda-ofertas.blogspot.com/p/loja.html`
- Store Post ID `4871366557503134389`
- Store Post `https://moda-ofertas.blogspot.com/2026/10/loja.html`

Arquivos permanentes:

- SAFE `.github/workflows/moda_ofertas_store_safe.yml`
- LIVE `.github/workflows/moda_ofertas_store_autonomous.yml`
- motor `blogger_stores/src/moda_ofertas_store.py`
- config `config/shopee_moda_ofertas.json`
- regras `config/shopee_moda_ofertas_intent_rules.json`
- kickoff SAFE manual preservado `blogger_stores/moda_ofertas_kickoff.txt`

Categorias finais:

1. Moda Feminina
2. Moda Masculina
3. Calçados & Bolsas
4. Acessórios
5. Beleza & Cuidados

Cada categoria possui quatro intenções; total de 20 produtos.

## SAFE e endurecimento semântico

O rollout foi deliberadamente fail-closed. As rodadas iniciais detectaram, antes da promoção final:

- difusor/acessório passando como secador;
- insuficiência do pool 180 para cobrir todas as intenções;
- erros transitórios Shopee `System Error 10000`;
- colisão de âncoras na identidade;
- suporte de parede passando como secador de cabelo;
- bundle de bolsa/carteira passando como carteira;
- short/`shoth` com cinto passando como cinto.

Correções permanentes:

- pool SAFE/LIVE `500`;
- reserva mantida;
- retry local limitado para erro Shopee `10000`, sem relaxar semântica;
- âncoras exatas e normalização idempotente;
- regressões com títulos reais dos falsos positivos;
- bloqueios específicos para acessórios/refis/suportes de secador, bundles de carteira e roupas contendo cinto.

SAFE final:

- run `41475489511` — **SUCCESS**
- regressão semântica **43/43**
- Policy Guard **20/20**
- seleção final revisada antes do LIVE.

## LIVE final

- run `41476423839` — **SUCCESS**
- job `125383073274`
- SAFE fresco PASS
- Policy Guard pré-LIVE PASS
- identity/store/hero dry-runs PASS
- Store Post: **20/20**
- hero: **12/12**
- identidade autenticada PASS
- HTTP público 200
- Policy Guard público PASS
- rotação persistida somente depois do PASS público
- commit de rotação `c5dfbd711800097f4ab083afefea532dfe753d95`

Leitura independente direta via Blogger_Bridge_V2 confirmou no Post ID original:

- status LIVE;
- 20 produtos + 12 hero;
- título `Beleza & Cuidados` correto;
- CTA `Ver moda feminina` → `#bls-moda-feminina`;
- CTA `Ver acessórios` → `#bls-acessorios`;
- CTA `Ver beleza` → `#bls-beleza-cuidados`;
- CTA `Ver moda masculina` → `#bls-moda-masculina`;
- secador válido `Secador De Cabelo Profissional Lizze Extreme`;
- cinto válido `Kit4 Cinto Feminino...`;
- falsos positivos conhecidos ausentes.

## Schedule final

- horário: **10:20 America/Recife**
- cron: `20 10 * * *`
- `workflow_dispatch` mantido para operação manual controlada;
- gatilho `push` removido;
- gate público reforçado com os CTAs/título corretos e bloqueio dos falsos positivos conhecidos;
- auditor central protege o horário e impede reintrodução de `push`.

Os workflows/scripts one-shot usados durante diagnóstico e promoção foram removidos. Permanecem apenas os componentes de produção e o kickoff SAFE manual.

**Moda e Ofertas não deve ser reaberto sem sinal concreto de regressão.**

---

# 5. FILA RESTANTE — EXATAMENTE 3 BLOGS

1. **Achadinhos de Beleza**
   - Blog ID `2562496977098748229`
   - Page LOJA ID `455853998448723529`
   - Store Post ID `7650631557624373238`
   - estado: `store_scaffold_needs_auto_rotation`

2. **Radar Tech BR**
   - Blog ID `7487888217273188851`
   - Page LOJA ID `6887385207246667244`
   - Store Post ID `906894044295273477`
   - estado: precisa de motor Blogger 20x12 próprio; o workflow Radar WordPress não substitui esse writer.

3. **Cozinha Sem Complicação**
   - Blog ID `3552757910439359679`
   - Page LOJA ID `6913756651435112886`
   - Store Post ID `7888042807715084117`
   - estado: `store_scaffold_needs_auto_rotation`

---

# 6. PRÓXIMO BLOCO PERMITIDO

O próximo blog é **Achadinhos de Beleza**, mas **não iniciar automaticamente neste mesmo bloco**.

Quando o usuário disser novamente **“continue”**, retomar por Achadinhos de Beleza e repetir exatamente a disciplina usada em Moda:

1. confirmar IDs e scaffold existente;
2. construir perfil semântico próprio;
3. instalar SAFE read-only;
4. revisar semanticamente a seleção real;
5. corrigir falsos positivos até SAFE confiável;
6. instalar LIVE inicialmente controlado/manual;
7. proteger no auditor central antes da escrita;
8. executar LIVE somente após SAFE + Policy Guard + dry-runs;
9. exigir HTTP público 200, 20 Store + 12 hero e identidade correta;
10. ler o Blogger independentemente após o LIVE;
11. somente então habilitar o próximo horário escalonado;
12. atualizar inventário e checkpoint.

Não trabalhar Radar Tech BR nem Cozinha Sem Complicação antes de concluir Achadinhos de Beleza.

---

# 7. REGRAS DE SEGURANÇA QUE NÃO PODEM REGREDIR

- nunca recriar Page/Post Loja quando os IDs existentes estão válidos;
- nunca aceitar Action verde como única prova de qualidade sem inspeção semântica quando houver dúvida;
- nunca persistir rotação antes do PASS público;
- nunca ignorar HTTP 429; usar retry até 200 ou falhar;
- nunca reintroduzir writer duplicado automático;
- nunca reintroduzir `push` em writer já promovido para schedule final;
- nunca ocultar/desativar aviso nativo de cookies;
- nunca compartilhar arquivo de estado/rotação entre blogs;
- nunca expandir globalmente sem validação blog a blog;
- sempre manter `src/blogger_policy_repo_audit.py` sincronizado com novos SAFE/LIVE/schedules.

---

# 8. RESUMO PARA RETOMADA RÁPIDA

**Estado:** 15/18 concluídos.  
**Último concluído:** Moda e Ofertas.  
**SAFE final Moda:** `41475489511` — PASS, 43/43.  
**LIVE final Moda:** `41476423839` — PASS, 20+12 e público validado.  
**Auditor pós-schedule:** `41477761596` — PASS, 15/15.  
**Schedule Moda:** 10:20 America/Recife.  
**Restam:** Achadinhos de Beleza, Radar Tech BR, Cozinha Sem Complicação.  
**Próximo somente após novo comando do usuário:** Achadinhos de Beleza.
