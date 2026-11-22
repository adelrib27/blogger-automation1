# V31 C81 — Correção de links institucionais do tema Blogger Móveis (22/11/2026)

## Escopo e causa comprovada
Blog: https://moveisparacadacanto.blogspot.com/ · Blogger ID `1439741542627895062`.

O navegador conectado leu o menu do cabeçalho e rodapé do tema e confirmou links fixos para `/p/sobre.html`, `/p/loja.html`, `/p/contato.html`, `/p/termos-de-uso.html` e `/p/aviso-de-afiliados.html`. A API Blogger mostrou que havia apenas três páginas, entre as quais `/p/sobre-o-moveis-para-cada-canto.html` e `/p/transparencia-comercial-e-links-de.html`; esses nomes não correspondiam aos links fixos. `/p/politica-de-privacidade.html` existia e estava correto.

[Preview salvo antes das mutações](CHECKPOINT_C81_MOVEIS_MENU_LINKS_PREVIEW_2026-11-22.md).

## Correções efetivadas
Criadas pela API Blogger v3 cinco páginas (HTTP 200, `status=live`), cada uma confirmada por GET individual após a criação, com path idêntico ao do menu:

| Item fixo no tema | Caminho confirmado | ID Blogger |
|---|---|---|
| Sobre | `/p/sobre.html` | `5171360877001212587` |
| Contato | `/p/contato.html` | `8715233324306119663` |
| Loja | `/p/loja.html` | `5105320514641154037` |
| Termos de Uso | `/p/termos-de-uso.html` | `848924806071723739` |
| Aviso de Afiliados | `/p/aviso-de-afiliados.html` | `1707302568283157916` |
| Política de Privacidade (já operante) | `/p/politica-de-privacidade.html` | `5725767004918622546` |

- `Sobre` e `Aviso de Afiliados` possuem um resumo e link às páginas editoriais completas criadas anteriormente; nenhum conteúdo original foi excluído.
- `Contato` oferece orientações para sugestões/comentários sem publicar nenhum endereço de e-mail pessoal não autorizado. **Falta canal privado de contato** (a definir pelo proprietário); não prometer que há formulário/e-mail operacional.
- `Loja` é página informativa que encaminha para os três artigos LIVE. Não inventa ofertas nem associa novos SKUs.
- `Termos de Uso` contém informação editorial geral; não alegar revisão jurídica final.

## Validação após escritas
- `list_pages` autenticado: **8 páginas LIVE** (3 anteriores, 5 novas).
- `get_page` autenticado: 5/5 novas páginas `status=live` com paths exatamente iguais aos hyperlinks lidos do tema.
- `list_published_posts`: **3 artigos LIVE**; `list_drafts`: **6 artigos DRAFT**, inclusive piloto assinado C81.
- **0 alterações em tema, menus, posts, DRAFTs, SKU, campanhas, Shopee, Cloudflare R2/D1, github variables ou política LIVE** nesta correção.
- Atenção: links têm agora destinos corretos por comparação HTML do tema vs. API Blogger; não houve browser público recarregado após a criação, então a verificação de renderização visual end-to-end fica distinta do GET autenticado.
- Não criar outra vez páginas com esses slugs. Em qualquer retry, fazer `list_pages` e GET do ID primeiro.

## Pendências restantes
1. Se o objetivo é um contato privado real, definir explicitamente o e-mail público ou formulário autorizado pelo titular e revisar a página `Contato` por `update_page` mantendo ID/slug.
2. Conferir menu visual da homepage após cache/atualização; se os links hardcoded não corresponderem, o conteúdo do template exigirá revisão por ferramenta apropriada, não pela API de páginas.
3. Trilha C81 de novos DRAFTs agendados continua independente, aguardando homologação com run `event=schedule` depois do rollout. Política LIVE nova continua desligada.
