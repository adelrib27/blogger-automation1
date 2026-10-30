# Infraestrutura — Blogger Automation sem ChatGPT Work

Snapshot: 2026-10-30.

## Topologia validada

```text
ChatGPT
  │
  ├─ Blogger_Bridge_V2 ───────────────► Blogger API v3
  │                                     (posts/páginas/leitura/escrita)
  │
  └─ Plugin privado "Blogger Local Runner"
        │ App-backed / MCP
        ▼
     Cloudflare Worker
     blogger-local-runner-gateway
        │ OAuth/PKCE + VPC Service binding BLOGGER_RUNNER
        ▼
     Runner no PC — 127.0.0.1:8765
        │ Playwright / CDP loopback
        ▼
     Google Chrome oficial — 127.0.0.1:9222
        ▼
     Blogger Admin UI
     (criação/configurações/tema)
```

Não há dependência de ChatGPT Work.

## Backup do gateway Cloudflare

Diretório:

`infrastructure/cloudflare/blogger-local-runner-gateway/`

Arquivos:

- `worker.js` — espelho normalizado do source de produção v7 (multipart removido/formatação normalizada; conteúdo lógico preservado).
- `worker-metadata.json` — script ID, versão, ETag, compatibility date, bindings e rotas sem valores de secrets.

Produção no snapshot:

- script: `blogger-local-runner-gateway`
- script ID: `0b0e553e489f47bebcf28d496718ae2d`
- versão: 7
- version ID: `0258427f-fb22-4aa8-afae-b1fe8c83c5c9`
- script ETag: `9f0c25773fb3fceea85dd45b5013df888c124778435580ea949a8373e7da99eb`
- modified: `2026-10-30T03:39:43.660773Z`
- compatibility date: `2026-10-29`

Bindings:

- `BLOGGER_RUNNER` — `vpc_service`, service ID `01a184cb-dd92-7242-8c7f-e8dd12909fa8`
- `OAUTH_SECRET` — `secret_text`; **valor não está no backup**.

MCP tools definidos no Worker v7:

1. `health`
2. `audit`
3. `preflight_blog`
4. `create_blog`
5. `preflight_settings`
6. `configure_settings`
7. `adopt_model_v20`

Rotas REST permitidas:

- `GET /v1/health`
- `POST /v1/audit`
- `POST /v1/preflight`
- `POST /v1/create-blog`
- `POST /v1/preflight/settings-profile`
- `POST /v1/configure-settings`
- `POST /v1/adopt-model-v20`

## Backup do plugin privado do ChatGPT

Diretório:

`infrastructure/chatgpt/blogger-local-runner/`

Arquivos:

- `.app.json`
- `plugin.json`
- `plugin-metadata.json`

Identidade:

- plugin ID: `plugin_asdk_app_6ae33f5d45f0819183150e461cff5616`
- App ID: `asdk_app_6ae33f5d45f0819183150e461cff5616`
- package name: `dev-6ae33f5d45f0819183150e461cff5616`
- display name: `Blogger Local Runner`
- version: `1.0.0`
- release: `PluginRelease_1c864196d5a881918c51960840960fcc`
- scope: `USER`
- discoverability: `PRIVATE`

### Importante sobre o plugin

O pacote é **App-backed**. Os arquivos do plugin não contêm a definição das ferramentas MCP. A superfície de tools vem da conexão App/MCP apontada para o gateway. Alterar somente `plugin.json` não adiciona uma rota nova.

## Runner local

Código remoto versionado em:

branch `blogger-safe-ui-provisioning-v0-2`

Diretório:

`tools/blogger_safe_automator_v0_2/`

Backend mais novo versionado:

`local_service_v05.py`

A instalação local conhecida fica em:

`C:\Blogger-Automator\blogger_safe_automator_v0_3`

### Dependências locais críticas não versionadas

As seguintes dependências foram **provadas em execução real** durante o backup/aplicação do V20, porém não existem na branch atual nem no histórico consultável do repositório:

- `tools/blogger_safe_automator_v0_2/apply_theme_safe.py`
- `tools/blogger_safe_automator_v0_2/backup_theme_safe.py`

Provas operacionais:

- `backup_theme_auto.py` conseguiu gerar backup XML válido usando `backup_theme_safe.py`.
- `apply_theme_auto.py` importou `apply_theme_safe.py` e aplicou o V20 com validação pública.
- A primeira tentativa chegou a lançar erro a partir de `apply_theme_safe.py` exigindo nome literal `theme.xml`, demonstrando a presença e execução do módulo local.

**Backup gap conhecido:** a conexão atual do ChatGPT não possui ferramenta de leitura arbitrária do filesystem do PC, portanto os bytes-fonte desses dois arquivos não puderam ser copiados remotamente nesta sessão. Não afirmar que eles estão respaldados no GitHub. Preservar a cópia local e, quando houver uma rota segura de exportação/arquivo local, versioná-los.

## Runtime no instante do checkpoint

- Local runner HTTP: respondendo.
- Health retornado pela conexão: versão `0.3`.
- Branch possui `local_service_v05.py`.
- Chrome CDP em `127.0.0.1:9222`: indisponível no instante da auditoria final.

Isso é estado transitório de runtime, não regressão do V20 já instalado.

## Recuperação

1. iniciar Chrome oficial com CDP loopback;
2. confirmar `/json/version` em `127.0.0.1:9222`;
3. iniciar/confirmar runner em `127.0.0.1:8765`;
4. rodar `health` e `audit`;
5. se a tool `adopt_model_v20` não aparecer no ChatGPT, atualizar ferramentas do plugin;
6. conferir gateway v7 / `tools/list`;
7. somente depois executar escrita.

Consulte também `CHECKPOINT_ATUAL.md` e os dois checkpoints mestre na raiz.
