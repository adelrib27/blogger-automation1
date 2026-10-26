# Temas Blogger — modelos independentes

Este diretório mantém modelos separados para **blogs editoriais** e **sites de produto/vitrine**. Não substitua um pelo outro automaticamente.

## 1. Tema editorial recomendado para novos blogs

Arquivo: `TEMA-EDITORIAL-BLOGGER-ACHADOS-V1.0.xml`

Esta versão é uma adaptação do tema **Achados para Casa — Profissional V2 com menu fixo**, que já foi testado e aceito pelo Blogger. A cópia preserva a estrutura nativa do tema Contempo 1.3.3, especialmente o widget `Blog1` e sua renderização padrão de publicações, páginas e arquivos.

### O que foi adaptado

- Nome e descrição do blog puxados dinamicamente das configurações do Blogger.
- Menu genérico com **Início** e **Artigos**, sem categorias nem URLs do Achados para Casa.
- Rodapé genérico, com divulgação condicional de links de afiliados.
- Links para Sobre, Contato, Privacidade e Termos não são incluídos enquanto as páginas não existirem — evita menu apontando para páginas vazias.
- Layout responsivo e widgets nativos do Blogger preservados.
- CSS específico de componentes de produto removido.

### Instalação e validação

1. Baixe o XML acima e instale manualmente em um **blog de teste**, pela interface do Blogger: **Tema → Restaurar/Enviar tema**.
2. Confira a página inicial e abra o permalink de um artigo publicado.
3. Verifique também busca, arquivos/rótulos e visualização em celular.
4. Só depois de confirmar o resultado, reutilize a cópia em outros blogs.

A validação automatizada confirma a estrutura do XML, mas não consegue comprovar a renderização pública. A instalação e a verificação no Blogger continuam necessárias.

### Páginas institucionais

A versão-base não cria nem publica páginas. Crie e revise o conteúdo de Sobre, Contato, Política de Privacidade e Termos antes de adicionar esses links ao menu. A renderização nativa do Blogger para páginas individuais é preservada.

## 2. Tema para sites de produto/vitrine

Arquivo: `BASE-VISUAL-SHOPEE-BLOGGER-MESTRE-V3.0.xml`

Este arquivo pertence ao projeto **Sites de Produtos Shopee — Blogger** e deve permanecer separado do tema editorial. Preserve-o para o formato de site centrado em um produto/vitrine. Não o use como base automática para blogs editoriais comuns.

## 3. Tema editorial independente V1.0 anterior

Arquivo: `TEMA-EDITORIAL-BLOGGER-INDEPENDENTE-V1.0.xml`

Este arquivo fica preservado para histórico e diagnóstico. No blog de teste, a publicação existia no Blogger, mas não era exibida pelo tema. **Não o use como tema de instalação recomendado**; prefira a versão derivada do tema Achados para Casa acima.

## Validação automatizada

O workflow `.github/workflows/validar_tema_mestre_blogger.yml` executa:

- `src/validar_tema_blogger.py` — tema de produto V3.0.
- `src/validar_tema_editorial_blogger.py` — tema editorial independente anterior, mantido para diagnóstico.
- `src/validar_tema_editorial_achados_blogger.py` — novo tema editorial baseado na versão funcional do Achados para Casa.

## Limitação da plataforma e proteção dos blogs

A Blogger API v3 não disponibiliza um recurso oficial para enviar o XML de tema. A instalação continua sendo manual pela interface do Blogger. Criar ou validar o arquivo no GitHub não significa que ele já esteja instalado em qualquer blog.

Esta adaptação altera apenas arquivos do repositório. Não instala temas nem cria, edita, publica ou remove posts e páginas em nenhum blog. Em particular, o Conecta Achados e seus 10 posts permanecem intocados.
