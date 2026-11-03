# CHECKPOINT — VIDA PET PRÁTICA — PRIMEIRO NOVO BLOG V20 E2E DE PRODUÇÃO

**Data operacional:** 2026-11-02 / fechamento técnico 2026-11-03 UTC  
**Projeto:** Blogger Automation — Sistema Mestre V20  
**Status:** `BLOGGER_NEW_BLOG_V20_E2E_ACCEPTED`  
**Escopo:** primeiro novo blog criado após o fechamento da rede legada 18/18, usando o contrato Page-target derivado do Casa Prática Lab.

## 1. Identidade e alvo

- Título: **Vida Pet Prática**
- Nicho: acessórios e rotina para cães e gatos, sem saúde/veterinária
- Blog ID: `8052455848487624244`
- URL: `https://vida-pet-pratica.blogspot.com/`
- Tema: TEMA MODELO V20
- Paleta: `teal`
- Page LOJA ID: `8624646966938350648`
- Page pública: `https://vida-pet-pratica.blogspot.com/p/loja.html`
- Store Post técnico staging ID: `7332800716046515902`
- staging final: **DRAFT**

O Blogger account possui agora **20 blogs** visíveis pela Bridge: 18 legados + Casa Prática Lab + Vida Pet Prática. O inventário legado permanece 18/18 e não foi alterado para absorver o novo blog.

## 2. Provisionamento V20

Validado no mesmo Blog ID:

- criação segura após preflight;
- URL pública validada na criação;
- settings/SEO aplicados;
- pesquisa ON;
- HTTPS redirect ON;
- lazy images ON;
- WebP ON;
- descrição de pesquisa ON;
- fuso GMT-03 / São Paulo;
- custom robots preservados;
- Tema Modelo V20 adotado com backup anterior;
- runtime guard V20 PASS;
- seis Pages LIVE, incluindo LOJA.

Pages:

1. Sobre — `6878993879704389957`
2. Aviso de Afiliados — `1350430457856034588`
3. Contato — `4143410372380721715`
4. Política de Privacidade — `8710919907791050900`
5. Termos de Uso — `4334921069046302045`
6. LOJA — `8624646966938350648`

A primeira tentativa de criar a Page LOJA recebeu HTTP 429. O sistema não presumiu sucesso, releu o estado, confirmou ausência do objeto e só então repetiu a criação com nova operação. Nenhuma Page duplicada foi criada.

## 3. Editorial inicial

Três artigos editoriais próprios foram criados primeiro como DRAFT, relidos pela Bridge e somente depois publicados. Todos possuem imagem válida e crédito de fonte:

1. `6872395270807124041` — Como escolher peitoral e guia para passeios mais confortáveis com seu cão
2. `2711795987490959590` — Enriquecimento ambiental para gatos: ideias simples para uma rotina mais interessante
3. `9175269088286950605` — Como montar um cantinho confortável para o pet em casa

A leitura final de posts LIVE confirma os três editoriais e ausência do Store Post técnico.

## 4. Perfil Shopee isolado

Config:

- `config/shopee_vida_pet_pratica.json`
- `config/shopee_vida_pet_pratica_intent_rules.json`

Motor:

- `blogger_stores/src/vida_pet_pratica_store.py`
- `blogger_stores/src/vida_pet_pratica_store_page.py`

Estado independente:

- `blogger_stores/data/vida_pet_pratica_selection.json`
- `blogger_stores/data/vida_pet_pratica_rotation.json`

Contrato semântico: **5 categorias × 4 intenções = 20 intenções**.

Categorias:

1. Passeio & Transporte
2. Alimentação & Rotina
3. Higiene & Organização
4. Conforto & Descanso
5. Brinquedos & Enriquecimento

O motor possui exclusões adicionais para medicamentos, suplementos, antipulgas/carrapatos, dispositivos de saúde/veterinária, claims clínicos e coleiras de choque, além do Blogger Policy Guard global.

## 5. SAFE e revisão independente

### SAFE #1

- run `41556913057` — SUCCESS técnico
- regressão semântica 42/42
- 20/20 produtos únicos
- Policy Guard 20/20
- nenhum writer Blogger executado

**Não promovido.** A revisão independente encontrou dois falsos positivos:

- `cama gato` havia selecionado um arranhador/protetor que apenas continha a palavra `cama`;
- `bola interativa pet` trazia claim `anti ansiedade` e semântica de lambedor/alimentador.

As regras foram endurecidas no commit `9bf245911260aa445f49da1b5dc79e3696bea30e` e o SAFE foi repetido do zero.

### SAFE #2

- run `41557355556` — SUCCESS
- nova seleção 20/20
- revisão independente dos 20 itens PASS
- falsos positivos anteriores eliminados

Regra consolidada: **Action SAFE verde é necessária, mas não suficiente para o primeiro LIVE de um novo nicho.**

## 6. LIVE controlado — falhas que evoluíram a arquitetura

### Tentativa 1

- run `41557781747`
- falhou antes de qualquer escrita pública
- causa: `sync-dry-run` da Page foi chamado quando o staging novo ainda estava 0+0
- Page pública, rotação e persistência ficaram intocadas

Aprendizado: a primeira publicação precisa preencher o staging DRAFT 20+12 antes do dry-run da Page futura.

### Tentativa 2

- run `41558142360`
- SAFE + dry-runs passaram
- staging foi preparado corretamente como DRAFT 20+12
- `sync-dry-run` da Page futura PASS
- falhou antes do `sync-live`
- causa: um segundo dry-run de share card tentou validar a Page pública antiga, ainda shell 0+0
- Page pública e persistência ficaram intocadas

Aprendizado: o share da primeira Page já deve ser validado no HTML futuro gerado pelo `sync-dry-run`; depois do `sync-live`, verificar novamente a Page real.

### Tentativa 3 — final

- run `41558454352` — **SUCCESS**
- job `125662983649`
- SAFE fresco PASS
- Policy Guard pré-LIVE PASS
- staging dry-runs PASS
- Store staging 20 PASS
- hero staging 12 PASS
- staging confirmado DRAFT
- Page futura em memória PASS
- Page `/p/loja.html` sincronizada
- Page relida por ID/URL
- share/carousel PASS
- aceitação pública Page + home + artigos PASS
- rotação persistida **somente depois** do PASS público

## 7. Estado público final

Leitura independente posterior pela Blogger Bridge confirmou a Page LOJA com:

- 20 `data-item-id`;
- 12 `data-hero-item-id`;
- cinco categorias pet;
- disclosure afiliado;
- links com `rel="nofollow sponsored noopener"`;
- Page surface fix;
- carousel delegado;
- share card;
- identidade Vida Pet Prática;
- ausência de identidade de outro blog.

Store Post técnico:

- ID `7332800716046515902`;
- status DRAFT;
- 20 Store + 12 hero;
- não aparece entre os posts LIVE.

Home:

- staging técnico ausente;
- três artigos editoriais presentes;
- artigos com imagens.

## 8. Writer final e schedule

Writer:

`.github/workflows/vida_pet_pratica_store_page_autonomous.yml`

Estado final:

- `workflow_dispatch` mantido;
- schedule `35 11 * * *`;
- timezone `America/Recife`;
- horário lógico do projeto: **11:35**;
- nenhum gatilho `push`;
- concurrency `vida-pet-pratica-store-live`;
- persistência continua depois da aceitação pública;
- writer automático único para o blog.

O horário foi colocado depois do auditor central das 11:20 e depois do último writer legado das 11:05, evitando colisão deliberada.

## 9. Auditor permanente e Policy Guard central

Auditor permanente:

`.github/workflows/vida_pet_pratica_acceptance_audit.yml`

- schedule `50 11 * * *`;
- timezone `America/Recife`;
- `contents: read`;
- push limitado a arquivos críticos, apenas para auditoria;
- nenhuma capacidade de escrita no Blogger/repositório;
- valida Page ID + URL + contrato 20+12;
- valida staging DRAFT;
- valida artigos editoriais LIVE;
- valida superfície pública Page + home + imagens.

Run final do auditor permanente:

- run `41559416203`
- job `125666130330`
- conclusão **SUCCESS**

Auditoria central de políticas:

- workflow `.github/workflows/blogger_policy_repo_audit.yml`
- rede legada 18/18 continua auditada separadamente;
- nova arquitetura Page-target possui auditor dedicado `src/blogger_new_blog_policy_repo_audit.py`;
- run `41559416511`
- job `125666131838`
- conclusão **SUCCESS**

## 10. Contrato genérico evoluído

`NEW_BLOG_E2E_CONTRACT_2026-11-02.md` foi atualizado após esta implantação para incorporar:

- sequência especial da primeira publicação;
- staging DRAFT 20+12 antes do Page dry-run;
- share card validado no HTML futuro e novamente no público;
- revisão semântica independente após SAFE inicial;
- diferença de metadados entre Blogger Pages e Posts na API;
- schedule somente depois da aceitação completa;
- auditor permanente read-only.

## 11. Gaps ainda conhecidos para a próxima evolução

Estes pontos **não invalidam o Vida Pet Prática**, mas devem ser melhorados antes/durante o próximo blog:

1. a descrição exposta pela tool do Local Runner ainda menciona retorno de 5 páginas, enquanto o código/contrato atual usa 6 incluindo LOJA;
2. `themes/blogger_modelo_v20/pages.json` ainda contém copy genérica com exemplos de nicho anterior em algumas páginas; o próximo avanço deve parametrizar identidade/nicho, em vez de exigir adaptação manual;
3. a sequência de primeira publicação validada neste blog deve virar caminho genérico padrão do provisionador/writer de novos blogs, evitando reproduzir as duas falhas controladas observadas aqui;
4. manter revisão semântica independente na primeira implantação de cada novo nicho até que existam regressões suficientemente maduras para aquele perfil.

## 12. Fechamento

**Vida Pet Prática está aceito como primeiro novo blog V20 E2E de produção após o laboratório.**

Marcador canônico:

`BLOGGER_NEW_BLOG_V20_E2E_ACCEPTED: Vida Pet Prática`

A próxima criação deve reutilizar esta engenharia validada, adaptar identidade/nicho, executar SAFE e procurar novos gaps sem regredir o contrato já comprovado.
