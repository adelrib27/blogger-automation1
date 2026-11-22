# V31 C92 — Ar-Condicionado sem Dúvidas: dois artigos novos com proteção contra ofertas esgotadas
Data: 22/11/2026. Blogger ID `2228849984262880811`, URL `https://ar-condicionado-sem-duvidas.blogspot.com/`.

## Estado pré-mutação autenticado
- 1 artigo LIVE: LG Dual Inverter Compact 12.000 BTUs Blogger ID `940950273343255024`.
- 0 DRAFTs e 10 páginas LIVE.
- Tema C91 homologado em produção, carrossel Loja com uma oferta: controles Anterior/Próximo `hidden` e `display:none`, contador 1 / 1. Preservar HOME, Loja, páginas, links Shopee.
- Campanha oficial existente `arcondicionadosemduvidas`, publicação automática LIVE V31 desativada.
- D1 `v31_shopee_conversion_attempts` em 22/11 tem slot 1 Cadeira Certa e slot 2 Ar-Condicionado/LG. **Restam no máximo um slot UTC nesse dia**, sujeito a concorrência com outros publicadores; NÃO ultrapassar limite nem duplicar tentativa.

## Gate de estoque
- Usuário pediu evitar produtos esgotados. O endpoint `productOfferV2` da API afiliada retorna ID, preço, período, comissão e offerLink, porém não garante estoque/quantidade de variantes no payload público documentado. A inspeção web da Shopee retorna página genérica com barreira de login, sem botões de compra verificáveis. **Não declarar que o estoque existe só porque a API retornou a oferta**. Preço positivo, período válido e offerLink apontam elegibilidade à divulgação, não necessariamente estoque físico.
- Tentar consulta autenticada READ ONLY de IDs exatos e selecionar duas ofertas de aparelhos completos, não controles, peças, acessórios ou itens usados.
- Se não houver prova de estoque, publicar os artigos educativos com avisos claros de que a disponibilidade e a variante precisam ser checadas no checkout; evitar preços e urgência; preferir omitir CTA de produto não confirmado se a oferta não for encontrada. Diferenciar anúncio ativo de estoque confirmado.
- Um link convertido por campanha apenas se a oferta exata passar gates + cota global D1, sem retries e sem inventar SubID. Para segunda oferta, avaliar `offerLink` oficial se a API o fornecer como link de afiliado, anotando que não possui campanha/SubID específico; ou produzir artigo informativo sem CTA se não houver confiança.

## Fontes
- Shopee Affiliate API `productOfferV2` — oficial autenticada via ambiente `v31-editorial-safe`.
- Inmetro PBE: https://www.gov.br/inmetro/pt-br/assuntos/regulamentacao/avaliacao-da-conformidade/programa-brasileiro-de-etiquetagem/tabelas-de-eficiencia-energetica/condicionadores-de-ar/sistema-pbe-para-consulta-dos-produtos-etiquetados
- Inmetro nova etiqueta: https://www.gov.br/inmetro/pt-br/assuntos/regulamentacao/avaliacao-da-conformidade/programa-brasileiro-de-etiquetagem/tabelas-de-eficiencia-energetica/condicionadores-de-ar/nova-etiqueta

## Segurança
Não editar o artigo LG existente, não reconverter LG, não usar shortlinks de outros blogs, não modificar C81/DRAFT assinado, não ativar LIVE automático, não associar modelos diferentes a foto/link. Criar no máximo dois novos artigos, GET cada rascunho antes do publish manual autorizado, verificar HTTP público, atualizar checkpoint.
