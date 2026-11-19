# V31 C62 — canário WordPress REAL em DRAFT: Casa e Decoração (19/11/2026)

**PRÉVIA DURÁVEL. Estado: EM_ANDAMENTO. Nenhum WordPress POST neste ponto.**

## Autorização / propósito
O proprietário pediu o teste das automações de artigos e remover o teto de três. C61 já criou um Blogger DRAFT real e removeu o teto. C62 verifica a pendência C60 de **primeiro WordPress DRAFT real** no Casa e Decoração (instalação e campanha reais), sem LIVE e sem alterar os cron legados.

## Contrato seguro
- Testar primeiro autenticação REST e histórico de posts WordPress via credenciais existentes do **próprio Casa**, acessíveis somente no Environment GitHub. Não registrar tokens.
- R2 da campanha `wordpress_casa_decoracao`, apenas SKU `eligible` com foto real e link exato convertido, não reutilizado nos posts e com pauta derivada de título de produto realmente disponível.
- Um pedido temporário e explícito de TESTE, **1 rascunho total**, será criado apenas no runtime da Action (não registrado em `site_requests.d` da main), para evitar cron novo não autorizado. O writer C60 será usado com `status=draft`, originalidade de IA, CTA, disclosure, internos e read-after-write. O teste não autentica credenciais de futuros sites; isso continua exigindo secret por instalação.
- Em erro de identidade, permissão, conteúdo, campanha, R2 ou qualidade: **0 POST**; se a escrita tiver sido tentada e resposta inconclusiva, verificar posts WordPress antes de qualquer repetição.
- Workflow temporário, disparo por arquivo de controle; primeiro `preview` sem escrita. Após prova/impedimento, remover temporários e registrar evidências.

## Base confirmada
- C61 PR #81 e #82 MERGED; Blogger Móveis 3 LIVE+1 DRAFT real com foto e 2 links internos após correção.
- C60 #44412775615 WP Casa preview R2+43 posts, 0 POST; ainda não foi confirmado POST real.
- GitHub Casa cron #44451960384 SUCCESS; nomes de credenciais protegidas existentes nos workflows Casa. Isso não comprova acesso do writer C60 ao endpoint `settings` do WordPress.

## Próximos passos
1. Auth/read-only real com logs apenas de contagens e booleanos.
2. Se identidade e candidatos passam, geração original IA com worker e 1 único POST draft, nunca LIVE.
3. Confirmar draft REST e portal, registrar PR/CI e remover workflow temporário.

**Não usar Blogger/WordPress conectores como fonte de segredos; não alterar Runner/Pinterest/Worker v1.0.**

## C62 marco — autenticação WP e histórico

- [Teste #44538164537](https://github.com/adelrib27/blogger-automation1/actions/runs/44538164537) **FALHOU fechado antes de POST**: credenciais Casa disponíveis, `site_settings()` foi aceito; `list_posts(include_unpublished=True)` retornou `wordpress_http_HTTPError` ao consultar múltiplos status no mesmo filtro REST. 0 WordPress writes, 0 Shopee/R2 writes.
- Próximo passo: diagnóstico GET somente com variantes de status (`any`, `publish`, `draft` e lista), expondo apenas códigos HTTP; corrigir contrato REST com teste fake se necessário antes de POST.
