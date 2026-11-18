
# V31 C56 — Artigos afiliados completos (18/11/2026)

A biblioteca universal Shopee R2 já fornece image_url dos CSVs e o cache de links por campanha. O objetivo não é gerar só texto: cada artigo comercial precisa ter produto aprovado e pertinente, foto REAL do anúncio, palavra-chave afiliada, CTA Shopee, disclosure e links internos confirmados.

**C52/C53:** auditoria de fotos reais [C52](https://github.com/adelrib27/blogger-automation1/actions/runs/44389396192) e conversões na campanha exclusiva do blog móveis [C53](https://github.com/adelrib27/blogger-automation1/actions/runs/44389838537), com persistência verificada.

**Três artigos LIVE de Móveis para Cada Canto:** foram atualizados pela API Blogger, preservando o texto; cada um contém imagem real do produto, três usos do mesmo link afiliado (foto, palavra-chave, botão), transparência comercial e dois links para artigos LIVE do próprio blog. Todos os conteúdos foram relidos pela API, com status LIVE, sem duplicar posts.

**C54:** [PR #71](https://github.com/adelrib27/blogger-automation1/pull/71) MERGED. Código reutilizável em Blogger e WordPress, bloqueando imagem/URL não confiável, item em revisão, campanha errada, assunto incompatível e repetição de bloco comercial.

**C55:** [PR #72](https://github.com/adelrib27/blogger-automation1/pull/72) MERGED. Workflow diário na main para gerar até um NOVO RASCUNHO Blogger por execução para blogs com pedidos reais, sem criar posts LIVE. Respeita quantidade total solicitada; Móveis para Cada Canto já tem 3 de 3 publicados e não deve receber quarto sem novo pedido. [PR #73](https://github.com/adelrib27/blogger-automation1/pull/73) corrigiu os enums LIVE/DRAFT de Blogger API v3. [Canário real](https://github.com/adelrib27/blogger-automation1/actions/runs/44394545587) confirmou quota respeitada, 0 posts criados.

**C56:** [PR #74](https://github.com/adelrib27/blogger-automation1/pull/74) MERGED. Workers AI agora usa Llama 3.3 JSON Mode, modelo documentado com JSON estruturado, no lugar de Qwen3 em descontinuação. [CI](https://github.com/adelrib27/blogger-automation1/actions/runs/44395583618): 330 testes V31, 24 Casa, 21 Oficina e cross-blog PASS. [Teste de IA real](https://github.com/adelrib27/blogger-automation1/actions/runs/44395785068): 8 parágrafos e 635 palavras válidas, zero posts e zero chamadas Shopee. Workflows e triggers temporários C52-C56 removidos.

**Limite de comprovação:** primeira execução futura do cron e primeiro ciclo REAL de novo rascunho com quota aberta ainda não observados. Atualização de textos LIVE e geração de rascunhos são tarefas distintas; publicação recorrente permanece desativada. A rotina C55 serve Blogger; WordPress recebeu o renderizador C54, mas não este cron.

**Continuidade:** V31-C56-3LIVE-FOTOS-CTA-INTERNOS-330TESTS-AI-635WORDS-20261118.
