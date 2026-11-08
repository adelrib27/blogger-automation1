# Checkpoint operacional V31 — 2026-11-08

> **Ordem obrigatória de confiança:** estado real ao vivo > arquitetura V31 R52 validada > backup/checkpoint mais recente > histórico. Este documento orienta próximas execuções; **não autoriza escrita** nem atesta estados futuros. Executar em fail-closed, com preflight, readback e verificação pública.

## Fluxo oficial de criação integral de novos blogs V31 (norma a partir de 08/11/2026)

> **Premissas operacionais determinadas pelo usuário:** Python de automação **já validado** na arquitetura do projeto; portanto, **não adicionar uma etapa separada para revalidar o Python** a cada replicação. **Não inserir uma etapa de backup no fluxo de criação**. O Tema V31 é responsável por gerar a identidade visual própria do novo blog. A identidade textual e institucional é definida **durante a criação das páginas institucionais**. A organização editorial usa **clusters de conteúdo, tópicos-pilar, SEO e autoridade temática**, com qualidade editorial antes da quantidade. A validação SAFE por blog, a conferência de estado real, os latches e o fail-closed **continuam obrigatórios**; Python validado como componente não significa que a criação de um blog novo foi validada sem testes.

1. **Planejamento do novo blog:** definir nicho, nome, endereço Blogspot, público-alvo, categorias e objetivos comerciais/editoriais.
2. **Criação automática pelo Python:** criar o blog no Blogger, confirmar Blog ID, URL e configurações iniciais; não reaproveitar identificadores de outro blog.
3. **Configurações do Blogger e SEO técnico:** aplicar descrição, idioma, fuso horário, indexação, metadados e demais configurações compatíveis, validando o resultado no blog correto.
4. **Instalação do Tema V31 pelo Python:** instalar o tema universal validado para a replicação, responsável pela identidade visual automática — cores, layout, cabeçalho, rodapé e componentes. Não copiar cores/identidade de outro blog nem substituir um tema já funcional sem necessidade.
5. **Criação das páginas institucionais:** criar **Sobre, Contato, Privacidade, Termos, Cookies, Transparência/Afiliados** e demais páginas previstas, com texto profissional, identidade do nicho e SEO. A identidade das páginas é trabalhada **aqui**, e não como etapa visual separada. Formulário, quando previsto, precisa de destino e página de retorno próprios, além de testes de envio.
6. **Criação de três artigos iniciais com produtos da API Shopee:** produzir e publicar exatamente **3 artigos originais, úteis e alinhados ao nicho**, usando produtos consultados na **API de afiliados da própria conta**, fotos originais `imageUrl` de anúncios correspondentes, links afiliados reais `offerLink`, divulgação transparente de comissões e SEO editorial básico (título, headings, imagem destacada, `alt`, descrição e intenção de busca). Verificar API/readback e publicação pública dos três posts, com imagens realmente visíveis. Não inventar preços, avaliações ou experiência de uso. **Esta etapa é anterior à Loja Shopee**; ao criar a Loja na etapa 7, conectar contextualmente os artigos à vitrine sem links quebrados. Estes são conteúdos comerciais iniciais, não substituem o planejamento posterior de pilares e clusters.
7. **Configuração da Loja Shopee:** integrar produtos reais da API, links de afiliado, categorias, carrossel e vitrine segundo contrato V31; não inventar preços, fotos ou links. Implantar guardas de blog/página e faixa com **hora da última atualização real**.
8. **Planejamento da arquitetura editorial:** definir categorias, intenção de busca, palavras-chave estratégicas, mapeamento de consultas e **clusters tópico-pilar**, evitando canibalização e repetição artificial.
9. **Produção dos conteúdos-pilar:** publicar guias centrais abrangentes, úteis, naturais, profissionais, originais e aprofundados, que organizem e respondam aos principais temas do nicho.
10. **Produção dos conteúdos de apoio (clusters):** criar artigos específicos que resolvam dúvidas e subtópicos dos pilares, complementem a cobertura e evitem preenchimento artificial.
11. **SEO On-Page e links internos:** otimizar títulos, URLs, headings, descrições de busca, imagens (origem, alt e miniatura), contexto, navegação e links internos relevantes. Cada pilar aponta para apoios; apoios retornam ao pilar e se interligam quando útil. Distribuir autoridade interna com critério, sem excesso ou links forçados.
12. **Estratégia de backlinks e autoridade:** planejar aquisição legítima de links editoriais por conteúdos citáveis, divulgação e parcerias pertinentes; **não automatizar backlinks artificiais** nem garantir links que terceiros ainda não criaram.
13. **Configuração da automação editorial:** integrar o Python validado, GitHub Actions e serviços necessários, com publicação, atualização da Loja, controle de duplicidade, isolamento por Blog ID, logs e validações SAFE; não afetar automações de outros blogs.
14. **Validação pública do blog:** conferir computador e celular, identidade do tema, páginas, contato, posts e **imagens realmente visíveis**, navegação, links internos/externos, Loja, SEO e primeiras execuções da automação; distinguir teste local, API, validação pública e teste E2E.
15. **Ativação e finalização:** após aprovação dos testes, ativar a operação, confirmar publicações reais, registrar configurações, URLs, IDs e evidências de que o blog funciona. Evitar declarar conclusão antes de comprovação.

### Padrão editorial, clusters e autoridade temática

**Exemplo (casa e decoração):** conteúdo-pilar **“Guia completo de organização de cozinhas pequenas”** conectado contextualmente aos clusters **“Como organizar armários de cozinha”**, **“Organizadores para gavetas pequenas”**, **“Aproveitamento do espaço vertical”** e **“Como organizar temperos e utensílios”**. O pilar apresenta e aponta os subtópicos; cada cluster retorna ao pilar, e clusters relacionados se conectam somente quando a leitura e a intenção de busca justificarem. Categorias e Loja são caminhos complementares, não motivo para inserir links desnecessários.

**Qualidade obrigatória:** informação útil, português brasileiro natural, leitura agradável, coerência temática, experiência prática quando houver evidência, SEO sem exagero, respostas completas, imagens originais de produto quando provenientes da API e links para fontes confiáveis quando necessários. **Não gerar textos em massa apenas para preencher o blog**; não inventar experiência de uso, testes, números, avaliações ou preços. Backlinks de terceiros são conquistados editorialmente ao longo do tempo, não resultados garantidos pelo Python.

**Regra de aplicação em próximas conversas:** consultar este arquivo versionado como norma da **ordem de criação V31**, depois conferir estado real e implementação atual antes de qualquer operação. Os contratos técnicos abaixo são verificações transversais e **não acrescentam etapas de backup ou validação inicial do Python à sequência oficial**.

## Referência real em 08/11/2026

- **Achados da Rotina:** Blogger ID `1637047917126642592`, URL `https://achados-da-rotina.blogspot.com/`, 3 posts LIVE, 7 páginas LIVE. Tema V31 R52 preservado; **não reinstalar** ao acrescentar conteúdo. Conteúdo validado por Blogger Bridge V2.
- **Página LOJA:** ID `8438575521830059724`, URL `/p/loja.html`, 16 cards únicos, 16 imagens e 16 links afiliados. Categorias: Casa e Organização, Cozinha, Tecnologia, Utilidades, 4 itens por categoria. Última leitura: banner `08/11/2026 às 00:29` (Recife), que representa a hora da última seleção, não atualização contínua.
- **Artigos:** Casa pequena organizada ID `6994155220056125656` (3 imagens), Cozinha funcional ID `5547064190852780400` (4 imagens), Home office ID `2774003915372214345` (4 imagens). 11 imagens HTML de produtos Shopee com alt e links afiliados. **Renderização das miniaturas não comprovada visualmente em navegador após refresh**.
- **Páginas:** LOJA `8438575521830059724`, Contato `1458007355190523475`, Mensagem enviada `2278921880876551168`, Aviso de Afiliados `2388749202664823255`, Termos de Uso `2061927278454118763`, Política de Privacidade `2904089566017165621`, Sobre `4028274752678139956`. Contato com FormSubmit e `_next`, mas teste E2E específico desse blog ainda pendente.
- **Casa Leve e Funcional:** ID `4739187376492839837`, `https://casa-leve-e-funcional.blogspot.com/`; renomeação manual preservou ID. Contato FormSubmit + `_next` funcionou em teste real relatado pelo usuário. **Não assumir a mesma validação em outros blogs.** Correção da renomeação automática pelo Runner ainda pendente.
- **Repo:** `adelrib27/blogger-automation1` (`main`). Ler HEAD vivo antes de editar: em 08/11 o HEAD observado era `d852689f8dd961ef8bae27227823bff4da72df43`. Não sobrescrever trabalho paralelo.

## Controles técnicos por etapa (apenas critérios de passagem, NUNCA outro fluxo)

**Regra de precedência:** este bloco é uma matriz de verificação e NÃO uma sequência adicional, paralela ou alternativa. As **15 etapas** acima são a única ordem oficial. Nenhum executor deve inferir uma sequência diferente ao ler itens deste checkpoint, um workflow, o histórico ou uma ferramenta. Se a etapa anterior não estiver concluída e validada no blog-alvo, interromper a criação (**STOP fail-closed**), registrar a pendência e retomar exatamente do ponto correto. As correções e travas são incorporadas **dentro da etapa correspondente**, sem reordenar fases.

| Etapa oficial | Gate técnico obrigatório para liberar a próxima etapa |
| --- | --- |
| **1. Planejamento** | Nicho, nome, slug Blogspot, categorias, público-alvo e objetivos definidos; sem reutilizar identidade específica de outro blog. |
| **2. Criação pelo Python** | Usar Runner validado, validar nome e endereço disponíveis, criar uma vez, obter Blog ID real e URL, confirmar identidade em leitura independente e resposta pública. Não usar o provisionamento V20 como fallback. |
| **3. Configurações Blogger e SEO técnico** | **Imediatamente depois da criação e obrigatoriamente antes da instalação do tema.** Aplicar descrição, descrição de pesquisa, visibilidade/indexação, HTTPS, idioma/fuso e configurações compatíveis pelo Runner; confirmar o estado persistido por leitura de retorno. Não pular para o Tema V31. |
| **4. Instalação do Tema V31** | Só depois do PASS da etapa 3. Usar o mecanismo oficial V31 do Runner, Blog ID autorizado, XML/template e identidade automática do nicho. Verificar o tema aplicado e o HTML público, sem bypass de allowlist/latch nem instalação V20. Se a rota V31 não estiver exposta, pausar **nesta etapa**, sem criar páginas, três artigos Shopee, Loja ou conteúdos por antecipação. |
| **5. Páginas institucionais** | Só depois do PASS da etapa 4. Criar e adaptar Sobre, Contato, Privacidade, Termos, Cookies, Transparência/Afiliados e demais páginas ao nicho; identidade editorial das páginas construída aqui. Verificar publicação, links, formulário e `_next`. Não confundir criação com teste real de recebimento. **A página Loja pertence à etapa 7, após os três artigos da etapa 6, não à 5.** |
| **6. Três artigos Shopee iniciais** | Só depois do PASS da etapa 5. Consultar a API Shopee autenticada, produzir **3 artigos** originais do nicho com imagens dos anúncios (`imageUrl`), links afiliados reais (`offerLink`), disclaimer e SEO básico; confirmar **3 posts LIVE**, imagens carregadas e vínculos corretos. Não misturar com os conteúdos-pilar e clusters das etapas 9 e 10. Quando a Loja for criada na etapa 7, adicionar links internos contextuais sem antecipar URLs inexistentes. |
| **7. Loja Shopee** | Só depois do PASS da etapa 5. Produtos genuínos da API, domínios permitidos, categorias, imagens `imageUrl`, links `offerLink`, preços de referência, disclaimer, carrossel/vitrine conforme o contrato V31. Confirmar HTML/categorias/produtos e região rotativa. |
| **8. Planejamento editorial** | Planejar tópicos-pilar, clusters, intenção de busca, palavras-chave, categorias e evitar canibalização. Não publicar artigos de apoio sem o mapa editorial. |
| **9. Conteúdos-pilar** | Artigos centrais completos, naturais, úteis, específicos do nicho, com imagens verdadeiras quando provenientes de produtos da API. Verificar título, URL, tags HTML e legibilidade; não criar texto genérico em massa. |
| **10. Conteúdos de apoio** | Cada cluster responde a uma busca/subtema, complementa o pilar e não replica passagens desnecessárias. |
| **11. SEO On-Page e interlinking** | Otimizar metadados, headings, alt/thumbnail real, URLs, links contextuais do pilar aos clusters e dos clusters ao pilar. Nenhum link artificial ou densidade forçada. |
| **12. Autoridade/backlinks** | Estratégia de divulgação e conteúdos citáveis, apenas backlinks legítimos; não fabricar ou prometer backlinks via Python. |
| **13. Automação** | GitHub Actions/Python isolados por **Blog ID e Page ID**, controle de duplicidade, latches, guardas, comparação antes de escrever e SAFE antes de LIVE. Rotação **diária** quando esse for o requisito do novo blog; não copiar cron de 20 minutos do LAB Achados da Rotina. |
| **14. Validação pública** | Desktop e celular; identidade V31, páginas, formulário, Loja, imagens visualmente carregadas, links, SEO e execução da automação. API readback não substitui validação pública nem teste E2E. |
| **15. Ativação** | Ativar produção apenas após aprovações, confirmar publicação real e URLs, registrar estados e pendências sem declarar o que não foi provado. |

### Invariantes de segurança válidas em todas as etapas

- **Somente estado real atual:** identificar blog, Blog ID, URL, branch HEAD, workflow e arquivos antes de qualquer escrita; preservar trabalho paralelo.
- **Fail-closed sempre:** sem credenciais? Blog ID divergente? Componente anterior não validado? Alteração paralela? **STOP**, sem contornar proteção nem migrar para arquitetura antiga.
- **Contrato Loja Shopee V31:** para a vitrine 4×4 já validada em Achados da Rotina, 16 produtos únicos, 4 categorias, `rel="nofollow sponsored noopener"`, `imageUrl` e `offerLink` autorizados. Respeitar os marcadores `<!-- UNIVERSAL_V31_STORE_AUTO_START -->` / `<!-- UNIVERSAL_V31_STORE_AUTO_END -->`, `adr-store-v31-css`, `ub-store-status`, `ub-product-card`. Para outros nichos, adaptar categorias/seleção sem copiar cegamente IDs ou conteúdo.
- **Validação de rotação:** preservar HTML fora da região rotativa, ler e comparar novamente o conteúdo e ETag antes de escrever; depois exigir retorno exato pela API, HTTP público 200, 16 cartões e carimbo da execução, com até 12 tentativas e 8 segundos entre elas para CDN. **Se API confirma e público ainda não confirma, existe escrita; investigar antes de repetir.** O teste de 20 minutos de Achados da Rotina é diagnóstico específico daquele blog e não determina o cron do novo blog.
- **Conteúdo editorial:** imagem destacada no início dos artigos e imagens contextuais Shopee quando usadas, alt, links reais, disclosure, prévia/validação visual de thumbnails. SEO por autoridade temática, não preenchimento automático.
- **Continuidade:** documentação/checkpoints guardam evidências, mas **não são etapa de backup da criação** nem autorizam modificações automaticamente. Registrar SAFE, LAB, API, público e E2E com distinção precisa.

## Provas e versões de código

- PR #9 (rotação), #10 (banner real), #11 (revalidação pública tolerante a cache mas rígida).
- Run `42442575493`: escrita API ocorreu, verificação HTTP falhou no prazo antigo; NÃO declarar PASS.
- Run `42442871710`: `SELF_TEST_PASS`, `PUBLIC_VERIFY_PASS`, `LIVE_API_AND_PUBLIC_PASS`, 16 produtos com `changed_ids=16`; Blogger Bridge confirmou 3 posts/7 páginas.
- Backup mestre curado de **07/11/2026** e backup operacional Windows de **07/11/2026** continuam históricos. O **checkpoint incremental de 08/11/2026** é uma camada de continuidade, não substituição do backup completo. Registrar código e configuração presente novamente no início da próxima execução.

## Pendências não validadas

- Ver as fotos Shopee realmente renderizadas nos cartões e miniaturas da homepage em navegador após atualização.
- Testar envio/recebimento/retorno FormSubmit no Achados da Rotina; no Casa Leve o usuário confirmou o teste.
- Observar três ciclos `schedule` válidos; só então propor/mudar para atualização diária.
- Corrigir automação de renomeação do Runner em LAB, sem arriscar blogs existentes.

**Segurança:** não publicar tokens, AppID/Secret, refresh tokens, cookies, e-mails privados ou sessões Chrome em documentos, logs, artefatos ou commits. Nunca confundir um checkpoint com estado real em produção.