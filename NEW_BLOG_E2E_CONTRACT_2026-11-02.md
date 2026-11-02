# CONTRATO E2E — BLOG NOVO BLOGGER V20 + LOJA SHOPEE

**Data:** 2026-11-02  
**Escopo:** blogs criados do zero pelo fluxo V20 a partir desta revisão.  
**Não altera:** arquitetura dos 18 blogs Blogger legados já inventariados.

## 1. Motivo desta revisão

O teste real com **Casa Prática Lab** revelou um gap que os gates anteriores não detectavam:

- o menu `LOJA` apontava corretamente para `/p/loja.html`;
- a vitrine moderna 20+12 era publicada em um Post técnico `Loja`;
- a auditoria validava somente o Post técnico;
- portanto `/p/loja.html` podia continuar sem produtos enquanto o pipeline declarava PASS;
- o Post técnico `Loja` também aparecia na home editorial e podia dominar o destaque;
- artigos editoriais sem `<img>` passavam pelo fluxo e o tema mostrava áreas vazias nos cards.

Logo, **Store Post 20+12 PASS isoladamente não é mais definição suficiente de E2E para um blog novo**.

## 2. Contrato canônico para blog novo

A superfície pública final da loja é:

```text
/p/loja.html
```

Ela deve conter, depois de cada LIVE aprovado:

- 20 produtos reais;
- 12 mini-cards de hero;
- 5 categorias específicas do blog;
- Policy Guard pré-LIVE e no HTML público;
- disclosure de afiliado;
- links `rel="nofollow sponsored noopener"`;
- imagens de origem aprovada;
- marcadores V20 `BLOGGER_STORE_AUTO_START/END` preservados;
- HTTP público 200, com retry controlado para 429;
- persistência de rotação somente depois do PASS público.

## 3. Store Post técnico

Quando o motor herdado 20+12 precisar de um Post para staging:

- o ID deve ser fixo e validado antes de qualquer escrita;
- ele pode receber Store/hero/identidade em staging;
- a Page LOJA é sincronizada somente depois dos dry-runs e gates;
- depois da sincronização, o Store Post técnico deve terminar em **DRAFT**;
- ele não pode aparecer na home pública;
- o writer deve conseguir localizar e atualizar o staging por ID mesmo em DRAFT;
- nenhuma execução pode criar um segundo Store Post por não encontrar o staging.

## 4. Home editorial

A aceitação E2E exige:

- Store Post técnico ausente da home;
- posts editoriais reais presentes;
- cada post editorial usado pela home deve possuir imagem válida;
- o sistema não pode declarar PASS apenas porque a URL técnica da Store responde 200.

## 5. Writer único

Para cada blog novo:

- exatamente um writer automático canônico;
- `workflow_dispatch + schedule` somente depois da validação completa;
- writer anterior/experimental deve ficar recovery-only, sem `schedule` e sem `push`;
- concurrency compartilhada quando houver artefato legado de recuperação;
- risco de writer duplicado deve ser zero.

## 6. Fail-closed

Falhar sem publicar/sincronizar estado incompleto quando houver:

- erro Shopee;
- produto semanticamente inválido;
- quantidade abaixo de 20;
- hero abaixo de 12;
- link ou imagem inválidos;
- marcadores ausentes;
- Blog ID, Page ID ou staging Post ID divergentes;
- falha de Policy Guard;
- Page pública sem 20+12;
- home contendo Store Post técnico;
- persistência ocorrendo antes da validação pública.

A versão pública anterior deve ser preservada sempre que a nova execução não passar todos os gates.

## 7. Separação da rede existente

Os **18 blogs legados** continuam sob o contrato inventariado em `NETWORK_STORE_INVENTORY_2026-11-02.json`, onde Page e Store Post LIVE já são objetos existentes que não devem ser recriados ou migrados em massa por causa deste laboratório.

Esta revisão vale para o caminho **novo blog zero → produção**, comprovado no Casa Prática Lab, e deve ser incorporada ao provisionamento/clonagem futura sem alterar automaticamente a rede legada.

## 8. Definition of Done de blog novo

Um blog novo só pode ser chamado de 100% ponta a ponta quando todos os itens abaixo passarem:

1. criação segura + Blog ID guard;
2. settings/SEO/timezone;
3. TEMA V20;
4. seis páginas, incluindo LOJA;
5. conteúdo editorial inicial com imagens;
6. SAFE Shopee 20/20 com perfil semântico próprio;
7. Policy Guard pré-LIVE;
8. Store 20 + hero 12 em memória;
9. Page `/p/loja.html` sincronizada e publicamente 20+12;
10. Store Post staging em DRAFT e ausente da home;
11. home com artigos editoriais e imagens;
12. persistência só depois do PASS público;
13. writer automático único;
14. schedule habilitado somente após aceitação;
15. auditor permanente cobrindo Page + home + conteúdo editorial;
16. checkpoint/backup atualizado.

## 9. Referência do laboratório

Casa Prática Lab:

- Blog ID: `8930870316690519385`
- Page LOJA ID: `7110845449177208439`
- Store Post staging ID: `7691087355641688975`
- Page: `https://casa-pratica-lab-20261102.blogspot.com/p/loja.html`
- Shopee AppID esperado: `18352820579`
- writer Page-target: `.github/workflows/casa_pratica_lab_store_page_autonomous.yml`
- adapter genérico: `blogger_stores/src/blogger_new_blog_store_page_target.py`
- wrapper staging: `blogger_stores/src/casa_pratica_lab_store_page.py`
- auditor: `.github/workflows/casa_pratica_lab_acceptance_audit.yml`

**Segredos não pertencem a este documento.**
