# Baseline de Políticas — Blogger / Google — 2026-11-01

## Escopo

Este documento é a fonte interna de implementação para as automações Blogger do repositório. Ele separa regras do **Blogger** (hospedagem/conteúdo), regras de **cookies/consentimento** e regras adicionais de **Google Publisher / AdSense**.

## Fontes oficiais

- Blogger — política atualizada com vigência em 16/12/2026: https://draft.blogger.com/content-policy?hl=pt-BR&version=upcoming
- Blogger — política atual: https://www.blogger.com/content-policy?hl=pt_BR
- Blogger — aviso de cookies para visitantes da UE: https://support.google.com/blogger/answer/6253244?hl=pt-BR
- Google Publisher Policies — conteúdo replicado: https://support.google.com/publisherpolicies/answer/11190248?hl=pt-BR
- Google AdSense — políticas/restrições para publishers: https://support.google.com/adsense/answer/10008391?hl=pt-BR

## Regras Blogger implementadas como fail-closed

### Produtos e serviços regulamentados
A automação não deve vender, anunciar nem facilitar a comercialização de categorias que o Blogger identifica como regulamentadas, incluindo álcool, jogos de azar, produtos farmacêuticos, suplementos não aprovados, tabaco, fogos de artifício, armas e dispositivos médicos/de saúde.

Implementação: `config/blogger_policy_guard.json` + `src/blogger_policy_guard.py`.

### Spam / automação repetitiva
O Blogger proíbe conteúdo comercial/promocional indesejado, conteúdo automatizado indesejado, conteúdo repetitivo ou mass solicitation. Portanto:

- cada blog deve ter identidade de nicho própria;
- categorias e regras semânticas devem ser próprias do nicho;
- a seleção Shopee precisa passar SAFE e curadoria semântica;
- não replicar o mesmo conjunto de produtos/descrições entre todos os blogs como solução padrão;
- conteúdo editorial deve agregar contexto e não ser simples republicação automática.

### Práticas enganosas e deturpação
A automação não deve inventar estoque, urgência, desconto, avaliação, garantia, benefício médico ou resultado. Textos gerados passam por uma lista inicial de frases de risco em `deceptiveGeneratedCopyPhrases`; essa lista é complementar à revisão semântica e pode ser ampliada.

### Afiliados
A Loja deve manter divulgação clara de que contém links afiliados e que o blog pode receber comissão. Links comerciais precisam usar `rel="nofollow sponsored noopener"` e apontar apenas para hosts aprovados.

### Imagens
Para a Loja Shopee, a imagem deve vir da fonte Shopee/API aprovada. O guard rejeita hosts de imagem fora dos domínios/CDNs permitidos.

## Cookies / visitantes da União Europeia

O Blogger fornece um aviso nativo de cookies para visitantes da UE. O Google informa que, se o tema ocultar esse aviso, a responsabilidade de notificar/obter consentimento passa para o proprietário do blog. Recursos adicionais que definem cookies (analytics/ads de terceiros etc.) podem exigir aviso ou consentimento adicional/diferente.

Regras internas:

- não usar `cookieChoices = {}` para desativar o aviso nativo;
- não ocultar seletores conhecidos do aviso via CSS;
- alterações de tema devem ser auditadas por esses padrões;
- teste de presença visual deve ser feito com navegador usando `?gl=fr` quando possível;
- não tratar simples presença de texto no HTML como prova suficiente de consentimento.

Auditoria do repositório em 2026-11-01: não foram encontrados `cookieChoices` nem `.cookie-choices-info` no código pesquisável.

## Google Publisher / AdSense

Estas regras adicionais só se tornam gate de monetização Google quando o blog usa anúncios veiculados pelo Google.

O Google Publisher Policies não permite anúncios Google em telas com conteúdo replicado/copied sem comentário, curadoria ou valor adicional; exemplos incluem conteúdo automaticamente gerado sem revisão/curadoria e republicação com mudanças mínimas.

Consequências para o projeto:

- posts editoriais devem ter valor próprio do nicho;
- não espelhar descrições de marketplace como artigos;
- usar comparações, orientação, contexto e revisão humana/semântica;
- lojas podem ser vitrines afiliadas, mas não devem substituir todo o conteúdo editorial do blog se o objetivo for monetização Google.

## Ordem obrigatória da Loja

`Shopee API -> BLOGGER_POLICY_GUARD -> filtros semânticos -> diversidade/rotação -> SAFE -> revisão -> LIVE -> hero 12 -> validação pública -> persistência -> schedule`

Se qualquer gate falhar, preservar a Loja pública anterior.
