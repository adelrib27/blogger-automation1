# C2.1 — Auditoria real dos dois feeds Shopee (15/11/2026)

**Código de continuidade:** `V31-EDITORIAL-C2.1-FEEDS-REAIS-20261115-PASS`  
**Projeto:** V31 Hub Editorial Shopee — Blogger & WordPress. **Pinterest excluído.**  
**Repositório:** `adelrib27/blogger-automation1`  
**PR isolado:** [#52](https://github.com/adelrib27/blogger-automation1/pull/52) (draft, sem merge).  
**Prova real:** [GitHub Actions run 43732094595](https://github.com/adelrib27/blogger-automation1/actions/runs/43732094595), conclusão **SUCCESS**, marcador `V31_C2_REAL_FEEDS_PASS`.

## O que foi comprovado

Foi executado **um único job de auditoria completo com os Secrets dos dois feeds**, sem expor URL assinada, título, descrição, ID, link de afiliado ou dado individual em logs. Os arquivos foram processados em diretório temporário e excluídos ao final.

| Métrica | Feed 1 | Feed 2 |
|---|---:|---:|
| Registros lidos | 100.000 | 10.000 |
| Tamanho baixado (bytes) | 196.689.791 | 21.731.395 |
| Colunas no cabeçalho | 24 | 16 |
| Coluna reconhecida de `itemId` | Sim | Sim |
| Coluna reconhecida de `shopId` | **Não** | **Não** |
| Coluna reconhecida de link afiliado | Não | Não |
| Colunas obrigatórias (título, URL) | Presente | Presente |
| Linhas com campos essenciais vazios | 0 | 0 |
| Correspondência com os nichos iniciais | 4.089 | 669 |
| Sem correspondência nos nichos iniciais | 95.911 | 9.331 |
| Marcados em revisão básica (independente da taxonomia) | 1.926 | 187 |

- **110.000 registros** foram lidos sem erro de largura de colunas após corrigir a detecção de aspas do CSV.
- **493 duplicações detectadas** pelo algoritmo de chaves atual (0 no primeiro feed e 493 no segundo, relativamente ao primeiro e ao conteúdo já lido).
- **109.507 chaves distintas** no algoritmo atual. **Não interpretar automaticamente como 109.507 produtos comerciais distintos:** `shopId` não vem em coluna reconhecida. Alguns registros podem estar identificados por URL, e URLs diferentes podem representar o mesmo produto.
- **4.758 registros classificados** em 20 nichos iniciais (4,325% das linhas); **105.242** permaneceram sem categoria precisa. `classified` **não equivale a `eligible`**, pois o bloqueio básico de risco é independente.
- Os produtos desconhecidos permanecem em revisão; não criar links nem artigos automaticamente por falta de correspondência.

## Correções técnicas decorrentes do teste real

1. O endpoint assinando no GitHub redireciona dentro do domínio `*.shopee.com.br`; `feed_download.py` agora aceita **somente** destinos HTTPS dentro desse domínio, sem usuário/senha na URL nem porta inesperada. Outros hosts continuam bloqueados.
2. O primeiro feed tem descrições com linhas múltiplas e aspas duplas; o `csv.Sniffer` estimava incorretamente um parâmetro de quoting. Agora o auditor e o importador do catálogo mantêm a escolha de delimitador, mas **forçam aspas duplas RFC4180 (`doublequote=True`)**.
3. Testes de regressão de redirecionamento, estrutura CSV e campos multiline adicionados.
4. O workflow de execução autenticada **`.github/workflows/v31_editorial_feed_audit_once.yml` foi removido após PASS**; módulo `feed_audit.py` fica disponível para futuras auditorias revisadas. Nenhuma execução automática ficou ativada.

## O que o PASS não comprova

- Nenhum CSV foi persistido em Git ou no Cloudflare R2.
- Nenhuma API `generateShortLink` foi usada; conversão comercial real continua pendente.
- Nenhum dado foi publicado em Blogger ou WordPress.
- Não há certificação do mapa de categorias, percentual final de elegibilidade, qualidade editorial ou garantia absoluta da deduplicação.
- A rotação da App Secret anteriormente exposta ainda precisa ser confirmada.
- O Environment `v31-editorial-safe` deve deixar de usar `No restriction` antes do LIVE.

## Próximo marco

- **C2.2:** revisar estratégia de deduplicação quando `shopId` não está presente, quantificar chaves baseadas em URL, expandir taxonomia em ambiente de revisão, sem publicar itens desconhecidos.
- **C3:** provisionar bucket Cloudflare R2 privado e credenciais de privilégio mínimo (`V31_EDITORIAL_R2_*`), testar backup/restore real, gravar catálogo com versionamento e retenção.
- **C4:** conversão piloto real de um produto selecionado, com App Secret rotacionada e resultado privado persistido.
- **C5:** integrar Blogger/WordPress por adaptadores, avaliação por nicho e campanhas, revisão humana antes de LIVE.

**Critério de segurança:** preservar workflows existentes, seguir em branch SAFE, não juntar o PR automaticamente e nunca versionar os dois links assinados de datafeed.
