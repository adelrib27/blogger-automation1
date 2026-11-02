# CHECKPOINT ATUAL — BLOGGER AUTOMATION

**Última atualização:** 2026-11-02 09:49 America/Recife  
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

Este arquivo prevalece quando houver diferença de estado operacional. Os checkpoints anteriores permanecem válidos como histórico/base de recuperação.

> O backup R3 de 2026-11-02 foi criado antes das conclusões de Conecta Achados, Estilo no Dia a Dia, Casa em Ordem e Escolha Certa Online. Para o estado posterior ao R3, este checkpoint + inventário + rollout são a fonte operacional mais recente.

---

# 1. ESTADO OPERACIONAL ATUAL VALIDADO

- Blogger Local Runner: **v0.8**.
- Conteúdo Blogger: `Blogger_Bridge_V2`.
- Rede conectada: **18 blogs Blogger**.
- TEMA MODELO V20 permanece como base canônica.
- **18/18** blogs possuem Page LIVE `/p/loja.html`.
- **18/18** blogs possuem Store Post LIVE `Loja`.
- Não recriar Page/Post Loja durante a expansão; usar os IDs existentes.

## Lojas modernas protegidas

O Blogger Policy Guard está integrado em **12 pipelines modernos** com:

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
9. Conecta Achados
10. Estilo no Dia a Dia
11. Casa em Ordem
12. **Escolha Certa Online**

Estado do inventário:

- `modern_blogger_auto_policy_guard: 12`
- `modern_blogger_auto_20x12_needs_policy_guard_upgrade: 0`
- `store_scaffold_needs_auto_rotation: 6`
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
- nunca compartilhar `store_last_selection.json` genérico entre blogs;
- nunca forçar item semanticamente inválido para completar 20 cards.

Regra de rotação:

1. preferir produto novo na janela;
2. se não houver, permitir produto antigo fora da última rodada;
3. somente sem alternativa válida, permitir carry-forward da última publicação;
4. todos os gates semânticos permanecem obrigatórios.

Regra de validação pública:

- HTTP público 200 continua obrigatório;
- HTTP 429 deve ser tratado com retry e espera, nunca ignorado;
- leitura autenticada do Blogger ajuda no diagnóstico, mas não substitui o gate público exigido pelo workflow;
- persistência somente ocorre depois de `20 + 12 + Policy Guard público + identidade` passarem.

---

# 3. POLICY GUARD / AUDITOR PERMANENTE

Arquivos centrais:

- `POLICY_BASELINE_BLOGGER_GOOGLE_2026.md`
- `config/blogger_policy_guard.json`
- `src/blogger_policy_guard.py`
- `src/blogger_policy_guard_self_test.py`
- `src/blogger_policy_repo_audit.py`
- `.github/workflows/blogger_policy_repo_audit.yml`

O auditor cobre os **12 SAFE/LIVE modernos**, `blogger_stores/src/**`, writers legados duplicados, proteção do aviso nativo de cookies e os schedules/navegações finais de Casa em Ordem e Escolha Certa Online.

Última validação, após habilitar o schedule do Escolha Certa Online:

- commit do schedule `92a6497a30aa5b365fefddf8ad31b1ca53781ab8`
- commit do reforço permanente do auditor `2d3c536dc499a7b193a9eb20fec97dda2c1263b8`
- run `41447386251` — **SUCCESS**
- job `125283757493`
- `blogger_policy_guard_self_test: 13/13 OK`
- `BLOGGER_POLICY_REPO_AUDIT_PASS`
- `SAFE/LIVE 12/12 protegidos; Casa em Ordem schedule 08:05 e Escolha Certa Online schedule 08:20 protegidos; writers legados manual-only; sem ocultação/desativação detectada do aviso nativo de cookies.`

---

# 4. VITRINE PRÁTICA — 7ª LOJA MODERNA

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

# 5. ACHADOS PARA CASA — 8ª LOJA MODERNA

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
- 20 produtos / 20 intenções / 20 links
- LIVE `41370529825` — SUCCESS
- Store 20 + hero 12
- identidade pública correta
- persistência somente pós-PASS
- artifact LIVE ID `13108559699`
- SHA-256 `9de04eb388ca543779ade9a5fabc8653fa2b67ad43ccdba63bb3365eaeafd128`
- schedule `07:20 America/Recife`
- auditor pós-schedule `41370840393` — SUCCESS 8/8

Lição permanente: um Action verde não basta quando houver dúvida semântica. A leitura independente encontrou falsos positivos em Clima & Bem-estar e levou ao perfil final: ventilador de teto, mini umidificador USB, climatizador e ventilador de mesa.

Não reabrir sem regressão concreta.

---

# 6. CONECTA ACHADOS — 9ª LOJA MODERNA

## Alvo

- Blog ID `1719259388907013414`
- Page LOJA ID `2386698852540729057`
- Store Post ID `259394788951394758`
- Page `https://conectaachados.blogspot.com/p/loja.html`
- Post `https://conectaachados.blogspot.com/2026/11/loja.html`
- SAFE `.github/workflows/conecta_achados_store_safe.yml`
- LIVE `.github/workflows/conecta_achados_store_autonomous.yml`
- motor `blogger_stores/src/conecta_achados_store.py`
- config `config/shopee_conecta_achados.json`
- regras `config/shopee_conecta_achados_intent_rules.json`
- histórico independente `blogger_stores/data/conecta_achados_rotation.json`

Categorias:

1. Casa & Organização
2. Cozinha & Utilidades
3. Tecnologia & Acessórios
4. Beleza & Cuidados
5. Dia a Dia & Praticidade

## Provas principais

- SAFE final `41430553714` — SUCCESS após endurecimento e inspeção manual do artifact
- auditor pré-LIVE `41430916398` — SUCCESS 9/9
- primeiro LIVE `41430973587` comprovou fail-closed: publicação ocorreu, gate público recebeu 429 e persistência foi pulada
- gate público foi reforçado com retries sem substituir HTTP 200 por leitura autenticada
- LIVE final `41431642751` — SUCCESS
- gate público: `429 → 429 → 200`
- `store=20 hero=12`
- Policy Guard público PASS
- identidade pública PASS
- persistência commit `7fae90ff6b235171f37d2b77475ffcda254a3527`
- artifact LIVE ID `13135215258`
- SHA-256 `c16a16107cb7b2b7a6219d3e652024999d39093e112aab9fc5624b51ebc8d352`
- leitura independente do Blogger confirmou fone sem fio, carregador USB-C real e lanterna tática USB
- schedule `07:35 America/Recife`
- auditor pós-schedule `41432136126` — SUCCESS 9/9

Não reabrir sem regressão concreta.

---

# 7. ESTILO NO DIA A DIA — CONCLUÍDO COMO 10ª LOJA MODERNA

## 7.1 Alvo

- Blog ID `4830103887652146866`
- Page LOJA ID `4843501559117111153`
- Store Post ID `3362829797679236320`
- Page `https://estilo-no-dia-a-dia-0071220800-2.blogspot.com/p/loja.html`
- Post `https://estilo-no-dia-a-dia-0071220800-2.blogspot.com/2026/11/loja.html`
- SAFE `.github/workflows/estilo_dia_a_dia_store_safe.yml`
- LIVE `.github/workflows/estilo_dia_a_dia_store_autonomous.yml`
- motor `blogger_stores/src/estilo_dia_a_dia_store.py`
- config `config/shopee_estilo_dia_a_dia.json`
- regras `config/shopee_estilo_dia_a_dia_intent_rules.json`
- histórico independente `blogger_stores/data/estilo_dia_a_dia_rotation.json`
- seleção `blogger_stores/data/estilo_dia_a_dia_selection.json`

A descrição oficial do blog confirmou o nicho de estilo, moda, beleza e acessórios. O scaffold genérico anterior não foi mantido como identidade final.

Categorias finais:

1. Moda Feminina
2. Calçados & Conforto
3. Bolsas & Acessórios
4. Cabelo & Styling
5. Cuidados Pessoais

Cada categoria possui 4 intenções: total 20.

## 7.2 SAFE — três rodadas e inspeção semântica independente

### SAFE 1

- run `41433616186`
- job `125237991848`
- SUCCESS técnico
- artifact ID `13135881271`
- SHA-256 `6a1376ec1f056817e5cdd933f17bca04fe69df85d5a346fe5e9224a293b2fd3d`

Não foi aceito como conclusão porque a inspeção manual encontrou:

- `bolsa feminina` selecionando necessaire;
- `cinto feminino` selecionando short com cinto.

### SAFE 2

- run `41434023538`
- job `125239310362`
- SUCCESS técnico
- artifact ID `13134669360`
- SHA-256 `c3e0c6834c01f28d360844b56ada2dd542b947a6753c3208c99a0a9fbd353f04`

Bolsa foi corrigida, mas `cinto feminino` ainda selecionou roupa com cinto. O SAFE técnico novamente não foi aceito como conclusão.

### SAFE 3 FINAL

Regras foram endurecidas para v3, bloqueando:

- necessaire/porta-maquiagem/estojo no intent de bolsa;
- kits e usos secundários no intent de carteira;
- short, shorts, calça, saia, vestido, macacão e conjunto no intent de cinto;
- acessórios/refis/peças nos intents de cabelo e cuidados;
- infantis/pets/miniaturas/acessórios nos intents de moda/calçados.

Run final:

- run `41434538973` — **SUCCESS**
- job `125240966066`
- artifact `estilo-dia-a-dia-store-safe-3`
- artifact ID `13136077291`
- SHA-256 `8dfa07de49edf795275e07cd5c692bdc5aefc335788e17a8557672a88ad38211`

A inspeção manual confirmou os 20 títulos coerentes. Em especial, o item de cinto final é **Cinto Feminino de Elástico com Fivela Metalizada**, não uma roupa com cinto incluso.

## 7.3 Auditor pré-LIVE

SAFE + LIVE foram instalados antes de qualquer kickoff público. O LIVE ficou sem schedule nesta fase.

Auditor:

- run `41434985540` — **SUCCESS**
- job `125242447480`
- Policy Guard 13/13
- `BLOGGER_POLICY_REPO_AUDIT_PASS`
- `SAFE/LIVE 10/10 protegidos`

Somente depois desse PASS foi criado o kickoff LIVE.

## 7.4 LIVE controlado comprovado

Kickoff commit:

- `093e1907f21f636d0c5d03511a089dabfe0aec59`

Run/job:

- run `41435064769` — **SUCCESS**
- job `125242704344`

Marcadores relevantes:

- Policy Guard self-test 13/13
- `ESTILO_SEMANTIC_REGRESSION_PASS: 20/20`
- ranking Shopee 180
- 20/20 produtos semânticos e links validados
- `ESTILO_SAFE_READY`
- `ESTILO_SELECTION_VALID_PASS: 20/20`
- `BLOGGER_POLICY_GUARD_PRELIVE_PASS: 20/20 produtos permitidos`
- `ESTILO_SEMANTIC_PRELIVE_PASS: 5 categorias x 4 intenções`
- `ESTILO_IDENTITY_DRY_RUN_PASS`
- `ESTILO_STORE_DRY_RUN_PASS`
- `ESTILO_HERO_DRY_RUN_PASS`
- `ESTILO_POST_PUBLISH_PASS: 20 produtos`
- `ESTILO_HERO_PASS: 12 mini-cards únicos`
- `ESTILO_IDENTITY_PASS`

Gate público:

- tentativa 1: HTTP 429
- tentativa 2: **HTTP 200**
- `store=20 hero=12`
- `BLOGGER_POLICY_GUARD_PUBLIC_PASS: 20 products + 12 hero`
- `ESTILO_IDENTITY_PUBLIC_PASS`

Somente após o PASS público ocorreu a persistência:

- commit automático `d5e32b4f7e6487f63cf1316225a2696ef51f6c69`
- mensagem `Atualizar rotação automática da Loja Estilo no Dia a Dia`

Artifact LIVE:

- `estilo-dia-a-dia-store-live-1`
- artifact ID `13136406819`
- SHA-256 `2bb6fd0784d4531242bb4352e0bb4bfc53c0c8abcb0ffb8d2d2b134b081db89d`

## 7.5 Leitura independente do Blogger

`Blogger_Bridge_V2.get_post` confirmou diretamente no Store Post LIVE:

- status LIVE;
- Page Loja correta;
- layout amplo preservado;
- sidebar/PopularPosts ocultos apenas na Loja;
- texto final focado em moda, beleza e acessórios;
- 5 categorias próprias;
- 20 Store cards;
- 12 hero;
- disclosure de afiliado;
- links `rel="nofollow sponsored noopener"`;
- produtos coerentes com o SAFE final.

A identidade pública agora contém:

- `Moda, beleza e acessórios para o dia a dia`
- `Estilo prático para vestir, cuidar e combinar melhor`

## 7.6 Correção pontual da navegação

A leitura independente detectou um detalhe de UX: o botão **Ver moda** do segundo slide apontava para Calçados em vez de Moda Feminina.

Foi executada uma correção exata, sem alterar produtos:

- workflow `.github/workflows/estilo_dia_a_dia_nav_fix.yml`
- kickoff commit `8802c27653c8f6ba1d669b9af9566a1553d111e1`
- run `41435662722` — **SUCCESS**
- job `125244679783`
- marcador `ESTILO_NAV_FIX_PASS: Ver moda -> Moda Feminina; 20+12 preservado`

Depois da correção, esse workflow foi rebaixado para **manual/recovery-only**:

- commit `1f9968973f0e2d710424ab8fc20f3550f884f8d3`
- apenas `workflow_dispatch`
- concurrency compartilhada `estilo-dia-a-dia-store-live`
- sem schedule/push automático.

## 7.7 Schedule final e auditor pós-schedule

O schedule foi habilitado somente depois de:

1. SAFE final limpo;
2. auditor 10/10 pré-LIVE;
3. LIVE 20+12;
4. PASS público;
5. persistência pós-PASS;
6. leitura independente limpa;
7. correção de navegação validada.

Workflow:

- `.github/workflows/estilo_dia_a_dia_store_autonomous.yml`

Agenda:

- `cron: "50 7 * * *"`
- `timezone: "America/Recife"`

Commit:

- `821fb4e6a7ef16348c7432a7094065ba56b418b2`

Auditor pós-schedule:

- run `41435835886` — **SUCCESS**
- job `125245260514`
- `blogger_policy_guard_self_test: 13/13 OK`
- `BLOGGER_POLICY_REPO_AUDIT_PASS`
- `SAFE/LIVE 10/10 protegidos`

Estilo no Dia a Dia está **CONCLUÍDO** como `modern_policy_guard_20x12`.

Não reabrir o diagnóstico sem evidência concreta de regressão.

---

# 8. CASA EM ORDEM — CONCLUÍDO COMO 11ª LOJA MODERNA

Alvo:

- Blog ID `4177382081459143374`
- Page LOJA ID `4031853959690608178`
- Store Post ID `5566188787681469799`
- Page `https://casa-em-ordem-pratica.blogspot.com/p/loja.html`
- Post `https://casa-em-ordem-pratica.blogspot.com/2026/11/loja.html`
- SAFE `.github/workflows/casa_em_ordem_store_safe.yml`
- LIVE `.github/workflows/casa_em_ordem_store_autonomous.yml`
- motor `blogger_stores/src/casa_em_ordem_store.py`
- histórico independente `blogger_stores/data/casa_em_ordem_rotation.json`

Perfil final: Organização & Armazenamento; Quarto & Roupa de Cama; Banheiro & Organização; Lavanderia & Limpeza; Decoração & Conforto — 5 categorias x 4 intenções.

## 8.1 SAFE e revisão semântica

- primeiro SAFE `41438524634` falhou corretamente antes de qualquer escrita: o bloqueio `pet` casava dentro de `tapete`;
- SAFE técnico `41438830523` ficou verde, mas não foi aceito: inspeção manual encontrou cesto em `caixa organizadora` e porta-papel em `prateleira banheiro`;
- perfil v3 endurecido;
- SAFE final `41439295948` — **SUCCESS**;
- 40/40 regressões semânticas;
- 20 produtos / 20 intenções / links 20/20;
- fallback 0 / carry 0;
- artifact SAFE final `13136984336`;
- SHA-256 `6d5a9c16eee3e3184a22ed399e3d65cbd69ae46d2a0daf2016d2fe9e377e06eb`;
- revisão manual final 20/20 coerente.

## 8.2 Auditor pré-LIVE

- run `41439709960` — **SUCCESS**;
- job `125258208273`;
- Policy Guard 13/13;
- `BLOGGER_POLICY_REPO_AUDIT_PASS`;
- `SAFE/LIVE 11/11 protegidos`.

## 8.3 LIVE final

- run `41439797912` — **SUCCESS**;
- job `125258499502`;
- Store 20 + hero 12;
- gate público HTTP `429 → 200`;
- `BLOGGER_POLICY_GUARD_PUBLIC_PASS: 20 products + 12 hero`;
- persistência somente depois do PASS público;
- commit automático `909382b375afc9dae578d7965873d9ece3736f9c`;
- artifact LIVE ID `13138591112`;
- SHA-256 `782b0bb47371bdc67d53a7e14e424152f65a2df45a4154fdde6f51f0e1d19cb9`.

## 8.4 Leitura independente e navegação

A leitura direta do Blogger confirmou a seleção e detectou quatro botões do hero com rótulo correto e âncora deslocada. A correção ocorreu sem nova rotação de produtos.

- commit do motor `d37e91fb922541f46770a759064e1016552d67b7`;
- run `41440262021` — **SUCCESS**;
- job `125260056522`;
- `CASA_ORDEM_NAV_FIX_PASS: 4/4 âncoras corretas; 20+12 preservado`;
- segunda leitura independente confirmou os quatro destinos e os 20 produtos inalterados.

## 8.5 Schedule final

- `cron: "5 8 * * *"`;
- `timezone: "America/Recife"`;
- commit `c77915f81c004774992b54487c31afd32ab06efd`;
- auditor reforçado para proteger horário e quatro âncoras;
- commit do auditor `d7e6c29cd519360ec1a2421986813ccc6263c729`;
- auditor pós-schedule `41440836794` — **SUCCESS**;
- job `125261986171`;
- Policy Guard 13/13;
- `BLOGGER_POLICY_REPO_AUDIT_PASS`;
- `SAFE/LIVE 11/11 protegidos; Casa em Ordem schedule 08:05 protegido`.

Casa em Ordem está **CONCLUÍDO** como `modern_policy_guard_20x12`. Não reabrir sem regressão concreta.

---

# 9. ESCOLHA CERTA ONLINE — CONCLUÍDO COMO 12ª LOJA MODERNA

Alvo:

- Blog ID `5151950717041967683`
- Page LOJA ID `3334029815604129982`
- Store Post ID `5474604520207119855`
- Page `https://escolha-certa-online.blogspot.com/p/loja.html`
- Post `https://escolha-certa-online.blogspot.com/2026/11/loja.html`
- SAFE `.github/workflows/escolha_certa_online_store_safe.yml`
- LIVE `.github/workflows/escolha_certa_online_store_autonomous.yml`
- motor `blogger_stores/src/escolha_certa_online_store.py`
- histórico independente `blogger_stores/data/escolha_certa_online_rotation.json`

Perfil final: Banheiro & Acessórios; Cama & Enxoval; Organização & Utilidades; Decoração & Jardim; Limpeza & Praticidade — 5 categorias x 4 intenções, alinhadas aos posts editoriais reais do blog.

## 9.1 SAFE e revisão semântica

- SAFE final `41444290462` — **SUCCESS**;
- job `125274237954`;
- Policy Guard 13/13 e 20/20 produtos permitidos;
- regressão semântica `40/40`;
- 20 produtos / 20 intenções / links 20/20;
- fallback 0 / carry 0;
- artifact SAFE `13140694375`;
- SHA-256 `99c68b44800270edf7e03e4a9c664e0bff3a88d8be295e0da67e250c0291c586`;
- revisão manual final: 20/20 títulos coerentes com as intenções.

## 9.2 Auditor pré-LIVE

- commit `39b16791a3f65bc046401890989c6d53a40466dc`;
- run `41445104053` — **SUCCESS**;
- job `125276140405`;
- `blogger_policy_guard_self_test: 13/13 OK`;
- `BLOGGER_POLICY_REPO_AUDIT_PASS`;
- `SAFE/LIVE 12/12 protegidos`.

## 9.3 Fail-closed comprovado em duas tentativas

Primeiro LIVE:

- run `41445195745` — **FAILURE** antes de qualquer escrita Blogger;
- job `125276442640`;
- causa: erros transitórios `Shopee System Error 10000`, deixando `lencol 400 fios` sem candidato válido;
- Store, hero, identidade e persistência foram pulados.

Segundo LIVE:

- run `41445486532` — **FAILURE**;
- job `125277398761`;
- SAFE fresco, Policy Guard, DRY-RUN e writers 20+12 passaram;
- identidade autenticada passou;
- gate público recebeu **12 respostas HTTP 429**;
- persistência foi pulada;
- artifact `13143020710`;
- SHA-256 `7c27776eab3683b91e54512915521c995e014691686a269903c468002cb7b0ab`.

Isso confirmou que nem falha da Shopee nem indisponibilidade pública permitem persistência antecipada.

## 9.4 LIVE final

- kickoff commit `f1924dd2118e78657e6f6351f0603b9ade4da4c0`;
- run `41446386899` — **SUCCESS**;
- job `125280409141`;
- regressão semântica 40/40;
- seleção fresca 20/20, fallback=0, carry=0;
- Policy Guard pré-LIVE 20/20;
- identidade, Store e hero DRY-RUN PASS;
- Store 20 + hero 12 publicados;
- gate público: HTTP `429 → 429 → 429 → 429 → 200`;
- `PUBLIC_COUNTS_ATTEMPT_5: store=20 hero=12`;
- `BLOGGER_POLICY_GUARD_PUBLIC_PASS: 20 products + 12 hero`;
- `ESCOLHA_CERTA_IDENTITY_PUBLIC_PASS`;
- persistência somente depois do PASS público;
- commit automático `4acc7ef5fbfb343bf3fd47cfc07b1b1f57d47ca9`;
- artifact LIVE `13142278325`;
- SHA-256 verificado localmente `321e646e4b60a636c50199c407b3885b0c18e7231d9379fe5c2639bc18c6f5a9`.

## 9.5 Leitura independente do Blogger

Leitura direta pós-LIVE confirmou:

- status LIVE;
- Page Loja e Store Post IDs preservados;
- layout amplo aprovado preservado;
- 20 Store cards e 12 hero;
- cinco categorias próprias;
- quatro botões do hero com âncoras corretas;
- disclosure de afiliado;
- links `rel="nofollow sponsored noopener"`;
- identidade genérica de tecnologia/beleza removida;
- os mesmos 20 produtos persistidos pelo LIVE final.

## 9.6 Schedule final e auditor pós-schedule

Após verificar diretamente os horários dos 11 writers anteriores, `08:20 America/Recife` estava livre.

- workflow `.github/workflows/escolha_certa_online_store_autonomous.yml`;
- `cron: "20 8 * * *"`;
- `timezone: "America/Recife"`;
- gatilho `push` removido; workflow final usa apenas `workflow_dispatch + schedule`;
- commit `92a6497a30aa5b365fefddf8ad31b1ca53781ab8`;
- auditor reforçado para proteger horário, ausência de push e quatro âncoras;
- commit `2d3c536dc499a7b193a9eb20fec97dda2c1263b8`;
- auditor pós-schedule `41447386251` — **SUCCESS**;
- job `125283757493`;
- Policy Guard 13/13;
- `BLOGGER_POLICY_REPO_AUDIT_PASS`;
- `SAFE/LIVE 12/12 protegidos; Casa em Ordem schedule 08:05 e Escolha Certa Online schedule 08:20 protegidos`.

Escolha Certa Online está **CONCLUÍDO** como `modern_policy_guard_20x12`. Não reabrir sem evidência concreta de regressão.

---

# 10. OUTRAS CAMADAS DE PROTEÇÃO PRESERVADAS

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

### Limpeza Inteligente

- canônico `.github/workflows/limpeza_inteligente_store_autonomous.yml`
- legado `.github/workflows/limpeza_store_autonomous.yml` recovery-only
- concurrency `limpeza-inteligente-store-live`

### Ventiladores em Foco

- canônico `.github/workflows/ventiladores_store_autonomous.yml`
- legado `.github/workflows/ventiladores_em_foco_store_autonomous.yml` recovery-only
- concurrency `ventiladores-store-live`

Não reintroduzir `schedule` nem `push` nos writers legados.

---

# 11. FILA RESTANTE — 6 BLOGS

Ordem atual:

1. **Achados que Valem**
2. Guia de Achados & Ofertas
3. Moda e Ofertas
4. Achadinhos de Beleza
5. Radar Tech BR Blogger
6. Cozinha Sem Complicação

Cada alvo exige perfil semântico próprio antes do LIVE.

---

# 12. PRÓXIMO BLOCO PERMITIDO — ACHADOS QUE VALEM, NÃO INICIADO

Alvo inventariado:

- Blog ID `7527651041649593600`
- Page LOJA ID `2615453333851618808`
- Store Post ID `953731363427123084`
- Page `https://achados-que-valem.blogspot.com/p/loja.html`
- Post `https://achados-que-valem.blogspot.com/2026/11/loja.html`
- estado atual `store_scaffold_needs_auto_rotation`
- perfil semântico ainda precisa ser definido e validado

**Não iniciar Achados que Valem automaticamente. Aguardar novo `continue` do usuário.**

---

# 13. REGRAS ESSENCIAIS PARA FUTURAS EXECUÇÕES

- Não reiniciar diagnóstico de Vitrine, Achados para Casa, Conecta, Estilo, Casa em Ordem ou Escolha Certa Online sem evidência concreta de regressão.
- Não pedir operação manual quando ferramentas conectadas já executam a ação.
- Confirmar Blog ID e Store Post ID antes de escrever.
- Não recriar Page/Post Loja.
- Preservar identidade do blog.
- Preservar Store 20 + hero 12.
- Preservar fail-closed.
- Preservar históricos independentes.
- Policy Guard deve existir em SAFE, pré-LIVE e HTML público.
- Persistir somente depois do PASS público.
- HTTP 429 no gate público deve usar retry, nunca bypass.
- Leitura autenticada ajuda no diagnóstico, mas não substitui PASS público.
- Não forçar produto semanticamente errado para preencher categoria.
- Um Action verde não substitui inspeção de artifact/HTML quando houver dúvida semântica.
- Preservar gate editorial anti-repetição.
- Nunca ocultar/desativar cookie notice nativo.
- Não armazenar secrets no repositório.
- Expandir **um blog por vez**.

---

# 14. BACKUP / RECUPERAÇÃO

Último backup completo criado antes de Conecta/Estilo:

- R3 `blogger-automation1-backup-2026-11-02-r3`
- run `41428226665` — SUCCESS
- artifact ID `13132752660`
- SHA-256 `65a76eecb33d126e00ffe80e657adbdf488ad93766fda1dd971beece2208b863`
- commit capturado `0e41104ffcadc37aedfd644875a1d42ebde8ee4f`

Como o R3 é anterior às conclusões de Conecta, Estilo, Casa em Ordem e Escolha Certa Online, um próximo backup completo deverá incluir os commits desses quatro blocos.

Se este arquivo for encontrado em uma conversa futura:

- Vitrine Prática = 7ª loja moderna concluída;
- Achados para Casa = 8ª loja moderna concluída;
- Conecta Achados = 9ª loja moderna concluída;
- Estilo no Dia a Dia = 10ª loja moderna concluída;
- Casa em Ordem = 11ª loja moderna concluída;
- Escolha Certa Online = 12ª loja moderna concluída;
- auditor permanente = **12/12**;
- inventário = **12 modernas / 6 restantes**;
- próximo bloco permitido = **Achados que Valem**, somente após comando explícito do usuário.
