# CHECKPOINT ATUAL — BLOGGER AUTOMATION

**Última atualização:** 2026-11-01  
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

Nos seis pipelines de lojas de nicho, o Policy Guard roda em SAFE e na validação pública LIVE. A persistência de rotação/histórico só ocorre depois de PASS público.

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
- **18/18 blogs possuem post LIVE `Loja`**, que é a superfície dinâmica usada pelos motores modernos para receber a vitrine.
- Portanto, NÃO recriar páginas Loja nem posts Loja na expansão; atualizar os alvos existentes por ID.
- **6 blogs de nicho** já possuem pipeline Blogger automático com contrato 20 produtos + 12 hero + Policy Guard + validação pública + persistência pós-PASS.
- **Vitrine Prática** já possui rotação Blogger automática 20 + 12 e validação pública, mas ainda deve receber o Policy Guard central para ficar no mesmo padrão dos seis nichos.
- **11 blogs** possuem scaffold Loja LIVE, porém ainda precisam receber o motor moderno de rotação Blogger/Shopee.
- A fila desses 11 alvos está criada como `PREPARED_NOT_DEPLOYED` e `enabled=false`; nenhum LIVE novo foi acionado nesta preparação.

### Risco técnico identificado antes da expansão

Há dois casos de writers agendados concorrentes apontando para o MESMO Blog ID e Store Post ID:

1. **Limpeza Inteligente**
   - `.github/workflows/limpeza_store_autonomous.yml`
   - `.github/workflows/limpeza_inteligente_store_autonomous.yml`

2. **Ventiladores em Foco**
   - `.github/workflows/ventiladores_store_autonomous.yml`
   - `.github/workflows/ventiladores_em_foco_store_autonomous.yml`

Não desativar nem escolher um deles no chute. A consolidação deve ser uma execução própria, preservando o estado/seleção vencedor e mantendo o workflow que passar no conjunto completo de Policy Guard + 20/12 + validação pública.

### Próxima ordem segura para expansão

1. Consolidar os writers duplicados de Limpeza e Ventiladores.
2. Endurecer Vitrine Prática com o Policy Guard central.
3. Promover **Achados para Casa** primeiro entre os 11 restantes, porque já existe SAFE específico (`achados_casa_store_safe.yml`).
4. Depois expandir o mesmo blueprint para os demais alvos da fila, sempre com perfil semântico próprio e histórico independente.

## Lojas Shopee de nicho — regra atual

As seis identidades de nicho que devem ser preservadas são:

- Ventiladores em Foco
- Air Fryers em Foco
- Limpeza Inteligente
- Cabelos em Foco
- Liquidificadores em Foco
- Eletroportáteis na Cozinha

Arquitetura canônica:

`Shopee API → Blogger Policy Guard → filtro semântico → dedup/rotação → SAFE → LIVE → hero 12 → validação pública → persistência`

Contrato:

- 20 produtos
- 12 hero
- histórico independente por blog
- fail-closed
- persistência somente após validação pública

Não voltar a um único histórico compartilhado entre blogs.

## Correções que não devem ser refeitas sem regressão comprovada

Vitrine Prática e Ventiladores em Foco já receberam a correção final da página Loja: largura 100%, uma coluna, sidebar e “Postagens mais visitadas” ocultos somente na Loja, `.bls-page` centralizada, 20 cards + 12 hero preservados e domínio/nome legado removido do cloner de Ventiladores em Foco.

## Próximo bloco de trabalho

A próxima execução recomendada é **consolidar os writers duplicados de Limpeza Inteligente e Ventiladores em Foco** antes de ampliar a automação para os 11 blogs restantes.

Depois disso, continuar a implantação da LOJA Blogger + Shopee em destaque na rede reutilizando a arquitetura existente, sem reconstruir o motor do zero.

Objetivo final:

`Blogger + automação local + APIs + tema/SEO + páginas institucionais + afiliados + Shopee + LOJA destacada + atualização automática`

## Regras essenciais

- Não refazer validações concluídas sem sinal concreto de regressão.
- Não pedir operação manual quando o Local Runner já oferece comando validado.
- Confirmar Blog ID antes de escrever.
- Preservar identidade por nicho.
- Preservar Store 20 + 12, fail-closed e históricos independentes.
- Preservar Policy Guard SAFE/LIVE e validação pública antes da persistência.
- Preservar o gate anti-repetição editorial.
- Nunca ocultar/desativar o aviso nativo de cookies do Blogger por tema/CSS.
- Não armazenar secrets no repositório.
- Não declarar sucesso sem validação concreta.

## Histórico e recuperação

Os detalhes completos do estado de 2026-10-30 — TEMA MODELO V20, infraestrutura, Cloudflare gateway, plugin privado, laboratório V20 e gaps locais antigos — continuam preservados nos checkpoints e manifestos datados de 2026-10-30.

Se este arquivo for encontrado em uma conversa futura, NÃO reiniciar o diagnóstico. Ler primeiro `CHECKPOINT_UPDATE_2026-11-01_POLICY_EDITORIAL_COOKIES.md`, depois o inventário de rede das Lojas, e continuar a partir do próximo bloco pendente.
