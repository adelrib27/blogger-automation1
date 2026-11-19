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
