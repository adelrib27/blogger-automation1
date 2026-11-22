# C90 — Correção de menus temáticos e Contato no XML Blogger

Fonte: tema exclusivo C89 do blog 2228849984262880811.
Arquivo completo C90 gerado: TEMA_EXCLUSIVO_AR_CONDICIONADO_SEM_DUVIDAS_V31_C90_MENUS_EDUCATIVOS.xml
Hash SHA256: 6bf24f9753f408df3857a7a2a36bf589d1ad2b085d9540e04a24c8e80950bb85 (217752 bytes).

## 1. Quatro links em vez de spans
No bloco com a classe clima-topics, substituir os quatro spans BTUs, Inverter, Consumo e Instalação por quatro elementos a href com os endereços exatos:
- BTUs: https://ar-condicionado-sem-duvidas.blogspot.com/p/btus-como-dimensionar-o-ar-condicionado.html
- Inverter: https://ar-condicionado-sem-duvidas.blogspot.com/p/inverter-como-funciona-e-quando-vale.html
- Consumo: https://ar-condicionado-sem-duvidas.blogspot.com/p/consumo-de-energia-como-comparar-ar.html
- Instalação: https://ar-condicionado-sem-duvidas.blogspot.com/p/instalacao-de-ar-condicionado-o-que.html

Atualizar as duas referências CSS .clima-topics span para .clima-topics a; adicionar estilos hover/focus-visible e cor de links visitados. O visual do banner não foi alterado.

## 2. Corrigir a página Contato ocultada pelo tema
No includable postBody do Blog1, C89 tem condição especial para a URL /p/contato.html e substitui todo conteúdo Blogger por aviso antigo 'ainda não possui um canal privado de contato'. C90 remove a condição e deixa apenas o wrapper post-body e data:post.body. Assim o formulário criado via Blogger Page é renderizado. Este é um ajuste estrutural, não CSS.
Ajustar input:not([type="hidden"]) para também excluir checkbox e definir estilo pequeno de checkbox.

## 3. Preservações
FeaturedPost1 visível false permanece; carrossel consulta #Blog1 .post-wrapper; 13 widgets iguais à origem; XML parser estrito PASS, cinco scripts node --check PASS.
FormSubmit usa blogbloggerautomation@gmail.com, mas o formulário reside somente no conteúdo público da página /p/contato.html, não no XML.
Não duplicar artigo LG ou páginas, não reconverter Shopee, não ativar publicação automática.

## 4. Status
O XML completo C90 foi entregue na conversa, mas NÃO instalado em produção. Após aplicar Tema → backup → Editar HTML → salvar, verificar carrossel, 4 links, formulário, responsividade e receber mensagem de teste FormSubmit antes de marcar a entrega do formulário como ativa.
