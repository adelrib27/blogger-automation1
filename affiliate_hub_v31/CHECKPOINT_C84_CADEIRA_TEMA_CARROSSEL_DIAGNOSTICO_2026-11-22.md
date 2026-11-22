# V31 C84 — falha do carrossel HOME Cadeira Certa — diagnóstico exato (22/11/2026)

## Pedido
Corrigir o fato de um artigo recém-publicado do blog **Cadeira Certa no Home Office** não entrar em destaque na homepage. O usuário anexou captura de 22/11/2026 mostrando Tok Boxbit como slide 1/5 e Office Arco ausente.

## Evidência direta: HTTP público + API autenticada
- Site: `https://cadeira-certa-home-office.blogspot.com/`; blog Blogger `7163624325768776034`.
- Firecrawl `rawHtml` ao vivo em 22/11 respondeu HTTP 200 e retornou código JavaScript original:
  `var cards = document.querySelectorAll('#Blog1 .post-wrapper');`
  logo após comentário `Build a separate highlight from the already rendered cards; never move or hide originals.`
- A inspeção do DOM confirmou, **por ID e seletor**:
  - `#FeaturedPost1 .post-wrapper` contém Office Arco ID `6656620121237912250` (post mais novo em 22/11).
  - `#Blog1 .post-wrapper` contém os outros **cinco posts**: `3691939235338797956` (Tok Boxbit), `5233454304666317388`, `8648967166394388356`, `7516498952063951593` e `4636680511643933177`.
- O carrossel `#ub-v21-featured` é criado no navegador **exclusivamente** a partir dos cards `#Blog1`, limitando a cinco e aplicando `seen[url.pathname]` para dedupe.
- Exatamente por isso Office Arco fica fora; quando Tok Boxbit era a mais recente, quem ficava de fora era Tok. Não é erro da API, do artigo ou da foto; é um seletor que ignora o widget `FeaturedPost1`.
- Blogger API v3 confirmou ambos os artigos `status=live`, URLs reais e HTML íntegro. **Não é recomendável republicar, duplicar, criar conteúdo falso ou mudar datas**.

## Correção pontual projetada

Documento executável para editor de HTML do Blogger:
[blogger_themes/patches/C84_CADEIRA_CERTA_CAROUSEL_SELECTOR.md](../blogger_themes/patches/C84_CADEIRA_CERTA_CAROUSEL_SELECTOR.md)

**Alterar exatamente uma linha no tema**:

Original:
```javascript
var cards = document.querySelectorAll('#Blog1 .post-wrapper');
```

Corrigido:
```javascript
var cards = document.querySelectorAll('#FeaturedPost1 .post-wrapper, #Blog1 .post-wrapper');
```

- Não muda 5 slots, links, fotos, scripts adicionais, layout, artigos ou outros blogs.
- O seletor CSS múltiplo respeita ordem DOM: FeaturedPost1 primeiro, Blog1 depois. Como o widget FeaturedPost1 contém o artigo mais novo, Office Arco será slide 1, Tok Boxbit slide 2, com dedup já existente.
- Para futuro V31 universal, aplicar correção equivalente **na fonte verdadeira do gerador de tema**, não instalar remendos JavaScript a cada publicação.

## Limites e estado desta sessão

**Diagnóstico completo e patch salvo na `main`, mas a alteração NÃO foi aplicada ao tema LIVE.**
Os únicos plugins Blogger conectados neste chat gerenciam conteúdo Posts/Pages/Settings; não há endpoint `theme.edit`/template. O Runner local tem lista expressa de três IDs autorizados para instalação de tema: `4739187376492839837`, `1625257710858445955`, `8476663092477971560`; o blog Cadeira não está autorizado e instalação integral de outro tema seria imprudente. Ferramenta Browser no chat é somente leitura; Cloud Browser com edição exige ChatGPT Work ou ação direta na interface do Blogger.

Assim, a ação restante é **uma única edição em Blogger → Tema → Editar HTML** com backup prévio, seguida de validação GET pública do DOM e controle Anterior/Próximo. **Não declarar C84 “corrigido em produção” enquanto o seletor LIVE ainda contiver a linha antiga.**

## Situação dos artigos/afiliados
C83 continua comprovadamente concluído: Office Arco post LIVE `6656620121237912250`, shortlink oficial `https://s.shopee.com.br/9fMfOM4016`, Tok Boxbit LIVE `3691939235338797956`; 6 posts LIVE e 0 DRAFT. Não reconverter nem republicar; política LIVE automática V31 continua OFF.
