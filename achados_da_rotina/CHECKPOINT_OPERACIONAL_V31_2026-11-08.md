# Checkpoint operacional V31 — 2026-11-08

> **Ordem obrigatória de confiança:** estado real ao vivo > arquitetura V31 R52 validada > backup/checkpoint mais recente > histórico. Este documento orienta próximas execuções; **não autoriza escrita** nem atesta estados futuros. Executar em fail-closed, com preflight, readback e verificação pública.

## Fluxo oficial de criação integral de novos blogs V31 (norma a partir de 08/11/2026)

> **Premissas operacionais determinadas pelo usuário:** Python de automação **já validado** na arquitetura do projeto; portanto, **não adicionar uma etapa separada para revalidar o Python** a cada replicação. **Não inserir uma etapa de backup no fluxo de criação**. O Tema V31 é responsável por gerar a identidade visual própria do novo blog. A identidade textual e institucional é definida **durante a criação das páginas institucionais**. A organização editorial usa **clusters de conteúdo, tópicos-pilar, SEO e autoridade temática**, com qualidade editorial antes da quantidade. A validação SAFE por blog, a conferência de estado real, os latches e o fail-closed **continuam obrigatórios**; Python validado como componente não significa que a criação de um blog novo foi validada sem testes.

1. **Planejamento do novo blog:** definir nicho, nome, endereço Blogspot, público-alvo, categorias e objetivos comerciais/editoriais.
2. **Criação automática pelo Python:** criar o blog no Blogger, confirmar Blog ID, URL e configurações iniciais; não reaproveitar identificadores de outro blog.
3. **Configurações do Blogger e SEO técnico:** aplicar descrição, idioma, fuso horário, indexação, metadados e demais configurações compatíveis, validando o resultado no blog correto.
4. **Instalação do Tema V31 pelo Python:** instalar o tema universal validado para a replicação, responsável pela identidade visual automática — cores, layout, cabeçalho, rodapé e componentes. Não copiar cores/identidade de outro blog nem substituir um tema já funcional sem necessidade.
5. **Criação das páginas institucionais:** criar **Sobre, Contato, Privacidade, Termos, Cookies, Transparência/Afiliados** e demais páginas previstas, com texto profissional, identidade do nicho e SEO. A identidade das páginas é trabalhada **aqui**, e não como etapa visual separada. Formulário, quando previsto, precisa de destino e página de retorno próprios, além de testes de envio.
6. **Configuração da Loja Shopee:** integrar produtos reais da API, links de afiliado, categorias, carrossel e vitrine segundo contrato V31; não inventar preços, fotos ou links. Implantar guardas de blog/página e faixa com **hora da última atualização real**.
7. **Planejamento da arquitetura editorial:** definir categorias, intenção de busca, palavras-chave estratégicas, mapeamento de consultas e **clusters tópico-pilar**, evitando canibalização e repetição artificial.
8. **Produção dos conteúdos-pilar:** publicar guias centrais abrangentes, úteis, naturais, profissionais, originais e aprofundados, que organizem e respondam aos principais temas do nicho.
9. **Produção dos conteúdos de apoio (clusters):** criar artigos específicos que resolvam dúvidas e subtópicos dos pilares, complementem a cobertura e evitem preenchimento artificial.
10. **SEO On-Page e links internos:** otimizar títulos, URLs, headings, descrições de busca, imagens (origem, alt e miniatura), contexto, navegação e links internos relevantes. Cada pilar aponta para apoios; apoios retornam ao pilar e se interligam quando útil. Distribuir autoridade interna com critério, sem excesso ou links forçados.
11. **Estratégia de backlinks e autoridade:** planejar aquisição legítima de links editoriais por conteúdos citáveis, divulgação e parcerias pertinentes; **não automatizar backlinks artificiais** nem garantir links que terceiros ainda não criaram.
12. **Configuração da automação editorial:** integrar o Python validado, GitHub Actions e serviços necessários, com publicação, atualização da Loja, controle de duplicidade, isolamento por Blog ID, logs e validações SAFE; não afetar automações de outros blogs.
13. **Validação pública do blog:** conferir computador e celular, identidade do tema, páginas, contato, posts e **imagens realmente visíveis**, navegação, links internos/externos, Loja, SEO e primeiras execuções da automação; distinguir teste local, API, validação pública e teste E2E.
14. **Ativação e finalização:** após aprovação dos testes, ativar a operação, confirmar publicações reais, registrar configurações, URLs, IDs e evidências de que o blog funciona. Evitar declarar conclusão antes de comprovação.

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

## Contratos técnicos e verificações transversais (não redefinem a ordem oficial)

1. **Preflight**: get_blog por ID exato, URL e título; posts/páginas LIVE, página LOJA, Runner, GitHub main/HEAD, workflow/cron, tema existente. Se divergir, STOP.
2. **Tema**: preservar R52 em blog já provisionado; não aplicar R53 candidato nem tema renderizado de outro blog. Para novo blog usar template base aprovado, identidade própria, SAFE, latch e validação pública.
3. **Institucional**: criar Sobre, Política de Privacidade, Termos, Aviso de Afiliados, Contato, Mensagem enviada e Loja adaptadas ao nicho. Validar IDs, títulos, HTML e status; formulário com nome/e-mail/mensagem e `_next`, sem confundir publicação com recebimento comprovado.
4. **Editorial Shopee**: usar dados verdadeiros da API, artigos originais e úteis com links `offerLink` assinados e aviso de afiliado. **Inserir imagem Shopee no início dos artigos para thumbnail do Tema R52**, mais imagens contextuais. Validar tags `img`, alt, HTTPS, links, status e renderização pública (a presença da tag não garante imagem visível).
5. **Loja**: gerar 16 produtos distintos (4×4) de fontes Shopee validadas. Não inventar imagens, preços, URLs ou disponibilidade. `imageUrl` e `offerLink` de domínios permitidos; `rel="nofollow sponsored noopener"`; preço é referência da seleção, não promessa corrente.
6. **Região rotativa**: preservar `<!-- UNIVERSAL_V31_STORE_AUTO_START -->` e `<!-- UNIVERSAL_V31_STORE_AUTO_END -->`, estilo `adr-store-v31-css`, faixa `ub-store-status`, 16 `ub-product-card`, demais partes da página. Apenas a região interna é alterável.
7. **Automação/segurança**: alterações GitHub isoladas por blog; PR SAFE primeiro, sem escrita; `BLOG_ID`, `PAGE_ID`, URL, título e marcadores como guardas; validar 16 produtos, categorias, preços e `src/blogger_policy_guard.py`. Bloquear credenciais ausentes, dados inválidos e qualquer mudança paralela (conteúdo/ETag). Nunca reutilizar credenciais, IDs, estados de rotação e latches de outro blog.
8. **LIVE e readback**: somente main após SAFE bem-sucedido; comparar conteúdo antes da escrita, preservar HTML fora dos marcadores; após escrita exigir leitura exata da API e HTTP público 200 + 16 cartões + carimbo exato da execução. Permitir até 12 tentativas com 8 segundos entre elas por atraso de CDN, nunca aceitar resultado parcial como PASS. **Se API salvou e HTTP falhou, houve escrita; inspecionar antes de repetir**.
9. **Rotação provisória**: workflow `.github/workflows/achados_da_rotina_rotation_v31.yml`, script `achados_da_rotina/rotation_v31.py`, cron `*/20 * * * *` só para o blog `1637047917126642592`. PASS SAFE `42442795380` e PASS LIVE por push `42442871710` (16 IDs novos, validação pública). **Ainda NÃO comprovada periodicidade por múltiplos eventos schedule**. Exigir 3 eventos `schedule` independentes com `LIVE_API_AND_PUBLIC_PASS`, 16 produtos e mudança real de IDs; se não houver, relatar o motivo. Só depois considerar alteração do cron exclusivamente desse blog para diário.
10. **Continuidade**: distinguir hipótese/SAFE/LAB/API/publicação pública/teste E2E do usuário. Registrar IDs, URL, commits/runs, status e pendências; atualizar checkpoint sem sobrescrever backup antigo sem auditoria.

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