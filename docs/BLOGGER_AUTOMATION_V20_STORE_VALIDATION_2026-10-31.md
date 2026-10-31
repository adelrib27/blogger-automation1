# Blogger Automation V20 — Validação da LOJA — 2026-10-31

## Resultado do modelo versionado

**Status:** PASS

O BLOGGER_MODELO_V20 foi atualizado para incorporar oficialmente a LOJA automatizada aprovada no piloto Conecta Achados.

### Contrato validado

- marcador base: `emporio-revisao-visual-20-modelo-final`
- extensão: `BLOGGER_MODELO_V20_STORE_EXTENSION`
- página: `/p/loja.html`
- menu: `LOJA` imediatamente depois de `Início`, com destaque visual
- largura máxima da LOJA no desktop: `1280px`
- sidebar: oculta somente na LOJA
- desktop: 4 produtos por linha
- tablet: 2 produtos por linha
- celular: 2 produtos por linha
- páginas V20: 6 (`sobre`, `afiliados`, `contato`, `privacidade`, `termos`, `loja`)
- LOJA: exatamente 20 produtos válidos em 5 categorias antes de considerar população concluída
- scaffold: nenhum produto, preço, imagem ou link afiliado fixo/inventado
- escrita automática: somente entre os marcadores da LOJA
- falha de seleção/leitura/escrita: preservar estado anterior
- pós-escrita: releitura e validação obrigatórias

## Piloto visual

- blog: Conecta Achados
- Blog ID: `1719259388907013414`
- URL: `https://conectaachados.blogspot.com/`
- layout da página LOJA aprovado pelo usuário em 2026-10-31
- grade aprovada: 4 / 2 / 2
- sidebar removida somente da LOJA
- 20 produtos reais mantidos pela automação

## Arquivos atualizados

- `tools/blogger_safe_automator_v0_2/extend_modelo_v20_store.py`
- `tools/blogger_safe_automator_v0_2/install_modelo_v20_adoption.py`
- `tools/blogger_safe_automator_v0_2/render_modelo_v20_pages.py`
- `tools/blogger_safe_automator_v0_2/provision_new_blog_v20.py`
- `tools/blogger_safe_automator_v0_2/validate_modelo_v20_store.py`
- `templates/blogger_modelo_v20/model_manifest.json`
- `templates/blogger_modelo_v20/pages.json`
- `themes/blogger_modelo_v20/pages.json`
- `templates/blogger_modelo_v20/README.md`
- `.github/workflows/blogger_modelo_v20_store_validation.yml`

## CI

Workflow: **Blogger Modelo V20 Store Validation**

Run ID: `41209053114`

Resultado: **SUCCESS**

Validações executadas:

- `py_compile` dos módulos V20 alterados: PASS
- paridade dos dois `pages.json`: PASS
- 6 páginas e ordem esperada: PASS
- contrato LOJA 20 produtos / 5 categorias: PASS
- ausência de produto/link Shopee fixo no scaffold: PASS
- aplicação da extensão em XML V20: PASS
- XML após extensão: PASS
- marcador STORE exatamente uma vez: PASS
- menu `/p/loja.html`: PASS
- 1280px: PASS
- grade 4/2/2: PASS
- extensão idempotente: PASS

## Estado do runner local

O Blogger Local Runner conectado está ativo na versão `0.7`, porém a execução em 2026-10-31 revelou que ele usa uma cópia operacional em:

`C:\Blogger-Automator\blogger_safe_automator_v0_3`

A adoção executada no Conecta Achados fez backup e preservou os posts, mas o retorno ainda não continha `store_extension_marker`, demonstrando que essa cópia operacional local ainda não recebeu a extensão versionada neste commit.

Portanto:

- **V20 versionado / contrato / CI:** PASS
- **piloto da página LOJA:** PASS
- **backup e adoção base no Conecta:** PASS
- **sincronização da cópia local v0_3 com a extensão STORE:** PENDENTE
- **menu LOJA global no tema público após essa sincronização:** PENDENTE DE REAPLICAÇÃO/VALIDAÇÃO

Não considerar a implantação local da extensão concluída enquanto o retorno de `adopt_model_v20` não incluir `store_extension_marker: BLOGGER_MODELO_V20_STORE_EXTENSION` e o menu público não for verificado.
