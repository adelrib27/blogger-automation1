# V31 / Radar Tech BR — C115: checkpoint PRÉVIO à Etapa 4 (proteção contra expiração do chat)

**Data:** 2026-11-23 (America/Recife). **Fase:** C115 Etapa 4 **a iniciar após este checkpoint**.
**Solicitação atual:** "siga para a etapa 4. mais antes gere a continuidade por precalção caso a coversa aqui nesse chat expire".
**Repositório oficial:** `adelrib27/blogger-automation1` — branch `main`.
**WordPress alvo:** https://radartechbr.com.br/ . Este trabalho não abrange outros blogs, Pinterest nem Mercado Livre.

## Contexto exato da retomada
- C109–C111: oito hubs de tecnologia publicados, SEO/menus e homepage. C112: cabeçalho FSE da página inicial remodelado com submenus Tecnologia (incluindo Smartphones, Computação, TVs e Ar-condicionado), Guias de Compra e Loja, faixa utilitária superior removida; backup do header em `affiliate_hub_v31/backups/C112_RADAR_HEADER_BEFORE_NAV_COMPACT_2026-11-23.html`.
- Categoria WordPress "Ar-condicionado" = ID 20, filha de Tecnologia ID 3, ainda sem artigos na última leitura; zero preenchimento artificial.
- C113: auditoria de dez falhas editoriais confirmadas em artigos e no código, registrada em `affiliate_hub_v31/CHECKPOINT_C113_RADAR_DIAGNOSTICO_10_PONTOS_2026-11-23.md`. Posts publicados representativos #314 (ventilador), #326 (aparador), contraste #324 (luminária USB).
- C114 / Etapa 3: ajustes **integrados à main** após PR #133, merge `ea4470ae4613a27421d84575ac41a0fdcd84ccd0`. Consultar `affiliate_hub_v31/CHECKPOINT_C114_RADAR_GERADOR_SEO_SAFE_MERGED_2026-11-23.md`.
  - Gerador corrigido no `radar_tech_br/src/generate_articles.py`: 1 CTA, meta 140–155 independente de `reader_need`, título até 60, evidência de oferta Shopee, categoria Tech/Ar-condicionado.
  - `quality_gate.py` atualizado para barrar vazamento, CTA duplicado, keyword/negrito excessivo, falta de SKU/link/fatos obrigatórios, repetição da conclusão.
  - `cta_context.py` passou a usar 1 cartão comercial, imagem do anúncio, informações verificadas opcionais e 1 disclosure.
  - `radar_tech_br/src/publish_generated.py` requer flag independente `RADAR_VNEXT_LIVE_OWNER_APPROVED=true` e testa link antes de LIVE; nenhuma foi habilitada.
  - Workflow legado `.github/workflows/radar_editorial_vnext_autonomous.yml` com `jobs.autonomo.if: ${{ false }}`, LIVE=false e WP_STATUS=draft. `config/wordpress.json` `publicacao_automatica=false`. `.github/workflows/wordpress_rascunho.yml` não chama mais o publicador geral antigo.
- C114 testes offline especializados aprovados, GitHub Actions run `45224366338`. Suite universal de V31 com **8 falhas** de fixtures/rotas antigos (6 assertions + 2 errors), não foi declarada verde, canário WordPress DRAFT real ainda não homologado.
- Última verificação WordPress: 37 posts publicados, categoria Ar-condicionado ID20 com 0 publicações. **Etapa 3 não alterou os artigos antigos**.

## Etapa 4 — próximo trabalho a executar agora
**Entendimento do escopo:** selecionar **10 artigos publicados mais importantes para reescrita**, elaborar plano editorial individual, preservar URLs e integridade de links de afiliados, sem aplicar alterações aos posts ainda. Solicitação anterior descreveu Etapa 4 como *selecionar os 10 artigos publicados mais promissores para reescrita*.

### Procedimento obrigatório e idempotente
1. Começar pela lista real `wp_list_posts(status=publish,per_page=100,context=edit)` e categorias, sem extrapolar números antigos. Evitar selecionar hubs que são **páginas** do WordPress, não posts.
2. Avaliar amostras completas diretamente com `wp_get_post_full(id,context=edit,include=[meta,terms,thumbnail,author])`: título, slug, data de modificação, URL, categoria, relevância tecnológica, valor de busca, especificidade, meta/excerpt, URL afiliada e imagem original, quantidade de cartões, vazamentos, repetição e alegações técnicas sem fonte.
3. Priorizar recuperação de **artigos relevantes para tecnologia e climatização**; não reescrever moda/beleza/cozinha apenas para forçá-los ao nicho. Posts históricos fora do nicho recebem roteiro de curadoria/realocação sem exclusão, URL/canonical e redirecionamentos sem consentimento.
4. Para os dez escolhidos, produzir tabela/ranking com **ID WordPress, URL real, problema observado, intenção de busca, proposta de H2/FAQ relevante, fontes/dados a obter e risco**; distinguir fatos confirmados de hipóteses. Não inventar modelo, ficha técnica, avaliações nem testes.
5. Registrar manifest de trabalho e checkpoint **C115 pós-seleção** no GitHub na `main`, atualizando `V31_CONTINUAR_AQUI.md` (de forma aditiva, protegendo revisões simultâneas).
6. **Não editar artigos publicados, não gerar novos LIVE, não mexer em credenciais/campanhas, não rodar workflows de escrita, não tentar forçar quota Shopee/Cloudflare**, nem alterar posts de outros blogs. Revisões são Etapa posterior, depois de verificar ofertas, backlinks, imagem, SEO e backup do HTML.

## Segurança operacional / próximos gates
- LIVE automático permanece **OFF**; se aparecer branch/PR/schedule paralelo, reconciliar com HEAD atual antes de escrever.
- O filtro de nichos Radar Tech BR se limita a tecnologia; Ar-condicionado ID20 foi criado, mas não é justificativa para atribuir conteúdo errado a ele.
- C114 qualidade da geração passou em testes offline, mas o V31 universal ainda tem 8 testes falhando; evitar anunciar homologação completa.
- Não assumir acesso à conversa expirada pelo link; este checkpoint contém a continuidade exata.

**Código de retomada:** `V31-RADAR-C115-20261123-CHECKPOINT-PRE-ETAPA4`.
**Operações até o ponto deste checkpoint:** apenas criação deste documento e indexação no GitHub; nenhuma edição de artigo, código ou workflow.
