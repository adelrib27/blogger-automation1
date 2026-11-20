# C78 — armazenamento privado e imutável do HTML revisado (contrato)

**Status:** biblioteca SAFE offline, sem adapter/credencial R2 real. Não habilitar writer nem LIVE com base apenas neste módulo.

## Motivação
Um D1 READY guarda somente `html_sha256` e metadados. O escritor CMS não pode regenerar com IA o artigo aprovado e alegar que ainda é o mesmo conteúdo. Os bytes revisados precisam ser recuperados sem alteração e associados ao mesmo site/campanha/SKU.

## Objeto privado
- Chave: `v31/private-ready/v1/{site_key}/{campaign}/{sha_prefix}/{html_sha256}.json`; somente identificadores aceitos pela rota real. Nunca publicar essa chave em domínio de acesso público.
- Conteúdo JSON canônico: schema, site_key, campaign, product_key, `html_sha256`, `content_html` exato e manifesto editorial assinado C77. Não duplica feed inteiro, preços, comissão ou dados de conta.
- O backend futuro PRECISA implementar `put_if_absent(key, bytes) -> bool` de modo atômico usando `If-None-Match: *` (R2), mais `get(key)` autenticado. Bloqueia sobrescrita concorrente: não usar teste GET/PUT sem CAS.
- Após upload, GET read-after-write deve devolver exatamente os bytes originais; chave existente igual é replay idempotente, diferente é falha fechada. Carregamento verifica novamente hash, tenant e HMAC; adulteração cancela.

## Ordem de integração futura, ainda NÃO executada
1. Pré-validação C77 de fonte comercial, SEO real da versão final, Evidence + fact gate, revista por verificador independente com HMAC (não IA/autovalidação).
2. Gravar envelope privado C78 e conferir readback; só depois reservar READY via SQL C76 com `html_sha256` do mesmo conteúdo.
3. Envelope órfão por falha posterior no D1 não é publicável. Retenção/GC deve ser implementada com cuidado e prova de não referenciamento; nunca deletar por conveniência.
4. Em writer futuro, validar `site_key+campaign+SHA` D1 e lease, `READY→USED` com evidência ainda válida, buscar envelope exato, revalidar comercial/SEO/manifesto, criar no máximo DRAFT e conferir CMS por GET. Sem aprovação LIVE implícita.

## Segurança
- O módulo não cria conta, bucket, segredo, Worker, cron ou post. Tests usam backend em memória com CAS simulado e conteúdo/fonte sintéticos.
- HMAC só verifica posse da chave, não substitui revisor real; chave dedicada ainda NÃO configurada. Nunca compartilhar a chave com IA ou escritor geral.
- R2 oficial e D1 oficial são da conta `adeiltonrib27@gmail.com`; não conectar D1 experimental de `adeiltonrml@gmail.com`.
- Ausente `V31_D1_API_TOKEN` no GitHub ambiente `v31-editorial-safe`, comprovado em C77. A biblioteca C78 ainda não acessa o R2 real.
- `articles:null` segue contínuo, `min_ready=3` reserva simultânea. LIVE só com manifesto de proprietário por post.

## Arquivos
- `private_ready_envelope.py` implementa chave, validação de tenant, assinatura, CAS e verificação de readback.
- `tests/test_c78_private_ready_envelope.py` testa replay, integridade, hash, tenant, assinatura e CAS falso.
