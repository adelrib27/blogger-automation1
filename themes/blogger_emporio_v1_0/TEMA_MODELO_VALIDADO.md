# TEMA MODELO — FINAL E VALIDADO

Status: **APROVADO / CONGELADO**  
Versão de referência: **V20**  
Marcador público: `emporio-revisao-visual-20-modelo-final`  
Data de validação visual: **2026-10-29**  
Blog de referência: **Guia de Achados & Ofertas**  
Blog ID de referência: `1453188702831337099`

## Regra de uso

Esta revisão passa a ser o **TEMA MODELO padrão** para novos blogs derivados deste projeto.

Não alterar o layout-base sem uma nova revisão explicitamente aprovada. Mudanças futuras devem partir desta baseline e preservar backup/rollback.

## Estrutura aprovada

- Tema nativo Blogger / Emporio preservado.
- Cabeçalho com identidade, menu institucional e busca.
- Home ampla e responsiva.
- Bloco **Achado em destaque** em formato editorial: imagem à esquerda, título, data, resumo e botão **Ver mais...** à direita.
- Grade principal com 3 cards em desktop e miniaturas proporcionais.
- Página interna de post com imagem principal, conteúdo, CTAs de afiliado e aviso de afiliados.
- Sidebar **Postagens mais visitadas** posicionada ao lado do conteúdo em desktop.
- Bloco **Artigos relacionados** abaixo do artigo, com até 3 cards, excluindo o post atual e priorizando conteúdo relacionado/recentes.
- Comentários/login removidos onde não fazem parte da experiência aprovada.
- Rodapé institucional consistente.
- Páginas Sobre, Afiliados, Contato, Privacidade e Termos alinhadas à largura editorial do site.
- Página Contato com campos visíveis de Nome, E-mail, Mensagem e botão Enviar.
- Layout responsivo para desktop, tablet e celular.

## Implementação final

Builder final:

`tools/blogger_safe_automator_v0_2/build_theme_revision_20_related_articles_model.py`

Tema gerado/aplicado localmente:

`themes/blogger_emporio_v1_0/generated/theme.xml`

Backup imediatamente anterior à V20:

`C:\Blogger-Automator\backups\blogger\1453188702831337099\theme-before-modelo-final-v20.xml`

## Critério de validação

A V20 foi considerada validada após inspeção visual pelo usuário no blog público, incluindo home, posts, páginas institucionais, sidebar, rodapé e bloco de artigos relacionados.

Qualquer automação futura que procure o **TEMA MODELO** deve tratar `emporio-revisao-visual-20-modelo-final` como a baseline aprovada até que exista uma revisão posterior explicitamente marcada como validada.
