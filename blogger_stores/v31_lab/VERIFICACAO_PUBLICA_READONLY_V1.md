# V31 — verificação pública independente e read-only (LAB)

Escopo rígido: blog `4739187376492839837`; página `2446067640331732447`; URL canônica `https://blog-teste-tema-worpress.blogspot.com/p/loja.html`.

## Problema observado
A primeira publicação real Shopee V23 → V31 do LAB foi confirmada no Blogger Bridge e na página pública, mas o verificador pós-PUT do GitHub Actions consultou o Blogger 6 vezes em uma rota com query variável (`?v31_daily_verify=`) e recebeu HTTP 429. Workflow de escrita #41753180692 foi marcado `failure`, apesar de o conteúdo ter sido efetivamente publicado. Não repetir a publicação.

## Correção arquitetural em LAB
- Separar **mutação** de **aceitação pública**. Este pacote nunca escreve no Blogger.
- Usar exclusivamente GET à URL canônica, sem query mutável; checar o HTML completo, tema V31 R1 e produto, imagem, categoria e link exatamente na ordem do artefato Shopee autenticado SAFE aprovado.
- Reconhecer `HTTP 429` ou `503` como estado `PUBLIC_PENDING_THROTTLED`; jamais marcar como sucesso nem disparar novo PUT/rollback por causa de rate limit.
- O workflow SAFE não tem schedule, não possui permissões de conteúdo de escrita, não injeta credenciais Blogger/Shopee, e dispara somente por arquivo de laboratório. O download do artefato usa `actions:read`.
- 14 testes unitários locais autônomos (sem rede) incluem simulações de 429, troca de cards/fotos/links e rejeição de redirecionamentos.

## Não coberto / gates ainda pendentes
- Validar retorno do GitHub Actions real a partir de seu próprio IP.
- Construir recuperação do estado `PUBLISHED_PENDING_PUBLIC` e só persistir rotação após sucesso público automatizado; prevenir duplicação pelo `selection_sha256`.
- Promover agendamento diário somente após validação completa e repetida em LAB.
- Nenhuma alteração em `main`, blogs de produção ou Runner Windows; flags permanecem false.