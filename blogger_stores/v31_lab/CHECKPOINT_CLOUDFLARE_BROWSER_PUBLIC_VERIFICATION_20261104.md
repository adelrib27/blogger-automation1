# Checkpoint — rota independente para verificação pública V31 LAB

## Contexto e causa

- Verificador direto no GitHub Actions: execução #2 `41758935782`, job `126341697951`.
- **14 testes unitários passaram** e o SHA-256 do artefato Shopee passou.
- GET HTTP direto à URL canônica da LOJA, a partir do runner hospedado do GitHub, retornou **HTTP 429**.
- Resultado correto: `PUBLIC_PENDING_THROTTLED`, `public_verified=false`, `publication_attempted=false`, código de saída 75.
- **Não rerodar** workflow de publicação `v31_lab_first_shopee_live_once.yml`: a gravação foi confirmada anteriormente.

## Nova rota: Cloudflare Browser Rendering REST API (probe read-only)

- A rota documentada `POST /accounts/{account_id}/browser-rendering/content` foi identificada no OpenAPI Cloudflare.
- Foram feitas duas consultas ao HTML público canônico `https://blog-teste-tema-worpress.blogspot.com/p/loja.html` usando Browser Rendering, sem criar Worker e sem modificar Blogger.
- Primeira consulta: resposta Cloudflare `success=true`, HTML ~175 KB, marcadores V31 presentes uma vez cada, Tema V31 R1 e 16 cards presentes.
- Segunda consulta independente: comparação de **listas ordenadas e exatas** entre HTML público obtido via Browser Rendering e `Blogger Bridge V2 get_page` ao vivo:
  - **16/16 IDs:** iguais.
  - **16/16 categorias:** iguais.
  - **16/16 links afiliados:** iguais.
  - **16/16 URLs de imagens:** iguais.
  - Tema V31 R1 detectado; marcadores `UNIVERSAL_V31_STORE_AUTO_START/END` presentes uma vez cada.
- Page ID `2446067640331732447`, Blog ID `4739187376492839837`; última atualização observada `2026-11-03T22:19:09-03:00`.
- A chamada foi feita por ferramenta autenticada Cloudflare, em leitura; **nenhum Worker, secret, tarefa, workflow ou blog de produção foi criado ou modificado.**

## Interpretação rigorosa

**VALIDADO EM LAB (leitura manual assistida):** o Cloudflare Browser Rendering conseguiu obter a página pública verdadeira que o runner GitHub recebeu como 429; HTML dos produtos coincidiu exatamente com a API Blogger.

**NÃO VALIDADO (automação):** não há ainda implementação de GitHub Actions/Cloudflare para receber/assinar/arquivar a prova automática, nem garantia de que Browser Rendering sempre retornará 200. Não habilitar agendamento, não alterar `PUBLISHED_PENDING_PUBLIC` e não promover produção.

## Engenharia aprovada como direção, sujeita a SAFE

1. Contrato de verificação público **pluggable**, com fonte HTTP direto e Browser Rendering, proibindo qualquer marcação de sucesso sem IDs, categorias, URLs de imagem/afiliado e marcadores iguais ao catálogo aprovado.
2. A autenticação da rota alternativa deve usar credencial de escopo mínimo em secret próprio, não exposta em arquivos, logs ou frontend; isolar ambiente LAB. Verificar custos/limites e autorização antes de integrar conta Cloudflare ao job GitHub.
3. Distinguir `PUBLIC_EXACT_PASS`, `PUBLIC_PENDING_THROTTLED`, `PUBLIC_DIVERGENCE` e `VERIFIER_UNAVAILABLE`. HTTP 429 nunca converte em sucesso e nunca repete PUT.
4. Persistir prova e histórico por operação idempotente com controle concorrente, e validar recuperação pós-reinício/execução duplicada antes de ativar cron.
5. Testar a integração automática em GitHub SAFE e validar seu artefato real antes de mover ledger para `PUBLIC_VERIFIED`.

## Estado

- Runner: `0.8-v31r1-lab`; `v31_enabled_for_new_blogs=false`, `daily_store_updates_enabled_by_runner=false`.
- LOJA LAB preservada com 16 produtos, 16 fotos e 16 links; sem publicação adicional neste checkpoint.
- Rota Browser Rendering **validada em leitura**; ciclo diário autônomo **pendente**.
