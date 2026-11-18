# V31 C60 — writer WordPress universal (checkpoint de início)

**Status:** EM_ANDAMENTO. **Prévia gravada ANTES de alterações de implementação**, em 18/11/2026. O trabalho deve continuar deste checkpoint se a conversa interromper.

## Base comprovada antes de começar
- Branch `main` consultada, HEAD `310e0d4cfeef4974340c3b40a5ecf3b14a04b249` antes da prévia.
- C59 foi encerrada no [checkpoint C59](CHECKPOINT_C59_WORDPRESS_AI_UNIVERSAL_SAFE_2026-11-18.md). [Canário IA/R2 44410047121](https://github.com/adelrib27/blogger-automation1/actions/runs/44410047121) DRAFT_READY, 743 palavras, sem publicação. Workflows SAFE [Casa 44410965031](https://github.com/adelrib27/blogger-automation1/actions/runs/44410965031), [Oficina 44410976595](https://github.com/adelrib27/blogger-automation1/actions/runs/44410976595), [Radar 44410496620](https://github.com/adelrib27/blogger-automation1/actions/runs/44410496620) PASS segundo checkpoint C59.
- `CONTINUIDADE_ESTADO.json` aponta C60 EM_ANDAMENTO, sem mutação remota em curso. Pedido Blogger piloto `articles=3`, três artigos LIVE já entregues; sem autorização para quarto ou LIVE geral.
- Objetivo da issue [#54](https://github.com/adelrib27/blogger-automation1/issues/54): biblioteca universal independente de nichos/sites previstos, produto aprovado e imagem real, campanha correta, publicação sob gates separados.

## Plano C60 seguro
1. Inspecionar os contratos `sites.d`, `site_requests.d`, catálogo R2, handoff, geradores, HTML comercial, cliente Workers AI e adaptadores WordPress.
2. Implementar caminho genérico de **rascunho WordPress**, com identidade/site e credenciais externos reais, quota de solicitação, idempotência e modo dry-run padrão. Não publicar LIVE, não criar blog fictício e não expor segredos.
3. Adicionar regressões com WordPress REST falso e testes de qualidade, limites de quota/campanha. Validar CI em PR antes de merge, se o conector permitir.
4. Distinguir `código/testes`, `dry-run real` e `DRAFT WordPress criado`: nenhuma publicação ou criação de rascunho remoto ocorrerá sem pedido autorizado e credenciais verificadas.
5. Conferir cron C55 nos serviços existentes (não inferir execução agendada só por existência de YAML).

## Trilho de resultados
- **FEITO:** prévia de missão e evidências documentadas neste arquivo.
- **EM ANDAMENTO:** inspeção de código e implementação C60.
- **PENDENTE:** evidências CI/PR, observação de cron, homologação com WordPress real e encerramento em `V31_CONTINUAR_AQUI.md`.

**Regra:** qualquer execução interrompida deve reler este documento e o JSON em `main`; não repetir writes sem read-after-write. Não tocar Worker v1.0/Pinterest/Runner nem forçar quality gates.
