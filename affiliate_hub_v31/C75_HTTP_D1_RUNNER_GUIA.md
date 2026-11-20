# C75 — cliente HTTP Cloudflare D1 SAFE (não ligado aos writers)

## Resultado pretendido

O banco `v31-universal-ready-safe` já existe na **mesma conta do R2 oficial**. O módulo [`d1_http_runner.py`](d1_http_runner.py) faz a ponte HTTP que faltava entre `UniversalD1ReadyState(query)` e a API D1, **sem nenhuma chamada na importação** e sem cron. Não publica, não consome produtos nem usa Firecrawl.

- Conta pinada: `ebb8d5b4cf9a2cb850c6d8051bd2661f` (login `adeiltonrib27@gmail.com`).
- Banco pinado: `9bfce7a4-6167-4bfc-a65e-a74c1a34f064` (`v31-universal-ready-safe` C74). A credencial deverá ter autorização exclusiva nesse destino, não em R2, Pet ou ARV.
- URL fixa `https://api.cloudflare.com/client/v4/accounts/<conta>/d1/database/<banco>/query`. Sem host customizado nem redirect. SQL+parâmetros JSON vinculados; uma declaração por chamada, resposta `success:true`, único resultado, substatus `success:true`, lista de linhas validada e limites de bytes/timeout.
- **SELECT habilitado somente quando o executor é construído explicitamente.** `INSERT/UPDATE/DELETE` exigem `allow_mutations=True` E variável `V31_D1_SAFE_WRITES_ENABLED=V31_D1_SAFE_SQL_ONLY`; não há auto-integração.
- Segredos operacionais, ainda **não configurados nesta fase**: `V31_D1_API_TOKEN` (secret), `V31_D1_ACCOUNT_ID` (igual ao ID oficial), `V31_D1_DATABASE_ID` (igual ao UUID C74). O código não imprime token, SQL, URL Shopee ou conteúdo de produto em exceções.
- Qualquer falha de rede, resposta D1, conta errada, parâmetros/SQL inválidos ou tentativa de escrita sem os dois sinais bloqueia a operação. Não existe fallback para o D1 C73 de `adeiltonrml@gmail.com`.

## Exemplo de uso LOCAL SAFE, sem ativar cron

```python
from affiliate_hub_v31.d1_http_runner import CloudflareD1HTTPRunner
from affiliate_hub_v31.d1_universal_ready import UniversalD1ReadyState

runner = CloudflareD1HTTPRunner.from_environment()  # SELECT-only
state = UniversalD1ReadyState(runner)
# Somente com site REAL cadastrado e campanha exata, por exemplo:
count = state.count_ready(site_key="blogger_moveis_para_cada_canto", campaign="moveisparacadacanto")
```

É necessário ter token Cloudflare D1 com permissões mínimas disponível por secret protegido no ambiente, porém **não** cadastrar o token nem rodar este exemplo antes da validação da conta do GitHub. Não adicionar ao pipeline de produção automaticamente.

## Antes do rollout

1. Confirmar o GitHub Actions `vars.V31_EDITORIAL_R2_ACCOUNT_ID` e o destino D1, criar token Cloudflare estritamente dedicado e salvar **somente** como GitHub Actions secret para o V31 (nunca em arquivo/PR/log).
2. Realizar teste isolado GET/SELECT D1 por workflow manual seguro, com verificação de identidade e ZERO escrita; depois canário concorrente D1 SQL via runner com fixtures isoladas e limpeza garantida.
3. Integrar cache de evidências, fato/HTML, seleção comercial e produto R2, SEO e budget Firecrawl com evidências completas; habilitar 1 DRAFT por site em canário, **zero LIVE**.
4. Nunca executar D1 na conta `adeiltonrml` por fallback. Não mexer nos cron jobs antigos; nenhum novo LIVE sem manifesto aprovado por post.

**Regra permanente:** `articles:null` é conteúdo contínuo, `min_ready=3` é apenas reserva operacional, e nomes/credenciais de novos blogs são descobertos em rotas registradas. A adoção do cliente HTTP é independente do nicho.
