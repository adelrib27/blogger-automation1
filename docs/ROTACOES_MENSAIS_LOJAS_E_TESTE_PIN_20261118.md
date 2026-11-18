# Rotações das Lojas — alteração mensal de 18/11/2026

**Projeto:** AR VARIEDADES — automações Blogger/WordPress.  
**Repo de execução:** `adelrib27/blogger-automation1`, branch `main`.  
**Regra adotada:** **exatamente 1 agendamento automático/mês por Loja**, com os dias de execução distribuídos entre **1 e 26** e preservação dos horários que cada workflow já utilizava. Horários abaixo convertidos para **America/Recife (UTC-3 em novembro/2026)**. Esta regra é sobre o **cron de atualização da Loja**, não sobre publicações de artigos.

| Dia do mês | Loja | Plataforma | Hora Recife | Workflow alterado |
|---|---|---|---|---|
| 01 | Achadinhos de Beleza | Blogger | 10:35 | `.github/workflows/achadinhos_beleza_store_autonomous.yml` |
| 02 | Achados da Rotina V31 | Blogger | 06:00 | `.github/workflows/achados_da_rotina_rotation_v31.yml` |
| 03 | Achados que Valem | Blogger | 09:50 | `.github/workflows/achados_que_valem_store_autonomous.yml` |
| 04 | Air Fryers em Foco | Blogger | 09:05 | `.github/workflows/air_fryers_store_autonomous.yml` |
| 05 | Ateliê Criativo V31 | Blogger | 06:00 | `.github/workflows/atelie_criativo_rotation_v31.yml` |
| 06 | Liquidificadores em Foco | Blogger | 08:35 | `.github/workflows/blogger_liquidificador_store_autonomous.yml` |
| 07 | Cabelos em Foco | Blogger | 08:50 | `.github/workflows/cabelos_store_autonomous.yml` |
| 08 | Casa em Ordem | Blogger | 08:05 | `.github/workflows/casa_em_ordem_store_autonomous.yml` |
| 09 | Casa e Decoração | WordPress | 08:10 | `.github/workflows/casa_store_autonomous.yml` |
| 10 | Conecta Achados | Blogger | 07:35 | `.github/workflows/conecta_achados_store_autonomous.yml` |
| 11 | Cozinha Sem Complicação | Blogger | 11:05 | `.github/workflows/cozinha_sem_complicacao_store_autonomous.yml` |
| 12 | Eletroportáteis na Cozinha | Blogger | 09:05 | `.github/workflows/eletroportateis_store_autonomous.yml` |
| 13 | Escolha Certa Online | Blogger | 08:20 | `.github/workflows/escolha_certa_online_store_autonomous.yml` |
| 14 | Estilo no Dia a Dia | Blogger | 07:50 | `.github/workflows/estilo_dia_a_dia_store_autonomous.yml` |
| 15 | Guia de Achados & Ofertas | Blogger | 10:05 | `.github/workflows/guia_achados_ofertas_store_autonomous.yml` |
| 16 | Limpeza Inteligente | Blogger | 09:20 | `.github/workflows/limpeza_inteligente_store_autonomous.yml` |
| 17 | Mala Pronta V31 | Blogger | 06:17 | `.github/workflows/mala_pronta_rotation_daily_v31.yml` |
| 18 | Moda e Ofertas | Blogger | 10:20 | `.github/workflows/moda_ofertas_store_autonomous.yml` |
| 19 | Oficina & Garagem | WordPress | 08:30 | `.github/workflows/oficina_store_autonomous.yml` |
| 20 | Pedal Leve V31 | Blogger | 06:00 | `.github/workflows/pedal_leve_rotation_v31.yml` |
| 21 | Radar Tech BR | WordPress | 07:40 | `.github/workflows/radar_store_autonomous.yml` |
| 22 | Portal Radar Tech Blogger | Blogger | 10:50 | `.github/workflows/radar_tech_blogger_store_autonomous.yml` |
| 23 | Ventiladores em Foco | Blogger | 09:35 | `.github/workflows/ventiladores_store_autonomous.yml` |
| 24 | Vitrine Prática | Blogger | 08:35 | `.github/workflows/vitrine_pratica_store_autonomous.yml` |
| 25 | Casa Prática Lab | Blogger | 10:20 | `.github/workflows/casa_pratica_lab_store_page_autonomous.yml` |
| 26 | Vida Pet Prática | Blogger | 11:35 | `.github/workflows/vida_pet_pratica_store_page_autonomous.yml` |

## Auditoria e escopo
- **26 workflows de Loja alterados e relidos no GitHub**, todos com cron mensal (campo day-of-month fixo 1–26, meses `*`). **23 Blogger e 3 WordPress.** Os três WordPress são `Casa e Decoração`, `Oficina & Garagem` e `Radar Tech BR`.
- A rotina `Achados da Rotina` deixou de executar a cada 20 minutos: agora tem cron `0 9 2 * *`, isto é, **dia 2 às 06:00 de Recife** (09:00 UTC).
- Nas quatro rotações V31 (`Achados da Rotina`, `Ateliê Criativo`, `Mala Pronta`, `Pedal Leve`), `LIVE` foi restringido ao evento `schedule`; execuções por `push`, PR ou manual seguem em `DRY_RUN=true`. Os gatilhos de `push` deixaram de incluir o próprio arquivo YAML, mantendo os testes SAFE em PR. Isso evita publicações LIVE acidentais ao editar configuração.
- Workflows legados `casa_pratica_lab_store_autonomous.yml`, `limpeza_store_autonomous.yml` e `ventiladores_em_foco_store_autonomous.yml` já eram exclusivamente manuais; **não foram agendados**.
- Conferidos via WordPress MCP os eventos nativos de WP-Cron em `radartechbr.com.br` (Radar), `casaedecoracao.radartechbr.com.br` e Oficina & Garagem: nenhum evento com hook de Loja/Shop/Store/Shopee. **Crons internos de manutenção do WordPress preservados**.
- Não foram alterados agendamentos editoriais, manutenção WordPress, Blogger páginas existentes, Pinterest V83, Cloudflare D1 ou conteúdo dos produtos.
- **Limitação:** esta auditoria comprova a configuração mensal dos 26 workflows, **não** uma execução mensal real já concluída; futuras execuções dependem de GitHub Actions e das respectivas credenciais. Alguns testes SAFE V31 disparados por mudanças em YAML apresentaram `failure`, mas os logs mostram `*_STORE_DRY_RUN: true`; não são comprovação de atualização LIVE nem razão para afirmar que os crons não foram alterados. Auditorias gerais do Blogger também falharam/cancelaram por múltiplos commits, a investigar separadamente.
- Eventos adicionais `push` de arquivos de kickoff continuam disponíveis para ações explícitas; não são agendamentos diários.

## Cobertura de blogs com Loja mas SEM rotação diária localizada

Uma leitura adicional da conta Blogger via API listou páginas `Loja` ou `LOJA` nos seguintes blogs **sem correspondência com workflow de Loja diário no inventário GitHub verificado**:

| Blog | Blog ID | Observação |
|---|---|---|
| Cadeira Certa no Home Office | `7163624325768776034` | Página Loja existe; sem cron de Loja localizado |
| Café na Medida | `4820923154548273510` | Página Loja existe; sem cron de Loja localizado |
| Violão do Começo — Acordes e Cuidados | `370856880185231084` | Página LOJA existe; sem cron de Loja localizado |
| Casa Leve e Funcional | `4739187376492839837` | Página LOJA existe; sem cron de Loja localizado |
| Jardim e Horta na Prática | `3644898524310766003` | Página LOJA existe; sem cron de Loja localizado |
| Achados para Casa | `1426630233929943394` | Página LOJA existe, mantida fora da V31 (blog backup) |

**Importante:** nenhuma dessas seis páginas foi alterada; a solicitação de converter frequências diárias não justifica inventar um novo writer para blogs sem rotina de Loja agendada localizada. Para cobrir as cinco não-backup, é necessário primeiro identificar/validar a origem de dados e o writer real. Outros dois blogs da conta não tinham páginas publicadas. Portanto, **26 schedules mensais modificados ≠ todas as páginas Loja da conta com um sistema de atualização mensal ativo**.

A conta WordPress.com também possui sites antigos, privados, em preparação ou desconectados que **não têm rotação comercial identificada** neste repositório. Os três WordPress self-hosted com `store_autonomous.yml` foram modificados.

## Teste único Pinterest independente
- **Uma publicação de teste**, agendada via **Metricool** na conta Pinterest conectada `ar_variedades` às **13:00, 18/11/2026, Recife**.
- Post Metricool `432975502`, board Pinterest resolvido `1131811018795306537`, `autoPublish=true`, `status=PENDING` na confirmação. Fonte pública: artigo `Como escolher a cadeira ideal para sua varanda` no WordPress `Casa e Decoração`, usando imagem de destaque do próprio blog (media ID `299`). Não utiliza link novo da API Shopee.
- Pin **ainda não comprovadamente publicado** antes das 13h; verificação independente agendada às 13:15.
- **Nenhuma alteração no Pinterest V83**: agendamento feito em ferramenta separada, sem acessar Worker, tokens, D1 ou cron do V83.

## Auditoria posterior solicitada — teste antigo de alta frequência
- Confirmado **novamente** em `.github/workflows/achados_da_rotina_rotation_v31.yml`: cron **`0 9 2 * *`** (dia 2 de cada mês, às 06:00 Recife) e o modo LIVE só para `schedule`. O antigo agendamento de **20 minutos está DESATIVADO**; não remover o cron mensal solicitado.
- Localizado outro diagnóstico SAFE temporário, independente do teste 20min, em `.github/workflows/v31_lab_daily_autonomous_dispatch.yml`: `*/5 15-16 5 11 *` (5min no dia 5 de novembro). Isso voltaria anualmente por causa do campo ano ausente no cron. Foi **REMOVIDO** em 18/11/2026, commit `7ecf24baccbc8bd992b0316a3cd442289486c035`.
- Os dois horários `17 10 * * *` e `23 15 * * *` da ponte editorial LAB foram preservados: **não são cron de Loja de 20 minutos**. Não desligar editoriais sem escopo explícito.
- V83 auditado separadamente: às 14h Recife, cron executou mas `SHOPEE_QUERY_UNAVAILABLE` (6/6 falhas de descoberta), sem publicar novo Pin. Não reduzir esse erro automaticamente a `quota`; o secret Cloudflare V83 precisa ser conferido após rotação feita apenas no GitHub.

## Retomada
Para validar alterações: reler cada YAML na branch `main`, consultar o estado de cada workflow e o próximo `schedule`. Para resultado do Pin, consultar ID `432975502` no Metricool após as 13h. Não confundir `PENDING` com publicado. Evitar duplicar Pin de teste.

## Correção de escopo do teste Pinterest — 18/11/2026, após 13h
- **Resultado real:** Metricool post ID `432975502`, rede Pinterest `ERROR`, HTTP `400`, resposta `Sorry! We blocked this link because it may lead to spam.`. **Nenhum Pin foi publicado.**
- **Falha de metodologia admitida:** este teste usou destino WordPress, que NÃO integra o contrato comercial AR VARIEDADES PFE. O erro do Pinterest não deve ser extrapolado para todos os blogs ou para links de produtos Shopee.
- **Contrato canônico de fontes:** a fonte primária é **Shopee Affiliate Open API**; os dois CSVs são a **fonte alternativa de catálogo** quando a busca pela API falha ou não apresenta ofertas adequadas. `product_short link` / `shope.ee` do CSV é apenas candidato comercial, não atribuição afiliada automaticamente comprovada. Selecionar produto elegível → converter via `generateShortLink` ou revalidar link previamente verificado → revisão e gates editoriais → publicação pelo publicador autorizado. Se a API falhar sem um link verificável, reter o Pin.
- Não usar URL de artigo Blogger/WordPress como substituto automático do destino de produto afiliado. O publicador Pinterest V83 permaneceu **não modificado**; nenhuma tentativa adicional foi criada.
- **Não reprogramar o mesmo post nem trocar destino só para contornar o bloqueio.** A próxima prova comercial precisa do pipeline original, aprovação editorial, link afiliado confirmado e autorização de publicação distinta.
