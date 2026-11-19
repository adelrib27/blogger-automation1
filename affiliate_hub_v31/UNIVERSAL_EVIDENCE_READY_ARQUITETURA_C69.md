# V31 C69 — fusão SAFE da engenharia Vida Pet no núcleo UNIVERSAL

**Status:** motor reutilizável, **não publicado nem implantado como cron**, para QUALQUER Blogger/WordPress real. Implementação: [`universal_evidence_ready.py`](universal_evidence_ready.py), testes [`test_c69_universal_evidence_ready.py`](tests/test_c69_universal_evidence_ready.py). Origem: relatório mestre Vida Pet Prática 19/11/2026, LAB R26/R27/R28, **interpretado como referência de engenharia**, não como evidência de funcionamento universal em produção.

## 1. A fusão não é uma migração de blog

**V31 continua soberano:** dois CSVs Shopee → R2/catalog universal (SKU/taxonomia/imagem/elegibilidade) → campanha exata de cada site → palavras-chave/SEO e cluster → geração Blogger ou WordPress DRAFT-first → revisão individual + LIVE gated. Os experimentos do Vida Pet fornecem gates complementares **entre escolha do candidato e geração/armazenamento do artigo**, sem substituir os gates comerciais de V31. O projeto não se torna pet-specific e pode atender tecnologia, móveis, casa, ferramentas, decoração e qualquer nicho permitido pelo motor.

O diretório original `vida_pet_pratica/` (R28) e o WordPress.com privado `vidapetpratica.wordpress.com` permanecem **completamente isolados**. Este PR **não altera código LAB, D1 vivo, cache R2 real, BLOGGER/WordPress LIVE ou rascunhos**, não ativa cron, não cria loja. Aquele WordPress não foi lançado, não tem writer, e não há permissão para editá-lo. A versão antiga do Blogger com nome parecido não entra no processo.

## 2. Engenharia reaproveitada e limites de evidência

| Mecanismo R28/Pet | Adaptação universal V31 C69 | Estado comprovado nesta entrega |
|---|---|---|
| Evidence Engine/Identity Matcher | `EXACT_PRODUCT`, `MATCHED_MODEL`, `SIMILAR_PRODUCT`: apenas EXACT para fatos específicos, por SKU `shopee:shop:item` e título normalizado coerente | **Código+unit tests offline** |
| Evidência externa + Facts Whitelist | 1 fonte externa autorizada e 2 evidências exatas (defaults conservadores), tipos de afirmação limitados e URLs HTTPS com **host revisado exatamente igual**, carimbo UTC, no mínimo suporte explícito; similar não empresta características | Código+testes com dados sintéticos; **fonte real online não verificada nesta fase** |
| Cache/reuso TTL | 7 dias de `verified_utc`, data da fonte também validada; **ler não renova TTL**; sem pacote válido = rejeição/missão sinalizada | Código+testes sem pesquisa real |
| Candidate Failover | Examinar candidatos aprovados sequencialmente, rejeitar cada falha e tentar próximo **sem afrouxar policy**, máximo 20 tentativas por chamada | Testes; sem busca real |
| Evergreen/anti-duplicação | fingerprint produto+keyword+ângulo, sem sinônimos iguais, similaridade Jaccard limiar .72, cooldown 30 dias para **mesmo site**; diferente blog não compartilha histórico | SQLite LAB e testes, **não migration D1/R2 de produção** |
| READY Buffer | meta operacional mínimo 3; se já 3 não preparar mais, se menor não inventa para preencher; marca READY somente após verificações de produto, evidência, SEO e qualidade fornecidas | Simulação local persistente+testes, **não writer ligado** |
| R27 telemetria | contadores agregados hit/miss/search/http/429/credits reportados; nada de SKU, links, queries, IDs ou segredos nos relatórios públicos | Código+mock |
| R28 orçamento | por rodada no simulador 2 SEARCH/3 HTTP e circuit breaker 429, falta de saldo confirmado bloqueia pesquisas; classes não executam rede | Código+testes; **NÃO garante limite de gasto em reais** |
| D1 persistente | `SQLiteReadyLabStore` demonstrou índices e estado por `site_key+campaign` em base local, persistente entre processos quando há arquivo físico | **D1 real NÃO implantado nem consultado nesta C69** |
| SEO C68 | `safe_refill_preview` só aceita status `READY_FOR_EDITORIAL_SAFE_REVIEW`, `keyword_source_verified=true` e `blockers=[]` originados do auditor real C68, além do QA editorial final atestado | Teste usa `future_blog_seo.audit_future_article` com fixture |

### Separação de evidências: a diferença entre SAFE e autorização comercial

- `Catalog.for_conversion` verifica moderação/taxonomia V31 e `_single_verified_offer` exige foto verdadeira da origem e URL afiliada cacheada **na campanha cadastrada** para o site real. Um candidato jamais se autoautoriza marcando `approved:true`.
- Em outro passo independente, `evidence_whitelist` exige **produto VERIFICADO, identidade e fonte exata** para cada afirmação. Aceita `authorized:true` e `review_status:AUTHORIZED` **somente de um verificador confiável**, não de texto de IA nem diretamente do crawler. O campo `approved_host` deve ter sido confirmado pelo verificador e coincidir com o domínio do link. O código offline verifica consistência, **não prova que o verificador upstream fez sua parte**.
- `used_evidence_ids` só pode referir a prova aprovada do mesmo SKU. A verificação automática de que todo fato material no HTML final corresponde às tags de evidência **AINDA PRECISA** de adaptador factual ou revisão humana antes de usar como gate de produção. O booleano `editorial_quality_verified:true` isolado não substitui verificação real do texto. C69 **não** autoriza publicação.
- Fotos, preço, comissões e estoque não podem ser inferidos da pesquisa genérica; são invariantes de fonte comercial do V31. Para novos blogs, C68 requer demanda SEO real e linkagem interna de posts publicados, ou cold-start explicitamente vazio.
- Proteções de pets contra recomendações veterinárias continuam específicas daquele nicho; princípios genéricos de não inventar fatos/saúde/segurança e source_policy permanecem no V31.

## 3. Contrato de input sem cadastrar sites fictícios

O módulo recebe um `site_key` **já registrado** em `routing.sites()` com `publish_enabled=false`, um `Catalog` V31 real **injetado pelo caller**, um `SQLiteReadyLabStore` isolado e candidatos com `product_key,keyword,angle,evidence,seo_audit,used_evidence_ids,editorial_quality_verified,article_title,content_html`. A campanha é **obtida da rota**, nunca passada por candidato. Não chama APIs externas e não cria posts nem links. Relatório retorna `BUFFER_HEALTHY`, `BUFFER_HEALTHY_NO_REFILL` ou `LOW_READY_FAIL_CLOSED`, contagens e razões de rejeição sem PII.

**Importante:** o contador `min_ready=3` é o número de artigos aprovados **em reserva simultânea por site**, não a quantidade total de artigos produzíveis. Quando artigos da reserva forem usados e cooldowns respeitados, outros podem entrar. O padrão de criação contínua `articles:null` e todas as campanhas/blogs futuros do V31 são preservados.

`candidate_target=5` é orientação de dimensão da seleção; `candidate_attempt_limit=20` é teto de falhas examinadas na chamada, não teto global de SKUs. Limites monetários e quotas do provider não devem ser deduzidos desses números.

## 4. Persistência futura — desenho seguro D1/R2 sem alterar estado vivo

**Separar**: R2 existente guarda **biblioteca de produtos**, URLs de origem e links de cada campanha; D1/SQLite novo guardaria apenas **metadados de evidência e fila editorial por site**. Não duplicar os ~203k SKUs e não substituir catálogo central por D1 do Vida Pet.

Tabela conceitual `editorial_ready`: `site_key,campaign,product_key,keyword,angle,fingerprint,article_sha256,evidence_checked_utc,status,created_utc,used_utc` com chave `(site_key,fingerprint)`, índices por `(site_key,campaign,status)` e status `READY/USED`. Tabela separada de evidência só precisa de `product_key,normalized_title,evidence_id,claim_type,source_host,source_url,authorization_status,verified_utc,expires_utc`; nenhuma fonte similar pode disponibilizar fatos. Manter joins por chave, não copiar Page IDs/WordPress Post IDs/Blogger Blog IDs entre sites.

**Para ativar D1 produtivo com segurança** (fase posterior): escolher uma única conta/DB ou namespaces por blog com controle de acesso; versão/migration reversível; transação e lock distribuído por site/cron e ID de idempotência; read-after-write e backup; contrato de leasing do READY; métricas/custos; controle de segredo; limites reais de pesquisa e quota por API; teste SAFE de um blog canário com 0 LIVE. O `SQLiteReadyLabStore` da C69 **não é** substituto de D1 multiworker e não grava o D1 do Vida Pet.

## 5. Pipeline universal esperado, mas ainda SEM deployment

```text
Dois CSVs → catálogo R2 global / taxonomia / curadoria V31
                           ↓
Pauta de intenção real → SEO C68 → site_key / campanha EXATA
                           ↓
      R2 SKU + foto original + URL afiliada verificada
                           ↓
              EVIDENCE CACHE por produto (TTL)
           (reuso) ↙                  ↘ (miss)
       Facts Whitelist            Firecrawl SEARCH_ONLY
                  ↘              (budget durável, 429)
                       Identity Matcher
                           ↓
       Candidate Failover / Evergreen / dedup por site
                           ↓
          IA (Workers AI ou Groq) recebe fatos autorizados
                           ↓
             Fact gate no HTML + SEO + qualidade
                           ↓
             VERIFIED_READY por site (buffer)
                           ↓
          Blogger/WordPress → DRAFT → CMS readback
                           ↓
    Revisão editorial/comercial + owner approval individual
                           ↓
             LIVE MANUAL (nunca por inferência)
```

**Nota de implementação:** o motor C69 cobre **até o buffer SAFE em simulação**. **Ainda não existe** adaptador real com Firecrawl/Groq/R2/D1, armazenamento de fontes verificadas em banco compartilhado, fact gate de texto IA integrado ou writer DRAFT usando READY. Não declarar pipeline acima como LIVE. Implementação dessas peças precisa de PR separado, tests e canário controlado. Não rodar cache miss real com crédito Firecrawl insuficiente nem com conta diferente sem validação.

## 6. Matriz de riscos e critérios de aceitação

- **Evidências:** só liberar fatos exatos, identificados, externos, aprovados e frescos; objeto similar/consulta sem apoio → `LOW_READY_FAIL_CLOSED`; não preencher o buffer com fatos inventados.
- **Comercial:** foto R2, moderação, origem, taxonomia, campanha exata e disclosure; o teste usa `Catalog` real **em SQLite fixture** com dados sintéticos, não a biblioteca R2 viva.
- **SEO:** fonte da intenção e cluster C68; links internos somente `publish/live`, mesmo hostname; blogue novo sem histórico gera 0 links, não URL falsa.
- **Idempotência:** fingerprint de produto/palavra-chave/ângulo, similaridade e cooldown. Conta de READY atômica **apenas no SQLite local**; múltiplos jobs exigem concorrência/lock real posteriormente.
- **Financeiro:** orçamento R28 de pesquisas/HTTP e telemetria são limites de chamadas por processo; não são garantia de custo em reais. Checar saldos de credenciais reais antes de qualquer Firecrawl pago.
- **Produção:** **NENHUM** cron/writer/R2/D1/WordPress/Blogger/SEO de blog atual muda na C69. Original Vida Pet LAB fica em R28, writer desligado; R29/C70 futuros só após validação apropriada.
- **Continuidade:** check C69 na main, PR+CI, atualizar `CONTINUIDADE_ESTADO.json` e `V31_CONTINUAR_AQUI.md`, preservar checagem real `event=schedule` prevista para 20/11, sem declarar cron funcionando antes da prova.

**Critério de entrega desta C69:** módulo e testes SAFE aprovados + integração com `Catalog` e auditor SEO **em fixture**, LAB original intocado, zero postagem/custo/R2/D1, checkpoint durável. Não equivale à homologação completa do cache miss real, da fila D1 ou da publicação via READY.
