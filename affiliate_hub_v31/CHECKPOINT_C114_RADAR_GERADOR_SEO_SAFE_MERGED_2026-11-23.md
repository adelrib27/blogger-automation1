# V31 C114 — Radar Tech BR: Etapa 3, correção do gerador editorial existente (SAFE, integrada)

**Data:** 23/11/2026 (America/Recife). **Status:** CÓDIGO INTEGRADO NA MAIN / TESTES OFFLINE APROVADOS / LIVE NÃO HOMOLOGADO E DESATIVADO.  
**Escopo:** `https://radartechbr.com.br/` e repositório `adelrib27/blogger-automation1`.  
**Origem:** arquivo `1_comando_chatgpt_corrigir_blog.txt`, etapas 1, 2, 3; decisão de focar WordPress Radar em tecnologia C105–C113.

## Mudanças de segurança imediatas em main
- `.github/workflows/radar_editorial_vnext_autonomous.yml`: `jobs.autonomo.if: ${{ false }}` (fail-closed), `RADAR_LIVE_PUBLISH_ENABLED=false`, `RADAR_WORDPRESS_STATUS=draft`. Cinco agendamentos históricos continuam declarados, mas job de escrita está desabilitado; isto **não** é prova de que nenhum run já iniciado em horário anterior terminou.
- `.github/workflows/wordpress_rascunho.yml`: desativada chamada geral antiga para `src/main_wordpress_auto.py` em `workflow_dispatch` sem filtro; preservado modo de teste direcionado em DRAFT.
- `config/wordpress.json`: `publicacao_automatica=false`; nicho atualizado a tecnologia incluindo Smartphones, Computação, TVs e Ar-condicionado.
- Não mexer em LIVE do V31 universal, Blogger, R2, Shopee, nem outros WordPress.

## Código corrigido no PR #133 (merge squash)
**Pull request:** https://github.com/adelrib27/blogger-automation1/pull/133  
**Commit de merge:** `ea4470ae4613a27421d84575ac41a0fdcd84ccd0`.

1. `radar_tech_br/src/generate_articles.py`: prompt factual orientado a intenção e `product_evidence` do item; `reader_need` interno nunca compõe metadescrição; função `meta_description(plan)` escolhe somente texto completo de 140–155 caracteres; título do plano 35–60 e rejeição de título vago; apenas **UM CTA**, após editorial e links internos; slug da nova categoria `tecnologia/ar-condicionado`.
2. `radar_tech_br/src/cta_context.py`: cartão com uma fotografia real do feed, título do anúncio, link afiliado e disclosure; fatos opcionais da Shopee (preço observado com data, avaliação agregada e loja) aparecem **somente se campos presentes**, rotulados como dados a confirmar na oferta. Nunca inventar segunda imagem, preço, review ou ficha técnica.
3. `radar_tech_br/src/quality_gate.py`: bloqueia `O leitor` e outras instruções públicas no HTML/meta/excerpt; título >60, meta fora 140–155, resumo diferente da meta, conclusão semelhante à introdução, negritos excessivos, bloco comercial múltiplo, SKU/produto/keyword/imagem ausentes, URL afiliada inválida/fora de domínio Shopee. Exige 1 CTA, 2 links dentro do mesmo cartão, 1 disclosure e atributos `nofollow sponsored`. Categorias aceitáveis pelo writer antigo restritas a Tecnologia e Ar-condicionado.
4. `radar_tech_br/src/prepare_slot.py`: falha se slot ainda pertencer a Casa/Cozinha/Ferramentas/Moda; passa snapshot real do produto `product_evidence` via campos retornados no scanner Shopee. **Não** inclui Ar-condicionado no scanner de cinco categorias legado; bloqueio vNext permanece até revisão editorial e teste com seleção válida.
5. `radar_tech_br/src/publish_generated.py`: exige adicional `RADAR_VNEXT_LIVE_OWNER_APPROVED=true` além de flags existentes (nenhuma foi habilitada), verifica `offerLink` com HEAD e permite apenas destino HTTPS Shopee. Qualquer 403/404/429/erro de rede/destino incerto bloqueia LIVE para revisão humana; não significa que o produto necessariamente deixou de existir. Log informa rejeição por qualidade. Mapeia Ar-condicionado para slug REST `ar-condicionado`.
6. `radar_tech_br/src/self_test.py` atualizado ao contrato C114; suíte nova `radar_tech_br/src/c114_quality_regression_self_test.py`; integração ao `radar_editorial_vnext_safe.yml`; workflow independente de PR `.github/workflows/radar_c114_offline_regression_safe.yml`, sem tokens/rede.
7. Prompt de referência legível, com variáveis e localização dos arquivos: `radar_tech_br/PROMPT_EDITORIAL_C114.md`. **Não precisa colar nada no WordPress**, pois código já está na main.

## Evidências de homologação
- PR SAFE workflow `Radar Tech BR — C114 Regression SAFE (sem publicacao)` run **45224366338**: **SUCCESS**; compila arquivos Python, executa `self_test.py`, `cta_card_self_test.py`, `word_count_threshold_self_test.py` e 15 cenários novos em `c114_quality_regression_self_test.py`, além da checagem textual do interlock LIVE. URL https://github.com/adelrib27/blogger-automation1/actions/runs/45224366338
- Teste C114 verifica rejeição de prompt vazado, título >60, meta curta, CTA duplicado, SKU ou afiliado ausentes, URL de host estranho, conclusão repetida, links HTTP 404 simulado, categoria Ar-condicionado, meta 140–155, fatos datados no cartão; **zero POST remoto**.
- Suite universal `V31 Editorial Shopee - Testes SAFE Blogger WordPress`, run **45224366190**: **FAILED 6 assertions + 2 errors em 604 testes**. Comparação com run anterior indica tests legados de rotas/nichos `wordpress_radartechbr` desatualizados desde política C105, em `test_draft_adapter`, `test_site_launch_plan`, `test_fallback_shop_alternatives`, `test_fallback_v23`, `test_inventory_audit`, `test_link_warmup`, `test_routing`. Uma quebra extra do contrato de log C58 introduzida no primeiro patch C114 foi corrigida em `publish_generated.py`, ausente da lista final. **Não afirmar suíte universal verde. Não corrigir 8 testes falseando expectativas; revalidar os fixtures contra a política nova em ciclo independente.**
- Arquivos C114 relidos diretamente da `main` após merge: workflow pausado, config com `publicacao_automatica=false`, prompt, gate e verificador de link presentes.
- WordPress autenticado após merge: `wp_list_posts(status=publish)` ainda retorna **37 posts LIVE**, e categoria `Ar-condicionado` ID20 segue filha da Tecnologia ID3 com **zero artigos**. Esta etapa não fez post/page write.

## Limitações conscientes
- Não houve geração remota de novo artigo a partir de Workers AI nem criação de DRAFT no WordPress nesta C114; isso requer checagem de quota/credentials e plano de homologação posterior sem LIVE.
- Verificação por HTTP HEAD pode classificar link válido como incerto devido a antifraude/405; em vez de aceitar sem evidência o mecanismo bloqueia publicação para revisão humana. Em futura retomada, implementar estratégia segura alternativa de verificação sem relaxar o gate.
- Schema `FAQPage` e segunda imagem não são criados sem fontes verificáveis; FAQ em texto pode ser útil, mas dados não podem ser inventados.
- As oito páginas hubs C110/C111 e o header C112 permanecem como publicados. Posts existentes (#314, #326 etc.) **não foram reescritos**. Etapa 4 será exclusivamente priorização dos 10 posts, sem reescrever automaticamente, após decisão do proprietário.
- O V31 universal ainda tem dívida de 8 testes de baseline da C105; não tratá-los como resultado verde nem conflitar com demais fluxos autônomos.

## Código de continuidade
`V31-RADAR-C114-20261123-MERGED-SAFE-TESTED-LIVE-OFF`

**Próxima ação recomendada:** resolver suite universal compatibilizando fixtures ao nicho tecnológico sem afrouxar filtros; somente depois validar canário 1 DRAFT real do Radar em ambiente SAFE, com link afiliado exato da campanha e bloqueio LIVE. Se proprietário solicitar Etapa 4, listar 10 posts com prioridade e checklist; **não reescrever sem pedido específico**.
