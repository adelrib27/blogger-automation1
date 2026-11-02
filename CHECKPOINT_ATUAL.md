# CHECKPOINT ATUAL — BLOGGER AUTOMATION

**Estado canônico:** 2026-11-02 — após conclusão de Radar Tech BR Blogger  
**Projeto:** Blogger Automation sem ChatGPT Work  
**Progresso:** **17/18 lojas Blogger modernas concluídas**

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
- **17/18** possuem automação moderna protegida pelo Blogger Policy Guard.
- **1/18** permanece com scaffold e ainda precisa de automação Blogger 20x12.
- Não recriar Page/Post Loja; preservar sempre os IDs existentes.
- TEMA MODELO V20 permanece como base canônica.
- Blogger Local Runner v0.8 e Blogger_Bridge_V2 continuam válidos.
- Rollout global permanece desabilitado. Trabalhar **um blog por vez**.

## Lojas modernas concluídas — 17/18

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
15. Moda e Ofertas
16. Achadinhos de Beleza
17. **Radar Tech BR Blogger**

Inventário atual:

- `modern_blogger_auto_policy_guard: 17`
- `modern_blogger_auto_20x12_needs_policy_guard_upgrade: 0`
- `store_scaffold_needs_auto_rotation: 1`
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
- serialização HTML pública pode transformar caracteres em entidades; gates textuais devem normalizar entidades sem relaxar os demais requisitos;
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

O auditor cobre **17 SAFE/LIVE modernos**, writers legados, proteção de cookies e schedules finais.

Schedules explicitamente protegidos neste estágio:

- Casa em Ordem — 08:05
- Escolha Certa Online — 08:20
- Achados que Valem — 09:50
- Guia de Achados & Ofertas — 10:05
- Moda e Ofertas — 10:20
- Achadinhos de Beleza — 10:35
- **Radar Tech BR Blogger — 10:50**

Prova do fechamento mais recente:

- commit do writer com schedule Radar: `9359e8b816cd0061bbc09e88e235d3a0ee1b14ee`
- commit do auditor final: `dc320f7b3cc34f11b32e3ff7116209ac7896e53f`
- auditor final run `41533505042` — **SUCCESS**
- `BLOGGER_POLICY_REPO_AUDIT_PASS`
- `SAFE/LIVE 17/17 protegidos`

O writer Blogger do Radar não possui gatilho `push`; fica em `workflow_dispatch` + schedule diário `50 10 * * *`, timezone `America/Recife`.

Observação de segurança: o auditor run `41533265581` falhou logo após a primeira ativação do schedule porque ainda aplicava deliberadamente a regra anterior de LIVE controlado sem schedule. O auditor foi então promovido para a política final 10:50 e o run `41533505042` passou. Não houve writer duplicado nem relaxamento de gates.

---

# 4. MODA E OFERTAS — 15ª LOJA MODERNA — CONCLUÍDA

## Alvo preservado

- Blog ID `2858597309582499028`
- Blog `https://moda-ofertas.blogspot.com/`
- Page LOJA ID `1341310014099438949`
- Page `https://moda-ofertas.blogspot.com/p/loja.html`
- Store Post ID `4871366557503134389`
- Store Post `https://moda-ofertas.blogspot.com/2026/10/loja.html`

Evidência final:

- SAFE `41475489511` — **SUCCESS**, regressão 43/43, Policy Guard 20/20;
- LIVE `41476423839` — **SUCCESS**, Store 20/20 + hero 12/12 + HTTP público 200 + Policy Guard público;
- rotação persistida apenas após PASS público;
- auditor `41477761596` — **SUCCESS**;
- schedule final **10:20 America/Recife**;
- leitura independente Blogger_Bridge_V2 confirmou identidade, CTAs e falsos positivos conhecidos ausentes.

**Moda e Ofertas não deve ser reaberto sem sinal concreto de regressão.**

---

# 5. ACHADINHOS DE BELEZA — 16ª LOJA MODERNA — CONCLUÍDA

## Alvo preservado

- Blog ID `2562496977098748229`
- Blog `https://canal-attitude.blogspot.com/`
- Page LOJA ID `455853998448723529`
- Page `https://canal-attitude.blogspot.com/p/loja.html`
- Store Post ID `7650631557624373238`
- Store Post `https://canal-attitude.blogspot.com/2026/10/loja.html`

Nenhuma Page ou Store Post foi recriada.

Evidência final:

- SAFE `41526176212` — **SUCCESS**, regressão 40/40, Policy Guard 20/20;
- LIVE `41527164226` — **SUCCESS**, Store 20/20 + hero 12/12;
- validação pública fez retry 429→200 sem relaxar gates;
- Policy Guard público PASS;
- rotação persistida somente depois do PASS público;
- commit de rotação `4f9fa4c77f572dc1b6c729586b0543f96a1d5e33`;
- Blogger_Bridge_V2 confirmou Post ID original LIVE, identidade e categorias;
- schedule final **10:35 America/Recife**;
- auditor final `41528127151` — **SUCCESS**, 16/16 protegidos.

**Achadinhos de Beleza não deve ser reaberto sem sinal concreto de regressão.**

---

# 6. RADAR TECH BR BLOGGER — 17ª LOJA MODERNA — CONCLUÍDA

## Alvo preservado

- Blog ID `7487888217273188851`
- Blog `https://portalradartechbr.blogspot.com/`
- Page LOJA ID `6887385207246667244`
- Page `https://portalradartechbr.blogspot.com/p/loja.html`
- Store Post ID `906894044295273477`
- Store Post `https://portalradartechbr.blogspot.com/2026/10/loja.html`

Nenhuma Page ou Store Post foi recriada.

## Separação obrigatória Blogger × WordPress

O workflow existente `.github/workflows/radar_store_autonomous.yml` continua sendo da loja WordPress `radartechbr.com.br` e **não** é o writer Blogger.

O Blogger recebeu arquitetura própria e isolada:

- SAFE `.github/workflows/radar_tech_blogger_store_safe.yml`
- LIVE `.github/workflows/radar_tech_blogger_store_autonomous.yml`
- motor `blogger_stores/src/radar_tech_blogger_store.py`
- config `config/shopee_radar_tech_blogger.json`
- regras `config/shopee_radar_tech_blogger_intent_rules.json`
- seleção `blogger_stores/data/radar_tech_blogger_selection.json`
- rotação `blogger_stores/data/radar_tech_blogger_rotation.json`

Não compartilhar estado, rotação ou writer com a automação WordPress.

## Categorias finais

1. Casa & Organização
2. Cozinha & Utilidades
3. Tecnologia & Acessórios
4. Beleza & Cuidados
5. Dia a Dia & Praticidade

Cada categoria possui quatro intenções; total de 20 produtos.

## SAFE e endurecimento semântico

A primeira seleção SAFE passou estruturalmente, porém a revisão humana detectou três candidatos inadequados:

- processador/picador/moedor 3L contendo “mixer” no título;
- suporte de vassoura/rodo/mop passando como organizador de cozinha;
- tomada de parede USB/USB-C passando como carregador USB-C convencional.

Foram adicionados bloqueios permanentes e regressões reais. A rodada seguinte falhou corretamente no novo teste por uma variante de **capa térmica para chapinha**, comprovando o fail-closed. O gate foi ampliado para a família semântica e repetido.

SAFE final:

- run `41531081733` — **SUCCESS**
- regressão semântica **12/12**
- seleção **20/20**
- cinco categorias × quatro intenções
- Policy Guard **20/20**
- Blogger permaneceu read-only durante SAFE
- seleção final revisada título a título.

## LIVE e gate público

Primeiro LIVE controlado:

- run `41531852901` — terminou **FAIL** somente no gate público textual;
- SAFE fresco, Policy Guard, dry-runs, Store 20/20, hero 12/12 e identidade autenticada já haviam passado;
- o HTML público do Blogger serializou o travessão `—` como `&#8212;`;
- a verificação textual exata rejeitou a página;
- **a rotação não foi persistida**, como exigido pelo fail-closed.

A correção normalizou entidades HTML antes dos checks textuais, preservando integralmente:

- HTTP 200;
- contagem 20 Store + 12 hero;
- Policy Guard público;
- cinco categorias e âncoras;
- URL/identidade Radar;
- bloqueio de referências de outros blogs;
- bloqueio dos falsos positivos conhecidos.

LIVE final:

- run `41532748296` — **SUCCESS**
- job `125576842674`
- regressão 12/12
- SAFE fresco 20/20
- Policy Guard pré-LIVE 20/20
- identity/store/hero dry-runs PASS
- Store Post original **20/20**
- hero **12/12**
- identidade autenticada PASS
- primeira tentativa pública: **HTTP 200**
- contagem pública: **20 Store + 12 hero**
- `BLOGGER_POLICY_GUARD_PUBLIC_PASS`
- `RADAR_TECH_BLOGGER_IDENTITY_PUBLIC_PASS`
- rotação persistida somente depois do PASS público
- commit de rotação `d30af368cb7c4223696903f72002e4599c202aac`.

Leitura independente direta via Blogger_Bridge_V2 confirmou no Post ID original:

- status LIVE;
- identidade `Radar Tech BR — tecnologia e achados práticos para a rotina`;
- cinco categorias corretas;
- 20 produtos e hero 12 sincronizados;
- seleção corrigida, incluindo mixer real, organizador de cozinha coerente e carregador USB-C PD;
- falsos positivos conhecidos ausentes.

## Schedule final

- horário: **10:50 America/Recife**
- cron: `50 10 * * *`
- `workflow_dispatch` mantido para operação manual controlada;
- gatilho `push` removido;
- auditor central protege horário, identidade, normalização de entidades HTML e falsos positivos;
- auditor final `41533505042` — **SUCCESS**, 17/17 protegidos.

**Radar Tech BR Blogger não deve ser reaberto sem sinal concreto de regressão.**

---

# 7. FILA RESTANTE — EXATAMENTE 1 BLOG

1. **Cozinha Sem Complicação**
   - Blog ID `3552757910439359679`
   - Page LOJA ID `6913756651435112886`
   - Store Post ID `7888042807715084117`
   - estado: `store_scaffold_needs_auto_rotation`

---

# 8. PRÓXIMO BLOCO PERMITIDO

O último blog pendente é **Cozinha Sem Complicação**, mas **não iniciar automaticamente neste mesmo bloco**.

Somente quando o usuário disser novamente **“continue”**, retomar por Cozinha Sem Complicação e repetir a disciplina canônica:

1. confirmar IDs e estado real do scaffold existente;
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
12. atualizar inventário e checkpoint para 18/18.

---

# 9. REGRAS DE SEGURANÇA QUE NÃO PODEM REGREDIR

- nunca recriar Page/Post Loja quando os IDs existentes estão válidos;
- nunca aceitar Action verde como única prova de qualidade sem inspeção semântica quando houver dúvida;
- nunca persistir rotação antes do PASS público;
- nunca ignorar HTTP 429; usar retry até 200 ou falhar;
- normalizar entidades HTML apenas para comparação textual, nunca para relaxar Policy Guard ou contagens;
- nunca reintroduzir writer duplicado automático;
- nunca reintroduzir `push` em writer já promovido para schedule final;
- nunca ocultar/desativar aviso nativo de cookies;
- nunca compartilhar arquivo de estado/rotação entre blogs;
- nunca confundir automação WordPress Radar com writer Blogger;
- nunca expandir globalmente sem validação blog a blog;
- sempre manter `src/blogger_policy_repo_audit.py` sincronizado com novos SAFE/LIVE/schedules.

---

# 10. RESUMO PARA RETOMADA RÁPIDA

**Estado:** 17/18 concluídos.  
**Último concluído:** Radar Tech BR Blogger.  
**SAFE final Radar:** `41531081733` — PASS, 12/12, Policy Guard 20/20.  
**Primeiro LIVE controlado:** `41531852901` — fail-closed por entidade HTML; rotação não persistida.  
**LIVE final Radar:** `41532748296` — PASS, HTTP 200, 20+12 e público validado.  
**Commit de rotação:** `d30af368cb7c4223696903f72002e4599c202aac`.  
**Auditor pós-schedule:** `41533505042` — PASS, 17/17.  
**Schedule Radar Blogger:** 10:50 America/Recife.  
**Resta:** somente Cozinha Sem Complicação.  
**Próximo somente após novo comando do usuário:** Cozinha Sem Complicação.
