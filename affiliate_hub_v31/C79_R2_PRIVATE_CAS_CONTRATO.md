# C79 — adaptador R2 real: CAS no bucket oficial e limites de ativação

## Base técnica verificada
- S3 Cloudflare R2 suporta `PutObject` com `If-None-Match: *` de modo atômico, com falha `412 PreconditionFailed` quando a chave já existe. Fonte primária (10/11/2026): https://developers.cloudflare.com/r2/api/s3/conditional-operations/ .
- Módulo `r2_private_ready_backend.py` implementa `put_if_absent` e `get` para o `ImmutablePrivateReadyEnvelope` C78. Conta fixa `ebb8d5b4cf9a2cb850c6d8051bd2661f`, bucket fixo `v31-editorial-shopee`, S3 endpoint R2 oficial. Lê var/secrets já existentes de `v31-editorial-safe` via `R2State.from_env()` e falha ANTES de criar cliente se account/bucket não coincidem.
- Todo objeto deve corresponder a rota real DRAFT-only de um blog, campanha exata, prefixo `v31/private-ready/v1`, SHA hex e pasta SHA prefix correta; fora do prefixo o backend nem chama S3.

## Semântica do CAS
- `put_if_absent` SEMPRE envia `IfNoneMatch='*'`, `ContentType: application/json`, `CacheControl: private, no-store`, metadata SHA256 e identificador único de tentativa.
- Retorna `True` somente se S3 confirmou write novo; retorna `False` **somente** no erro R2 412 `PreconditionFailed` e implica que a camada C78 deve ler/revalidar os bytes. Falhas 409/403/5xx, timeout/ambiguidade são bloqueantes, sem tratar como ausência ou sucesso. Não há método de excluir/substituir objetos nesse adaptador.
- `get` usa exatamente a chave aprovada, valida `ContentLength`, lê no máximo `MAX_BYTES+1`, fecha stream, confere `x-amz-meta-v31sha256`. 404 somente com código `NoSuchKey` é ausência; o restante bloqueia.
- O procedimento de retry de PUT em rede instável deve respeitar write-id e leitura de reconciliação, conforme documentação oficial. O engine C78 pode repetir com segurança bytes idênticos; jamais trocar manifesto no mesmo SHA.

## Implantação segura
1. CI offline com boto3 simulado deve passar antes de qualquer teste R2 remoto.
2. Um canário opcional em `environment: v31-editorial-safe`, que cria chave **sintética única** de rota C79 temporária não cadastrada, confirma PUT/GET/412 e deleta apenas objeto próprio, sempre com readback e chave sintética, nunca catálogo/pointer/blog real.
3. A publicação DRAFT não é ativada só porque R2 funciona. Ainda faltam HMAC de revisão autêntica, fontes/comissão verificadas, segredo `V31_D1_API_TOKEN` de mínimo privilégio no GitHub, teste SELECT D1, concorrência SQL e coordenação `envelope → READY → DRAFT` sem race.
4. Proibidos LIVE automáticos sem revisão individual, qualquer alteração nos ambientes Cloudflare `adeiltonrml`, `comercebem` ou ARV/Vida Pet/Pinterest.

**Limite de prova:** implementar contrato S3 com testes simulados não comprova autorização de bucket real. Registrar canário R2 real em checkpoint separado se e quando ocorrer.
