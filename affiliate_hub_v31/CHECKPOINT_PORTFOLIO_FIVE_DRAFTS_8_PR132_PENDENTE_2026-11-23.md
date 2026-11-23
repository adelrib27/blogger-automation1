# V31 — Consolidação para 5 Blogger: 8 rascunhos concluídos, PR #132 pendente
Data: 2026-11-23, America/Recife.

## Decisão original do proprietário
Manter cinco Blogger:
1. Cozinha Sem Complicação `3552757910439359679`;
2. Móveis para Cada Canto `1439741542627895062`;
3. Estilo no Dia a Dia `4830103887652146866`;
4. Limpeza Inteligente `7757953554206491487`;
5. Vida Pet Prática `8052455848487624244`.

**Escopo deste ciclo:** 16 blogs listados pela API Blogger Bridge V2 na conta conectada (há outros Blogger em outras conexões C103). Não apagar blogs de contas não auditadas.

## Ações REAIS concluídas (Blogger)
- 11/11 backups integrais dos blogs de origem já foram salvos em Google Docs e relidos exatamente, totalizando 95 publicados, 73 páginas e 3 drafts. URLs de recuperação em `affiliate_hub_v31/BLOGGER_PORTFOLIO_FIVE_2026-11-23.json`.
- 8 **novos DRAFTs originais** criados e relidos via GET, confirmando HTML idêntico, status DRAFT:
  - Cozinha: sanduicheira/grill `5513820607691719534`, liquidificador `1972066528706408498`, métodos de café `6989724121072195864`, balança digital `2428730622218583526`.
  - Móveis: cadeira mesh/estofada `5667175148968856980`.
  - Estilo: looks jeans `7538746411189780835`, touca/modelador de cetim `8826080853584006959`.
  - Limpeza: carrinho organizador para materiais de limpeza `8350292185500005781`.
  - Vida Pet não ganhou rascunho: nenhuma fonte dos 11 blogs era naturalmente pertinente a pets.
- Sem importação de fotos de terceiros, links Shopee de campanha antiga ou preços/descontos não verificados. Conteúdo deve passar por homologação editorial/comercial antes de qualquer LIVE.
- 0 posts publicados LIVE e 0 blogs ou posts antigos excluídos.

## Automação — mudanças propostas, ainda NÃO ATIVAS
PR [#132](https://github.com/adelrib27/blogger-automation1/pull/132) criado em branch `v31-portfolio-five-retired-store-freeze-20261123`: congelamento dos gatilhos `schedule` e `push` em sete workflows de lojas legadas:
`eletroportateis_store_autonomous.yml`, `cabelos_store_autonomous.yml`, `guia_achados_ofertas_store_autonomous.yml`, `ventiladores_store_autonomous.yml`, `moda_ofertas_store_autonomous.yml`, `blogger_liquidificador_store_autonomous.yml`, `pedal_leve_rotation_v31.yml`.
Foram confirmados manual-only na branch, mas **PR NÃO MESCLADO**. O CI #45207337525 falhou: 604 testes, 6 failures e 2 errors em testes de roteamento antigo Radar Tech/fallback; nenhum módulo Python de roteamento foi alterado no PR. Investigar/resolver o baseline e homologar antes de merge. Até lá não anunciar desativação de agendamentos de produção.

## Candidatos do proprietário à exclusão manual após revisão
- Eletroportáteis na Cozinha (11); Cadeira Certa no Home Office (7); Ar-Condicionado sem Dúvidas (4); Cabelos em Foco (10); Ventiladores em Foco (10); Guia de Achados & Ofertas (11); Moda e Ofertas (9); Liquidificadores em Foco (10); Café na Medida (6); Pedal Leve (12); Jardim e Horta na Prática (5).
- 7 origens têm pelo menos uma pauta aproveitada em DRAFT; Ar, Ventiladores, Pedal e Jardim não têm encaixe natural na seleção.
- Não confundir backup com redirecionamento ou preservação de SEO: ausência de verificação GSC/backlinks para a maioria e falta de redirect cross-Blogspot podem causar perdas. Os rascunhos novos ainda não estão LIVE. Especial cuidado com a página Loja Café na Medida (35 ofertas históricas).
- Blog delete não existe nos conectores desta sessão; exclusão será manual pelo proprietário, depois de decidir aceitar o risco residual de SEO e verificar o congelamento de fluxos antigos.

## Continuidade
- Manifesto detalhado dos 8 rascunhos está em branch do PR: `affiliate_hub_v31/BLOGGER_PORTFOLIO_FIVE_DRAFT_MIGRATION_2026-11-23.json`.
- Issue #131 segue como rastreio do plano; C103 e C104 contêm ressalvas SEO reais.
- Nenhum dado R2/D1, projetos Pinterest/Mercado Livre, WordPress ou blogs não listados nesta conexão foi alterado.
