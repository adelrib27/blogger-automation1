# V31 — Radar Tech BR: Etapa 1 de auditoria editorial e categoria Ar-condicionado (PREVIEW)
**Data:** 2026-11-23. **Origem:** solicitação explícita do proprietário para levantar gerador existente, 2 posts e campos da Shopee sem recriar sistema, e incluir a categoria Ar-condicionado no Radar Tech BR.

## Baseline antes de qualquer alteração
- WordPress conectado: `https://radartechbr.com.br/`.
- Categorias por `wp_list_categories` (READ ONLY): `Guias de Compra` ID 1, slug `guias-de-compra`, 23 posts; `Tecnologia` ID 3, slug `tecnologia`, 14 posts. **Nenhuma Ar-condicionado existente**.
- Posts publicados: 37 (`wp_list_posts(status=publish)`).
- Decisão C105/C106/C110/C111: Radar Tech BR somente WordPress, foco tecnologia; menu tecnológico aplicado com hubs existentes; `publish_enabled=false` na rota `wordpress_radartechbr` e LIVE automático bloqueado.

## Mutação limitada autorizada
Criar **somente** taxonomia WordPress `Ar-condicionado` com slug `ar-condicionado`, descrição educativa, **parent=3 (Tecnologia)**, sem reclassificar posts, publicar artigo, tocar no menu FSE ou liberar writers. Conferir por GET após criação e registrar ID/URL no checkpoint final. A categoria pode inicialmente ficar sem artigos: categoria é solicitada explicitamente; evitar submenu vazio até existir conteúdo real e suficiente.

## Auditoria ETAPA 1 (somente leitura)
Buscar no repo ativo: prompt/editorial guide, gerador Radar Tech (legado), escritor universal V31, publicador e schemas do objeto Shopee; comparar textos de 2 artigos reais selecionados no WordPress. A Etapa 1 recolhe provas e origens; correções de texto/código pertencem à Etapa 2/3 e não estão autorizadas nesta etapa.

**Segurança:** zero edição de posts; sem alteração de categorias existentes ou rotas; zero LIVE automático; sem nova cobrança de API Shopee/Firecrawl.
