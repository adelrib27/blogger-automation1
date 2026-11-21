# C81 — retomada de 21/11/2026
Código de continuidade `V31-C81-20261121-DRAFT`. Continuação do [checkpoint de pausa](CHECKPOINT_C81_PAUSA_WORK_LIMITE_2026-11-20.md). Base da auditoria `a0f0e3d925bbb157ab5f9969f5e0c70fd7be8e8c`.

## Blogger
O [agendamento de 04h17 de Brasília](https://github.com/adelrib27/blogger-automation1/actions/runs/44879578667/job/136771860650) concluiu histórico autenticado, verificação independente e entrega. O replay retornou o mesmo ID `4106024906916105222` e SHA-256 HTML `acf054f9eb4b65196aa46544c8402e7d603144d781604e006042059ba263569c`. GET independente confirmou status draft e título “Guarda-roupa Toledo Santos Andirá: o que conferir antes de comprar”. HTML contém SKU `shopee:1243712796:23398984325`, foto Shopee, link interno de guarda-roupa, aviso de comissão, link patrocinado e CTA. D1 marcou o job USED na campanha moveisparacadacanto. Preservar ID.

## Agendas e cotas
O [scheduler editorial C81](https://github.com/adelrib27/blogger-automation1/actions/runs/44881521670) pulou os quatro jobs. A [ponte LAB](https://github.com/adelrib27/blogger-automation1/actions/runs/44841131720) concluiu seu despacho. Execuções legadas Casa e Oficina concluíram com sucesso, Radar registrou um sucesso e uma falha. Estas agendas são independentes da homologação C81.
Na leitura inicial do D1 de 21/11 UTC, Blogger utilizava 1/3 HTTP e 1/3 SEARCH, sem bloqueio. WordPress sem linha de orçamento e sem lease. O conversor tinha zero de três reservas do dia. O Firecrawl conectado ao chat informou 978 créditos. A execução operacional confere separadamente a chave do GitHub.
 
## WordPress em acompanhamento
Busca autenticada do SKU `shopee:400124163:42079451217` em Casa sem resultados. O READY anterior de outro SKU deve ser preservado. O [disparador isolado](https://github.com/adelrib27/blogger-automation1/actions/runs/44908860014) solicita orçamento 1, com trava e deduplicação do conversor existente. A tentativa anterior teve erro de sintaxe YAML e zero jobs. Conferir resultado do conversor, canário e CMS antes de qualquer repetição. Política LIVE em `pending_policy_approval`.

A chave Firecrawl do ambiente operacional confirmou 978 créditos. O [primeiro conversor](https://github.com/adelrib27/blogger-automation1/actions/runs/44908874467) parou nos testes por falta de cryptography. Zero reservas D1 em 21/11 após a falha. A [correção](https://github.com/adelrib27/blogger-automation1/commit/1b7ea2332a0a48f49dc8d75e532ec2d37a2428a0) instala a dependência antes do teste. Acompanhar o [conversor após correção](https://github.com/adelrib27/blogger-automation1/actions/runs/44908968569) e o canário disparado pela conclusão dele. Disparador temporário removido.
