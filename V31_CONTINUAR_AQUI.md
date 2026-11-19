# V31 — CONTINUAR AQUI (ponto de entrada permanente)

> **Para um novo chat do projeto:** leia ESTE arquivo no GitHub `main`, depois [estado estruturado](affiliate_hub_v31/CONTINUIDADE_ESTADO.json), [checkpoint técnico atual C61](affiliate_hub_v31/CHECKPOINT_C61_TESTE_REAL_SEM_TETO_ARTIGOS_2026-11-19.md) (histórico em [C57](affiliate_hub_v31/CHECKPOINT_C57_CONTINUIDADE_GITHUB_2026-11-18.md) e [C56](affiliate_hub_v31/CHECKPOINT_C56_ARTIGOS_AFILIADOS_AUTOMACAO_2026-11-18.md)) e [issue-mestre #54](https://github.com/adelrib27/blogger-automation1/issues/54). Confirme os dados atuais nos serviços antes de executar. **Não confundir com `CHECKPOINT_ATUAL.md`**, que conserva o histórico/canon legado da rede Blogger em 02/11 e não descreve o V31 atual.

**Projeto:** [adelrib27/blogger-automation1](https://github.com/adelrib27/blogger-automation1) · ramo `main` · trilha V31.  
**Última conferência contextual:** 18/11/2026. O JSON de estado é atualizado por fase; dados e números nele são observações históricas, NÃO leitura ao vivo.  
**Protocolo:** [CONTINUIDADE_PROTOCOLO.md](affiliate_hub_v31/CONTINUIDADE_PROTOCOLO.md) · [estado JSON](affiliate_hub_v31/CONTINUIDADE_ESTADO.json).

## 1. Por que o V31 existe (não se desviar)

Construir uma biblioteca **UNIVERSAL**, permanente e independente de blogs/nichos previamente imaginados, alimentada pelos **dois CSVs Shopee** em R2. Organizar o acervo completo em categorias e facetas oficiais, revisão segura e pesquisa textual. **Somente depois** de um pedido concreto de blog por nicho e plataforma, selecionar produtos aprovados pertinentes, usar a campanha afiliada REAL daquele blog, converter/cachear links, criar textos originais com **foto real do mesmo produto**, link em palavra-chave, **botão CTA Shopee**, aviso comercial e links para postagens reais do próprio blog; encaminhar ao publicador Blogger ou WordPress com gates de aprovação.

**Nunca transformar o V31 em reserva exclusiva de três WordPress**, não adivinhar nichos/blogs futuros nem fabricar IDs, campanhas, preços, comissões, vendas, imagens ou dados de estoque.

## 2. Linha do tempo essencial e provas (início → meio → estado recente)

| Fase | O que foi verificado | Evidências |
|---|---|---|
| C15–C33 | Dois feeds somados sem descartar histórico; catálogo universal 203.649, categorias oficiais, FTS5, revisão e leitura R2 | [Issue-mestre #54](https://github.com/adelrib27/blogger-automation1/issues/54), [C33](affiliate_hub_v31/CHECKPOINT_C33_UNIVERSAL_PRIORITY_REASSESSMENT_R2_2026-11-18.md) |
| C42–C44 | 594 históricos reclassificados com evidência dupla, preservando links e R2; restantes 194.370 REVIEW na última medição | [C44 GitHub Actions](https://github.com/adelrib27/blogger-automation1/actions/runs/44352445875) |
| C45–C47 | Manutenção semanal conservadora + índice privado de revisão; 10.565 pistas para SKUs sem categoria (NÃO aprovações) | [PR #64](https://github.com/adelrib27/blogger-automation1/pull/64), [PR #65](https://github.com/adelrib27/blogger-automation1/pull/65), [PR #66](https://github.com/adelrib27/blogger-automation1/pull/66) |
| C48 | Blog Blogger REAL **Móveis para Cada Canto** criado, ID `1439741542627895062`, campanha `moveisparacadacanto`, primeiro link real no R2 | [PR #67](https://github.com/adelrib27/blogger-automation1/pull/67), [canário C48](https://github.com/adelrib27/blogger-automation1/actions/runs/44376578794) |
| C49–C50 | Dono pediu 3 artigos (sala, quarto, home office) e autorizou publicá-los; Blogger API confirmou os **3 LIVE** | [Checkpoint C49+C50](affiliate_hub_v31/CHECKPOINT_C49_MOVEIS_FIRST_THREE_DRAFTS_2026-11-18.md) |
| C52–C54 | Corrigida a lacuna comercial: nos 3 artigos, **foto REAL do SKU**, link afiliado da campanha exata, link em palavra-chave, botão Shopee, aviso de afiliado e 2 links internos por artigo | [PR #71](https://github.com/adelrib27/blogger-automation1/pull/71), [canário C53](https://github.com/adelrib27/blogger-automation1/actions/runs/44389838537) |
| C55–C56 | Gerador agendado de **até 1 rascunho Blogger/dia** para pedido real, quota respeitada, publicação LIVE OFF; Workers AI modelo com JSON Mode testado com 8 parágrafos/635 palavras; 330 testes V31 passaram | [PR #72](https://github.com/adelrib27/blogger-automation1/pull/72), [PR #73](https://github.com/adelrib27/blogger-automation1/pull/73), [PR #74](https://github.com/adelrib27/blogger-automation1/pull/74), [C56 AI real](https://github.com/adelrib27/blogger-automation1/actions/runs/44395785068) |
| C57 | **CONTINUIDADE C57 VALIDADA:** prévia gravada ANTES do trabalho, índice fixo e registro legível por máquina, verificador automático diário, 8 testes aprovados | [Checkpoint C57](affiliate_hub_v31/CHECKPOINT_C57_CONTINUIDADE_GITHUB_2026-11-18.md) · [Action PASS](https://github.com/adelrib27/blogger-automation1/actions/runs/44402454026) |

Os números acima são o último estado comprovado nas execuções citadas, não alegações de que o R2/Jobs continuam idênticos hoje.

## C58–C59 — WordPress universal validado em produção SAFE (18/11/2026)

- **C58:** os agendamentos WordPress Casa/Oficina/Radar foram auditados, com Casa/Oficina inicialmente quebrando por importação do núcleo V31. [PR #75](https://github.com/adelrib27/blogger-automation1/pull/75) corrigiu imports dos geradores e incluiu links internos para posts REAIS do mesmo WordPress. [R2 + IA + WP C58](https://github.com/adelrib27/blogger-automation1/actions/runs/44407697822) PASS: Casa **9**, Oficina **6**, Radar **15** ofertas aprovadas com imagem real/campanha correta, Casa criou prévia efêmera 8 parágrafos/537 palavras, 2 links internos, 0 posts.
- **C59:** [PR #76](https://github.com/adelrib27/blogger-automation1/pull/76) substituiu o Qwen3 antigo dos 3 fluxos WP por cliente Llama 3.3 JSON/HTML com gate. Primeira tentativa real bloqueou título curto; [PR #77](https://github.com/adelrib27/blogger-automation1/pull/77) retenta o plano sem baixar exigência. [C59 AI real 44410047121](https://github.com/adelrib27/blogger-automation1/actions/runs/44410047121) PASS: artigo Casa 743 palavras, `DRAFT_READY`, foto R2, Shopee campanha exata, CTA e 2 links internos, **0 posts**. [PR #78](https://github.com/adelrib27/blogger-automation1/pull/78) corrigiu imports também nos publicadores WordPress.
- **Três workflows SAFE EXISTENTES passaram depois dos patches:** [Casa](https://github.com/adelrib27/blogger-automation1/actions/runs/44410965031), [Oficina](https://github.com/adelrib27/blogger-automation1/actions/runs/44410976595), [Radar](https://github.com/adelrib27/blogger-automation1/actions/runs/44410496620). Nenhum deles habilitou LIVE. Radar LIVE anterior bloqueou alegação de acessibilidade não comprovada e esse veto foi preservado.
- [Checkpoint C58](affiliate_hub_v31/CHECKPOINT_C58_AUDITORIA_UNIVERSAL_ARTIGOS_WP_BLOGGER_2026-11-18.md) · [Checkpoint C59](affiliate_hub_v31/CHECKPOINT_C59_WORDPRESS_AI_UNIVERSAL_SAFE_2026-11-18.md). **Estado superado pela C60:** o writer universal WordPress já existe em `main` e passou em CI/preview real (veja abaixo). Ainda não há comprovação de novo POST de rascunho ou publicação LIVE após os patches; criação remota depende de pedido real e credenciais daquele site.

## C60 — WordPress FUTURO genérico, em rascunho (18/11/2026)

- [PR #79 MERGED](https://github.com/adelrib27/blogger-automation1/pull/79): `automatic_wordpress_drafts.py` + workflow diário WordPress universal em `main`. Aceita qualquer registro WordPress real e pedido em `site_requests.d`; usa foto real R2, link exclusivo da campanha, texto original Workers AI, botão Shopee e links internos de posts publicados. Protege a quota por site, evita duplicatas, **cria apenas draft** e verifica retorno da API. **Execução real de POST draft ainda não ocorreu** porque não há pedido/credenciais novas do proprietário para esse writer.
- [CI #44412438334](https://github.com/adelrib27/blogger-automation1/actions/runs/44412438334) **365 testes V31 +24 Casa +21 Oficina +crossblog PASS**. [Canário R2 + WP Casa #44412775615](https://github.com/adelrib27/blogger-automation1/actions/runs/44412775615) **PASS**: 43 posts reais lidos, 1 produto pertinente encontrado com foto real/campanha exata, **2 links internos**, 0 posts/0 R2 writes. Cron diário WordPress configurado como **PREVIEW por padrão**, aguardando site/credenciais/pedido real e liberação específica.
- [Checkpoint C60](affiliate_hub_v31/CHECKPOINT_C60_WORDPRESS_UNIVERSAL_DRAFT_SAFE_2026-11-18.md) · [Guia para credenciais seguras por WordPress](affiliate_hub_v31/WORDPRESS_AUTODRAFT_ANY_SITE.md). Não habilitar LIVE irrestrito nem inventar sites futuros.

## C61 — geração contínua e quarto artigo em RASCUNHO REAL (19/11/2026)

- **Removido o teto total de 3 artigos:** [PR #81](https://github.com/adelrib27/blogger-automation1/pull/81) MERGED, `articles:null` em `site_requests.d` agora significa **geração contínua** para Blogger e WordPress; 24 permanece apenas lote de seleção/cache, não quota total. No piloto Móveis, o pedido está ativo com `articles:null`; geração por ciclo continua limitada a um único DRAFT Blogger, sem LIVE automático.
- **Canário real completo:** [PREVIEW](https://github.com/adelrib27/blogger-automation1/actions/runs/44534753873) detectou falta de novo link na campanha, [fila](https://github.com/adelrib27/blogger-automation1/actions/runs/44535072335) encontrou 1 candidato, [conversão Shopee R2](https://github.com/adelrib27/blogger-automation1/actions/runs/44535276120) confirmou 1 URL da campanha correta com read-after-write. [Execução Blogger real](https://github.com/adelrib27/blogger-automation1/actions/runs/44535723037) criou **1 DRAFT** de guarda-roupa, ID `3612281866616913629`, com foto real, link afiliado, CTA e aviso, **0 posts LIVE**.
- **Falha detectada e corrigida:** o novo rascunho saiu inicialmente sem links internos porque a API não retornou o atributo status em cada item. [PR #82](https://github.com/adelrib27/blogger-automation1/pull/82) MERGED e [CI #44536428588](https://github.com/adelrib27/blogger-automation1/actions/runs/44536428588) **372 V31 +24 Casa +21 Oficina +crossblog PASS**; o **mesmo rascunho** foi corrigido no Blogger e revalidado com **2 links internos reais**, sem criar duplicata e sem publicar. Estado Blogger verificado: **3 LIVE + 1 DRAFT**.
- Workflows/gatilhos temporários C61 já removidos da `main`; rotina diária Blogger permanente preservada. Próxima prova: primeiro cron diário real depois desta mudança, com 1 DRAFT máximo por execução e SKU sem repetição. WordPress C60 ainda precisa de autenticação e pedido real para primeiro POST de rascunho; Radar legado apresentou falhas recentes de confirmação a investigar sem alterar seus gates.
- [Checkpoint C61](affiliate_hub_v31/CHECKPOINT_C61_TESTE_REAL_SEM_TETO_ARTIGOS_2026-11-19.md) · [estado JSON](affiliate_hub_v31/CONTINUIDADE_ESTADO.json). Sem segredo ou inventário alterado indiscriminadamente.

## 3. Blog piloto existente: três LIVE entregues e mais um DRAFT de teste

[Móveis para Cada Canto](https://moveisparacadacanto.blogspot.com/) — Blogger ID `1439741542627895062`, rota `affiliate_hub_v31/sites.d/blogger_moveis_para_cada_canto.json`, campanha `moveisparacadacanto`. Três artigos já publicados:

- [Sofá para sala pequena](https://moveisparacadacanto.blogspot.com/2026/11/sofa-para-sala-pequena-como-escolher.html)
- [Guarda-roupa para quarto](https://moveisparacadacanto.blogspot.com/2026/11/guarda-roupa-para-quarto-portas-medidas.html)
- [Home office: mesa e cadeira](https://moveisparacadacanto.blogspot.com/2026/11/home-office-confortavel-como-escolher.html)

O pedido persistido em `affiliate_hub_v31/site_requests.d/blogger_moveis_para_cada_canto.json` está **`articles:null` (contínuo)** desde o pedido explícito C61. Os três primeiros artigos permanecem LIVE e o **quarto é um DRAFT** real com foto/CTA/dois internos; novos drafts não têm teto TOTAL de 3 nem 24, mas dependem de produtos novos com links reais da campanha e do limite seguro de geração por ciclo. **`publish_enabled=false`** continua bloqueando publicação LIVE automática V31. O usuário relatou ter instalado um **tema provisório manualmente**; isso não é uma verificação técnica de tema V31 completo. O Runner Windows ainda tem bloqueio estático de ID para o tema, registrado na [Issue #70](https://github.com/adelrib27/blogger-automation1/issues/70), com [PR LAB #69](https://github.com/adelrib27/blogger-automation1/pull/69), **não implantado no serviço Windows**. O usuário preferiu adiar essa correção.

## 4. O que NÃO está comprovado ou liberado

- A fila REVIEW (último resultado: **194.370**) não equivale a produtos publicáveis; **10.565** pistas taxonômicas são apenas sugestões privadas.
- O canário **manual/push** C61 já criou um novo DRAFT Blogger real. A **primeira execução agendada C55 após `articles:null`** ainda precisa ser observada; canário não equivale a cron diário comprovado.
- A prévia R2 + WordPress REAL da C60 foi confirmada, inclusive imagem/CTA/2 links internos; **a criação autenticada de novo rascunho WordPress não foi testada em produção** por ausência de pedido e credenciais específicos.
- Nenhum pedido de publicação LIVE irrestrita foi autorizado. A autorização C50 foi pontual aos três artigos.
- Não publicar Pins, não modificar Worker v1.0, não habilitar crons LIVE só para acelerar resultado.
- Relatórios de vendas, cliques e comissões só com dados verificáveis.

## 5. Próximas ações permitidas, em prioridade

1. **Retomar do `active_work` do JSON em `main`**, atualmente C60 `PRONTO_PARA_PROXIMA_ETAPA`; conferir HEAD, PRs, Actions e serviço antes de qualquer nova mutação.
2. **Observar próximos crons reais** Blogger C55, WordPress universal C60 (PREVIEW por padrão) e os três WordPress legados: workflow configurado não prova execução agendada.
3. **Validar primeiro POST de rascunho WordPress universal** apenas com pedido real por tema/site, credenciais próprias no GitHub secret protegido e autorização de DRAFT. Confirmar `status=draft` via REST sem habilitar LIVE.
4. **Observar próximo cron Blogger C55** já sem teto total (`articles:null`), com limite de 1 DRAFT por ciclo, SKU novo e campanhas isoladas; não repetir rascunho de guarda-roupa C61.
5. Continuar reclassificação conservadora do acervo completo R2 dos dois CSVs; preservar produtos REVIEW e campanhas isoladas.
6. Runner/tema apenas quando o proprietário retomar o assunto.

## 6. Regra para QUALQUER novo chat ou execução longa

**ANTES** de pesquisar/alterar código: atualizar `affiliate_hub_v31/CONTINUIDADE_ESTADO.json` com fase, objetivo, `EM_ANDAMENTO`, último passo validado e próximo passo; gravar **prévia durável no GitHub**. **DURANTE**: após cada commit, PR, execução R2/Blogger ou avanço significativo, atualizar checkpoint e evidência com status claro `FEITO`/`PENDENTE`/`FALHOU` e efeitos em produção; dar prévia concisa ao usuário. **AO FINAL**: fechar checkpoint, conferir arquivos e atualizar este índice com o link do checkpoint mais recente.

Em caso de chat expirado, **não acreditar somente na última mensagem da conversa**. Reabrir estes arquivos via conector GitHub e verificar a diferença entre estado declarado e serviços reais. Se algo estava `EM_ANDAMENTO`, continuar daquele ponto sem repetir uma mutação. Não afirmar que uma etapa foi executada apenas por haver código ou PR criado.

O arquivo `CHECKPOINT_ATUAL.md` da raiz permanece fonte histórica para a **rede legada**, sem substituição, para evitar quebrar outros blogs.

**Frase curta para reabrir o projeto:** `Continue o V31 usando V31_CONTINUAR_AQUI.md e CONTINUIDADE_ESTADO.json da main; confira primeiro o active_work e as evidências.`
