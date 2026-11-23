# C114 — Prompt editorial do gerador existente Radar Tech BR

**Onde está implementado:** `radar_tech_br/src/generate_articles.py` nas funções `editorial_plan_prompt`, `universal_article_rules`, `article_prompt` e `repair_prompt`; o CTA permanece em `radar_tech_br/src/cta_context.py`.  
**Modelo:** Cloudflare Workers AI configurado no projeto. Nenhum serviço pago adicional obrigatório.  
**Importante:** este documento é a especificação humana; **o código já contém as regras**. Não colar manualmente no WordPress nem substituir o gerador.

## Variáveis reais de entrada

| Campo | Origem | Política |
|---|---|---|
| `product` | `productName` da Shopee | Nome do anúncio, não prova técnica |
| `shopee_item_id` | `itemId` Shopee | Obrigatório |
| `affiliate_link` | `offerLink` da campanha correta | HTTPS e domínio Shopee; verificação HTTP antes de LIVE |
| `image_url` | `imageUrl` | Imagem real; não criar outra supostamente do produto |
| `source_keyword` | Fila do scanner | Obrigatória |
| `category` | Regra Radar do slot | Somente Tecnologia ou Ar-condicionado |
| `product_evidence` | Snapshot de `priceMin`, `priceMax`, `ratingStar`, `shopName`, `source_date` | Campos opcionais e datados; ausência significa DESCONHECIDO |
| `title`, `keyword`, `reader_need`, `product_connection` | Planejamento editorial da IA | `reader_need` é **interno**, nunca público |

## Direção de planejamento

> Atue como editor sênior de um portal brasileiro de tecnologia. Parta da intenção de busca, não de um título comercial. Escolha título objetivo de 35 a 60 caracteres, com o tipo de equipamento e a pergunta que o artigo consegue responder. Use o anúncio como contexto factual, mas jamais invente especificações, testes, preços, avaliações ou recomendações. “Vale a pena?” exige critérios verificáveis; “Melhores X até R$ Y” e “X ou Y” exigem mais de uma opção com evidências comparáveis e por isso **não são habilitados no fluxo de uma só oferta**. Produza JSON com `title`, `keyword`, `reader_need` e `product_connection` — as duas últimas são instruções privadas, nunca metadados públicos.

## Direção do corpo

> Escreva em português brasileiro, atendendo à dúvida específica da busca. Use apenas evidências recebidas, separe informações observadas de pontos a conferir no anúncio. Considere o perfil de uso, compatibilidade, limitações, tamanho, manutenção e diferença entre variantes somente quando pertinente. Não reproduza a descrição do vendedor e não apresente experiência de uso não realizada. O texto deve contribuir para a decisão: explique para quem o modelo pode servir **com base nos dados disponíveis**. Evite introdução e conclusão equivalentes, repetição de palavra-chave em negrito, afirmações genéricas e promessas de economia. Use H2 variados conforme o tema; FAQ apenas se houver perguntas genuínas, sem inventar respostas técnicas.

## Formatos e bloqueios determinísticos

- Título público **até 60 caracteres** (o planejador escolhe preferencialmente de 35 a 60).
- Metadescrição e resumo público **140–155 caracteres**, produzidos pelo código a partir do título e de orientações de conferência, jamais do `reader_need`.
- Um único bloco de produto com imagem do feed, nome, eventual preço observado/datado e eventual nota agregada fornecida pela Shopee, advertência de conferência e aviso de afiliado.
- Links internos reais do mesmo WordPress; nenhuma URL alheia assumida.
- Um só disclosure explícito; as âncoras comerciais usam `rel="nofollow sponsored"`.
- **Falha fechada:** “O leitor” ou instruções de prompt, título/meta inválidos, SKU ausente, link externo ao domínio esperado, imagem ausente, bloco comercial duplicado, conclusão repetida ou excesso de negrito.
- Ao tentar promover a LIVE no publicador legado, validar **novamente** o conteúdo, exigir aprovação operacional explícita e checar a URL afiliada via HTTP. Destino inacessível ou incerto implica bloqueio, não suposição.
- A publicação LIVE automática continua DESATIVADA; testes somente offline e sem credenciais.

## Observações de escopo

A nova categoria WordPress `Ar-condicionado` é filha de `Tecnologia`. Incluí-la no gate não significa habilitar a produção automática de posts sobre ar-condicionado; o scanner legado de cinco nichos permanece pausado. Não forçar categoria vazia com ofertas de acessórios ou peças que não sejam aparelhos.

FAQ estruturado não é gerado automaticamente a partir de suposições; o texto pode ter perguntas frequentes úteis quando as respostas forem sustentadas. Não há obrigação de inventar segunda fotografia para um feed que entregou somente uma imagem.

**Etapa 4 (separada):** priorizar as 10 reescritas do acervo publicado, com backups e URLs preservadas. Esta Etapa 3 não altera posts existentes.
