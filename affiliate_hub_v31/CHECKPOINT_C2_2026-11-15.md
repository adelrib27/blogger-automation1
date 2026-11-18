# V31 Hub Editorial Shopee — Checkpoint C2 SAFE (15/11/2026)

**Código de continuidade:** `V31-EDITORIAL-C2-TAXONOMIA-R2-20261115-SAFE`

## Escopo e segurança

Este projeto trata **somente de Blogger e WordPress**, não integra Pinterest. O repositório `adelrib27/blogger-automation1` é público. Todos os arquivos comerciais (CSV, SQLite, links gerados e segredos) são privados e **jamais devem ser commitados**.

Branch isolada: `feature/v31-affiliate-hub-c1-safe-20261115`, PR draft [#52](https://github.com/adelrib27/blogger-automation1/pull/52), sem merge automático. Nenhum writer de blogs existentes foi modificado, nenhuma publicação foi feita.

## Pipeline C2

```text
Secrets DATAFEED_URL_1 / _2  [ainda não cadastrados]
    ↓ download HTTPS com host/path allowlist, limites e arquivo temporário privado
CSV 1 + CSV 2
    ↓ ingestão atômica em SQLite staging (rollback se qualquer feed falhar)
    ↓ deduplicação por shopId:itemId ou URL, classificação sensível e semântica
20 nichos em 15 categorias; desconhecido, conflitante ou acessório bloqueado → REVISÃO
    ↓ filtragem por Blogger/WordPress e campanha por site
    ↓ consulta ao cache de link de afiliado
    ├── existe link válido e o produto segue aprovado → reutilizar
    └── falta link → generateShortLink (client pronto, teste real ainda NÃO executado)
               ↓ rechecagem de elegibilidade e domínio
       cache privado em SQLite / snapshot R2
    ↓ ADAPTADORES BLOGGER E WORDPRESS (ainda não ligados)
```

**Seleção por site:** `routing.plan_site` alterna categorias/nichos (round-robin) e retorna produtos com links em cache **e** sem links. O inventário de conversão `Catalog.candidates` permanece separado e considera apenas os que ainda faltam converter. Campanhas continuam distintas por site para rastreamento sem sobreposição.

**Antes da conversão:** classificar e restringir o site/nicho, sem fazer chamadas para itens suspeitos ou sem match. **Depois da conversão:** validar domínio do link, reconsultar estado do produto e persistir sem sobrescrever conversões da mesma campanha. A aprovação automática de artigo permanece desligada.

### Arquivos principais

- `taxonomy.json` / `taxonomy.py` — regras versionadas de categorias/nichos, palavras delimitadas, ambiguidades e revisão.
- `site_routes.json` / `routing.py` — rotas preliminares para **18 Blogger** do inventário legado e **2 WordPress** confirmados em configurações do repositório. **Todas publish_enabled=false.**
- `catalog.py` — catálogo privado SQLite, dedup, revisão, tabela de taxonomia, cache por campanha e filtros para nicho.
- `converter.py` — cliente `generateShortLink`, assinatura reutilizada de C1, um subID derivado de campanha, sem retry automático da mutation, idempotência por campanha.
- `feed_download.py` — URLs privadas estritamente permitidas para `affiliate.shopee.com.br/api/v1/datafeed/download` (redirect externo rejeitado; se provado necessário, revisar manualmente allowlist).
- `ingest.py` — duas importações em banco temporário, integridade e substituição atômica do estado local.
- `r2_state.py` — snapshot SQLite versionado com checksum SHA-256 e ponteiro privado `CURRENT.json` atualizado somente após upload e head check. Exige um writer único.
- `ingest_cli.py` — CLI local para QA ou `--mode cloud` para GitHub Actions.
- `.github/workflows/v31_editorial_ingest_r2_safe.yml` — execução manual restrita à `main`, com Environment e confirmação de armazenamento privado; **não tem schedule nem rotina de publicação**.
- `.gitignore` — protege novos CSVs, bancos e downloads contra commit acidental.

### Dados de origem realmente verificados

- C1.3: a Shopee Open API aceitou **uma consulta real** `productOfferV2`, run [43725343531](https://github.com/adelrib27/blogger-automation1/actions/runs/43725343531).
- C2: importações e mutação de conversão estão **implementadas e testadas de modo offline/mock**.
- A contagem anterior de **100.000 + 10.000** foi relatada em conversa, mas **estes feeds não foram baixados nem auditados nesta etapa C2**. O esquema CSV real deve ser comprovado antes da ingestão comercial.
- Conversão `generateShortLink`: contrato pronto, **nenhum pedido real de mutation nesta etapa**. Confirmar comportamento da API com lote mínimo em etapa posterior.
- A chave Shopee já exibida anteriormente em uma captura deve ser **rotacionada**. Não assumir que a mudança para GitHub Environment secret fez a rotação.

### Secrets / Variables ainda necessários para importar em cloud

Registrar no Environment `v31-editorial-safe` (não em repository variables):

| Tipo | Nome |
| --- | --- |
| Secret | `V31_EDITORIAL_DATAFEED_URL_1` |
| Secret | `V31_EDITORIAL_DATAFEED_URL_2` |
| Secret | `V31_EDITORIAL_R2_ACCESS_KEY_ID` |
| Secret | `V31_EDITORIAL_R2_SECRET_ACCESS_KEY` |
| Variable | `V31_EDITORIAL_R2_ACCOUNT_ID` |
| Variable | `V31_EDITORIAL_R2_BUCKET` |

O bucket **precisa existir, ser privado, com credenciais próprias de privilégio mínimo** e política de retenção/recuperação. Não presumir que foi provisionado. Requer `boto3` apenas na execução de cloud (o workflow o instala no runner). A documentação dos nomes existentes fica em `SECRETS.md`.

### Segurança operacional dos workflows

- Restringir `v31-editorial-safe` em **Deployment branches and tags** às branches aprovadas, idealmente somente `main` após revisão. O uso de `No restriction` não é recomendado para execução de segredos.
- O workflow de importação exige confirmação manual e possui `permissions: contents: read`.
- `concurrency: v31-editorial-catalog-single-writer` deve ser **idêntico para todo futuro writer** que atualize o ponteiro R2.
- Nenhum arquivo de banco ou CSV deve ser publicado em Actions artifacts ou commits de repositório público.
- Snapshot R2 com ponteiro é recuperável, porém não substitui backups/rotinas de retenção. Outros writers fora do GitHub Actions quebrariam a garantia do grupo de concorrência.

## Provas automatizadas C2 (15/11/2026)

- GitHub Actions SAFE (sem tokens): **45/45 testes aprovados** após correções de quarentena e inicialização de R2. Runs de PR/push no PR #52.
- **Benchmark com 110.000 produtos sintéticos**: GitHub Actions [43728505370](https://github.com/adelrib27/blogger-automation1/actions/runs/43728505370), **SUCCESS**, registro de log:
  - entrada: **100.000 + 10.000 linhas**;
  - duplicatas deliberadas no teste: **5.000**;
  - produtos únicos esperados e obtidos: **105.000**;
  - elegíveis pela taxonomia de teste: **87.500**, em revisão: **17.500**;
  - tempo registrado no runner: **18,41 segundos**.
- Este benchmark **não demonstra** contagem, cobertura de nichos, duplicatas ou velocidade dos feeds comerciais reais; os arquivos foram gerados com dados fictícios.
- O gatilho de benchmark `.github/workflows/v31_editorial_scale_once.yml` foi **apagado da branch** logo após o PASS. O benchmark reutilizável `bench_scale.py` permanece sem disparo automático.
- O primeiro snapshot no R2 exige `initialize_new_catalog=true` no despacho manual. Ausência do ponteiro remoto, sem esse consentimento, **falha fechada** para evitar reset de histórico.
- Feeds vazios ou malformados não substituem a base existente.

## Próximas validações obrigatórias

1. Cadastrar duas URLs assinadas de feeds como Secrets e configurar bucket R2 privado com acesso mínimo.
2. Testar importação real dos dois feeds em workflow manual, registrando apenas contagens e cobertura por nicho, sem expor catálogo.
3. Auditar taxas de itens não classificados e falsos positivos; revisar e ajustar taxonomia, rotas e política editorial por blog.
4. Validar uma conversão real `generateShortLink` com credencial rotacionada, um item e uma campanha, salvando no R2 sem afetar outros blogs.
5. Implementar adaptadores SAFE dos sites e apenas depois revisar procedimentos de aprovação LIVE, idempotência de posts e schedules na nuvem.

**Status C2:** código e testes offline validados; serviço cloud real ainda não executado. Não fazer merge ou ativar agendamentos só com esta evidência.
