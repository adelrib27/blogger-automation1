# C3.2 — R2 REAL: credenciais validadas e catálogo persistido (15/11/2026)

**Código de continuidade:** `V31-EDITORIAL-C3.2-R2-CATALOG-REAL-PASS-20261115`

## Resumo técnico e prova

- Projeto: **V31 Hub Editorial Shopee — Blogger & WordPress**, sem Pinterest.
- Repositório: `adelrib27/blogger-automation1`, PR draft [#52](https://github.com/adelrib27/blogger-automation1/pull/52), branch `feature/v31-affiliate-hub-c1-safe-20261115`.
- GitHub Environment `v31-editorial-safe`: captura comprova 6 secrets e 2 variables nos locais corretos (valores de secrets são irrecuperáveis pelo GitHub). **Não cadastrar credenciais em código.**
- Bucket R2 privado: `v31-editorial-shopee`, classe Standard, sem domínio público `r2.dev` habilitado.

### Provas de execução REAL no GitHub Actions

1. [Run 43770484104](https://github.com/adelrib27/blogger-automation1/actions/runs/43770484104) — **SUCCESS**: `V31_C3_R2_SMOKE_PASS`; gravou pequeno objeto sintético, leu e comparou os bytes, e excluiu o objeto. Antes disso, **67/67 testes offline passaram**.
2. [Run 43770670661](https://github.com/adelrib27/blogger-automation1/actions/runs/43770670661) — **SUCCESS**: `V31_C2_INGEST_PASS` e `V31_C3_REAL_RESTORE_PASS`. Feeds reais lidos, catálogo SQLite enviado como snapshot privado, `CURRENT.json` gravado e banco integral restaurado de volta do R2 em novo diretório temporário, com `PRAGMA integrity_check` verificado.
3. [Run 43770827629](https://github.com/adelrib27/blogger-automation1/actions/runs/43770827629) — **SUCCESS**: testes de retenção com cliente R2 simulado; conserva snapshot atual e anterior, removendo outros snapshots do prefixo controlado. **O código de retenção foi implantado na branch depois da primeira importação real e ainda não foi exercido contra múltiplos snapshots R2 reais.**

### Contagens do catálogo REAL no R2

| Métrica | Valor |
| --- | ---: |
| Linhas lidas — feed 1 | 100.000 |
| Linhas lidas — feed 2 | 10.000 |
| Linhas de entrada | 110.000 |
| Chaves distintas no catálogo | 109.507 |
| Classificados e elegíveis na triagem inicial | 4.674 |
| Em revisão / sem nicho | 104.833 |
| Links de afiliado já salvos | 0 |
| Primeiro snapshot restaurado antes de importar | Não |
| Snapshot gravado no R2 após importar | Sim |
| Restauração do snapshot pelo GitHub Actions | Sim |

**Decisão editorial do usuário:** produtos duplicados são permitidos como insumo. A prioridade é **tema/abordagem/título diferentes por artigo**, preservando as palavras-chave mais relevantes. Não investir a próxima etapa em deduplicação adicional de produtos. O módulo `editorial.py` cria reserva transacional de pautas por produto+ângulo e título normalizado, com revisão obrigatória. A quantidade 104.833 é de itens não aprovados na triagem automatizada inicial e **não prova que sejam todos impróprios**.

## Segurança e custo

- Os workflows transitórios `.github/workflows/v31_editorial_r2_smoke_once.yml` e `.github/workflows/v31_editorial_ingest_once.yml` foram **removidos do código** depois dos runs aprovados. Os históricos dos Actions permanecem para auditoria.
- R2 conserva **banco, links, taxonomia e histórico editorial**, não arquivos de imagens; imagens dos produtos serão referenciadas pelas URLs Shopee conforme escolha do usuário.
- Em `r2_state.py`, a política de retenção conserva **somente snapshot atual e anterior**; falha de limpeza será sinalizada em `retention_pending=true`, pois o ponteiro atualizado não pode ser desfeito.
- Todos os escritores futuros compartilham `concurrency: v31-editorial-catalog-single-writer`. Evitar writers R2 externos ao GitHub que não usam o mesmo lock.
- Antes da fase LIVE, restringir `Deployment branches and tags` de `v31-editorial-safe` (screenshot ainda indica **No restriction**).
- A rotação da chave Shopee App Secret anteriormente revelada em uma captura **não foi confirmada**. Necessário substituir/sincronizar credenciais nos sistemas dependentes antes de operações LIVE.
- A taxa real de artigos ainda não foi validada: somente **20 sites mapeados** (18 Blogger + 2 WordPress), contra objetivo de no mínimo 50 blogs. Não inventar IDs dos 30 restantes.

## Próximas etapas

1. **C4:** executar piloto de conversão real `generateShortLink` com **1 produto elegível** e uma campanha isolada, salvando o resultado no R2 e verificando reutilização sem nova chamada.
2. **C5:** validar fila editorial por site em cima do catálogo R2 real, revisar títulos/pautas e preparar rascunhos Blogger/WordPress.
3. **C6:** implementar controles de publicação autorizada, reconciliação de artigos remotos, imagens por URL Shopee (cuidado com validade/hotlink), revisões e scheduling gradual. **Nenhum artigo foi publicado nesta etapa.**
4. Monitorar R2 classe Standard, volume de dados e uso de APIs para evitar excedentes não previstos.

**Não fazer merge automático do PR #52** nem ativar jobs de publicação sem revisão e pré-condições de segurança.
