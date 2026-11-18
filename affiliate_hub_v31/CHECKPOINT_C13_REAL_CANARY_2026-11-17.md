# C13 — Canário R2 real + históricos da main + reserva controlada (17/11/2026)

**Código de continuidade:** `V31-EDITORIAL-C13-CANARY-137-REAL-R2-14-LINKS-20261117`

**Estado de release:** branch `feature/v31-affiliate-hub-c1-safe-20261115`, [PR #52 DRAFT](https://github.com/adelrib27/blogger-automation1/pull/52); **nenhum merge na `main` e nenhum novo publicador/agendamento LIVE foi ativado**. Não habilitar as flags até os gates abaixo.

## Decisão preservada para DEPOIS do V31

Todas as páginas de loja dos blogs atualizam produtos **diariamente**. O usuário suspeita que essas rotações, somadas às buscas editoriais e às 5 categorias do Radar, possam concentrar chamadas Shopee e contribuir para erros 1000. **Hipótese ainda não demonstrada**; erro 1000 e erro 10030 não devem ser tratados como sinônimos. Só quando o V31 estiver concluído: medir uso/horários, avaliar rotação mensal distribuída por blog, **sem desativar lojas**. Registro completo no `C10_RELEASE_RUNBOOK_2026-11-16.md`. Nenhum cron/script de loja foi alterado na C13.

## C13 — melhorias técnicas

- `history_readiness.py` e `tests/test_history_readiness.py`: auditoria somente leitura dos históricos de publicação e rascunhos antigos; compara IDs + título com corpo histórico mínimo, contando **apenas** a capacidade verificável para reutilização editorial. Não imprime IDs, títulos, URLs, conteúdo ou dados de usuários.
- `queue_identity.py` e `tests/test_queue_identity.py`: proteção contra sobrescrita de rascunhos anteriores. Ao gerar um artigo novo no modo reutilização, identifica o maior ID já presente em `editorial_queue.json` e `data/generated/*.json`. Um reset da fila NÃO reinicia a numeração nem sobrescreve artigo antigo; caminhos simbólicos/IDs inválidos são rejeitados.
- Os construtores de fila originais do Casa e Oficina invocam `highest_reserved_id` **somente com o opt-in editorial ON**, preservando comportamento antigo quando OFF. Testes integram scripts originais em pastas temporárias.
- O teste C13 passou a consultar **também o histórico da `main` vigente na hora da execução** por `git fetch` + `git archive` em pasta temporária, sem modificar o checkout nem a `main`. Isso revelou a divergência natural entre a branch de desenvolvimento e os agendamentos que continuam publicando.
- Workflows temporários de execução C13 foram **removidos** após os testes; não houve acréscimo de schedules.

## Canário real, ZERO publicação

[GitHub Actions 44086403960](https://github.com/adelrib27/blogger-automation1/actions/runs/44086403960) — **SUCCESS**:

- **137/137 testes V31** no checkout; testes originais Casa **24/24**, Oficina **21/21**, cross-blog guard PASS.
- Auditoria read-only de **R2 REAL**.
- Fila ORIGINAL Casa e fila ORIGINAL Oficina geradas de R2 em diretórios temporários e validadas.
- Radar: scanner original recebeu erro 1000 **SIMULADO**, leu links reais armazenados no R2 e montou 5 categorias/5 lojas/5 slots em pasta temporária.
- `publication_calls=0`, `r2_writes=0`, Shopee API real **0 chamadas**.
- Registros editoriais **atuais da main** no canário:
  - Casa e Decoração: **46 registros publicados**, 42 com itemId e título, **41 produtos com corpo histórico verificável**, **1 item publicado com corpo anterior não localizável**. Os outros 4 registros não apresentam itemId; não inventar vínculo.
  - Oficina & Garagem: **12 publicações**, 12 com itemId/título, apenas **1 produto com texto anterior verificável** e **11 sem documento histórico correspondente**, portanto reutilização desses 11 deve **continuar bloqueada**.
- A branch testada mantém snapshot antigo de Casa com 45 registros, enquanto `main` tinha 46 no momento da consulta; o PR está **divergente de main (26 commits atrás na verificação)**. Reconciliar/rebase antes de merge, não carregar histórico antigo para produção.

## Reposição REAL limitada e verificada (um lote somente)

[GitHub Actions 44086617987](https://github.com/adelrib27/blogger-automation1/actions/runs/44086617987) — **SUCCESS**:

1. **137/137 testes PASS**.
2. Shadow read-only ANTES: R2 com **11** links afiliados (incluindo 1 Blogger); Casa **2/9**, Oficina **2/6**, Radar **6/15**.
3. `cache_replenish --site all --budget 3` (dry-run): **0 chamadas Shopee, 0 gravações**.
4. `cache_replenish --site all --budget 3 --execute` (um lote real): **3 tentativas/3 conversões bem-sucedidas**, exatamente **1 para cada campanha WordPress**; snapshot R2 salvo e restaurado/verificado; `api_interrupted=false`, `retention_pending=false`; **nenhum post**.
5. Shadow read-only DEPOIS:

| Blog | Links válidos para a campanha | Meta de 3 dias | Categorias cobertas | Status |
|---|---:|---:|---:|---|
| Casa e Decoração | **3** | 9 | 3/8 | `NOT_READY` |
| Oficina & Garagem | **3** | 6 | 3/6 | `NOT_READY` |
| Radar Tech BR | **7** | 15 | 5/5 obrigatórias | `NOT_READY` |

**Total R2:** 14 links (13 WordPress + 1 Blogger piloto), 109.507 produtos no catálogo, 4.674 elegíveis. Ainda faltam **17 links WordPress** para metas iniciais (6 Casa +3 Oficina +8 Radar). `SHADOW_READY`, quando surgir, será condição necessária **mas não liberação automática** para publicar.

## Condições ainda necessárias para produção

1. Manter **todos switches V31 OFF**; sem merge automático. Os 3 workflows existentes e seus publicadores continuam em produção pelo caminho antigo.
2. Acumular os **17 links restantes** ao longo de execuções pequenas, com orçamento/observabilidade global, **sem criar rajadas Shopee** nem tocar agendas de páginas de loja agora. Um único lote C13 já foi realizado; não repetir automaticamente.
3. Validar a consistência com o histórico `main` mais recente no momento do merge; não sobrescrever filas, históricos nem JSONs gerados por versão desatualizada.
4. Reutilização editorial do Casa/Oficina (C11/C12) requer flag própria, título/ângulo/SEO/HTML diferentes e documento histórico verificável; os 11 itens do Oficina sem corpo anterior ficam bloqueados. Radar conserva política própria de não repetição editorial, até adaptação comprovada.
5. Revisar configuração e coexistência de jobs e credenciais em PR, fila de artigos original e acesso ao Environment antes do primeiro canário publicado. **Não criar novos geradores WordPress**, nem publicar posts de teste.
6. Escalar configurações dos novos blogs com rotas reais em `sites.d` e `shadow.d`; sistema não possui limite fixo de 3 blogs, mas só 3 perfis shadow estão prontos.

**Próximo marco:** **C14 — reposição gradual da reserva de campanha, reconciliação do PR com a main, decisão supervisionada de liberação por blog e rollback.** A análise da carga das páginas de loja é **posterior** ao V31.
