# C122 — PONTO DE RETOMADA ANTES DE INVESTIGAR QUATRO OFERTAS SHOPEE
**Data:** 23/11/2026, America/Recife. **Repositório:** adelrib27/blogger-automation1, branch main.
**Pedido:** usuário autorizou prosseguir após a C121. O próximo objetivo é localizar no catálogo V31/R2 ou em registros autênticos a identidade de produto, imagem e link afiliado da campanha apropriada para os artigos WordPress Radar Tech BR #29, #28, #25 e #24. Sem fabricar URLs.

## Estado confirmado via fontes vivas
- Checkpoint C121 e ledger C121 relidos na main. **Seis artigos anteriores** concluídos: #260, #314, #311, #278, #256 e #138. **Não reexecutar nem atualizar** sem nova necessidade evidenciada.
- Quatro pendentes: #29 Arctic Air Cooler (featured media 73), #28 Scanner OBD2 (72), #25 Kapbom KA-8955 (69), #24 Luz RGB (67). Foi observado previamente que não possuem link Shopee no HTML/meta. Isso não é prova de que o produto não esteja no R2.
- C114 writer legado Radar em fail-closed, LIVE automático OFF, suite V31 universal com 8 falhas de contratos legados sem reconciliação comprovada. **Preservar**.
- Fontes de arquitetura C80 do proprietário: Cloudflare conta oficial ID ebb8d5b4cf9a2cb850c6d8051bd2661f, R2 bucket v31-editorial-shopee, D1 v31-universal-ready-safe ID 9bfce7a4-6167-4bfc-a65e-a74c1a34f064. O D1 de segurança não é necessariamente índice de produtos; não inferir que ausência nele significa ausência do catálogo.

## Plano idempotente C122
1. Consultar arquivos/manifests que descrevem chaves de objetos R2 e índices históricos de produto/afiliado; localizar base verificável do SKU, com escopo de campanha e imagem vinculada.
2. Procurar na biblioteca por correspondência da foto/nome/modelo; exigir correspondência específica (não apenas termos genéricos).
3. Se houver oferta validada com URL afiliada da campanha correta, salvar original do post individual, criar prévia editorial factual, conferir, editar URL existente e validar WordPress + público. Do contrário manter o post publicado sem troca artificial de CTA e registrar bloqueio justificável.
4. Não alterar itens de outros blogs, workflows, D1, R2, segurança nem LIVE; nenhuma quota de conversão acionada sem confirmação da identidade.
5. Salvar checkpoint final C122, manifest por item e atualizar V31_CONTINUAR_AQUI.md, distinguindo provas de pendências.

**Código de retomada:** V31-RADAR-C122-20261123-RECUPERAR-QUATRO-OFERTAS-SAFE.
