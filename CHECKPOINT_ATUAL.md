# CHECKPOINT ATUAL — BLOGGER AUTOMATION

**Última atualização:** 2026-11-01 21:30 America/Recife  
**Projeto:** Blogger Automation sem ChatGPT Work

## LEIA PRIMEIRO

Antes de qualquer operação Blogger neste projeto, leia nesta ordem:

1. `CHECKPOINT_UPDATE_2026-11-01_POLICY_EDITORIAL_COOKIES.md`
2. `blogger_multi_store/data/NETWORK_STORE_INVENTORY_2026-11-01.json`
3. `blogger_multi_store/config/network_store_rollout_2026-11-01.json`
4. `CHECKPOINT_UPDATE_2026-10-30_LAB_CANONICAL_V20.md`
5. `CHECKPOINT_BLOGGER_AUTOMATION_MASTER_2026-10-30.md`
6. `CHECKPOINT_BLOGGER_AUTOMATION_MASTER_2026-10-30.json`
7. `infrastructure/README.md`
8. `BACKUP_MANIFEST_BLOGGER_AUTOMATION_2026-11-01.json`
9. `BACKUP_MANIFEST_BLOGGER_AUTOMATION_2026-10-30.json`

O checkpoint de 2026-11-01 prevalece quando houver diferença de estado operacional. Os arquivos de 2026-10-30 permanecem como histórico/base de recuperação.

## Estado operacional atual validado

- Blogger Local Runner: **v0.8**.
- Chrome oficial/CDP conectado e autenticado.
- Capacidades v0.8 reportadas: `create`, `settings`, `v20`, `provision-new-blog-v20`, `v20-runtime-sync-guard`.
- Conteúdo Blogger: `Blogger_Bridge_V2`.
- Rede conectada: **18 blogs Blogger**.
- TEMA MODELO V20 continua sendo a base canônica já documentada no checkpoint de 2026-10-30.

## Camadas de proteção concluídas em 2026-11-01

### Blogger Policy Guard

Arquivos centrais:

- `POLICY_BASELINE_BLOGGER_GOOGLE_2026.md`
- `config/blogger_policy_guard.json`
- `src/blogger_policy_guard.py`
- `src/blogger_policy_guard_self_test.py`
- `src/blogger_policy_repo_audit.py`

O Policy Guard está agora integrado em **7 pipelines Blogger modernos**, em SAFE/pré-LIVE e na validação pública LIVE. A persistência de rotação/histórico só ocorre depois de PASS público.

Lojas protegidas:

- Eletroportáteis na Cozinha
- Cabelos em Foco
- Ventiladores em Foco
- Air Fryers em Foco
- Limpeza Inteligente
- Liquidificadores em Foco
- **Vitrine Prática**

### Gate anti-repetição editorial

Arquivos:

- `config/editorial_cross_blog_guard.json`
- `src/editorial_cross_blog_guard.py`
- `src/editorial_cross_blog_guard_self_test.py`
- `.github/workflows/editorial_cross_blog_guard_safe.yml`

Escopo atual: Casa & Decoração, Oficina & Garagem e Radar Tech BR.

Validação SAFE concluída com sucesso no run ID `41358905465`.

### Auditoria europeia de cookies Blogger

Arquivos:

- `src/blogger_eu_cookie_audit.py`
- `.github/workflows/blogger_eu_cookie_audit_safe.yml`

Validação real usando navegador Chromium/Playwright, locale `fr-FR` e `?gl=fr`:

- **18/18 blogs PASS**
- **0 FAIL**
- HTTP 200 em todos
- banner francês visível em todos
- botão de consentimento visível em todos
- clique confirmou remoção do banner em todos
- screenshots antes/depois + relatório JSON salvos como artifact

Run final otimizado: `41359632797` — **SUCCESS**.

## Lojas Blogger + Shopee — inventário vivo da rede

Inventário canônico:

- `blogger_multi_store/data/NETWORK_STORE_INVENTORY_2026-11-01.json`
- `blogger_multi_store/config/network_store_rollout_2026-11-01.json`

Estado validado em 2026-11-01:

- **18/18 blogs possuem página LIVE `/p/loja.html`**.
- **18/18 blogs possuem post LIVE `Loja`**, superfície dinâmica dos motores modernos.
- NÃO recriar páginas Loja nem posts Loja na expansão; atualizar os alvos existentes por ID.
- **7 blogs** possuem pipeline Blogger automático com contrato 20 produtos + 12 hero + Policy Guard central + validação pública + persistência pós-PASS.
- **11 blogs** possuem scaffold Loja LIVE, porém ainda precisam receber o motor moderno de rotação Blogger/Shopee.
- A fila desses 11 alvos está `PREPARED_NOT_DEPLOYED` e `enabled=false`.
- `duplicate_writer_risks: 0`.

## Vitrine Prática — POLICY GUARD CENTRAL CONCLUÍDO

Alvo validado:

- Blog ID `9144338307944682868`
- Page LOJA ID `8344701886444887322`
- Store Post ID `115613719594316807`
- Post público `https://vitrine-pratica.blogspot.com/2026/11/loja.html`
- SAFE `.github/workflows/vitrine_pratica_store_safe.yml`
- LIVE `.github/workflows/vitrine_pratica_store_autonomous.yml`

### 1. SAFE comprovado

Commit da proteção SAFE:

- `217090e5e3c3efb4008187eb8dcdd7d063c94660` — `policy: proteger SAFE da Vitrine Pratica`

Run/job:

- run `41364558522` — **SUCCESS**
- job `125021851051`

Marcadores comprovados nos logs:

- `DRY_RUN=true`
- `blogger_policy_guard_self_test: 13/13 OK`
- `blogger_store_auto_self_test: 10/10 OK`
- semântica Vitrine: **28/28 OK**
- 20 produtos únicos em 5 categorias
- `BLOGGER_POLICY_GUARD_SAFE_PASS: 20/20`
- Blogger não alterado pelo SAFE

### 2. Auditor permanente 7/7 comprovado

Integração do auditor:

- commit `b3c2fa167b79a8424778fa272ea6b38016e2f58b` — auditor passou a proteger a Vitrine e monitorar `vitrine_pratica_store/src/**`.
- run de comprovação anterior `41364606766` — SUCCESS
- job `125022000939`

Após a correção final do LIVE, o auditor foi disparado novamente:

- commit do workflow final `a6898875cf8bcdb9a16eaa80875f507e400bc47b`
- run `41367352735` — **SUCCESS**
- job `125030229025`

Marcadores:

- `blogger_policy_guard_self_test: 13/13 OK`
- `BLOGGER_POLICY_REPO_AUDIT_PASS`
- `SAFE/LIVE 7/7 protegidos; writers legados manual-only; sem ocultação/desativação detectada do aviso nativo de cookies.`

### 3. Regressão pública encontrada e corrigida

Durante leitura independente do Store Post, foi detectado que o menu do HTML público ainda apontava para:

- `https://liquidificadores-em-foco.blogspot.com/p/loja.html`

A origem foi isolada: `vitrine_pratica_store/src/store_layout_patch.py` já possuía a URL correta da Vitrine, mas o LIVE apenas compilava o patch e não o executava.

Foi mantido o layout aprovado e adicionada somente a execução do patch, junto de gate público explícito de identidade.

Commit:

- `a6898875cf8bcdb9a16eaa80875f507e400bc47b` — `fix: aplicar patch final de identidade na Vitrine Pratica LIVE`

Kickoff controlado:

- `3ed06c1889e15c6d8f2e5cb8fd40df98e181db96` — `live: validar Policy Guard e identidade da Vitrine Pratica`

### 4. LIVE controlado comprovado

Run/job:

- run `41367361852` — **SUCCESS**
- job `125030258705`
- head SHA `3ed06c1889e15c6d8f2e5cb8fd40df98e181db96`

Provas dos logs:

- Policy Guard self-test **13/13 OK**
- Vitrine self-test **10/10 OK**
- semântica **28/28 OK**
- `BLOGGER_POLICY_GUARD_PRELIVE_PASS: 20/20 produtos permitidos`
- `PUBLICAÇÃO OK: 20 produtos únicos; alvo Blogger 115613719594316807 verificado.`
- `HERO OK: 12 mini-cards únicos sincronizados.`
- `LAYOUT_WIDE_APPLIED`
- `STORE_TARGET_VITRINE_PRATICA_OK`
- `POPULAR_POSTS_HIDDEN_ON_STORE_OK`
- `STORE_VIEWPORT_CENTERED_OK`
- `BLOGGER_POLICY_GUARD_PUBLIC_PASS: 20 products + 12 hero`
- `VITRINE_IDENTITY_PUBLIC_PASS: domínio e link LOJA corretos`
- persistência executada somente depois do PASS público

Commit automático pós-PASS:

- `0c54a7f0b701515288a944244753dbf4b58c19ae` — `Atualizar rotação automática da Loja Vitrine Prática`

Artifact do LIVE:

- `vitrine-pratica-store-live-5`
- artifact ID `13107641975`
- SHA-256 do artifact registrado no log: `31c48d272c4e8befdb470e110f5c6d4364b37143b2e303e61893d68ab1451745`

### 5. Leitura independente do Blogger após LIVE

`Blogger_Bridge_V2.get_post` confirmou diretamente no Store Post LIVE:

- URL da Page Loja correta no script: `https://vitrine-pratica.blogspot.com/p/loja.html`
- domínio legado `liquidificadores-em-foco.blogspot.com/p/loja.html` removido
- layout de uma coluna/largura ampla preservado
- sidebar e PopularPosts continuam ocultos apenas na Loja
- disclosure de afiliado presente
- links Shopee com `rel="nofollow sponsored noopener"`
- vitrine e hero permanecem no contrato 20 + 12 validado pelo gate público

### 6. Estado persistente atualizado

Inventário:

- commit `8df40051de33c730df5b721759f2111284b6a5d3`
- `modern_blogger_auto_policy_guard: 7`
- `modern_blogger_auto_20x12_needs_policy_guard_upgrade: 0`
- Vitrine = `modern_policy_guard_20x12`
- `duplicate_writer_risks: 0`

Rollout:

- commit `3080d4399e448834c2a5046ccda53fe73ee80c95`
- blocker de upgrade da Vitrine removido
- blocker real restante: perfil semântico/categorias por blog
- `enabled=false` preservado
- `mode=PREPARED_NOT_DEPLOYED` preservado

## Consolidação dos writers duplicados — CONCLUÍDA

### Limpeza Inteligente

- automático canônico: `.github/workflows/limpeza_inteligente_store_autonomous.yml`
- legado recovery-only: `.github/workflows/limpeza_store_autonomous.yml`
- concurrency: `limpeza-inteligente-store-live`
- SAFE `41362247655` — SUCCESS
- Guard 13/13; semântica 16/16; 20 produtos únicos; Blogger não alterado

### Ventiladores em Foco

- automático canônico: `.github/workflows/ventiladores_store_autonomous.yml`
- legado recovery-only: `.github/workflows/ventiladores_em_foco_store_autonomous.yml`
- concurrency: `ventiladores-store-live`
- SAFE `41362260056` — SUCCESS
- Guard 13/13; semântica 28/28; 20 produtos únicos; Blogger não alterado

Regra permanente: não reintroduzir `schedule` nem `push` nos writers legados.

## Arquitetura canônica das lojas modernas

`Shopee API → Blogger Policy Guard → filtro semântico → dedup/rotação → SAFE → LIVE → hero 12 → validação pública → persistência`

Contrato:

- 20 produtos
- 12 hero
- Policy Guard pre-LIVE
- Policy Guard no HTML público
- histórico independente por blog
- fail-closed
- persistência somente após validação pública
- writer automático único por blog

## Próxima ordem segura para expansão

1. **Achados para Casa** → revisar o SAFE existente (`achados_casa_store_safe.yml`) e promover para o padrão LIVE moderno usando Page/Post IDs já inventariados, sem recriar Loja.
2. Depois expandir o blueprint aos outros 10 alvos restantes, cada um com perfil semântico próprio e histórico independente.

O rollout permanece desabilitado globalmente (`enabled=false`). Cada alvo deve ser validado individualmente antes de LIVE.

## Achados para Casa — próximo bloco permitido, NÃO iniciado ainda

- Blog ID `1426630233929943394`
- Page LOJA ID `3841238517239710135`
- Store Post ID `854861801599328533`
- Page `https://achadosparacasa2026.blogspot.com/p/loja.html`
- Post `https://achadosparacasa2026.blogspot.com/2026/10/loja.html`
- SAFE existente `.github/workflows/achados_casa_store_safe.yml`
- blueprint canônico `.github/workflows/air_fryers_store_autonomous.yml`

Não iniciar esse bloco automaticamente. Aguardar `continue` do usuário.

## Regras essenciais

- Não refazer validações concluídas sem sinal concreto de regressão.
- Não pedir operação manual quando o Local Runner já oferece comando validado.
- Confirmar Blog ID antes de escrever.
- Não recriar Page/Post Loja existentes.
- Preservar identidade por nicho.
- Preservar Store 20 + 12, fail-closed e históricos independentes.
- Preservar Policy Guard SAFE/LIVE e validação pública antes da persistência.
- Preservar o gate anti-repetição editorial.
- Nunca ocultar/desativar o aviso nativo de cookies do Blogger por tema/CSS.
- Não armazenar secrets no repositório.
- Não declarar sucesso sem validação concreta de run/job/log e, quando aplicável, estado público.

## Histórico e recuperação

Os detalhes completos do estado de 2026-10-30 — TEMA MODELO V20, infraestrutura, Cloudflare gateway, plugin privado, laboratório V20 e gaps locais antigos — continuam preservados nos checkpoints e manifestos datados de 2026-10-30.

Se este arquivo for encontrado em uma conversa futura, NÃO reiniciar o diagnóstico. A **Vitrine Prática já está concluída como a 7ª loja protegida**. O próximo bloco permitido é **Achados para Casa**, e somente após comando explícito do usuário.
