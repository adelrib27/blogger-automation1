# Checkpoint — Integração Cloudflare Browser Rendering V31 LAB em SAFE

Data técnica: 2026-11-04 UTC. Escopo: `adelrib27/blogger-automation1`, branch `lab/v31r1-shopee-safe-20261103`.

## O que foi observado no estado real

- Runner `0.8-v31r1-lab`, `AUDIT_OK`.
- Flags: `v31_enabled_for_new_blogs=false` e `daily_store_updates_enabled_by_runner=false`.
- LOJA LAB: blog ID `4739187376492839837`, Page ID `2446067640331732447`, 16 produtos, 16 imagens, 16 links; página atualizada em `2026-11-03T22:19:09-03:00`.
- O verificador GitHub Actions anterior passou 14 testes e verificou SHA da seleção, mas recebeu HTTP 429 na consulta HTTP pública e retornou `PUBLIC_PENDING_THROTTLED` (código 75). Não houve re-publicação.
- Consulta ao vivo Cloudflare Browser Rendering REST (`content`, cacheTTL=0) havia demonstrado HTML público exato vs Blogger Bridge: 16 IDs, 16 categorias, 16 links e 16 URLs de imagens coincidentes. **Somente validação manual assistida**.

## Implementação nessa etapa

- Novo adaptador `blogger_stores/src/v31_public_verify_cloudflare.py` **somente leitura**. Usa o mesmo `reference()` e `verify_html()` de `blogger_stores/src/v31_public_verify_readonly.py`, sem reimplementar regras de catálogo.
- Fonte pública fixa: `https://blog-teste-tema-worpress.blogspot.com/p/loja.html`.
- Cloudflare API oficial por `POST /client/v4/accounts/{id}/browser-rendering/content?cacheTTL=0`, sem Worker novo; token apenas por variável de ambiente, resposta máxima de 4MB e **redirecionamentos proibidos** para não encaminhar bearer token a terceiros.
- Erros 429/503/504 e indisponibilidade de rede => `PUBLIC_PENDING_THROTTLED`, exit 75. Erro de autenticação, seleção adulterada, fotos/links/IDs divergentes, HTML incompleto => `PUBLIC_VERIFICATION_FAILED`, exit 2. Somente a correspondência exata confirma `PUBLIC_EXACT_PASS`, exit 0.
- Workflow `.github/workflows/v31_lab_cloudflare_contract_safe.yml` para testes offline sem credenciais, sem rede e sem escrita, acionado na branch LAB pelo arquivo `blogger_stores/lab/v31_cf_contract.trigger`.
- Workflow `.github/workflows/v31_lab_cloudflare_public_live_readonly.yml` **preparado mas NÃO ACIONADO**. Lê artefato Shopee previamente aprovado, exige SHA pin e secrets GitHub LAB exclusivos, verifica catálogo e publica apenas relatório efêmero de auditoria (GitHub Actions artifact); **não possui cron nem Blogger OAuth nem contents:write**.

## Evidências de teste

- Ambiente local: Python 3.13, `python -m unittest discover -s blogger_stores/tests/v31_cf`: **22/22 OK**.
- Mesmo ambiente: testes existentes de `blogger_stores/tests/v31_public`: **14/14 OK**.
- CI de contrato Python 3.12: disparada por commit `8c90be57fdda407234b30c01c8b5d2e016addafe`; **resultado da execução ainda NÃO confirmado**. Não declarar sucesso de CI sem consultar run real.
- Arquivos no GitHub branch LAB foram re-lidos após commit e conferidos byte a byte contra os textos enviados.
- Nenhum blog, tema ou workflow de produção foi alterado. Branch `main` preservada.

## Limitações e critérios para continuar

1. Configurar uma credencial Cloudflare **dedicada e de escopo mínimo** para Browser Rendering/Browser Run no GitHub, usando `V31_CF_LAB_ACCOUNT_ID` e `V31_CF_LAB_BROWSER_TOKEN` como repository/environment secrets somente com autorização específica. Não reutilizar credenciais do ChatGPT ou token administrativo.
2. Somente depois disparar explicitamente a rota LIVE READ-ONLY. O workflow está preso ao artefato Shopee V23 `run-id 41751202914` e SHA `46ef8a293875720f036d90430d1e57c862277b42bde966fbf34b15f9d2cb6c0c`: é um **teste de aceitação único**, não automação diária definitiva. Artefatos Actions são temporários: verificar disponibilidade antes de executar.
3. Conferir CI e relatório contendo `PUBLIC_EXACT_PASS` e hashes; simular 429/401/divergência e validar que não há repetição de PUT.
4. **Somente após o fluxo LIVE READ-ONLY aprovado**, vincular prova autenticada ao ledger com compare-and-swap e persistência idempotente do histórico, testar retomada e reinício.
5. Nenhuma ativação diária, alteração de flags, provisionamento de outros blogs ou promoção para produção nesta etapa.

Status resumido: `CLOUDFLARE_ADAPTER_OFFLINE_SAFE_PASS`; `GITHUB_CONTRACT_CI_PENDING`; `AUTOMATED_PUBLIC_PROOF_PENDING`; `DAILY_ROTATION_DISABLED`.