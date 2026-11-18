# Checkpoint C11 — Reutilização editorial condicionada de produtos (SAFE)

**Data:** 16/11/2026
**Código:** `V31-EDITORIAL-C11-REUSE-GATED-125-PASS-20261116`
**Estado:** branch `feature/v31-affiliate-hub-c1-safe-20261115`, [PR #52 DRAFT](https://github.com/adelrib27/blogger-automation1/pull/52), **sem merge nem qualquer ativação em produção**.

## Decisões confirmadas

1. V31 é um **serviço central universal de produtos e links** para os blogs atuais/futuros (Blogger e WordPress), **não cria outros geradores/publicadores**.
2. Quando a API Shopee retorna erro 1000, usar CSV/R2 como fonte alternativa de produtos, exclusivamente com URL afiliada real já convertida para a campanha.
3. Um produto **pode sustentar artigos diferentes**, desde que título, assunto, intenção de busca e texto realmente difiram, mantendo SEO e controles anti-spam.
4. O usuário também identificou hipótese sobre **requisições acumuladas** das páginas de loja de **TODOS** os blogs (atualização diária), artigos e categorias Radar. **Só depois de concluir V31** medir horários/chamadas e avaliar rotação mensal distribuída das lojas. Não alterar lojas agora; não presumir que erros 1000 e 10030 sejam iguais. Registro primário também no [Runbook C10](C10_RELEASE_RUNBOOK_2026-11-16.md).

## Implementado nesta etapa, sem chamadas externas

- `affiliate_hub_v31/reuse_policy.py`: avaliação genérica de título distinto (normalização, sobreposição de tokens e sequência), histórico de publicações por produto, política-piloto conservadora de **até dois artigos por produto**, garantia de intenção/título/keyword/corpo presentes e detecção de alteração de histórico entre fila e publicação.
- **Casa e Oficina** `src/build_editorial_queue.py`: modo de reutilização **opt-in**; mantém bloqueio anterior por item/fingerprint quando OFF. Quando ON, um produto já publicado com histórico confiável e uma pauta anterior pode entrar como `reuse_candidate`; preserva bloqueio de produtos semelhantes de **outros** IDs. Aloca novos IDs de fila para não sobrescrever rascunho anterior.
- **Qwen3 existente** de Casa e Oficina: prompt inclui títulos previamente usados com aquele produto, e `make_plan` rejeita uma segunda pauta de título igual ou muito parecido **antes de gerar o corpo**. Não trocamos modelo nem criamos novas automações de artigos.
- **Publicadores existentes**: antes de qualquer POST WordPress, `validate_publication` reavalia histórico/título, impede publicação repetida e permite registrar uma segunda publicação do mesmo item apenas como `produto+título` distinto. Quando a flag estiver OFF, mantém integralmente o bloqueio original por produto.
- **Terceiro opt-in próprio da reutilização**: `V31_EDITORIAL_PRODUCT_REUSE_ENABLED`, adicional ao `V31_EDITORIAL_C9_RELEASE_ENABLED` global e à flag do blog. Só a combinação explícita de **três true** libera a alteração editorial. Ausente/false = comportamento anterior.
- Radar Tech BR ainda usa o gate de diversidade da fila original, com 5 categorias/lojas; **não foi modificado para reutilizar produtos publicados**. O motor V31 é genérico; os consumidores legados precisam validar sua própria política de pauta.

## Evidência e regressões

- [GitHub Actions 43910337180](https://github.com/adelrib27/blogger-automation1/actions/runs/43910337180): **SUCCESS**.
  - `python -m unittest discover -s affiliate_hub_v31/tests -q`: **125/125 testes PASS**, incluindo testes reais de funções dos construtores e histórico dos publicadores originais com flag ON/OFF, ausência de mutações API e validação de tópicos.
  - `casa_decoracao/src/self_test.py`: **24/24 PASS**.
  - `oficina_garagem/src/self_test.py`: **21/21 PASS**.
  - `src/editorial_cross_blog_guard_self_test.py`: **PASS**.
- O workflow C11 temporário de QA foi **retirado** da branch depois do PASS. Logs históricos permanecem acessíveis.
- **Nenhum post foi criado, modificado ou publicado. Nenhuma mutation Shopee nem escrita no R2.** O modo reutilização está OFF no PR e não foi mesclado na main.

## Riscos e próximas etapas que NÃO foram concluídas

1. Reutilização segura de um produto **não significa que todo conteúdo novo será diferente**: Qwen3 precisa passar pelo quality gate, cross-blog guard, histórico de títulos, e revisões de similaridade do corpo. A implementação acima é **etapa de validação técnica**, não autorização de LIVE; recomenda-se adicionar comparação do corpo do novo artigo com versões anteriores do mesmo blog antes de ligar o modo.
2. Testar com histórico real de Casa/Oficina sem publicar, incluindo posts antigos, rascunhos, retries, colisões de slug e dependências de categoria; verificar integridade e idempotência antes de qualquer canário.
3. Reserva de links afiliados continua menor que metas de três dias: **Casa 2/9, Oficina 2/6 e Radar 6/15** no último inventário confirmado (total 11 links R2 incluindo um Blogger). Não aumentar a frequência de consultas Shopee sem medir demanda e sem orçamento.
4. O seletor Radar ainda deve receber implementação editorial para pauta diferente antes de reaproveitar um produto publicado; fila original de cinco lojas/categorias foi validada na C9.
5. Habilitação do fallback e do reuso só mediante canário aprovado, flags por blog, observabilidade, política de originalidade e **merge deliberado**; `main` continua intacta.

**Próximo marco:** C12 — qualidade do texto contra histórico, auditoria de estoque e canário de ponta a ponta sem publicação. Posteriormente, liberação progressiva com rollback.
