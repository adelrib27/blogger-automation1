# CHECKPOINT — CASA PRÁTICA LAB / E2E PAGE-TARGET

**Data:** 2026-11-02  
**Projeto:** `adelrib27/blogger-automation1`  
**Status:** **PASS — correção estrutural + E2E fresco validado**

## 1. Escopo e fonte de verdade

Este checkpoint documenta a correção descoberta no teste real do blog novo **Casa Prática Lab**. Ele complementa o checkpoint operacional da rede Blogger existente e o contrato `NEW_BLOG_E2E_CONTRACT_2026-11-02.md`.

Não usar este checkpoint para migrar em massa os 18 blogs legados. A rede existente continua com a arquitetura inventariada no estado atual do `main`.

## 2. Blog validado

- Título: `Casa Prática Lab`
- Blog ID: `8930870316690519385`
- URL: `https://casa-pratica-lab-20261102.blogspot.com/`
- Page LOJA ID: `7110845449177208439`
- Page pública: `https://casa-pratica-lab-20261102.blogspot.com/p/loja.html`
- Store Post staging ID: `7691087355641688975`
- Shopee AppID esperado: `18352820579`
- Store Post staging final: **DRAFT**
- Posts editoriais LIVE finais: **3**

## 3. Defeito real encontrado

O E2E anterior estava tecnicamente verde, mas validava a superfície errada para um blog criado do zero:

1. o menu `LOJA` apontava para `/p/loja.html`;
2. o motor moderno escrevia Store 20 + Hero 12 no Post técnico `/2026/11/loja.html`;
3. a auditoria verificava somente esse Post técnico;
4. `/p/loja.html` podia permanecer vazia;
5. o Post técnico `Loja` aparecia na home editorial e podia virar o destaque principal;
6. os três artigos iniciais haviam sido criados sem imagem, gerando cards vazios.

Portanto, `Store Post 20+12 PASS` isoladamente não é mais definição suficiente de E2E para **blog novo**.

## 4. Correção arquitetural

Para o caminho **novo blog zero → produção**:

- a superfície pública final da loja é a **Page `/p/loja.html`**;
- a Page recebe Store 20 + Hero 12;
- `BLOGGER_STORE_AUTO_START/END` são preservados;
- o Store Post técnico permanece apenas como staging e termina em **DRAFT**;
- o writer consegue localizar/atualizar o staging pelo ID mesmo em DRAFT;
- o staging não pode aparecer na home;
- a home deve conter os artigos editoriais reais;
- artigos usados pela home devem possuir imagem;
- persistência da rotação só ocorre depois do PASS público completo.

A arquitetura dos 18 blogs legados não foi alterada por esta correção.

## 5. Arquivos permanentes

### Contrato
- `NEW_BLOG_E2E_CONTRACT_2026-11-02.md`

### Adapter genérico de blog novo
- `blogger_stores/src/blogger_new_blog_store_page_target.py`
- lê staging por ID em LIVE/DRAFT/SCHEDULED;
- sincroniza `pages.update`;
- reverte staging para DRAFT;
- valida Page 20+12 e marcadores V20.

### Motor Page-target do Lab
- `blogger_stores/src/casa_pratica_lab_store_page.py`
- leitura, escrita e verificação compatíveis com staging DRAFT;
- reaproveita semântica/seleção/renderização validada do motor do Lab;
- não altera o motor genérico dos 18 blogs.

### Aceitação pública
- `blogger_stores/src/casa_pratica_lab_public_acceptance.py`
- retry controlado para 429/5xx;
- Page 20+12 + Policy Guard + markers;
- home sem Store Post técnico;
- três artigos presentes;
- três artigos com `post-hero`.

### Writer canônico
- `.github/workflows/casa_pratica_lab_store_page_autonomous.yml`
- `workflow_dispatch + schedule`;
- cron `20 10 * * *`;
- timezone `America/Recife`;
- sem `push`;
- concurrency `casa-pratica-lab-store-live`;
- persistência somente pós-PASS.

### Writer antigo
- `.github/workflows/casa_pratica_lab_store_autonomous.yml`
- recovery-only;
- sem `schedule`;
- sem `push`;
- sem escrita automática.

### Auditor permanente
- `.github/workflows/casa_pratica_lab_acceptance_audit.yml`

## 6. Migração real da superfície pública

Run de migração final:

- run: `41482829050`
- job: `125405339216`
- resultado: **SUCCESS**

Provas principais:

- staging DRAFT legível e atualizável;
- Page sync 20+12 PASS;
- Store Post staging DRAFT PASS;
- Page pública HTTP 200;
- `store=20`;
- `hero=12`;
- Store técnico ausente da home;
- `3/3` artigos com imagem.

Os workflows temporários de migração foram removidos depois do PASS.

## 7. Auditoria permanente

Run:

- `41483351173`
- conclusão: **SUCCESS**

O verificador público demonstrou retry real de 429 e terminou com:

- Page 20+12 PASS;
- Policy Guard público PASS;
- home editorial PASS;
- 3/3 artigos com imagem PASS;
- `CASA_PRATICA_LAB_PUBLIC_E2E_PASS`.

## 8. E2E fresco com nova coleta Shopee

Para provar que a correção não dependia da seleção antiga, foi executado um ciclo completo novo usando a API Shopee e o AppID esperado.

Run:

- `41483681540`
- job: `125408303213`
- conclusão: **SUCCESS**

SAFE fresco:

- regressão semântica: **40/40**;
- 20 produtos;
- 20 intenções;
- 5 categorias;
- links: **20/20**;
- Policy Guard: **20/20**;
- fallback: **0**;
- carry: **0**.

Dry-runs:

- identidade DRAFT PASS;
- Store 20 PASS;
- Hero 12 PASS;
- gate combinado 32 links PASS;
- Page-target dry-run PASS.

LIVE Page-target:

- 20 produtos gravados no staging e relidos;
- 12 hero gravados e relidos;
- identidade gravada e relida;
- `/p/loja.html` sincronizada;
- marcadores V20 preservados;
- staging retornou a DRAFT;
- Page verificada 20+12.

Aceitação pública do ciclo fresco:

- Page HTTP 200 na primeira tentativa;
- home: `429 → 429 → 200`;
- artigo organização: 200;
- artigo air fryer: `429` repetido e depois 200 na tentativa 7;
- artigo ventilador/climatizador: 200;
- staging ausente da home;
- 3/3 artigos presentes e com imagem;
- `CASA_PRATICA_LAB_PUBLIC_E2E_PASS`.

Persistência:

- executada somente depois do PASS público;
- commit: `c0de5cfc7c9d30e9436198e2b993fd77000136b1`;
- mensagem: `Validar E2E fresco Page-target Casa Prática Lab`.

Artifact:

- ID: `13161655621`
- SHA-256: `cb032fc7ea27299a94fa331b1e746ba985bdaaae7de9fc70346589b95d7b41ae`

O workflow temporário usado para esta prova fresca foi removido depois do SUCCESS.

## 9. Estado vivo final esperado

### Posts LIVE
Somente os três artigos editoriais:

1. `7732798999877296654` — Como organizar uma cozinha pequena sem gastar muito
2. `5391626968548073797` — Air fryer: 7 pontos para conferir antes de comprar
3. `1671345332688351619` — Ventilador ou climatizador: qual faz mais sentido para cada ambiente?

### Draft técnico

- `7691087355641688975` — Loja

### Page LOJA

- `7110845449177208439` — LIVE
- 20 produtos
- 12 hero
- 5 categorias
- affiliate disclosure
- `nofollow sponsored noopener`
- marcadores V20 preservados

## 10. Proteção para próximos blogs novos

Um blog novo não pode mais ser declarado 100% E2E apenas porque um Store Post técnico passou.

Definition of Done obrigatória:

1. Blog ID/URL corretos;
2. settings/SEO/timezone;
3. tema V20;
4. seis páginas;
5. conteúdo editorial inicial com imagens;
6. SAFE Shopee 20/20;
7. Policy Guard pré-LIVE;
8. Store 20 + Hero 12 em memória;
9. Page `/p/loja.html` pública 20+12;
10. staging DRAFT e fora da home;
11. home editorial correta;
12. 3/3 imagens editoriais ou equivalente definido para o novo blog;
13. persistência só pós-PASS;
14. writer automático único;
15. schedule só após aceitação;
16. auditor permanente Page + home + conteúdo;
17. checkpoint/backup atualizado.

## 11. Rede legada preservada

No estado atual do repositório durante esta correção:

- rede de produção: **18 blogs**;
- modernos + Policy Guard: **15**;
- scaffolds restantes: **3**;
- riscos de writer duplicado: **0**;
- Casa Prática Lab continua isolado e não foi inserido no rollout dos 18.

## 12. Regra de retomada

Ao retomar Casa Prática Lab ou criar outro blog do zero:

1. ler `NEW_BLOG_E2E_CONTRACT_2026-11-02.md`;
2. ler este checkpoint;
3. não aplicar automaticamente a arquitetura legada Page+Store Post LIVE ao blog novo;
4. validar a superfície que o usuário realmente abre;
5. validar a home, não apenas a Store técnica;
6. validar imagens editoriais;
7. manter fail-closed;
8. não expor secrets;
9. não alterar os 18 blogs legados por associação.

**CASA PRÁTICA LAB PAGE-TARGET E2E: PASS**
