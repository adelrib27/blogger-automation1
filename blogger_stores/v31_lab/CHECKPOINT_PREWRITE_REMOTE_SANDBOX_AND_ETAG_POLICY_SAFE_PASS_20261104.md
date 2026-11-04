# Checkpoint V31 R1 LAB — Claim de tentativa única em Git sandbox e política ETag SAFE

Data: 2026-11-04 (America/Recife). **VALIDADO EM SANDBOX/OFFLINE, NÃO É PUBLICAÇÃO NEM CLAIM REMOTO OPERACIONAL.**

## Identidade e estado operacional reconfirmado
- Repositório GitHub: `adelrib27/blogger-automation1`.
- Branch LAB: `lab/v31r1-shopee-safe-20261103`; `main` não alterada nesta etapa.
- Blogger LAB `4739187376492839837`, Page LOJA `2446067640331732447`, https://blog-teste-tema-worpress.blogspot.com/p/loja.html
- Tema `TEMA_BLOGGER_UNIVERSAL_V31_R1_PLAY_REFINADO_LAB.xml` aprovado e preservado.
- Reserva `PLAN` segunda rotação **real**, commit `801381b4e0d2d23fa60f478da67b6dca6ec3df32`, operação `2ab915f6079855824374fd9577411783bf6d8e5c2bca7eb36a4aa8e1d08d5a93` (NÃO criar outra).
- Ledger blob `8331d025d77fc752230eec71f6c7d8ba86ece5a5`, operações `PERSISTED + PLAN`; nenhum `prewriteClaim` operacional.
- Histórico blob `de0f022994ca47f0b8316169815afe25722fdfff`, duas entradas.
- Blogger `live`, `updated_at=2026-11-03T22:19:09-03:00`, 16 cards e links. Não houve PUT.
- Runner `0.8-v31r1-lab`: `daily_store_updates_enabled_by_runner=false`, `v31_enabled_for_new_blogs=false`.

## Implementação nesta etapa: arquivos novos e exclusivamente LAB
1. `blogger_stores/v31_core/v31_prewrite_claim_sandbox_safe.py`: propõe metadados de claim `ATTEMPT_CLAIMED_BEFORE_PUT` na operação `PLAN` e salva HTML backup **no mesmo commit Git**. Exige 2 operações, histórico correspondente, hash do HTML original, ETag forte, nonce aleatório, escopo LAB. Exercita dois clones disputando o mesmo `git push` não forçado em repositório local `bare` marcado como sandbox. Faz readback diretamente no bare remoto dos três objetos: backup, ledger e histórico intacto. Nunca conecta ao GitHub remoto real nem envia Blogger PUT.
2. `blogger_stores/v31_core/v31_blogger_etag_policy_safe.py`: classificador de evidência de `If-Match` **sem rede nem escrita**. Aceita estruturalmente apenas prova auditável de `blogger.pages.update` real com ETag FORTE e distinto, envio de `If-Match`, resposta `HTTP 412` e GET autenticado da página sem modificação. **Não existe tal prova real nesta etapa**. O classificador nunca autoriza publicação.
3. `blogger_stores/tests/v31_prewrite_claim/test_v31_prewrite_claim_sandbox_safe.py`: 48 testes de segurança, concorrência, integridade remota, bloqueio de repetição e políticas ETag.
4. `.github/workflows/v31_lab_prewrite_claim_remote_sandbox_safe.yml`: CI por `push` apenas para os novos arquivos da branch LAB, permissões `contents: read`, `actions: read`, sem credenciais persistidas, sem Blogger secrets, PUT, commits no ledger operacional, cron ou upload de artefatos.

## Evidência GitHub Actions
- Run https://github.com/adelrib27/blogger-automation1/actions/runs/41922704424 — **completed/success**, commit `5288781d9614c891a7830628dbfbca2645753f8b`.
- **257/257 testes PASS**: 48 novos + 30 publicador one-shot anterior + 32 prewrite gate + 28 Git write-gate + 14 Git read-only + 36 CAS + 26 recovery + 14 ledger + 29 atomic.
- Marcadores: `V31_PREWRITE_GIT_OPERATIONAL_STILL_UNCLAIMED_PASS` e `V31_PREWRITE_REMOTE_SANDBOX_CAS_PASS`.
- O HTML original da primeira rotação veio de artefato imutável (SHA256 `6f3810a364fe2114865b96fa5f118c10495bfe39943406624710ac9aaf25f450`); HTML candidato `d33070c001281ed795489a032a504accfcab2b593010c1a9e8cf5bb86b8109b8`.
- Não foi criado novo ZIP de artefatos no Actions, a pedido do usuário.

## Conclusão documental sobre ETag/If-Match — pendência real
- Documentação específica `https://developers.google.com/blogger/docs/3.0/reference/pages/update` informa PUT e identidade da página, mas não descreve garantia explícita de `412` com ETag stale.
- Documento geral `https://developers.google.com/blogger/docs/3.0/performance` recomenda `If-Match` para recursos que usam ETag, usando exemplos de API genérica. Isso **não é prova** do comportamento real `Blogger.pages.update`.
- O ETag é retornado por GET autenticado; ainda NÃO há evidência obtida por teste de `PUT` com ETag inválido contra uma página sacrificial. Não usar essa ausência como autorização para publicar.
- O teste de compatibilidade deve ser separado, isolado em página de teste não operacional, explicitamente autorizado, com prova de `412` + readback idêntico. Nunca testar `PUT` na LOJA da primeira rotação sem aprovação.
- A segurança não deve depender exclusivamente do cabeçalho de ETag sem comprovação: revalidar Git HEAD, HTML, backup, ID/URL, e bloquear em divergência.

## Próximo marco pendente
1. Integrar atestação **durável real** do backup original e claim remoto **não forçado no GitHub LAB**, atualizando readback do executor sem interpretar `PLAN` claim como publicação; obter autorização específica para a escrita operacional antes de qualquer commit de claim.
2. Validar a rejeição real de ETag stale do Blogger **numa página temporária separada**, com autorização própria (nenhum PUT foi realizado nesta etapa).
3. Somente após gates comprovados, preparar workflow de PUT único no LAB e solicitar autorização explícita separada. Não repetir se houver resultado incerto.
4. Após PUT autorizado: GET autenticado, Cloudflare `PUBLIC_EXACT_PASS`, persistência atômica ledger+histórico, teste recorrente diário, e replicação universal V31.
5. Limpeza de armazenamento do GitHub Actions permanece pendente para auditoria SAFE separada, sem exclusão agora.

**Limites:** não modificar `main`, outros blogs, Tema V31 R1 ou substituir pela V20 antiga. Este checkpoint NÃO autoriza Blogger PUT, claim GitHub operacional, atualização diária nem alterações de produção.
