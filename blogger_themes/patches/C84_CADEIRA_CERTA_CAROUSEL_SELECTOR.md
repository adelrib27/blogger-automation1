# V31 C84 — correção pontual do carrossel do Blogger Cadeira Certa (fonte do tema)

**Blog:** [Cadeira Certa no Home Office](https://cadeira-certa-home-office.blogspot.com/)  
**Blogger ID:** `7163624325768776034`  
**Data da auditoria:** 22/11/2026  
**Estado:** PATCH PREPARADO — **NÃO APLICADO NO TEMA LIVE**. Somente quem possui acesso ao editor de HTML do Blogger deverá aplicá-lo.

## Causa comprovada em `rawHtml` público, não hipótese

O tema atualmente contém a lógica do carrossel independente em um script:
```javascript
// Build a separate highlight from the already rendered cards; never move or hide originals.
var featured = document.getElementById('ub-v21-featured');
if (featured) {
  try {
    var track = featured.querySelector('.ub-v21-track');
    var seen = Object.create(null);
    var cards = document.querySelectorAll('#Blog1 .post-wrapper');
    Array.prototype.forEach.call(cards, function (card) {
      if (track.children.length >= 5) return;
      // ... restante do código original
    });
  } catch (ignore) {
    featured.hidden = true;
  }
}
```

O widget `FeaturedPost1` do Blogger inclui o artigo **mais recente** (Office Arco, post `6656620121237912250`). O widget `Blog1` lista os outros cinco artigos. Portanto a regra de seleção atual ignora permanentemente qualquer artigo colocado pelo Blogger no widget de destaque. Quando o Tok Boxbit era o mais recente, ele era excluído; após publicar Office Arco, esta passou a ser excluída e Tok entrou no carrossel. Diagnóstico confirmado por inspeção HTML pública do widget e do código.

## Correção mínima e robusta (uma linha no código do tema)

Localize **exatamente uma ocorrência** do seletor original, no script que começa pelo comentário `Build a separate highlight from the already rendered cards`.

**ANTIGO:**
```javascript
var cards = document.querySelectorAll('#Blog1 .post-wrapper');
```

**NOVO:**
```javascript
var cards = document.querySelectorAll('#FeaturedPost1 .post-wrapper, #Blog1 .post-wrapper');
```

**Não alterar** o restante da rotina. O seletor composto agrega candidatos na **ordem real do DOM** (no tema observado, `FeaturedPost1` precede `Blog1`). O código existente já possui `seen[url.pathname]` para remover duplicações e `if (track.children.length >= 5) return;` para limitar a cinco slides. As imagens continuam vindo do próprio Blogger, sem inserir fotos inventadas. Nenhum post precisa ser duplicado, republicado ou ter data alterada.

**Estimativa esperada após aplicar o patch em 22/11/2026:**
1. Office Arco (mais recente; vindo do `FeaturedPost1`).
2. Tok Boxbit (primeiro do `Blog1`).
3. Gamer versus escritório.
4. Ajustes de altura/braços/lombar.
5. Mesh versus estofada.

O sexto artigo permanece na seção regular de postagens. A posição de cada título é dinâmica e evolui conforme novos posts entram no widget FeaturedPost.

## Gate operacional

1. Fazer **backup do tema XML** em Blogger → Tema → Fazer backup, preservando o arquivo original.
2. Blogger → Tema → menu ao lado de Personalizar → Editar HTML. Procurar `var cards = document.querySelectorAll('#Blog1 .post-wrapper');`.
3. Conferir que a ocorrência pertence ao comentário `Build a separate highlight from the already rendered cards`.
4. Substituir apenas essa linha pelo seletor composto acima. Salvar.
5. Abrir a homepage anônima em janela nova; confirmar no `#ub-v21-featured` Office Arco e Tok Boxbit (5 slides), imagens, botões Anterior/Próximo, link e responsividade.
6. Verificar também `FeaturedPost1`, o arquivo de postagens, link original dos dois posts e a página Loja. Restaurar o backup se qualquer invariável falhar.
7. Documentar prova da versão LIVE (HTML público depois da edição) antes de marcar concluído. **Não usar CSS extra, scripts externos, nem HTML inserido nos artigos para contornar falha do tema.**

## Limite de escrita desta sessão

Os conectores Blogger disponíveis acessam Posts e Pages, mas **não oferecem edição de Template/Layout**. O Blogger Local Runner V31 possui escrita de tema restrita a **outros IDs autorizados** (não inclui `7163624325768776034`); uma tentativa de instalar modelo inteiro neste blog seria indevida e destrutiva. Os conectores de navegação nesta conversa só leem as abas. Portanto este arquivo é patch aprovado para **aplicação via editor autenticado no Work/Blogger**, ainda não mudança LIVE. O usuário não deve receber uma afirmação de conclusão antes da verificação pública pós-salvamento.
