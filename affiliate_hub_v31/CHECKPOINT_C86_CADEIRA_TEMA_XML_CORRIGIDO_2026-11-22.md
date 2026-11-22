# V31 C86 — Tema XML Cadeira Certa corrigido e validado localmente (22/11/2026)

## Escopo
Blog https://cadeira-certa-home-office.blogspot.com/ · Blogger ID `7163624325768776034`.
Solicitação do proprietário: corrigir postagem Office Arco que aparece no carrossel mas desaparece da grade principal, SEM reescrever os artigos e mantendo 12 postagens configuradas no Blogger.

## Fonte exata
O proprietário enviou o **HTML completo do tema** via arquivo `Pasted text.txt` no chat V31 C86 (22/11/2026). O original foi validado como XML Blogger íntegro pelo parser lxml (1172 elementos antes da alteração, 14 widgets). O XML é do modelo Universal V31 R52 e já inclui a correção C84 do seletor de carrossel.

### Defeito efetivo confirmado no XML da fonte
Há uma seção:
```xml
<b:section class='featured-post' id='featured_post' name='Featured Post' showaddelement='false'>
  <b:widget cond='data:view.isHomepage' id='FeaturedPost1' locked='true' title='' type='FeaturedPost' visible='true'>
    <b:widget-settings>
      ...
      <b:widget-setting name='useMostRecentPost'>true</b:widget-setting>
    </b:widget-settings>
    ...
  </b:widget>
</b:section>
```
A seção é ocultada por CSS via `.featured-post{display:none!important}`, enquanto o widget ativo marca o post mais recente como destaque. Por isso, o Blogger exibiu Office Arco somente no `FeaturedPost1`, excluindo o cartão da lista `Blog1`. O carrossel V31 estava buscando nos dois, funcionando visualmente, mas a grade do Blog1 tinha cinco dos seis artigos.

## Alterações cirúrgicas no HTML recebido
1. **Removida integralmente a seção `featured_post` contendo o único widget `FeaturedPost1`**, pois ela é oculta, não aparece no Layout e conflita com o componente de carrossel universal. Nenhuma outra seção/gadget modificada.
2. Atualizado o seletor do carrossel de:
   ```javascript
   var cards = document.querySelectorAll('#FeaturedPost1 .post-wrapper, #Blog1 .post-wrapper');
   ```
   para:
   ```javascript
   var cards = document.querySelectorAll('#Blog1 .post-wrapper');
   ```
   O carrossel continua com deduplicação por permalink e até cinco slides; a grade de Blogger recebe todos os posts conforme limite 12 configurado pelo proprietário no Blogger.

**Somente dois hunks de diff**. Widget count original 14 → corrigido 13; todas as outras IDs de widgets preservadas. Nenhum código de campanha, links de afiliados, posts, páginas, D1/R2 ou LIVE V31 foi alterado.

## Resultado da criação do artefato
- **XML corrigido:** `Cadeira_Certa_Home_Office_V31_C86_TEMA_CORRIGIDO.xml` (217.584 bytes)
- **TXT equivalente:** `Cadeira_Certa_Home_Office_V31_C86_HTML_COMPLETO.txt` (217.584 bytes)
- **Backup original:** `Cadeira_Certa_Home_Office_V31_C86_BACKUP_ORIGINAL.xml` (224.834 bytes)
- **Patch diff:** `Cadeira_Certa_Home_Office_V31_C86_ALTERACOES.patch`
- **Relatório:** `RELATORIO_C86_CORRECAO_TEMA_CADEIRA_CERTA.md`.
- SHA256 do XML final: `e3e40311bf161a707c68c289c3018ffa999c57604fcd8bee05fbbe3b0455ac92`
- Arquivos criados e verificados no runtime da **conversa**. **Não fazer afirmação de que estes XMLs estão commitados no GitHub**, somente este checkpoint de instrução está.

## Testes realizados antes da entrega
- `lxml.etree.XMLParser(recover=False,no_network=True)` passou no XML original e corrigido.
- Invariantes de `Blog1`, `page_body`, carrossel `ub-v21-featured`, Loja, scripts de identidade visual, rodapé e componentes V31 preservados.
- `node --check` do script real `UNIVERSAL_V21_SCRIPT` passou.
- O diff tem duas regiões apenas: seção ocultada removida e uma linha seletor atualizado.
- Nenhum teste de salvamento no Blogger ou renderização LIVE pós-troca; **a edição ainda não foi aplicada no Blogger**.

## Próxima ação e homologação
1. Proprietário deve fazer backup independente do tema antes de instalar e copiar/substituir o XML completo via **Tema → Editar HTML**, salvando.
2. Verificar publicamente `#Blog1 .post-wrapper` com 6 IDs únicos, Office Arco e Tok Boxbit, `#ub-v21-featured` com 5 slides, links e imagens, navegação e mobile. Em publicações futuras, a grade respeita limite 12 definido no Blogger.
3. Se falhar validação pós-save, restaurar XML de backup e reavaliar o XML normalizado pelo Blogger, sem duplicar posts.
4. Manter `V31_AUTOLIVE_ACTIVE=false` até homologação da política global V31; Office Arco já está LIVE, não republicar nem reconverter.
