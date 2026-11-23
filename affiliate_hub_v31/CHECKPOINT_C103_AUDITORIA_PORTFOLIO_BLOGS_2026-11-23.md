# V31 C103 — FILTRAGEM ESTRATÉGICA DE BLOGS POR CATEGORIA E NICHO
**Data da auditoria:** 23/11/2026 • **Decisão:** recomendação editorial, ainda NÃO executada em CMS ou automações.
**Critérios aplicados:** identidade de nicho, sobreposição temática, ativos editoriais existentes, flexibilidade da plataforma e potencial comercial/qualidade de tráfego. NÃO atribuir receita, SEO rank ou lucro não medidos.

## Escopo confirmado por leitura autenticada
- **32 Blogger**: 30 com produção editorial, 1 laboratório separado (Casa Prática Lab, 7 posts), 1 blog não iniciado (Meu Céu Noturno, 0 posts).
- **3 WordPress ativos**: Casa e Decoração 51 artigos publicados, Radar Tech BR 37, Oficina & Garagem 17.
- Fonte Blogger: API `list_blogs` e manifesto C102 de 30 posts LIVE. Fonte rotas: `affiliate_hub_v31/site_routes.json` e `sites.d/*.json`. As categorias de vários sites já concorrem entre si na própria arquitetura de nichos.
- **Nenhuma métrica de Google Search Console/GA4 ou venda/comissão por blog foi disponibilizada.** Logo, esta classificação é uma decisão de FOCO, não prova de rentabilidade.
- **35 blogs registrados no total** (32 Blogger + 3 WP). Proposta: **10 sites comerciais em desenvolvimento, 23 Blogger congelados para saída planejada, 1 lab preservado e 1 astronomia não lançado**.

## MANTER — 10 sites comerciais (6 núcleo + 4 pilotos)
| Projeto | Plataforma | Publicados aprox. | Categoria/nicho exclusivo | Decisão | Razão |
|---|---|---:|---|---|---|
| [Casa e Decoração](https://casaedecoracao.radartechbr.com.br/) | WordPress | 51 | Casa, organização, decoração e utilidades | Manter e aprofundar | Domínio próprio/subdomínio, 51 artigos; concentrar guias evergreen de organização e cômodos, reduzir títulos genéricos. |
| [Radar Tech BR](https://radartechbr.com.br/) | WordPress | 37 | Tecnologia, eletrônicos e casa conectada | Manter e aprofundar | Domínio próprio, 37 artigos; eliminar da pauta conteúdos soltos de moda, beleza e cozinha. Tech como assunto principal. |
| [Oficina & Garagem](https://oficina.radartechbr.com.br/) | WordPress | 17 | Ferramentas, oficina e acessórios automotivos | Manter e aprofundar | Nicho técnico distinto, 17 artigos; resolver posts repetitivos sobre suportes e manutenção. |
| [Achados para Casa](https://achadosparacasa2026.blogspot.com/) | Blogger | 85 | Achados Shopee e comparativos de utilidades para casa | Manter e aprofundar | Maior acervo Blogger (85 posts); diferenciar do WordPress Casa: curadoria de ofertas/produtos, não copiar guias de decoração. |
| [Café na Medida](https://cafe-na-medida.blogspot.com/) | Blogger | 6 | Cafeteiras, métodos e acessórios para café | Manter e aprofundar | Identidade comercial de nicho, loja própria C96 de 35 ofertas; 6 posts, ainda precisa ganhar profundidade. |
| [Vida Pet Prática](https://vida-pet-pratica.blogspot.com/) | Blogger | 9 | Acessórios para cães e gatos, cuidados não médicos | Manter e aprofundar | Nicho suficientemente diferente dos demais, 9 posts; focar segurança, enriquecimento, higiene, cuidados sem alegações médicas. |
| [Móveis para Cada Canto](https://moveisparacadacanto.blogspot.com/) | Blogger | 11 | Móveis completos, salas, quartos e home office | Manter sob teste de 60 dias | Nicho mais definido e loja C101 com 27 anúncios; testar cliques/conversão antes de escalar por frete, montagem e compra de maior consideração. |
| [Cabelos em Foco](https://cabelos-em-foco.blogspot.com/) | Blogger | 11 | Secadores, modeladores e acessórios capilares | Manter sob teste de 60 dias | Diferenciação frente a blogs genéricos de beleza; 11 posts e catálogo do nicho. Tratar temas capilares com cautela sem promessas clínicas. |
| [Mala Pronta e Viagem Prática](https://mala-pronta-viagem-pratica.blogspot.com/) | Blogger | 14 | Bagagem, malas e organização de viagem | Manter sob teste de 60 dias | 14 posts e nicho distinto, mas demanda pode ser sazonal e marca ainda não comprovou vendas. |
| [Jardim e Horta na Prática](https://jardim-e-horta-na-pratica.blogspot.com/) | Blogger | 5 | Jardinagem, vasos, cultivo e ferramentas leves | Manter sob teste de 60 dias | Conteúdo evergreen e nicho diferenciado; só 5 posts, dependerá de dados para justificar continuar. |

**Regra anti-cannibalização:** Casa e Decoração WP = guias editoriais de cômodos e organização; Achados para Casa Blogger = descoberta de produtos/curadoria Shopee, não publicar artigos quase iguais. Radar Tech WP = somente eletrônicos e tecnologia; Oficina WP = ferramentas e garagem. Móveis Blogger = móveis completos e compra informada; Cabelos Blogger = cuidados não clínicos e ferramentas capilares.
**Pilotos**: Móveis, Cabelos, Mala, Jardim, reavaliar com dados reais após 60 dias ou período suficiente para indexação.

## CONGELAR E PREPARAR DESCONTINUAÇÃO — 23 Blogger
| Blog | Publicados | Categoria/nicho | Destino se houver artigo valioso | Por quê cortar |
|---|---:|---|---|---|
| Cozinha Sem Complicação | 12 | Cozinha/eletrodomésticos | Casa e Decoração WP | Amplo e sobreposto às categorias cozinha dos sites centrais; preservar Loja antiga. |
| Liquidificadores em Foco | 10 | Cozinha/liquidificadores | Casa e Decoração WP | Micro-site de uma só linha de produto, sem identidade adicional demonstrada. |
| Eletroportáteis na Cozinha | 12 | Cozinha/eletroportáteis | Casa e Decoração WP | Cobre eletroportáteis já presentes em Cozinha e Casa. |
| Air Fryers em Foco | 11 | Cozinha/air fryers | Casa e Decoração WP | Subnicho que pode funcionar como cluster de artigos em vez de domínio separado. |
| Ventiladores em Foco | 11 | Climatização/ventilação | Casa e Decoração WP | Tema sazonal, categoria pequena e aderente a conforto da casa. |
| Limpeza Inteligente | 11 | Casa/limpeza | Casa e Decoração WP e Oficina WP se houver equipamentos técnicos | Assunto já atendido por utilidades e equipamentos de limpeza. |
| Casa em Ordem | 12 | Casa/organização | Casa e Decoração WP | Mesma intenção de pesquisa de organização doméstica e utilidades. |
| Casa Leve e Funcional | 9 | Casa/organização e decoração | Casa e Decoração WP | Tema praticamente idêntico a Casa em Ordem e Casa e Decoração. |
| Cadeira Certa no Home Office | 7 | Móveis/cadeiras | Móveis para Cada Canto | Subnicho de mobiliário; integrar como cluster ergonômico sem duplicar análises. |
| Ar-Condicionado sem Dúvidas | 4 | Climatização/ar-condicionado | Casa e Decoração WP | Só 4 posts, exige conteúdo técnico mais responsável e não sustenta domínio separado no estágio atual. |
| Portal Radar Tech | 17 | Gadgets/tecnologia/automotivo | Radar Tech BR WP | Concorre diretamente com a marca e o domínio próprio Radar Tech BR. |
| Escolha Certa Online | 12 | Gadgets/achadinhos diversos | Radar Tech BR e Casa e Decoração conforme tema | Marca generalista sem fronteiras temáticas; conteúdo redistribuível por intenção. |
| Conecta Achados | 18 | Achadinhos/tecnologia/casa | Radar Tech BR e Achados para Casa | Mix semelhante a outros blogs genéricos e divisão entre tech/casa. |
| Guia de Achados & Ofertas | 11 | Achadinhos/variados | Achados para Casa, Radar Tech BR e Oficina WP | Pauta pulverizada sem vertical exclusiva. |
| Achados que Valem | 12 | Achadinhos/casa/gadgets/pets | Achados para Casa, Radar Tech BR e Vida Pet | Sem recorte único; tópicos redistribuídos para projetos especialistas. |
| Vitrine Prática | 12 | Achadinhos/organização doméstica | Achados para Casa | Redundância de vitrine com o blog âncora de 85 posts. |
| Achados da Rotina | 8 | Achadinhos/casa utilidades | Achados para Casa | Proposta generalista e foco comercial similar. |
| Moda e Ofertas | 9 | Moda/vestuário | Não manter domínio de blog; moda continua nos canais sociais próprios | Publicações genéricas, sem diferenciação de catálogo e canal social já alinhado a moda. |
| Estilo no Dia a Dia | 12 | Moda/beleza | Descontinuar blog, preservar ativos de moda úteis | Sobrepõe moda e beleza, sem eixo único. |
| Achadinhos de Beleza | 15 | Beleza/maquiagem/cabelos | Cabelos em Foco só para cabelo; demais temas congelados | Diferenciação fraca frente ao especialista capilar; domínio canal-attitude não reforça o nome atual. |
| Violão do Começo — Acordes e Cuidados | 7 | Instrumentos/música | Não incorporar aos e-commerces V31 atuais | Nicho distinto mas de pouca sinergia com os hubs prioritários; sem prova de tráfego/conversão. |
| Pedal Leve — Mobilidade e Ciclismo Urbano | 12 | Ciclismo/mobilidade | Não incorporar ao hub automotivo sem afinidade real | Vertical independente exigiria pesquisa técnica e editor especializado; baixa sinergia operacional atual. |
| Ateliê Criativo em Casa | 13 | Artesanato/hobbies | Somente guias de organização do espaço em Casa WP | Nicho real porém fora do eixo de maior concentração comercial; pausar enquanto mede valor real. |

**Separados dos 33 comerciais:** `Casa Prática Lab`: manter como laboratório privado/de teste, nunca incluído no ritmo editorial público; `Meu Céu Noturno`: não lançar, arquivar o projeto vazio.

## Execução recomendada — SEM DESTRUIÇÃO PREMATURA
1. **Agora:** parar de planejar novos artigos nos 23 blogs marcados para saída. Não criar novas lojas ou editorias neles. Preservar 10 projetos ativos. Hoje a publicação automática do V31 está OFF, portanto essa decisão NÃO requer mexer em workflows ou ativar LIVE.
2. **Antes de excluir fisicamente:** exportar XML/HTML, imagens/links/IDs/permalinks e registrar estoque de artigos, backlinks e impressões/CTR/cliques do Google Search Console por blog. Conferir também cliques de afiliados e comissões Shopee (por SubID se existir).
3. **Priorizar recuperação de conteúdo, não cópia idêntica:** artigos úteis podem ser atualizados e absorvidos no destino temático, com contexto editorial próprio. Evitar duplicação entre domínios; preferir redirecionamentos por URL específica quando tecnicamente viáveis e coerentes, preservando o acesso do usuário. NÃO redirecionar em massa para homepage, nem excluir sites com páginas que ainda tragam tráfego valioso.
4. **60 dias:** medir impressões, cliques orgânicos, sessões, clique em CTA, taxa de saída para Shopee, vendas válidas e comissões líquidas por blog, custo editorial e volatilidade da oferta. Descartar até mesmo algum dos 4 pilotos se não demonstrar valor relativo.
5. **Limites decisórios:** manter com sinais de demanda qualificada, crescimento consistente ou comissão; cortar se duplicado, sem marca distintiva e sem sinal nas métricas após coleta adequada. Com dados indisponíveis, **classificar como RECOMENDADO PARA DESCONTINUAÇÃO, não como NEGÓCIO COM ZERO VENDAS**.

## Fontes e alertas SEO
- Google Search Central, política de conteúdo em escala: https://developers.google.com/search/docs/essentials/spam-policies
- Google Search Central, conteúdo útil com foco em pessoas: https://developers.google.com/search/docs/fundamentals/creating-helpful-content
- Google Search Central, atualizações principais: https://developers.google.com/search/docs/appearance/core-updates — remoção de conteúdo é último recurso, não ajuste rápido.
- Métricas oficiais: https://support.google.com/webmasters/answer/10268906
- Nenhuma inferência de penalização automática por ter muitos blogs. Risco real é escalar páginas similares e rasas sem valor próprio.

## GARANTIAS DE SEGURANÇA
- **0 blogs apagados, 0 posts excluídos, 0 páginas Loja alteradas, 0 temas mexidos, 0 rotas/crons alterados, 0 LIVE automático ativado.** Documento é somente avaliação e decisão de portfólio proposta.
- Antes de qualquer mudança irreversível futura: backup, plano por URL, validação pré/pós e aprovação explícita de exclusão de sites.
- Preservar checkpoint C101 (lojas originais restauradas, Móveis C101 com 27 itens) e C102 (30 artigos LIVE publicados no dia 23/11).
