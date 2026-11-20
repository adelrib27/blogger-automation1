# C80 — autenticação GitHub Actions → D1 oficial V31, SAFE

**PREVIEW EM_ANDAMENTO — gravada na main ANTES dos testes.**

## Confirmação recebida do proprietário
- Captura da página GitHub Environment `v31-editorial-safe`, em `adelrib27/blogger-automation1`, mostra `V31_D1_API_TOKEN` em **Environment secrets** atualizado `now` e variáveis `V31_EDITORIAL_R2_ACCOUNT_ID` / `V31_EDITORIAL_R2_BUCKET` da conta R2 oficial.
- Não recebemos valor do segredo e NÃO devemos solicitá-lo em chat ou log. Captura **não comprova autenticação** do token no D1; exige teste SELECT real.
- Identidade D1 destino imutável no código C75: account `ebb8d5b4cf9a2cb850c6d8051bd2661f`, database `9bfce7a4-6167-4bfc-a65e-a74c1a34f064` (`v31-universal-ready-safe`). Ambiente protegido V31 deve ser explicitamente usado.
- Continuidade anterior: C79 [PR #104](https://github.com/adelrib27/blogger-automation1/pull/104) CI 537 PASS; [canário R2 #44776685517](https://github.com/adelrib27/blogger-automation1/actions/runs/44776685517) real CAS/412 PASS e objeto sintético removido; D1 com quatro tabelas e zero dados no último SELECT.

## Etapas da C80
1. Criar workflow temporário com `environment: v31-editorial-safe` e permissão `contents: read`, branch `main`, token somente na variável de processo `V31_D1_API_TOKEN` sem qualquer print/artefato.
2. Usar `CloudflareD1HTTPRunner.from_environment(allow_mutations=False)` com UUID e account oficiais fixos (não usar credenciais de outra conta); consultar **somente SELECT** em `sqlite_master` e contagens de quatro tabelas; testar bloqueio local de INSERT por padrão. Nenhuma escrita D1/CMS/R2.
3. Se GitHub Actions confirmar sucesso e ausência de registros imprevistos, remover workflow temporário e registrar prova. Em caso de falha, não adulterar segredo nem dar fallback para D1 de outra conta; registrar bloqueio sem revelar token.
4. Somente após SELECT autenticado, planejar canário SQL isolado de concorrência com limpeza e sem writer, seguido de ligação do envelope R2 C79 ao D1 C76 e DRAFT real; LIVE continua individual e não permitido por autorização geral.

## Escopo protegido
- Conta Cloudflare `adeiltonrib27@gmail.com` do R2 oficial, D1 exclusivo; não alterar `adeiltonrml`, `comercebem`, Vida Pet, ARV, Pinterest, outros bancos, crons, CMS ou URLs Shopee.
- A opção de token **sem expiração** é decisão do proprietário, mas demanda revisão/rotação programada; acesso de conta D1 Edit não é restrito ao único banco, por isso o código fixa conta+database e o runner nega escrita por padrão.

**Estado inicial C80:** `EM_ANDAMENTO`; apenas prévia escrita no GitHub. `mutation_in_progress=false`, `remote_operation_in_progress=false`.

## C80.1 — token GitHub validado em D1 real, somente leitura
- [GitHub Actions #44786171930](https://github.com/adelrib27/blogger-automation1/actions/runs/44786171930) **SUCCESS**, ambiente protegido `v31-editorial-safe`, credencial `V31_D1_API_TOKEN` por `${{ secrets... }}`, account/database oficiais fixos; nenhum token/URL privada exposto.
- Logs finais comprovam `V31_C80_GITHUB_D1_TOKEN_AUTHENTICATED=true`, `V31_C80_D1_READ_ONLY_QUERY_PASS=true`, `V31_C80_D1_OFFICIAL_FOUR_TABLES_PASS=true`, `V31_C80_D1_READBACK_ZERO=true`, `V31_C80_D1_WRITES_DISABLED_BY_DEFAULT=true` e `V31_C80_NO_CMS_R2_OR_FIRECRAWL_CALLS=true`.
- Essa prova substitui a observação antiga C79 de segredo D1 ausente: o segredo NOVO foi cadastrado pelo proprietário e funciona. O primeiro teste foi estritamente SELECT, sem mutação.

## C80.2 — próximo teste sintético isolado de concorrência
- Executar workflow TEMP e **somente nele** colocar `V31_D1_SAFE_WRITES_ENABLED=V31_D1_SAFE_SQL_ONLY`, além de `allow_mutations=True`. Em todos os workflows permanentes, escrita permanece desativada.
- Dois pedidos de lease `refill` simultâneos pelo cliente D1 HTTP C75, para site/campanha sintéticos únicos do run, exigem um único vencedor, adversário bloqueado, liberação por proprietário correto, recuperação de expiração e limpeza por tenant.
- Readback final zero nas quatro tabelas; falha implica parar/registrar e nunca acionar CMS/Firecrawl/arquivos R2 ou outro D1. Remover workflow após o teste.

**Estado intermediário:** autenticação real D1 comprovada; aguardando ensaio concorrente com dados sintéticos. 0 posts.
