# C66 — revisão editorial real e teste de segurança LIVE (19/11/2026)

**STATUS: EM_ANDAMENTO — prévia durável na main antes de mutações.**

## Reabertura
- Fonte obrigatória C65: [V31_CONTINUAR_AQUI.md](../V31_CONTINUAR_AQUI.md), [CONTINUIDADE_ESTADO.json](CONTINUIDADE_ESTADO.json), [CHECKPOINT_C65](CHECKPOINT_C65_TRES_PENDENCIAS_HOMOLOGACAO_2026-11-19.md).
- WordPress Casa post **305** está em **DRAFT**; [pré-validação LIVE somente leitura #44564287283](https://github.com/adelrib27/blogger-automation1/actions/runs/44564287283) registrou SHA256 original `d4da2df9095fe9a560c3d7cfb9bfb0ea3d55f161b8dbc2bcb4c0f1acb2d8584a`, `AWAITING_OWNER_APPROVAL`, 0 POSTS.
- Conversa 19/11: usuário autorizou avançar hoje na revisão e teste LIVE; autorização genérica de prosseguir **não equivale à aprovação explícita do conteúdo exato do post 305** exigida pelo contrato C65. Não gerar manifesto `owner_authorized:true` por conta própria.
- Inspeção do HTML bruto do #305 revelou um defeito editorial **reproduzível e não coberto pelo gate C65**: cabeçalho “Materiais e manutenção” tem texto sobre estilos; “Comparação de especificações” tem texto sobre erros comuns; “Perguntas para o anúncio” contém a conclusão. O parser mapeia 7–9 parágrafos soltos a cabeçalhos fixos por índice. A cláusula de H2 atual não certifica correspondência semântica.
- A composição comercial não deve ser reescrita: bloco R2 com SKU `shopee:1718605288:58259898640`, fotografia CSV real, URL afiliada campanha WordPress Casa, 3 links afiliados, CTA, disclosure, 2 links internos já verificados. Não inserir preço, avaliação, disponibilidade ou dados não fundamentados.

## Plano
1. Preparar **versão editorial corrigida** do post 305 (somente DRAFT, sem alterar SKU/campanha/CTA); checar tamanho, duplicações, factualidade, links internos e status remoto antes e depois da edição. Edição de conteúdo altera SHA256 e **invalida autorização antiga**; não publicar.
2. Melhorar gerador WordPress universal com correspondência determinística entre cabeçalho e tema do parágrafo, testes de falha fechada e regressões. Blogger pode ser auditado separadamente; não forçar blocos potencialmente desalinhados em LIVE.
3. Testar de forma conectada a rota manual LIVE em **preview/no approval** contra HTML atualizado, demonstrar que nenhuma publicação ocorreu e registrar SHA256 posterior. Não criar manifesto de aprovação sem consentimento do post específico, não simular LIVE real como já efetuado.
4. PR+CI, checkpoint final/JSON/índice `main`. A última pendência `event=schedule` será verificada pela checagem de 20/11; não alterar crons em C66.

## Estado inicial
- Feito: leitura do index, C65, JSON e HTML API #305; discrepância editorial objetiva identificada.
- Pendente: revisão/edição de DRAFT, código de qualidade e testes, readback, fechamento.

## C66 — correção editorial remota concluída (DRAFT, ZERO LIVE)
- Conferência API WordPress pré-edição: Casa **43 LIVE +59 DRAFT**, post #305 ainda `draft`; dois links internos existentes e publicados, IDs **298** (cadeira para varanda) e **295** (organização de alimentos).
- Corrigido **apenas o DRAFT #305** via plugin WordPress com `status=draft`, novo título “Como escolher um vaso decorativo âmbar para sua sala”, excerto descritivo prudente e oito seções editoriais alinhadas ao tema. Corpo gerado manualmente com **753 palavras**, entre **548–645 caracteres** por parágrafo, sem inventar materiais, preço, estoque ou especificações não fornecidas. Os H2 passam a representar a respectiva seção, com checagem de anúncio e checklist. Slug original V31/hash SKU preservado para antirrepetição.
- **Bloco comercial original copiado byte a byte e preservado**: SKU `shopee:1718605288:58259898640`, imagem exata R2, **3 ocorrências de link afiliado real `https://s.shopee.com.br/8pnOgLent4`**, CTA, disclosure, 2 links internos. Texto anterior 6094 chars → **7249 chars**. Nenhum link fabricado ou reconvertido.
- API WordPress independente depois da edição: **#305 status=draft**, título atualizado, **10 H2** (8 editoriais + 2 blocos comerciais), foto exata, CTA/disclosure, 3 URLs da campanha e 2 links internos. Totais continuam **43 LIVE +59 DRAFT**. Data de modificação do post `2026-11-19T14:14:55` horário do site.
- SHA256 antigo da C65 está **invalidado** pelo novo HTML; obter o novo SHA via preflight autenticado ao fim desta fase. Não criar aprovação/manifesto LIVE sem autorização individual posterior.
