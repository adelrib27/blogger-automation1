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
16. checkpoint/backup atualizado;
17. enquadramento visual do Tema V20 preservado na Page LOJA;
18. identidade textual e visual específica do próprio blog, sem copy herdada de outro nicho.

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

## 10. Sequência obrigatória da primeira publicação — validada no Vida Pet Prática

O primeiro LIVE de um blog novo é diferente de uma atualização de uma loja já madura. O staging recém-criado pode começar com **0 Store + 0 hero**. Portanto, o fluxo canônico da primeira publicação é:

```text
SAFE fresco 20/20
→ Policy Guard pré-LIVE
→ dry-runs de identidade / Store / hero no staging
→ gravar Store 20 no Store Post técnico ainda DRAFT
→ gravar hero 12 no mesmo staging DRAFT
→ validar identidade e reler staging por ID
→ confirmar explicitamente que staging continua DRAFT
→ gerar em memória a Page futura a partir do staging já maduro 20+12
→ validar Page futura, Policy Guard, carousel e share card em memória
→ sincronizar /p/loja.html
→ reler Page por ID e URL canônica
→ confirmar novamente staging DRAFT
→ validação pública Page 20+12 + Policy Guard + carousel/share
→ validar home sem staging + artigos editoriais com imagens
→ persistir rotação somente após todos os PASS
```

Regras derivadas:

- `sync-dry-run` da Page **não deve ser chamado enquanto o staging ainda estiver 0+0**;
- um dry-run separado de share card contra a Page pública antiga não deve bloquear a primeira publicação quando o `sync-dry-run` já validou o HTML futuro com share card injetado;
- depois do primeiro `sync-live`, o share card deve ser verificado novamente na Page real;
- o writer final promovido para schedule deve perder qualquer gatilho `push` usado apenas para kickoff de implantação;
- o auditor permanente pode reagir a `push` de arquivos críticos somente se for estritamente read-only e tiver `contents: read`.

## 11. Revisão semântica independente antes do primeiro LIVE

Action SAFE verde é necessária, mas não suficiente para a primeira implantação de um novo nicho.

Antes do primeiro LIVE:

- inspecionar independentemente os 20 itens selecionados;
- verificar se o título realmente representa a intenção da categoria, não apenas se contém palavras-chave;
- endurecer as regras quando houver falso positivo;
- repetir o SAFE do zero depois da correção;
- somente promover uma seleção nova após nova revisão independente.

No Vida Pet Prática, a primeira seleção SAFE passou tecnicamente, mas a revisão independente encontrou:

- um arranhador/protetor que continha a palavra `cama` e havia sido classificado como `cama gato`;
- uma bola/brinquedo com claim `anti ansiedade` incompatível com o perfil de baixo risco adotado.

As regras foram endurecidas e o SAFE repetido antes de qualquer LIVE. A primeira seleção nunca foi publicada.

## 12. Auditoria de Page pela Blogger API

Pages e Posts não expõem exatamente o mesmo contrato de metadados na Blogger API.

Para uma Page pública, o auditor read-only deve validar pelo menos:

- Page ID esperado;
- URL canônica esperada `/p/loja.html`;
- conteúdo maduro 20+12;
- Policy Guard e contrato visual;
- HTTP público 200 na aceitação pública.

Não exigir `page.status == LIVE` se o endpoint `pages().get()` não fornecer esse campo. Para o Store Post staging, o status **DRAFT** continua sendo obrigatório e deve ser verificado explicitamente.

## 13. Referência de produção E2E — Vida Pet Prática

Vida Pet Prática:

- Blog ID: `8052455848487624244`
- URL: `https://vida-pet-pratica.blogspot.com/`
- Page LOJA ID: `8624646966938350648`
- Page: `https://vida-pet-pratica.blogspot.com/p/loja.html`
- Store Post staging ID: `7332800716046515902`
- três posts editoriais LIVE com imagens;
- 5 categorias × 4 intenções = 20 intenções próprias do nicho pet;
- saúde/veterinária, medicamentos, suplementos e dispositivos de saúde excluídos do perfil;
- SAFE #1 não promovido após revisão independente;
- SAFE endurecido e repetido;
- LIVE controlado final: run `41558454352` — SUCCESS;
- writer final: `.github/workflows/vida_pet_pratica_store_page_autonomous.yml`;
- schedule final: `11:35 America/Recife`;
- auditor permanente: `.github/workflows/vida_pet_pratica_acceptance_audit.yml` às `11:50 America/Recife`;
- auditor central mantém separação explícita entre rede legada 18/18 e nova arquitetura Page-target.

## 14. Contrato visual canônico do Tema V20 — obrigatório em novos blogs

A correção validada primeiro no **Casa Prática Lab** e depois promovida ao **Vida Pet Prática** fixa o padrão visual mostrado pelos blogs V20 já aprovados da rede.

A Page `/p/loja.html` deve usar o **Tema Modelo V20 como moldura visual**, e o Page-target deve cuidar apenas da vitrine dinâmica, carousel, share e sincronização. O adapter não pode substituir o tema por uma superfície própria `clean/full-width`.

Obrigatório:

- preservar o marcador de tema `emporio-revisao-visual-20-modelo-final`;
- preservar fundo decorativo, shell/card e espaçamentos definidos pelo Tema V20;
- preservar a estrutura de header, navegação e rodapé do Tema V20;
- a Store pode ocultar a sidebar somente no escopo necessário à Loja, conforme o contrato do próprio tema;
- a Page sincronizada deve conter `<!-- BLOGGER_NEW_STORE_PAGE_THEME_FRAME_PRESERVED -->`;
- largura, colunas e responsividade da Store devem respeitar o contrato V20, sem redefinir globalmente a superfície da página.

É proibido ao adapter Page-target introduzir novamente regras equivalentes a:

- `.bg-photo-container{display:none!important...}`;
- `.bg-photo{display:none!important...}`;
- neutralização global do card/shell do post com fundo transparente, borda zero e sombra zero;
- remoção do enquadramento do tema apenas para fazer a vitrine ocupar quase toda a viewport.

A presença dessas regras na camada Page-target é **falha de contrato**, mesmo que 20+12 e Policy Guard estejam verdes.

O patch BLS específico da própria vitrine pode continuar controlando sua grade interna e ocultando a sidebar no escopo da Loja; ele não deve ser confundido com a antiga camada Page-target que escondia `.bg-photo-container` e `.bg-photo` do Tema V20.

Qualquer alteração futura deste contrato visual deve passar em **LAB antes de produção**. Nunca promover diretamente uma mudança visual genérica para um novo blog real sem validar primeiro no Casa Prática Lab ou laboratório sucessor explicitamente designado.

## 15. Isolamento obrigatório de identidade e nicho

Reutilizar V20 significa reutilizar **engenharia e estrutura**, nunca textos específicos de outro blog.

Para cada blog novo:

- `BLOG_TITLE` vem do título real do próprio blog;
- a identidade textual institucional deve derivar da **descrição real do próprio blog** já configurada no Blogger;
- a página Sobre não pode conter exemplos fixos como `casa, cozinha, tecnologia e dia a dia` quando o nicho é outro;
- o rodapé deve sincronizar título e descrição do próprio blog, usando a fonte canônica do Blogger, em vez de manter copy fixa do blog-modelo;
- categorias, textos de hero, disclosure contextual, filtros semânticos e paleta devem pertencer ao blog alvo;
- nenhum nome, URL, Page ID, Post ID, categoria, nicho, histórico de rotação ou copy de outro blog pode vazar para o alvo.

O provisionador V20 deve resolver `{{BLOG_TITLE}}` e `{{BLOG_DESCRIPTION}}`, escapar o conteúdo textual e falhar fechado se qualquer token de identidade permanecer sem resolver.

A auditoria deve tratar vazamento de identidade como erro E2E, não como detalhe cosmético.

## 16. Ordem de promoção de mudanças genéricas

Toda mudança que afete tema, Page-target, identidade, layout ou renderer compartilhado deve seguir:

```text
código/configuração
→ testes estáticos/CI
→ Casa Prática Lab (ou LAB sucessor) com backup
→ dry-run
→ publicação LAB controlada
→ auditoria pública LAB
→ somente após PASS: um blog novo de produção
→ auditoria pública de produção
→ tornar migrações recovery-only/manual
→ atualizar contrato/checkpoint
```

Falha em qualquer etapa encerra a promoção sem avançar ao próximo alvo.

**Segredos não pertencem a este documento.**
