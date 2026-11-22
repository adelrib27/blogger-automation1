# V31 C90 — Ar-Condicionado sem Dúvidas: botões BTUs, Inverter, Consumo, Instalação e formulário

Data: 22/11/2026. Blog Blogger ID 2228849984262880811 — https://ar-condicionado-sem-duvidas.blogspot.com/

## Estado verificado
- XML atual C89 instalado, homepage pública HTTP 200, sem terceiro bloco duplicado. Os quatro chips do hero ainda são SPAN não clicáveis no HTML público.
- Quatro páginas NOVAS foram criadas e verificadas via Blogger API (status live 4/4) e HTTP 200 público (4/4):
  1. BTUs: como dimensionar o ar-condicionado — página ID 3513751614909335910 — https://ar-condicionado-sem-duvidas.blogspot.com/p/btus-como-dimensionar-o-ar-condicionado.html
  2. Inverter: como funciona e quando vale a pena — página ID 4817529374906340538 — https://ar-condicionado-sem-duvidas.blogspot.com/p/inverter-como-funciona-e-quando-vale.html
  3. Consumo de energia: como comparar ar-condicionados — página ID 2758729216149220117 — https://ar-condicionado-sem-duvidas.blogspot.com/p/consumo-de-energia-como-comparar-ar.html
  4. Instalação de ar-condicionado: o que conferir antes — página ID 1503167106936207154 — https://ar-condicionado-sem-duvidas.blogspot.com/p/instalacao-de-ar-condicionado-o-que.html
- Conteúdo original: explicações, FAQ, checklists, fontes oficiais Inmetro, Procel e fabricante LG, links internos.
- A página Contato ID 1229660535318855287 EXISTENTE foi atualizada, sem duplicação, com formulário POST para https://formsubmit.co/blogbloggerautomation@gmail.com, campos nome/e-mail/assunto/mensagem, consentimento, honeypot, reCAPTCHA padrão do serviço e mailto de fallback.
- O proprietário confirmou blogbloggerautomation@gmail.com como endereço público de contato padrão dos blogs Blogger deste projeto. Nenhuma outra conta ou endereço pessoal foi utilizado.
- Política de Privacidade ID 3365012459566429524 atualizada para mencionar processamento pelo FormSubmit.
- Identificou-se que o XML C89 contém um override condicional do postBody para /p/contato.html: mesmo com o novo conteúdo salvo pela API Blogger, o site público continua mostrando a mensagem antiga sobre não haver canal privado e NÃO mostra o formulário. Esse override foi removido no XML C90; nenhuma mutação no tema vivo foi executada.
- As páginas Sobre ID 8479275003826990437 e Loja ID 4814998680660659640 ganharam links aos quatro assuntos, mantendo CTA e foto Shopee. O artigo LG ID 940950273343255024 também recebeu links internos, preservando o shortlink https://s.shopee.com.br/8fU8IIYmXO. Não houve conversão repetida nem nova publicação de artigo.
- Contagem Blogger final confirmada: 10 páginas LIVE, 1 artigo LIVE, 0 DRAFT.

## Tema C90 entregue no chat — PRONTO, NÃO INSTALADO
Nome exato: TEMA_EXCLUSIVO_AR_CONDICIONADO_SEM_DUVIDAS_V31_C90_MENUS_EDUCATIVOS.xml
TXT idêntico: TEMA_EXCLUSIVO_AR_CONDICIONADO_SEM_DUVIDAS_V31_C90_MENUS_EDUCATIVOS_HTML_COMPLETO.txt
SHA256 XML: 6bf24f9753f408df3857a7a2a36bf589d1ad2b085d9540e04a24c8e80950bb85
Tamanho: 217752 bytes. A versão XML completa foi criada no container da conversa e NÃO foi commitada neste checkpoint.

Alterações: 4 SPAN → 4 links A com permalinks exatos; CSS dos chips com hover/focus; ajuste de checkbox; remoção da condição de postBody que suprimia a página Contato; Blogger Pages como fonte única por data:post.body. Preservados os 13 widgets de C89, FeaturedPost1 visible=false, Blog1, carrossel, Loja, header e SEO. XML estrito passou; node --check em 5 scripts passou.
Patch: conferir artefato local C90_ALTERACOES_TEMA_AR_CONDICIONADO.patch ou guia no GitHub blogger_themes/patches/C90_AR_CONDICIONADO_MENUS_E_CONTATO.md.

## Próximo gate necessário
1. Proprietário faz backup do tema C89 e instala o XML completo C90 no Blogger Tema → Editar HTML.
2. GET da HOME: os quatro chips passam a ser links e abrem páginas verdadeiras.
3. GET público de /p/contato.html deve renderizar o formulário da Blogger Page, e não o aviso antigo.
4. Primeiro envio de teste via FormSubmit pode exigir confirmação de endereço na caixa blogbloggerautomation@gmail.com. Até teste confirmado, NÃO declarar entrega funcional ou ativação concluída. O contato direto mailto é alternativa disponível após instalação.
5. Verificar mobile, carrossel, grade, Loja, foto e CTA do LG. Manter AUTO LIVE V31 desativado e não repetir conversão Shopee.

Fontes: https://www.gov.br/inmetro/pt-br/assuntos/regulamentacao/avaliacao-da-conformidade/programa-brasileiro-de-etiquetagem/tabelas-de-eficiencia-energetica/condicionadores-de-ar ; https://www.lg.com/br/suporte/suporte-servico-politica-instalacao/ ; https://formsubmit.co/documentation
