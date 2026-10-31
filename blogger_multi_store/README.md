# Blogger Multi Store — implantação de lojas Shopee

Camada criada em 2026-10-31 para levar a arquitetura de loja já validada no Blogger a todos os blogs da conta que ainda não possuíam loja.

## Estado de origem

Auditoria inicial da conta Blogger:

- 18 blogs na conta;
- 1 loja completa pré-existente: Liquidificador Philips Walita RI2242;
- 17 blogs sem página `Loja` e sem post LIVE com título exato `Loja`.

A loja Philips permanece como referência funcional da arquitetura original (post Loja + página estável `/p/loja.html` + rotação Shopee própria). Esta camada multi-store não sobrescreve a loja Philips.

## Arquitetura adotada

Cada nova loja usa duas peças:

1. **Post LIVE `Loja`** — vitrine comercial; contém apenas ofertas reais previamente validadas ou, na futura rotação, dados vindos diretamente da Shopee Affiliate API.
2. **Página LIVE `Loja`** — endereço estável `/p/loja.html`, que redireciona/canonicaliza para o post Loja atual.

O HTML gerenciado pelo bootstrap é delimitado por:

```html
<!-- BLOGGER_MULTI_STORE_AUTO_START -->
...
<!-- BLOGGER_MULTI_STORE_AUTO_END -->
```

Links comerciais devem manter:

```text
rel="nofollow sponsored noopener"
```

## Segurança

O bootstrap é idempotente e fail-safe:

- procura post LIVE com título **exatamente** `Loja` antes de criar;
- procura página LIVE com título **exatamente** `Loja` antes de criar;
- não duplica objetos encontrados;
- valida post e página após a criação;
- usa backoff progressivo em HTTP 429 / rate limit do Blogger;
- não exclui posts ou páginas;
- não altera posts editoriais existentes;
- não inventa preço, estoque, especificação ou imagem;
- quando não existe imagem real validada no snapshot, mostra placeholder textual em vez de imagem falsa.

## Arquivos

```text
blogger_multi_store/config/bootstrap_missing_stores.json
blogger_multi_store/src/bootstrap_missing_stores.py
.github/workflows/blogger_multi_store_bootstrap.yml
blogger_multi_store/data/bootstrap_result.json  # criado somente após execução integral PASS
```

## Produtos-semente

O arquivo de configuração contém somente ofertas reais já usadas/validadas no projeto. Os produtos-semente servem para a instalação inicial. A evolução prevista é substituir apenas a região gerenciada por seleção atualizada da Shopee Affiliate API, preservando o post e a URL da loja.

## Quota Blogger

Durante a implantação em 2026-10-31, a Blogger API respondeu HTTP 429 `rateLimitExceeded` após uma sequência de escritas. O bootstrap foi corrigido para usar backoff progressivo e retomada idempotente. Nunca contornar a quota com rajadas de chamadas ou recriar objetos sem releitura.

## Definition of Done por blog

Uma implantação só pode ser considerada PASS quando houver:

```text
1 post LIVE chamado Loja
1 página LIVE chamada Loja
URL do post válida
URL estável /p/loja.html válida
links comerciais com nofollow sponsored noopener
sem duplicata de Loja
validação posterior por leitura da Blogger API
```

## Próxima evolução

Depois que todos os blogs tiverem a implantação base validada, generalizar a rotação automática da loja Philips para um motor multi-blog, mantendo:

- Shopee Affiliate API;
- filtro semântico v2.3;
- diversidade de produtos/lojas;
- estado de rotação persistente;
- overwrite somente dentro dos marcadores gerenciados;
- validação pública/API antes de persistir estado.
