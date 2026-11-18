# C51 — Substituir autorização estática de IDs no Blogger Local Runner

**Estado: módulo de correção preparado e testável no GitHub; NÃO instalado no Runner Windows.**

## Incidente real (18/11/2026)

- Blogger criado, SEO configurado e três artigos LIVE: https://moveisparacadacanto.blogspot.com/
- Blog ID: `1439741542627895062`.
- Runner `0.9-v31-r52-candidate`, Chrome/CDP loopback e sessão funcionando.
- `health` mostra `universal_v31_allowed_blog_ids` com somente **3 IDs predefinidos**: `4739187376492839837`, `1625257710858445955`, `8476663092477971560`. O blog recém-criado não está incluído.
- `adopt_model_v31_exact` com identidade exata retorna `target_not_authorized`. Esse é um bloqueio da implementação local, **não do Blogger nem uma preferência solicitada pelo proprietário**.
- `source_manifest_v31()` retorna `inspection_not_enabled`, portanto o código em execução `local_service_v31.py` **não pode ser lido ou corrigido no PC com as tools atualmente disponíveis**. O projeto GitHub contém o backup dos arquivos até `local_service_v08.py` em branch histórica e um adaptador de inspeção V31 em branch LAB; **não contém uma cópia comprovada do `local_service_v31.py` instalado**.

## Correção esperada

Uma lista congelada de blogs de laboratório **não pode decidir quais novos blogs V31 podem receber tema**. O Runner deve autorizar automaticamente um blog ao verificar sua identidade em uma sessão Blogger autenticada, preservando:

1. ID, título e URL públicos fornecidos na chamada são comparados com o **inventário de blogs obtido pelo Runner diretamente da conta Blogger autenticada**, nunca da própria requisição. Se inventário indisponível, abortar.
2. Aba Chrome/CDP aponta ao **mesmo Blog ID** e host Blogger oficial (não outro blog da conta).
3. Bloquear duplicidade, IDs desconhecidos, divergência de título/URL, URLs falsas, login não disponível e falhas de leitura; não adicionar uma permissão universal irrestrita.
4. Com a identidade confirmada, manter backup XML anterior e rollback, verificação de tema público e execução serializada do Writer. A aprovação do destino não basta para garantir instalação segura.
5. No `provision_new_blog_v31`, após criar novo blog, revalidar automaticamente a identidade pelo inventário autenticado e prosseguir à instalação sem solicitar uma nova autorização manual de ID.
6. `health` deve expor diagnóstico sem lista fixa de alvos como regra de autorização; `v31_enabled_for_new_blogs` precisa refletir o comportamento realmente implantado.

**Código disponível:** `authorization_v31.py` é o verificador puro fail-closed (nenhum write), com testes de blog recém-criado, IDs futuros, URLs/IDs errados e conta/aba divergentes. É apenas o bloco de autenticação, NÃO uma implementação do instalador.

## Integração necessária no Runner REAL

Na máquina Windows, após confirmar backup e origem do serviço ativo:

- Recuperar/inspecionar `local_service_v31.py` atual pelo mecanismo seguro de inspeção somente leitura, **sem copiar segredos**. O mecanismo já aparece no plugin, mas está explicitamente desligado pelo gate `BLOGGER_V31_SOURCE_INSPECTION_ENABLED`.
- Localizar a condição que emite `target_not_authorized` e substituir o requisito de ID na lista estática pelo `authorize_theme_target(...)`. O inventário e URL ativos devem vir de código de sessão autenticada, nunca campos de entrada; **não eliminar o gate de identidade**.
- Integrar a verificação também no `provision_new_blog_v31`, preservando locks/CDP, backups e validações do tema. Atualizar os contratos MCP somente se houver novo endpoint (não é necessário para trocar a regra interna da rota existente).
- Testar em SAFE com ID conhecido inválido e com o Blogger criado; validar backup, instalação, identidade e leitura pública. Só depois afirmar `theme_installed=true`.
- A instalação local do Runner e o restart **não são executáveis pela conexão GitHub**, e o plugin atual não possui operação de atualização do código do serviço Windows. Não declarar uma alteração no GitHub como implantação no Windows.
- Não usar `provision_new_blog_v31` de novo com mesmo slug para tentar instalar: isso poderia duplicar ou falhar de forma inesperada. O blog já existe!

## Objetivo original do projeto

Ajustar o Runner para que todo novo blog criado pelo **V31 universal** possa receber o tema sem um cadastro de ID adicional, respeitando as proteções contra alteração no blog errado. Os três artigos já publicados e o conversor R2 devem permanecer intactos.

**Bloqueio atual de implantação:** permissão de inspeção de fonte desligada no serviço Windows e ausência de ferramenta remota de alteração/restart do código local. A liberação da inspeção não substitui a revisão segura do patch de instalação.
