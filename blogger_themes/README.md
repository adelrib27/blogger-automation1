# Temas Blogger — modelos independentes

Este diretório mantém **dois temas diferentes para dois usos diferentes**. Não misture os modelos nem substitua um pelo outro automaticamente.

## 1. Tema editorial para blog comum

Arquivo: `TEMA-EDITORIAL-BLOGGER-INDEPENDENTE-V1.0.xml`

Use para blogs editoriais com artigos convencionais, tutoriais, notícias, guias, análises ou outros conteúdos que precisam funcionar como um blog — não como uma vitrine de produto.

### O que inclui

- Página inicial com título e descrição do próprio blog.
- Cards gerados dinamicamente a partir dos posts publicados, sem títulos ou URLs de artigos fixados no XML.
- Permalink individual com título e corpo completo do post.
- Páginas institucionais com conteúdo vindo do Blogger.
- Listas de pesquisa/arquivo/rótulos e paginação.
- Layout responsivo, acessibilidade básica, metadados SEO e Open Graph.
- Nenhuma vitrine de produto, preço fixo ou CTA de compra embutido.

### Instalação e teste

1. Instale o XML em um **blog de teste**, pela interface do Blogger: **Tema → Restaurar/Enviar tema**.
2. Defina o título e a descrição do blog.
3. Crie, se forem necessárias, as páginas com estes caminhos:
   - `/p/sobre.html`
   - `/p/contato.html`
   - `/p/politica-de-privacidade.html`
   - `/p/termos-de-uso.html`
4. Publique um artigo de teste que tenha título, parágrafos e pelo menos um subtítulo.
5. Confirme separadamente:
   - a página inicial mostra o card do artigo;
   - clicar no card abre o permalink correto;
   - a página individual exibe título e corpo completo;
   - uma página institucional exibe o conteúdo salvo no Blogger;
   - o layout funciona em celular e desktop.
6. Só considere o tema validado em produção depois de conferir as páginas públicas reais.

## 2. Tema para sites de produto/vitrine

Arquivo: `BASE-VISUAL-SHOPEE-BLOGGER-MESTRE-V3.0.xml`

Este arquivo pertence ao projeto **Sites de Produtos Shopee — Blogger** e deve permanecer separado do tema editorial. Preserve-o para o formato de site centrado em um produto/vitrine. Não o use como base automática para blogs editoriais comuns.

## Validação automatizada

O workflow `.github/workflows/validar_tema_mestre_blogger.yml` executa verificações estruturais para os dois XMLs:

- `src/validar_tema_blogger.py` — tema V3.0 existente.
- `src/validar_tema_editorial_blogger.py` — tema editorial independente.

Esses testes confirmam sintaxe XML e invariantes do arquivo, mas **não comprovam a renderização pública do Blogger**. A validação final exige instalar o tema em um blog de teste e conferir a home e um permalink individual.

## Limitação da plataforma

A Blogger API v3 não disponibiliza um recurso oficial para enviar o XML de tema. A instalação continua sendo manual pela interface do Blogger. Criar ou validar o arquivo no GitHub não significa que ele já esteja instalado em qualquer blog.

## Proteção de projetos

A criação deste tema não altera blogs, posts ou páginas publicados. Em particular, não instalar este XML no Conecta Achados nem modificar seus 10 posts existentes sem autorização explícita.
