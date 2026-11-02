# CHECKPOINT ATUAL — BLOGGER AUTOMATION

**Última atualização:** 2026-11-02 07:52 America/Recife  
**Projeto:** Blogger Automation sem ChatGPT Work

## LEIA PRIMEIRO

Antes de qualquer operação Blogger neste projeto, leia nesta ordem:

1. `CHECKPOINT_ATUAL.md`
2. `blogger_multi_store/data/NETWORK_STORE_INVENTORY_2026-11-01.json`
3. `blogger_multi_store/config/network_store_rollout_2026-11-01.json`
4. `CHECKPOINT_UPDATE_2026-11-01_POLICY_EDITORIAL_COOKIES.md`
5. `BACKUP_MANIFEST_BLOGGER_AUTOMATION_2026-11-02_R3.json`
6. `CHECKPOINT_UPDATE_2026-10-30_LAB_CANONICAL_V20.md`
7. `CHECKPOINT_BLOGGER_AUTOMATION_MASTER_2026-10-30.md`
8. `CHECKPOINT_BLOGGER_AUTOMATION_MASTER_2026-10-30.json`
9. `infrastructure/README.md`

Este arquivo prevalece quando houver diferença de estado operacional. Os checkpoints anteriores permanecem como histórico/base de recuperação.

> O backup R3 de 2026-11-02 foi criado **antes** da conclusão do Conecta Achados. Portanto, para o estado posterior ao R3, este checkpoint + inventário + rollout são a fonte operacional mais recente.

---

# 1. ESTADO OPERACIONAL ATUAL VALIDADO

- Blogger Local Runner: **v0.8**.
- Conteúdo Blogger: `Blogger_Bridge_V2`.
- Rede conectada: **18 blogs Blogger**.
- TEMA MODELO V20 permanece como base canônica.
- **18/18** blogs possuem Page LIVE `/p/loja.html`.
- **18/18** blogs possuem Store Post LIVE `Loja`.
- Não recriar Page/Post Loja durante a expansão; usar IDs existentes.

## Lojas modernas protegidas

O Blogger Policy Guard está integrado em **9 pipelines modernos** com:

- SAFE;
- Policy Guard pré-LIVE;
- contrato **20 produtos + 12 hero**;
- DRY-RUN antes da escrita;
- validação pública;
- identidade por blog;
- fail-closed;
- persistência somente depois do PASS público;
- histórico independente por blog;
- writer automático único por blog.

Lojas modernas:

1. Eletroportáteis na Cozinha
2. Cabelos em Foco
3. Ventiladores em Foco
4. Air Fryers em Foco
5. Limpeza Inteligente
6. Liquidificadores em Foco
7. Vitrine Prática
8. Achados para Casa
9. **Conecta Achados**

Estado do inventário:

- `modern_blogger_auto_policy_guard: 9`
- `modern_blogger_auto_20x12_needs_policy_guard_upgrade: 0`
- `store_scaffold_needs_auto_rotation: 9`
- `duplicate_writer_risks: 0`

Rollout global continua:

- `enabled=false`
- `mode=PREPARED_NOT_DEPLOYED`

Nunca habilitar expansão em lote. Trabalhar **um blog por vez**.

---

# 2. ARQUITETURA CANÔNICA DAS LOJAS MODERNAS

```text
Shopee API
→ Policy Guard
→ filtro semântico específico do blog
→ deduplicação / rotação
→ SAFE
→ Policy Guard pré-LIVE
→ DRY-RUN contra o alvo existente
→ LIVE Store Post
→ hero 12
→ identidade/layout
→ validação pública 20 + 12
→ Policy Guard no HTML público
→ persistência de estado
→ schedule
```

Contrato obrigatório:

- 20 produtos;
- 12 mini-cards no hero;
- Page Loja existente preservada;
- Store Post existente preservado;
- links afiliados com `rel="nofollow sponsored noopener"`;
- disclosure de afiliado;
- preço/estoque/frete confirmados no destino;
- nenhum pagamento processado pelo blog;
- persistência somente depois de PASS público;
- histórico/config independente por blog;
- nunca forçar item semanticamente inválido para completar 20 cards.

Regra de rotação:

1. preferir produto novo na janela;
2. se não houver, permitir produto antigo fora da última rodada;
3. somente sem alternativa válida, permitir carry-forward da última publicação;
4. todos os gates semânticos permanecem obrigatórios.

---

# 3. POLICY GUARD / AUDITOR PERMANENTE

Arquivos centrais:

- `POLICY_BASELINE_BLOGGER_GOOGLE_2026.md`
- `config/blogger_policy_guard.json`
- `src/blogger_policy_guard.py`
- `src/blogger_policy_guard_self_test.py`
- `src/blogger_policy_repo_audit.py`
- `.github/workflows/blogger_policy_repo_audit.yml`

O auditor cobre também `blogger_stores/src/**`, SAFE/LIVE do Achados e SAFE/LIVE do Conecta.

Última validação após habilitar schedule do Conecta:

- commit `15ccd4f6e1c508675423948f543a71e4f7f472d7`
- run `41432136126` — **SUCCESS**
- job `125233038467`
- `blogger_policy_guard_self_test: 13/13 OK`
- `BLOGGER_POLICY_REPO_AUDIT_PASS`
- `SAFE/LIVE 9/9 protegidos; writers legados manual-only; sem ocultação/desativação detectada do aviso nativo de cookies.`

---

# 4. VITRINE PRÁTICA — CONCLUÍDA COMO 7ª LOJA MODERNA

Alvo:

- Blog ID `9144338307944682868`
- Page LOJA ID `8344701886444887322`
- Store Post ID `115613719594316807`

Provas principais:

- SAFE `41364558522` — SUCCESS
- auditor `41367352735` — SUCCESS
- LIVE `41367361852` — SUCCESS
- 20 produtos + 12 hero
- identidade pública correta
- domínio legado de Liquidificadores removido
- persistência pós-PASS commit `0c54a7f0b701515288a944244753dbf4b58c19ae`
- artifact LIVE ID `13107641975`
- SHA-256 `31c48d272c4e8befdb470e110f5c6d4364b37143b2e303e61893d68ab1451745`

Não reabrir esse diagnóstico sem sinal concreto de regressão.

---

# 5. ACHADOS PARA CASA — CONCLUÍDO COMO 8ª LOJA MODERNA

Alvo:

- Blog ID `1426630233929943394`
- Page LOJA ID `3841238517239710135`
- Store Post ID `854861801599328533`
- SAFE `.github/workflows/achados_casa_store_safe.yml`
- LIVE `.github/workflows/achados_casa_store_autonomous.yml`
- histórico independente `blogger_stores/data/achados_casa_rotation.json`

Provas finais:

- SAFE `41370322415` — SUCCESS
- job `125039197072`
- Policy Guard 13/13
- semântica 10/10
- 20 produtos / 20 intenções / 20 links
- LIVE `41370529825` — SUCCESS
- job `125039829532`
- Policy Guard pré-LIVE PASS
- Store 20 + hero 12
- identidade pública correta
- persistência somente pós-PASS
- artifact LIVE ID `13108559699`
- SHA-256 `9de04eb388ca543779ade9a5fabc8653fa2b67ad43ccdba63bb3365eaeafd128`
- schedule `07:20 America/Recife`
- auditor pós-schedule `41370840393` — SUCCESS 8/8

Lição permanente desta implantação: um Action verde não basta quando houver dúvida semântica. A leitura independente detectou falsos positivos em Clima & Bem-estar e levou à especialização final:

1. ventilador de teto
2. mini umidificador USB
3. climatizador
4. ventilador de mesa

Não reabrir sem regressão concreta.

---

# 6. CONECTA ACHADOS — CONCLUÍDO COMO 9ª LOJA MODERNA

## 6.1 Alvo e arquivos

- Blog ID `1719259388907013414`
- Page LOJA ID `2386698852540729057`
- Store Post ID `259394788951394758`
- Page `https://conectaachados.blogspot.com/p/loja.html`
- Post `https://conectaachados.blogspot.com/2026/11/loja.html`
- SAFE `.github/workflows/conecta_achados_store_safe.yml`
- LIVE `.github/workflows/conecta_achados_store_autonomous.yml`
- motor independente `blogger_stores/src/conecta_achados_store.py`
- config `config/shopee_conecta_achados.json`
- regras `config/shopee_conecta_achados_intent_rules.json`
- histórico independente `blogger_stores/data/conecta_achados_rotation.json`
- seleção `blogger_stores/data/conecta_achados_selection.json`

Categorias aprovadas:

1. Casa & Organização
2. Cozinha & Utilidades
3. Tecnologia & Acessórios
4. Beleza & Cuidados
5. Dia a Dia & Praticidade

Cada categoria possui 4 intenções: total 20.

## 6.2 SAFE e endurecimento semântico

Primeiro SAFE:

- run `41429777047`
- job `125225155175`
- **FAILED corretamente antes de qualquer escrita**
- regressão detectou acessórios escapando: capa de fone e tampa de garrafa térmica.

Segundo SAFE:

- run `41429916904`
- job `125225624811`
- SUCCESS técnico
- artifact `conecta-achados-store-safe-2`
- artifact ID `13134430186`
- SHA-256 `7bf5c8b83ab6ac78d2f692708623843e337a0f8a607cee8e10ababc926d24f5a`

Esse SUCCESS **não foi aceito como conclusão**. A inspeção manual do artifact encontrou:

- intenção `carregador usb c` selecionando cabo;
- intenção `fone bluetooth` selecionando item Lightning ambíguo;
- intenção `lanterna recarregavel` selecionando rádio/caixa de som com lanterna secundária.

As regras foram endurecidas, sem afrouxar o contrato:

- fone Bluetooth bloqueia Lightning/com fio/P2 e acessórios;
- carregador USB-C bloqueia qualquer cabo e exige fonte/carregador;
- lanterna recarregável bloqueia rádio/caixa de som/Bluetooth e acessórios.

SAFE final v3:

- run `41430553714` — **SUCCESS**
- job `125227806104`
- head `6b48bb2e4f3b29dfa8afc446a0905955d455814d`
- `blogger_policy_guard_self_test: 13/13 OK`
- `CONECTA_SEMANTIC_REGRESSION_PASS: 16/16`
- ranking 180
- 20 produtos
- 20 intenções
- 20/20 links afiliados resolvidos
- fallback=0
- carry-forward=0
- `BLOGGER_POLICY_GUARD_SAFE_PASS`
- `CONECTA_SAFE_READ_ONLY_PASS`

Artifact final SAFE:

- `conecta-achados-store-safe-6`
- artifact ID `13133308250`
- SHA-256 `dd2519c93c3514fa25f26358805faa079df6a2c95e960c063f5aac12bd63e7ca`

A inspeção manual do artifact final confirmou produtos coerentes com as 20 intenções.

## 6.3 Auditor pré-LIVE

Após instalar SAFE + LIVE, o auditor foi promovido para 9/9:

- commit `6d48acac7d70d73dcec9f8f9984034fdef62baee`
- run `41430916398` — SUCCESS
- job `125228969403`
- Policy Guard 13/13
- `BLOGGER_POLICY_REPO_AUDIT_PASS`
- `SAFE/LIVE 9/9 protegidos`

## 6.4 Primeiro LIVE e prova do fail-closed

Primeiro LIVE controlado:

- run `41430973587`
- job `125229161822`

A execução passou:

- SAFE fresco
- Policy Guard pré-LIVE
- identidade
- DRY-RUN Store/hero
- publicação Store 20
- hero 12

Mas o gate público recebeu HTTP **429** em todas as tentativas.

Resultado correto:

- run terminou FAIL;
- **persistência foi pulada**;
- Blogger tinha conteúdo novo, mas o histórico não foi gravado sem PASS público.

Artifact:

- `conecta-achados-store-live-1`
- artifact ID `13134067910`
- SHA-256 `ec7c3b4e0f746a2eaa6e7ca2a5e01ae78263e6befd73fcb3fc17d185ff57108e`

A leitura autenticada do Blogger mostrou que o HTML estava correto, mas ela **não foi usada como substituto do PASS público**.

## 6.5 Gate público resiliente a 429

O workflow foi corrigido sem enfraquecer a validação:

- mantém exigência de HTTP público 200;
- browser User-Agent;
- `Accept-Language`;
- `Cache-Control: no-cache`;
- até 12 tentativas;
- 429 espera e tenta novamente;
- ainda exige 20 Store + 12 hero + identidade + Policy Guard público;
- persistência continua depois do PASS.

Commit da correção:

- `0191879806183f65cf4e9def2c51a7265cd5521f`

## 6.6 LIVE final comprovado

Kickoff final head:

- `d6b9cbb111e7cc994485da68f92d1ddbd1744867`

Run/job:

- run `41431642751` — **SUCCESS**
- job `125231384106`

Marcadores comprovados:

- Policy Guard self-test 13/13
- `CONECTA_SEMANTIC_REGRESSION_PASS: 16/16`
- SAFE fresco: 20 produtos / 20 intenções / 20 links
- `BLOGGER_POLICY_GUARD_PRELIVE_PASS: 20/20 produtos permitidos`
- `CONECTA_SEMANTIC_PRELIVE_PASS`
- `CONECTA_IDENTITY_PASS`
- `CONECTA_STORE_DRY_RUN_PASS`
- `CONECTA_HERO_DRY_RUN_PASS`
- `CONECTA_POST_PUBLISH_PASS: 20 produtos`
- `CONECTA_HERO_PASS: 12 mini-cards únicos sincronizados`

Gate público:

- tentativa 1: HTTP 429
- tentativa 2: HTTP 429
- tentativa 3: **HTTP 200**
- `PUBLIC_COUNTS_ATTEMPT_3: store=20 hero=12`
- `BLOGGER_POLICY_GUARD_PUBLIC_PASS: 20 products + 12 hero`
- `CONECTA_IDENTITY_PUBLIC_PASS`

Somente depois disso:

- `CONECTA_ROTATION_PERSIST_PASS`
- commit automático `7fae90ff6b235171f37d2b77475ffcda254a3527` — `Atualizar rotação automática da Loja Conecta Achados`

Artifact LIVE final:

- `conecta-achados-store-live-2`
- artifact ID `13135215258`
- SHA-256 `c16a16107cb7b2b7a6219d3e652024999d39093e112aab9fc5624b51ebc8d352`

## 6.7 Leitura independente final

`Blogger_Bridge_V2.get_post` confirmou diretamente no Store Post LIVE:

- status LIVE;
- Page Loja correta `https://conectaachados.blogspot.com/p/loja.html`;
- layout amplo preservado;
- sidebar/PopularPosts ocultos apenas na Loja;
- 5 categorias corretas;
- 20 Store cards;
- 12 hero;
- disclosure afiliado;
- links com `rel="nofollow sponsored noopener"`;
- nenhuma referência executável à Vitrine Prática, Achados para Casa ou Liquidificadores;
- fone = sem fio Bluetooth 5.3;
- carregador USB-C = tomada/fonte USB + USB-C, não cabo;
- lanterna = lanterna tática recarregável USB, não rádio.

## 6.8 Schedule final

O schedule foi habilitado somente depois de SAFE + LIVE + PASS público + leitura independente limpa.

- workflow `.github/workflows/conecta_achados_store_autonomous.yml`
- `cron: "35 7 * * *"`
- `timezone: "America/Recife"`
- commit `15ccd4f6e1c508675423948f543a71e4f7f472d7`

Auditor pós-schedule:

- run `41432136126` — SUCCESS
- job `125233038467`
- `BLOGGER_POLICY_REPO_AUDIT_PASS`
- `SAFE/LIVE 9/9 protegidos`

Conecta Achados está **CONCLUÍDO** como `modern_policy_guard_20x12`.

---

# 7. OUTRAS CAMADAS DE PROTEÇÃO PRESERVADAS

## Gate anti-repetição editorial

- `config/editorial_cross_blog_guard.json`
- `src/editorial_cross_blog_guard.py`
- `src/editorial_cross_blog_guard_self_test.py`
- `.github/workflows/editorial_cross_blog_guard_safe.yml`
- escopo: Casa & Decoração, Oficina & Garagem, Radar Tech BR
- SAFE validado `41358905465`

## Auditoria europeia de cookies Blogger

- `src/blogger_eu_cookie_audit.py`
- `.github/workflows/blogger_eu_cookie_audit_safe.yml`
- **18/18 PASS**
- 0 FAIL
- run `41359632797` — SUCCESS

Regra permanente: nunca ocultar/desativar o aviso nativo de cookies do Blogger por tema/CSS.

## Writers duplicados consolidados

Limpeza Inteligente:

- canônico `.github/workflows/limpeza_inteligente_store_autonomous.yml`
- legado `.github/workflows/limpeza_store_autonomous.yml` recovery-only
- concurrency `limpeza-inteligente-store-live`

Ventiladores em Foco:

- canônico `.github/workflows/ventiladores_store_autonomous.yml`
- legado `.github/workflows/ventiladores_em_foco_store_autonomous.yml` recovery-only
- concurrency `ventiladores-store-live`

Não reintroduzir `schedule` nem `push` nos writers legados.

---

# 8. FILA RESTANTE — 9 BLOGS

Ordem atual:

1. **Estilo no Dia a Dia**
2. Casa em Ordem
3. Escolha Certa Online
4. Achados que Valem
5. Guia de Achados & Ofertas
6. Moda e Ofertas
7. Achadinhos de Beleza
8. Radar Tech BR Blogger
9. Cozinha Sem Complicação

Cada alvo exige perfil semântico próprio antes do LIVE.

---

# 9. PRÓXIMO BLOCO PERMITIDO — ESTILO NO DIA A DIA, NÃO INICIADO

- Blog ID `4830103887652146866`
- Page LOJA ID `4843501559117111153`
- Store Post ID `3362829797679236320`
- Page `https://estilo-no-dia-a-dia-0071220800-2.blogspot.com/p/loja.html`
- Post `https://estilo-no-dia-a-dia-0071220800-2.blogspot.com/2026/11/loja.html`
- estado atual `store_scaffold_needs_auto_rotation`
- perfil semântico ainda precisa ser definido e validado

**Não iniciar Estilo no Dia a Dia automaticamente. Aguardar novo `continue` do usuário.**

---

# 10. REGRAS ESSENCIAIS PARA FUTURAS EXECUÇÕES

- Não reiniciar diagnóstico de Vitrine, Achados ou Conecta sem evidência concreta de regressão.
- Não pedir operação manual quando ferramentas conectadas já executam a ação.
- Confirmar Blog ID e Store Post ID antes de escrever.
- Não recriar Page/Post Loja.
- Preservar identidade do blog.
- Preservar Store 20 + hero 12.
- Preservar fail-closed.
- Preservar históricos independentes.
- Policy Guard deve existir em SAFE, pré-LIVE e HTML público.
- Persistir somente depois do PASS público.
- HTTP 429 no gate público deve ser tratado com retry, nunca ignorado.
- Leitura autenticada do Blogger ajuda no diagnóstico, mas não substitui o gate público exigido pelo workflow.
- Não forçar produto semanticamente errado para preencher categoria.
- Um Action verde não substitui inspeção de artifact/HTML quando houver dúvida semântica.
- Preservar gate editorial anti-repetição.
- Nunca ocultar/desativar cookie notice nativo.
- Não armazenar secrets no repositório.
- Expandir **um blog por vez**.

---

# 11. BACKUP / RECUPERAÇÃO

Último backup completo criado antes deste bloco:

- R3 `blogger-automation1-backup-2026-11-02-r3`
- run `41428226665` — SUCCESS
- artifact ID `13132752660`
- SHA-256 `65a76eecb33d126e00ffe80e657adbdf488ad93766fda1dd971beece2208b863`
- commit capturado `0e41104ffcadc37aedfd644875a1d42ebde8ee4f`

Como o R3 é anterior à conclusão do Conecta, um próximo backup deverá incluir os commits deste bloco.

Se este arquivo for encontrado numa conversa futura:

- Vitrine Prática = 7ª loja moderna concluída;
- Achados para Casa = 8ª loja moderna concluída;
- Conecta Achados = 9ª loja moderna concluída;
- auditor permanente = **9/9**;
- restam **9 blogs**;
- próximo bloco permitido = **Estilo no Dia a Dia**, somente após comando explícito do usuário.
