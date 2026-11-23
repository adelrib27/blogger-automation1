# V31 C139 — decisão de escopo: todos os blogs atuais ativos; qualidade acima de quantidade

**Data:** 2026-11-23 (America/Recife).
**Código de retomada:** `V31-C139-20261123-SCOPE-5-BLOGGER-3-WP-EXCLUDE-ARCOND-QUALITY-FIRST-LIVE-OFF`.
**Status:** DIRETRIZ DO PROPRIETÁRIO REGISTRADA; **nenhum rollout/writer LIVE autorizado**.

## Regra solicitada pelo proprietário
- Trabalhar com **TODOS os blogs atualmente existentes, ativos e acessíveis do Blogger**, exceto o **Ar-Condicionado sem Dúvidas** (ID `2228849984262880811`), que o proprietário pretende desativar permanentemente em breve. **Não deletar nem desativar o blog por conta própria; apenas EXCLUIR novos artigos e automação editorial V31 nele.**
- Abranger **TODOS os WordPress atualmente ativos** (Casa e Decoração, Oficina & Garagem e Radar Tech BR).
- Priorizar **QUALIDADE, coerência, originalidade, SEO, links internos, foto real, CTA afiliado exato e não duplicação**. Não implantar teto global artificial de três artigos; manter cotas diárias sustentáveis por site/canal.
- Possibilitar blogs novos futuramente com a mesma arquitetura universal; não reabrir implementação em um nicho específico.
- `DRAFT` e homologação gradativa por site **não equivalem** a ativação automática LIVE. Política `pending_policy_approval` e confirmação final explícita permanecem.

## Inventário autenticado nesta conversa
A chamada **Blogger Bridge V2 list_blogs** retornou seis blogs na conta atualmente conectada:
1. `1439741542627895062` — Móveis para Cada Canto — alvo.
2. `7757953554206491487` — Limpeza Inteligente — alvo.
3. `4830103887652146866` — Estilo no Dia a Dia e Acessórios — alvo.
4. `3552757910439359679` — Cozinha Sem Complicação — alvo.
5. `8052455848487624244` — Vida Pet Prática — alvo a integrar **após verificar campanha Shopee real e cadastrar rota V31**, sem inventar.
6. `2228849984262880811` — Ar-Condicionado sem Dúvidas — **EXCLUIR** do novo rollout editorial, não excluir os dados existentes sem pedido.

Três conectores WordPress autenticados responderam a **GET /wp/v2/posts** com posts publicados, e os alvos possuem rotas registradas no V31:
- `wordpress_casa_decoracao` — `https://casaedecoracao.radartechbr.com.br/`
- `wordpress_oficina_garagem` — `https://oficina.radartechbr.com.br/`
- `wordpress_radartechbr` — `https://radartechbr.com.br/`

**Instantâneo do escopo conhecido: 5 Blogger + 3 WordPress = 8 alvos.** Esse valor reflete apenas as contas e fontes conectadas verificadas em 23/11; é uma fotografia, **NÃO um limite de oito ou de cinco blogs**. Ao descobrir outro blog ativo futuramente, verificar a propriedade/CMS/campanha e adicioná-lo sem reconstruir o V31. A consulta não prova ausência de blogs em outras contas não conectadas.

## Distinção com fontes históricas e código existente
- `BLOGGER_PORTFOLIO_FIVE_2026-11-23.json` é um *backup histórico de seleção/migração*, contendo blogs de origem antigos; **não deve servir como filtro permanente nem como autorização de novos posts**. Apesar de haver cinco Blogger atuais neste instantâneo, esse número não é teto fixo.
- `affiliate_hub_v31/site_routes.json` e `sites.d` possuem rotas de alguns blogs antigos e ainda incluem Ar-Condicionado; a existência de rota antiga **não significa blog ativo/selecionado**. Antes do próximo rollout, implementar guard de escopo nos pontos de planejamento/seleção de writes e conciliar o registry com a lista autenticada.
- `blogger_vida_pet_pratica` é blog CMS real e alvo editorial declarado, mas **sem campanha verificada/rota V31** até esta auditoria; não ativar DRAFT nele sem esse pré-requisito.
- Casa WP continua com READY conflitante com DRAFT #314 (C135), não consumir, não recriar. C137 confirmou 12 candidatos de três Blogger, 0 URLs de afiliados cacheadas em suas campanhas. C138 confirmou fila de dois pedidos ativos e limite de tentativas de conversão 3/3 no dia UTC 23/11; não contornar quota.

## Registro oficial do escopo
Arquivo estruturado criado na `main`: [`EDITORIAL_ACTIVE_SCOPE_POLICY.json`](EDITORIAL_ACTIVE_SCOPE_POLICY.json), commit `b9718a376194c3a5c71d878ca77e5fb530e147c9`. A política **declarativa** NÃO ativa writers, flags, chamadas Shopee, D1 ou LIVE. Este checkpoint preserva a intenção exata para retomada em chats novos e jobs seguintes.

## Próxima fase técnica
1. Fazer reconciliação de escopo autenticado, de forma dinâmica, sempre excluindo Ar-Condicionado e evitando incluir blogs de origem históricos sem verificação de atividade. O guard operacional ainda precisa ser integrado a planejadores e writers V31; não declarar essa integração como concluída.
2. Homologar individualmente DRAFT real e a fonte factual para os atuais cinco Blogger e três WordPress, sem resetar limite, converter link fictício ou publicar LIVE. Vida Pet exige verificação de campanha + rota.
3. Manter monitor C136 e os relatórios C137/C138 ativos como evidências; exigir hashes/GET CMS e antirrepetição antes de escrita.
4. Qualidade antes de volume; separar Pinterest e Mercado Livre deste projeto.

**Ações nesta etapa:** leitura das seis identidades Blogger, dos três WordPress e do estado GitHub; criação/atualização **apenas de documentação/estado na main**. Nenhum artigo criado, alterado ou publicado; nenhuma alteração D1, R2, Shopee ou LIVE.
