# Checkpoint LAB V31 — Correção de import do verificador público

## Evidência do defeito
- Run GitHub Actions **41756165331**, job **126332666580**: falha em `Testes do verificador puro`.
- Erro: `ModuleNotFoundError: No module named 'v31_public_verify_readonly'`.
- O teste em `blogger_stores/tests/v31_public/test_v31_public_verify_readonly.py` referenciava `Path(__file__).resolve().parents[1]/'src'`, o que aponta para `blogger_stores/tests/src`; o módulo verdadeiro está em `blogger_stores/src`.
- O job parou antes de baixar a seleção, consultar Blogger ou verificar a página pública.

## Correção mínima de contrato
- Alteração somente na branch `lab/v31r1-shopee-safe-20261103`, commit `b0a6b8c72eb39f658ab7614a2339174c8b30c908`.
- Corrigido import para `Path(__file__).resolve().parents[2]/'src'`, independente da pasta de instalação ou CWD.
- Excluída variável `ROOT` inativa que apontava para pasta temporária estranha à estrutura do repositório.
- Nenhuma alteração na lógica de produção do verificador; nenhum ajuste de critérios, de links, de quotas ou de permissões.

## Teste reproduzível
Em espelho de diretórios equivalente ao GitHub (`blogger_stores/src` e `blogger_stores/tests/v31_public`):
- Antes: `python -m unittest discover -s blogger_stores/tests/v31_public -v` reproduziu exatamente `ModuleNotFoundError`.
- Depois: o mesmo comando passou **14/14** testes; `PYTHONPATH=''` não impediu os testes. Também passou `python -m py_compile`.
- Este teste local foi feito em Python 3.13; GitHub usa Python 3.12, logo o status de CI ainda deve ser verificado.
- Disparo de revalidação read-only: commit `570a26454ed3c2f3af86acea133680690ed33a2f`.

## Estado e segurança
- LOJA LAB: primeiro catálogo real de 16 produtos publicado em `2026-11-03T22:19:09-03:00`, sem nova escrita desde então, conforme Blogger Bridge consultado antes desta correção.
- Sem novas publicações de produtos, sem alterações em `main` ou blogs de produção.
- `v31_enabled_for_new_blogs=false` e `daily_store_updates_enabled_by_runner=false` permanecem.
- **Não declarar o verificador automático como validado** até observar o run atualizado e confirmar resultado + relatório. HTTP 429 deve resultar em pendência, nunca sucesso ou nova gravação.
