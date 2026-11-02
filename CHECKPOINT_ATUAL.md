# CHECKPOINT ATUAL — BLOGGER AUTOMATION

**Última atualização:** 2026-11-01 22:08 America/Recife  
**Projeto:** Blogger Automation sem ChatGPT Work

## LEIA PRIMEIRO

Antes de qualquer operação Blogger neste projeto, leia nesta ordem:

1. `CHECKPOINT_ATUAL.md`
2. `CHECKPOINT_UPDATE_2026-11-01_POLICY_EDITORIAL_COOKIES.md`
3. `blogger_multi_store/data/NETWORK_STORE_INVENTORY_2026-11-01.json`
4. `blogger_multi_store/config/network_store_rollout_2026-11-01.json`
5. `CHECKPOINT_UPDATE_2026-10-30_LAB_CANONICAL_V20.md`
6. `CHECKPOINT_BLOGGER_AUTOMATION_MASTER_2026-10-30.md`
7. `CHECKPOINT_BLOGGER_AUTOMATION_MASTER_2026-10-30.json`
8. `infrastructure/README.md`
9. `BACKUP_MANIFEST_BLOGGER_AUTOMATION_2026-11-01.json`
10. `BACKUP_MANIFEST_BLOGGER_AUTOMATION_2026-10-30.json`

Este arquivo prevalece quando houver diferença de estado operacional. Os checkpoints anteriores continuam válidos como histórico/base de recuperação.

---

# 1. ESTADO OPERACIONAL ATUAL VALIDADO

- Blogger Local Runner: **v0.8**.
- Chrome oficial/CDP conectado e autenticado.
- Capacidades v0.8 reportadas: `create`, `settings`, `v20`, `provision-new-blog-v20`, `v20-runtime-sync-guard`.
- Conteúdo Blogger: `Blogger_Bridge_V2`.
- Rede conectada: **18 blogs Blogger**.
- TEMA MODELO V20 permanece como base canônica documentada em 2026-10-30.
- **18/18** blogs possuem Page LIVE `/p/loja.html`.
- **18/18** blogs possuem Store Post LIVE `Loja`.
- Não recriar Page/Post Loja durante expansão; usar os IDs inventariados.

## Lojas modernas protegidas

O Blogger Policy Guard está integrado em **8 pipelines modernos** com:

- SAFE;
- Policy Guard pré-LIVE;
- contrato de **20 produtos + 12 hero**;
- validação pública;
- identidade por blog;
- fail-closed;
- persistência de rotação somente depois de PASS público;
- histórico independente por blog;
- writer automático único por blog.

Lojas protegidas:

1. Eletroportáteis na Cozinha
2. Cabelos em Foco
3. Ventiladores em Foco
4. Air Fryers em Foco
5. Limpeza Inteligente
6. Liquidificadores em Foco
7. Vitrine Prática
8. **Achados para Casa**

Estado do inventário:

- `modern_blogger_auto_policy_guard: 8`
- `modern_blogger_auto_20x12_needs_policy_guard_upgrade: 0`
- `store_scaffold_needs_auto_rotation: 10`
- `duplicate_writer_risks: 0`

O rollout global permanece:

- `enabled=false`
- `mode=PREPARED_NOT_DEPLOYED`

Nenhum próximo blog deve ser ativado em lote.

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
- persistência apenas depois de validação pública;
- sem compartilhamento de histórico entre blogs;
- nunca forçar item semanticamente inválido apenas para completar 20 cards.

Regra de rotação validada no Achados para Casa:

1. preferir produto novo na janela;
2. se não houver, permitir produto antigo fora da última rodada;
3. somente se não existir alternativa válida, permitir carry-forward da última publicação;
4. todos os gates semânticos continuam obrigatórios em qualquer fase.

---

# 3. POLICY GUARD / AUDITOR PERMANENTE

Arquivos centrais:

- `POLICY_BASELINE_BLOGGER_GOOGLE_2026.md`
- `config/blogger_policy_guard.json`
- `src/blogger_policy_guard.py`
- `src/blogger_policy_guard_self_test.py`
- `src/blogger_policy_repo_audit.py`
- `.github/workflows/blogger_policy_repo_audit.yml`

O auditor agora cobre também:

- `blogger_stores/src/**`
- `.github/workflows/achados_casa_store_safe.yml`
- `.github/workflows/achados_casa_store_autonomous.yml`

Validação final após habilitar o schedule do Achados para Casa:

- commit `c92688b6fde38dac8c2b1795b5672e4592d50480`
- run `41370840393` — **SUCCESS**
- job `125040766487`
- `blogger_policy_guard_self_test: 13/13 OK`
- `BLOGGER_POLICY_REPO_AUDIT_PASS`
- `SAFE/LIVE 8/8 protegidos; writers legados manual-only; sem ocultação/desativação detectada do aviso nativo de cookies.`

---

# 4. VITRINE PRÁTICA — CONCLUÍDA COMO 7ª LOJA PROTEGIDA

Alvo:

- Blog ID `9144338307944682868`
- Page LOJA ID `8344701886444887322`
- Store Post ID `115613719594316807`
- SAFE `.github/workflows/vitrine_pratica_store_safe.yml`
- LIVE `.github/workflows/vitrine_pratica_store_autonomous.yml`

Provas principais:

- SAFE run `41364558522` — SUCCESS
- auditor final daquela etapa `41367352735` — SUCCESS
- LIVE `41367361852` — SUCCESS
- 20 produtos + 12 hero
- identidade pública da Vitrine correta
- domínio legado de Liquidificadores removido
- persistência pós-PASS: commit automático `0c54a7f0b701515288a944244753dbf4b58c19ae`
- artifact LIVE ID `13107641975`
- SHA-256 `31c48d272c4e8befdb470e110f5c6d4364b37143b2e303e61893d68ab1451745`

Não reabrir esse diagnóstico sem sinal concreto de regressão.

---

# 5. ACHADOS PARA CASA — CONCLUÍDO COMO 8ª LOJA PROTEGIDA

## Alvo

- Blog ID `1426630233929943394`
- Page LOJA ID `3841238517239710135`
- Store Post ID `854861801599328533`
- Page `https://achadosparacasa2026.blogspot.com/p/loja.html`
- Post `https://achadosparacasa2026.blogspot.com/2026/10/loja.html`
- SAFE `.github/workflows/achados_casa_store_safe.yml`
- LIVE `.github/workflows/achados_casa_store_autonomous.yml`
- Shopee AppID autorizado `18352820579`
- histórico independente `blogger_stores/data/achados_casa_rotation.json`

## 5.1 Engenharia instalada

Scripts principais:

- `blogger_stores/src/achados_casa_safe_scan_v2.py`
- `blogger_stores/src/achados_casa_safe_scan_v3.py`
- `blogger_stores/src/achados_casa_safe_scan_v6.py`
- `blogger_stores/src/achados_casa_publish_post.py`
- `blogger_stores/src/achados_casa_hero_sync_post.py`
- `blogger_stores/src/achados_casa_layout_patch.py`
- `blogger_stores/src/achados_casa_persist_rotation.py`

Perfil semântico:

- `config/shopee_achados_casa.json` — versão 5
- `config/shopee_achados_casa_intent_rules.json` — versão 4

Categorias finais:

1. Organização & Armazenamento
2. Cozinha & Utilidades
3. Limpeza & Lavanderia
4. Decoração & Conforto
5. Clima & Bem-estar

Cada categoria possui 4 intenções semânticas próprias.

## 5.2 SAFE final comprovado

Run/job final do perfil limpo:

- run `41370322415` — **SUCCESS**
- job `125039197072`
- head SHA `a4e520c0e35facbf5f38a94f661eec92b6e9e8e8`

Marcadores:

- Policy Guard self-test **13/13 OK**
- AppID correto
- `Testes semânticos Achados v5: 10/10 OK`
- ranking Shopee: 180 candidatos
- 20 produtos válidos
- 20 palavras-chave cobertas
- 20/20 links afiliados resolvidos
- `BLOGGER_POLICY_GUARD_SAFE_PASS: 20/20 produtos permitidos`
- `ACHADOS_SAFE_READ_ONLY_PASS: nenhum writer Blogger executado`

Artifact:

- `achados-casa-store-safe-22`
- artifact ID `13108793579`
- SHA-256 `91694e8771bf1f38232959a4798dc98b377a8f988c09fedba1b85e2340db1088`

A inspeção independente do artifact confirmou que a categoria Clima & Bem-estar continha aparelhos reais.

## 5.3 Regressões semânticas encontradas durante a implantação

O primeiro LIVE tecnicamente verde **não foi aceito como conclusão** porque uma leitura independente do Store Post encontrou falsos positivos na categoria Clima & Bem-estar.

Problemas detectados durante a investigação:

- consulta genérica `ventilador` podia selecionar escova limpadora de ventilador;
- também podia selecionar produto de cílios com descrição `forma ventilador`;
- `ar condicionado portatil` retornava mini ventilador/climatizador vendido com marketing de ar-condicionado;
- tentativa de usar `aquecedor eletrico` encontrou aquecedores de água/mergulhão, não aquecedores de ambiente.

A correção não afrouxou gates. O perfil foi tornado mais específico.

Perfil final de Clima & Bem-estar:

1. `ventilador de teto`
2. `mini umidificador usb`
3. `climatizador`
4. `ventilador de mesa`

Gates finais exigem sinais positivos de aparelho completo e rejeitam peças, acessórios, beleza, moldes, escovas e outros usos indevidos.

Essa ocorrência é uma regra de projeto: **run verde não substitui validação semântica independente quando houver sinal de falso positivo**.

## 5.4 LIVE corrigido comprovado

Run/job:

- run `41370529825` — **SUCCESS**
- job `125039829532`
- head SHA `1fb7fd6f682a31fb22ad92f34ed0f093deb4acbb`

Marcadores dos logs:

- `Testes semânticos Achados v5: 10/10 OK`
- `BLOGGER_POLICY_GUARD_PRELIVE_PASS: 20/20 produtos permitidos`
- `ACHADOS_SEMANTIC_PRELIVE_PASS: schema v6, 5 categorias x 4 produtos`
- `ACHADOS_CASA_STORE_DRY_RUN_PASS`
- `ACHADOS_CASA_HERO_DRY_RUN_PASS`
- `ACHADOS_CASA_LAYOUT_DRY_RUN_PASS`
- `ACHADOS_CASA_POST_PUBLISH_PASS: 20 produtos`
- `ACHADOS_CASA_HERO_PASS: 12 mini-cards únicos sincronizados`
- `ACHADOS_CASA_LAYOUT_PASS`
- `BLOGGER_POLICY_GUARD_PUBLIC_PASS: 20 products + 12 hero`
- `ACHADOS_CASA_IDENTITY_PUBLIC_PASS: nicho casa + Page LOJA corretos`
- `ACHADOS_CASA_ROTATION_PERSIST_PASS: 20 produtos registrados após validação pública`

Persistência automática após PASS:

- commit `db72d98` — `Atualizar rotação automática da Loja Achados para Casa`

Artifact LIVE:

- `achados-casa-store-live-4`
- artifact ID `13108559699`
- SHA-256 `9de04eb388ca543779ade9a5fabc8653fa2b67ad43ccdba63bb3365eaeafd128`

## 5.5 Leitura independente do Blogger após LIVE corrigido

`Blogger_Bridge_V2.get_post` confirmou diretamente no Store Post LIVE:

- URL da Page Loja correta: `https://achadosparacasa2026.blogspot.com/p/loja.html`
- status LIVE
- layout amplo preservado
- sidebar/PopularPosts ocultos apenas na Loja
- identidade textual focada em casa
- 5 categorias corretas
- 20 cards de Store
- 12 mini-cards de hero
- disclosure de afiliado presente
- links com `rel="nofollow sponsored noopener"`
- sem referências executáveis à Vitrine Prática/Liquidificadores

Clima & Bem-estar confirmado no HTML público:

- item `18699585471` — **Ventilador de Teto** com controle remoto
- item `23197150622` — **Mini Umidificador USB**
- item `44503561166` — **Climatizador Ventisol 16 L**
- item `58218004530` — **Ventilador de Mesa Prime Air Maxx Force**

Os falsos positivos encontrados nos testes anteriores não permanecem no Store Post final.

## 5.6 Rotação

Na execução final:

- 19 produtos foram rotacionados normalmente;
- apenas a fritadeira `23198020257` foi mantida por carry-forward porque não havia alternativa semanticamente válida no ranking atual;
- a escolha foi explícita e registrada;
- nenhum gate semântico foi relaxado para forçar novidade.

## 5.7 Schedule final

O schedule foi habilitado **somente depois de SAFE + LIVE + leitura independente limpa**.

Workflow:

- `.github/workflows/achados_casa_store_autonomous.yml`

Agenda:

- `cron: "20 7 * * *"`
- `timezone: "America/Recife"`

Commit:

- `c92688b6fde38dac8c2b1795b5672e4592d50480` — `achados: habilitar schedule diario apos validacao completa`

Auditor pós-schedule:

- run `41370840393` — SUCCESS
- job `125040766487`
- `BLOGGER_POLICY_REPO_AUDIT_PASS`
- `SAFE/LIVE 8/8 protegidos`

Achados para Casa está agora **CONCLUÍDO** como `modern_policy_guard_20x12`.

---

# 6. OUTRAS CAMADAS DE PROTEÇÃO PRESERVADAS

## Gate anti-repetição editorial

Arquivos:

- `config/editorial_cross_blog_guard.json`
- `src/editorial_cross_blog_guard.py`
- `src/editorial_cross_blog_guard_self_test.py`
- `.github/workflows/editorial_cross_blog_guard_safe.yml`

Escopo atual:

- Casa & Decoração
- Oficina & Garagem
- Radar Tech BR

SAFE validado no run `41358905465`.

## Auditoria europeia de cookies Blogger

Arquivos:

- `src/blogger_eu_cookie_audit.py`
- `.github/workflows/blogger_eu_cookie_audit_safe.yml`

Última validação documentada:

- **18/18 PASS**
- 0 FAIL
- banner francês visível
- botão de consentimento visível
- clique removeu o banner
- run `41359632797` — SUCCESS

Regra permanente: nunca ocultar/desativar o aviso nativo de cookies do Blogger por tema/CSS.

## Writers duplicados consolidados

### Limpeza Inteligente

- automático canônico: `.github/workflows/limpeza_inteligente_store_autonomous.yml`
- legado recovery-only: `.github/workflows/limpeza_store_autonomous.yml`
- concurrency compartilhada: `limpeza-inteligente-store-live`

### Ventiladores em Foco

- automático canônico: `.github/workflows/ventiladores_store_autonomous.yml`
- legado recovery-only: `.github/workflows/ventiladores_em_foco_store_autonomous.yml`
- concurrency compartilhada: `ventiladores-store-live`

Não reintroduzir `schedule` nem `push` nos writers legados.

---

# 7. FILA RESTANTE — 10 BLOGS

Ordem atual do rollout:

1. **Conecta Achados**
2. Estilo no Dia a Dia
3. Casa em Ordem
4. Escolha Certa Online
5. Achados que Valem
6. Guia de Achados & Ofertas
7. Moda e Ofertas
8. Achadinhos de Beleza
9. Radar Tech BR Blogger
10. Cozinha Sem Complicação

Cada alvo continua exigindo perfil semântico próprio antes de qualquer LIVE.

---

# 8. PRÓXIMO BLOCO PERMITIDO — CONECTA ACHADOS, NÃO INICIADO

Alvo inventariado:

- Blog ID `1719259388907013414`
- Page LOJA ID `2386698852540729057`
- Store Post ID `259394788951394758`
- Page `https://conectaachados.blogspot.com/p/loja.html`
- Post `https://conectaachados.blogspot.com/2026/11/loja.html`
- estado atual: `store_scaffold_needs_auto_rotation`
- perfil semântico: ainda precisa ser definido/validado

**Não iniciar Conecta Achados automaticamente. Aguardar novo comando explícito do usuário.**

---

# 9. REGRAS ESSENCIAIS PARA A PRÓXIMA CONVERSA

- Não reiniciar diagnóstico de Vitrine Prática nem Achados para Casa sem evidência concreta de regressão.
- Não pedir operação manual quando ferramentas conectadas já executam a ação.
- Confirmar Blog ID e Store Post ID antes de qualquer escrita.
- Não recriar Page/Post Loja existentes.
- Preservar identidade de nicho.
- Preservar Store 20 + 12.
- Preservar fail-closed.
- Preservar históricos independentes.
- Policy Guard deve existir em SAFE, pré-LIVE e HTML público.
- Persistir rotação somente depois do PASS público.
- Não forçar produto semanticamente errado para preencher categoria.
- Quando uma palavra-chave for semanticamente ambígua, especializar a intenção em vez de apenas ampliar listas de bloqueio.
- Preservar gate anti-repetição editorial.
- Nunca ocultar/desativar o aviso nativo de cookies.
- Não armazenar secrets no repositório.
- Não declarar sucesso somente porque o GitHub Action ficou verde: validar logs e, quando aplicável, o estado público e a semântica real.
- Expandir **um blog por vez**.

---

# 10. HISTÓRICO E RECUPERAÇÃO

Os detalhes completos do estado de 2026-10-30 — TEMA MODELO V20, infraestrutura, Cloudflare gateway, plugin privado, laboratório V20 e gaps locais antigos — permanecem preservados nos checkpoints e manifestos datados de 2026-10-30.

Se este arquivo for encontrado em uma conversa futura:

- Vitrine Prática já está concluída como a 7ª loja moderna;
- Achados para Casa já está concluído como a 8ª loja moderna;
- o auditor permanente está em **8/8**;
- restam **10 blogs**;
- o próximo bloco permitido é **Conecta Achados**, somente após comando explícito do usuário.
