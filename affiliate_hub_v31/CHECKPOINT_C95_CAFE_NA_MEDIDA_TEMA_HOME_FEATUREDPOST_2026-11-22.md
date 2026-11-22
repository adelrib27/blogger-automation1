# C95 — Café na Medida: artigo mais recente ocultado pela HOME

**Data:** 22/11/2026 — **Status: DIAGNÓSTICO CONFIRMADO; ARQUIVO XML LOCAL CORRIGIDO; INSTALAÇÃO LIVE PENDENTE**

## Blog e identidade imutáveis
- Nome: Café na Medida
- Blogger ID: `4820923154548273510`
- URL: https://cafe-na-medida.blogspot.com/
- Post original: `5908389765438644073`, publicado 22/11/2026 17:18:36 -03:00 — [Cafeteira italiana de inox: 200 ou 300 ml, moagem e uso em fogão de indução](https://cafe-na-medida.blogspot.com/2026/11/cafeteira-italiana-de-inox-200-ou-300.html). **Não republicar nem alterar**.

## Diagnóstico LIVE comprovado
O GET da HOME pública em 22/11 retornou HTTP 200. Na estrutura HTML, a seção `id="featured_post"` contém um `id="FeaturedPost1"` **ativo** com o post mais recente `5908389765438644073`. A seção `#Blog1` exibe apenas os **4** posts antigos; o carrossel `#ub-v21-featured` mostra 4 slides e status 1/4. Resultado: artigo não aparece na grade nem no carrossel.
Causa é a estrutura do tema universal V31, **não publicação ou indexação do artigo**. Ocorrência da mesma família C86/C89.

## Correção C95 preparada em artefatos desta conversa
O XML completo entregue ao usuário é:
- `C95_CAFE_NA_MEDIDA_V31_TEMA_HOME_ARTIGOS_CORRIGIDO.xml` (213.346 bytes)
- Cópia TXT `C95_CAFE_NA_MEDIDA_V31_TEMA_HTML_COMPLETO.txt`
- Backup da BASE de referência universal `C95_CAFE_NA_MEDIDA_BACKUP_BASE_REFERENCIA_V31_C86.xml` **não é backup do tema LIVE do Café**.
- Diff `C95_CAFE_NA_MEDIDA_ALTERACOES.patch`
- Relatório `C95_CAFE_NA_MEDIDA_RELATORIO.md`
- Provas `C95_CAFE_NA_MEDIDA_VALIDACAO.json`
SHA-256 do XML final: `ad7af394be28d7fb8f58f8a027f7258fc1ac57eaf3144e17509232698ec1d43c`.

A fonte de referência foi `Pasted text.txt` previamente fornecida e igual a `Cadeira_Certa_Home_Office_V31_C86_BACKUP_ORIGINAL.xml`; não foi possível exportar o XML atual instalado no Café via ferramentas desta sessão. Portanto, a versão preparada **não foi homologada como idêntica à configuração atual do Café** e não deve substituir eventual customização exclusiva sem primeiro fazer backup.

### Delta técnico aplicado à fonte de referência
1. Preservar seção `featured_post` e ID `FeaturedPost1`; trocar widget ativo por `visible='false'`, `useMostRecentPost=false`, includable `main` vazio. Evita migração do gadget legado ao salvar no Blogger.
2. Carrossel: selecionar só `document.querySelectorAll('#Blog1 .post-wrapper')`. Não clonar nem ocultar artigos por CSS.
3. Corrigir título estático Header1 e URL PageList1 da origem Cadeira Certa para Café na Medida.
4. Preservar paleta auto, CSS, navegação, loja, cookie, scripts e todos os demais 14 IDs dos widgets da fonte.
5. Validações: XML estrito PASS, JS standalones 6 PASS, CSS sem erros, 1 Blog1, 1 widget legado explicitamente desativado.

## Execução e autorização
- Não houve alteração em posts, páginas, temas LIVE, links afiliados, R2, D1, cron, política automática nem Pinterest.
- A conexão Blogger Bridge V2 não altera tema. O Blogger Local Runner `adopt_model_v31_exact` autoriza só os IDs `4739187376492839837`, `1625257710858445955` e `8476663092477971560`, **não** `4820923154548273510`. Nunca confundir blog de laboratório com Café nem tentar forçar a allowlist.
- Para aplicar, exportar primeiro o XML atual do Café no painel Blogger → Tema → Fazer backup. Aplicar a mesma correção diretamente àquele XML, preservando customizações; ou instalar tema C95 se o backup confirmar que equivale à base universal.
- Depois da instalação verificar: HTML público NÃO contém `#FeaturedPost1` ativo, cinco IDs de posts dentro de `#Blog1`, cinco slides no `#ub-v21-featured` incluindo `5908389765438644073`, páginas, afiliado, menu, loja e mobile.
- Se o Blogger normalizar/reinserir gadget, exportar HTML normalizado e corrigir sobre o código efetivamente salvo; restaurar backup se necessário.

**Próxima ação de continuidade:** obter export do template LIVE do Café para patch exato ou executar instalação via Work (navegador autenticado) com rollback e teste, nunca afirmar que C95 está instalado antes de verificar.

## Validação do patcher reutilizável C95
O script offline `blogger_themes/tools/fix_featuredpost1_legacy_v31.py` foi adicionado à branch `main`. Workflow [#45069132403](https://github.com/adelrib27/blogger-automation1/actions/runs/45069132403) concluído **SUCCESS**: `python -m py_compile` PASS e teste de fixture XML com `FeaturedPost1` ativado verificou desativação, seleção exclusiva `Blog1` e **idempotência** (segunda aplicação não altera o resultado). O teste é offline e não significa que o tema C95 já foi instalado no Café.
