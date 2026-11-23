# V31 / Radar Tech BR — C115 Etapa 4: seleção de 10 artigos para reescrita (concluída sem editar posts)

**Data:** 23/11/2026 · **Status:** PLANO EDITORIAL CONCLUÍDO; WORDPRESS SEM ALTERAÇÕES.  
**Continuidade prévia já salva:** `affiliate_hub_v31/CHECKPOINT_C115_PRE_ETAPA4_CONTINUIDADE_2026-11-23.md`.  
**Manifest estruturado com briefs completos:** `affiliate_hub_v31/C115_RADAR_TOP10_REESCRITA_MANIFEST_2026-11-23.json`.  
**C114, etapa anterior:** `affiliate_hub_v31/CHECKPOINT_C114_RADAR_GERADOR_SEO_SAFE_MERGED_2026-11-23.md`.

## O que foi efetivamente verificado
- WordPress `https://radartechbr.com.br/`: GET autenticado `wp_list_posts(status=publish,per_page=100,context=edit)` encontrou **37 posts**; categoria Tecnologia (ID 3): **14**, Guias de Compra (ID 1): **23**, categoria Ar-condicionado (ID 20, filha de Tecnologia): **0**.
- `wp_get_post_full(context=edit,include=[meta,terms,thumbnail])` consultou conteúdo bruto de **mais de 20 candidatos**, contando H2s, palavras aproximadas, cartões comerciais, imagens inline, âncoras e SEO; critérios e evidências estão no manifest. Posts e páginas/hubs foram distinguidos.
- Listagem AIOSEO TruSEO devolveu **score 0 para 36 posts listados**, sem distinguir os candidatos por desempenho. Portanto a priorização é **editorial**, não uma promessa de audiência: **nenhuma métrica real de Google Search Console, CTR ou conversão afiliada foi usada**.
- Muitos artigos do gerador vNext anterior ainda incluem **2 cartões comerciais idênticos**; artigos manuais históricos podem apresentar **zero CTA/links afiliados no HTML original**. A correção C114 não reescreve retroativamente artigos publicados.

## Ranking final para revisão editorial futura
| Ordem | ID | Artigo original (preservar URL) | Prioridade | Problema/decisão |
|---:|---:|---|---|---|
| 1 | 260 | [Smartwatch com monitor de frequência cardíaca](https://radartechbr.com.br/smartwatch-com-monitor-de-frequencia-cardiaca/) | P0 | `O leitor` vazado na meta; dois CTAs; limites de sensores de saúde devem ser claros |
| 2 | 314 | [Escolhendo o Melhor Ventilador para o Verão](https://radartechbr.com.br/escolhendo-o-melhor-ventilador-para-o-verao/) | P0 | Meta vazada, 2 CTAs, 28 negritos com termo ventilador, categoria genérica |
| 3 | 29 | [Arctic Air Cooler portátil](https://radartechbr.com.br/arctic-air-cooler-portatil-o-que-conferir-antes-de-comprar/) | P0 | Artigo curto sem links afiliados inline; **não confundir mini cooler/climatizador com ar-condicionado**, e não atribuir categoria Ar-condicionado automaticamente |
| 4 | 311 | [Caixa de som Bluetooth com microfones e luzes](https://radartechbr.com.br/caixa-de-som-bluetooth-com-microfones-e-luzes-para-eventos/) | P1 | CTA duplicado, introdução genérica, sem links internos |
| 5 | 278 | [Controle remoto para projetor portátil](https://radartechbr.com.br/controle-remoto-para-projetor-portatil/) | P1 | Compatibilidade de modelos sem fontes suficientes, CTA duplicado |
| 6 | 28 | [Scanner OBD2 Bluetooth](https://radartechbr.com.br/scanner-obd2-bluetooth-o-que-verificar-antes-de-comprar/) | P1 | Oferta 'universal' exige evidência por veículo/app; zero CTA e zero imagens inline |
| 7 | 256 | [Ventilador portátil com resfriamento e iluminação](https://radartechbr.com.br/ventilador-portatil-com-resfriamento-e-iluminacao/) | P1 | Não afirmar refrigeração sem comprovar mecanismo; dois CTAs |
| 8 | 25 | [Caixa de som Kapbom KA-8955](https://radartechbr.com.br/caixa-som-kapbom-ka-8955-guia-antes-da-compra/) | P1 | Ficha de potência/TWS/resistência à água não comprovada; zero CTA |
| 9 | 138 | [Relógio inteligente com tela infinita](https://radartechbr.com.br/como-escolher-um-relogio-inteligente-com-tela-infinita/) | P1 | Expressão 'tela infinita' sem métrica precisa; links internos ausentes, diferenciação do #260 |
| 10 | 24 | [Luz RGB portátil para vídeo e celular](https://radartechbr.com.br/luz-rgb-portatil-video-celular-o-que-conferir/) | P1 | Conteúdo curto, sem CTA/links inline; alimentação, montagem e faixa cromática precisam de fontes |

**Síntese de contagens na seleção:** 5/10 com dois cartões de compra; 4/10 sem links afiliados no HTML bruto (IDs 29,28,25,24); 2/10 com metadescrição `O leitor` visivelmente vazada (260,314). Há featured_media para os quatro guias sem foto inline — **não dizer que perderam a imagem destacada**.

## O plano de reescrita (NÃO executado nesta C115)
- Os **10 briefs individualizados** no manifest incluem: título sugerido **até 60 caracteres**, intenção de busca específica, palavra-chave, H2 propostos, perguntas frequentes só se sustentadas, fontes faltantes, link ao hub adequado e guardas de integridade.
- Etapa posterior: confirmar tráfego de busca via GSC quando disponível e valor afiliado real, sem assumir projeções.
- Antes de editar *cada* post: refetch WordPress e comparar `post_modified`; guardar **HTML bruto completo + título + slug + meta AIOSEO + resumo + categoria + featured_media + links** no GitHub; confirmar produto e link afiliado **na campanha específica**, foto verdadeira e especificações da oferta; planejar alteração por revisão WordPress, sem mudar URL/canonical nem remover backlinks.
- Após a revisão aprovada, atualizar **somente um artigo por vez**, conferir cartão único e `rel="nofollow sponsored"`, disclosure, link funcional, meta 140–155, ausência de `reader_need`, pertinência de links internos e renderização. Não inserir preço/histórico/avaliações não verificados.
- Reescrever não é sinônimo de publicar artigo novo: a intenção é melhorar as **URLs existentes** e preservar tráfego/SEO sem duplicar conteúdo.
- Evitar canibalização: #260 e #138 têm intenções distintas de relógios; #311 não deve reproduzir o artigo de karaokê #235; #25 tem SKU identificado, não reescrever como guia genérico de toda caixa de som.
- **Alerta fora dos dez:** post #320, sobre “escolher parafusadeiras”, tem CTA para **conjunto de ponteiras PH2**, não para uma parafusadeira. Problema real de integridade produto/título e candidato à curadoria emergencial **fora do escopo do portal tecnológico**; não apagar/reclassificar automaticamente.
- Artigo #324 (luminária LED USB) é referência de contraste por estrutura mais específica, mas a ferramenta AIOSEO indica campos SEO ainda não preenchidos; tratar separadamente de reescrita completa.
- Moda, cozinha, beleza e ferramentas históricas permanecem publicados e precisam de plano próprio de curadoria, não reescritas técnicas artificiais.

## Proteções e estados preservados
- `main`: C114 integrada via PR #133, LIVE do writer legado bloqueado por `if: ${{ false }}`, `RADAR_LIVE_PUBLISH_ENABLED=false`, `config/wordpress.json.publicacao_automatica=false`; autorização operacional adicional no publicador.
- GitHub C114 regression SAFE verde, **V31 universal ainda com 8 testes falhando** (baselines antigos); geração real de novo DRAFT não homologada.
- Nenhuma alteração de WordPress realizada na C115: **zero** posts escritos, nenhuma mudança de slug/categoria, zero tags, zero mídia, zero scripts ou API Shopee rodados e zero LIVE.

## Retomada em um novo chat
Ler primeiro: `V31_CONTINUAR_AQUI.md` e `affiliate_hub_v31/CHECKPOINT_C115_PRE_ETAPA4_CONTINUIDADE_2026-11-23.md`; depois este checkpoint e manifest estruturado.  
**Código de retomada:** `V31-RADAR-C115-20261123-TOP10-PLANEJADOS-NO-WP-WRITES`.  
**Próxima ação:** preservar estado SAFE, resolver os 8 testes legados sem enfraquecer filtros; confirmar que o proprietário quer avançar para edição de posts existentes; então escolher um único canário, salvar seu HTML e evidências antes de qualquer edição.
