# Blogger Automation V31 R1 — Shopee V23, primeira seleção real SAFE

**Escopo único:** blog LAB `4739187376492839837`, Page LOJA `2446067640331732447`.

**Sem automação de publicação:** esta etapa apenas chama o motor Shopee V23 autenticado no GitHub Actions, valida intenção e links de afiliado, exige 16 fotos e 16 itens diferentes e produz o artefato `selecao_shopee_v23_REAL_SAFE.json`.

A seleção não é fabricada a partir de produtos de outros blogs. O histórico inicial foi semeado por leitura do Blogger Bridge V2 da página pública aprovada em 2026-11-03, antes da primeira consulta Shopee. Nenhum item desse seed foi tratado como consulta recente da API.

## Fluxo SAFE

1. Configuração explícita com quatro categorias: Decoração, Organização, Cozinha e Quarto; quatro intenções por categoria.
2. `shopee_oportunidades_v23.scan_v23()` consulta a Shopee Affiliate API com os secrets já configurados no GitHub, sem imprimir chaves.
3. Filtros semânticos existentes + 16 regras específicas; Policy Guard central bloqueia itens proibidos, falsos positivos e URLs de imagem inválidas.
4. Priorização de itens fora da última janela de rotação; fallback registrado quando necessário; uma oferta por intenção, máximo dois itens por loja.
5. `generateShortLink()` existente emite 16 links; `resolved_to_shopee()` comprova o domínio de destino; imagem HTTPS de fonte Shopee para todos os 16.
6. Adapter V23→V31 revalida 16 produtos; script salva apenas artefato SAFE e encerra, **sem Blogger.write**.
7. Workflow GitHub `push` restrito à branch LAB e somente ao arquivo `blogger_stores/lab/v31_shopee_safe_trigger.txt`, `permissions: contents: read`, sem `schedule`. Falha aborta e não publica.

## Critérios de promoção

- Ter um run GitHub Actions concluído com sucesso e seleção gerada hoje/48 h, sem secret vazado.
- Reexecutar Policy Guard na seleção obtida, comparar IDs e histórico, verificar 16 fotos e links, checar o LAB público.
- Executar o publicador em `--apply` apenas depois de backup do HTML público, SHA do conteúdo atual, primeira prévia SAFE e confirmação explícita; readback + prova pública após PUT. Nunca pular esta etapa.
- Somente após sucesso LIVE e persistência de rotação avaliar o workflow diário e replicação para novos blogs.

## Estado

O código local foi verificado com testes offline e regressões semânticas V23. **Não implica execução autenticada Shopee, publicação Blogger nem agendamento diário**, que exigem suas provas de execução independentes.