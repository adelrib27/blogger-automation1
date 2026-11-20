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
