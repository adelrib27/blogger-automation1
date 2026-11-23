# V31 — PREVIEW da consolidação de 16 para 5 blogs Blogger
**Data:** 2026-11-23, America/Recife. **Status:** PREVIEW / antes de alterações em rotas, CMS ou exclusões.
**Escopo verificável:** 16 blogs retornados por Blogger Bridge V2 na conta conectada; 142 posts publicados e 11 rascunhos. Não abrange automaticamente os 32 Blogger descritos no C103 em conexões distintas. Não tocar blogs WordPress, laboratório, projetos Pinterest ou Mercado Livre.

## Decisão explícita do proprietário — 5 blogs finais
1. Cozinha Sem Complicação — blog_id `3552757910439359679`, 12 publicados.
2. Móveis para Cada Canto — blog_id `1439741542627895062`, 5 publicados / 6 drafts.
3. Estilo no Dia a Dia — blog_id `4830103887652146866`, 12 publicados.
4. Limpeza Inteligente — blog_id `7757953554206491487`, 10 publicados / 1 draft.
5. Vida Pet Prática — blog_id `8052455848487624244`, 8 publicados / 1 draft.

## Demais 11: preservar antes de qualquer eventual exclusão
- Cadeira Certa `7163624325768776034` 7: móveis/home office → Móveis.
- Ar-Condicionado `2228849984262880811` 4: sem destino natural nesses cinco; não replicar artificialmente.
- Cabelos em Foco `6319734511998091378` 10 + 1 draft: beleza capilar → Estilo, com separação editorial.
- Eletroportáteis na Cozinha `8658632621591002634` 11 + 1 draft sem título: → Cozinha.
- Ventiladores em Foco `4473989735719981382` 10 + 1 draft: sem destino natural nesses cinco; não replicar artificialmente.
- Guia de Achados `1453188702831337099` 11: triagem por artigo entre Cozinha/Móveis/Estilo/Limpeza.
- Moda e Ofertas `2858597309582499028` 9: → Estilo, removendo conteúdo sem relação antes de migrar.
- Liquidificadores em Foco `5271798990390532475` 10: → Cozinha.
- Café na Medida `4820923154548273510` 6: → Cozinha, preservar cluster e Loja (página).
- Pedal Leve `4073458513010284301` 12: sem encaixe natural nesses cinco; preservar backup e avaliar.
- Jardim e Horta `3644898524310766003` 5: sem encaixe natural nesses cinco; preservar backup e avaliar.
Total origem: 95 publicados (142 - 47 nos cinco). Sempre comparar IDs e URLs ao agir.

## Regras de segurança
1. Nenhuma exclusão até backup integral de posts, páginas, drafts e links, inventário de URLs e validação de recuperação.
2. Nenhuma replicação LIVE automática: regras V31 exigem revisão/publicação individual; eventual importação em DRAFT somente sem alterar SEO ou campanha indevidamente.
3. Ao migrar, reconverter links afiliados por campanha do destino; checar SKU/foto e nunca copiar links de origem para destino sem autorização/verificação.
4. Analisar Search Console, indexação e backlinks antes de excluir; impossibilidade de redirect externo Blogger requer retenção de origem enquanto houver risco.
5. Auditar GSC C104; NÃO atribuir zero tráfego aos sites sem propriedade conectada.
6. SAFE_ONLY / publish_enabled=false em todas as rotas; os cinco são únicos destinos do escopo conectado. Fora de escopo: os demais 16 Blogger do C103 e 3 WordPress.
7. Pontos de recuperação: GitHub `main`, C103, C104, C105, C110/C111, este checkpoint e snapshots de HTML antes de mutar.

**Nenhuma exclusão, publicação ou mudança de rota foi realizada ao escrever este PREVIEW.**
