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

## Ordem correta de boot/reconexão

### 1. Iniciar Chrome oficial com CDP loopback

```bat
start "" "%ProgramFiles%\Google\Chrome\Application\chrome.exe" ^
  --remote-debugging-port=9222 ^
  --remote-debugging-address=127.0.0.1 ^
  --user-data-dir="C:\Blogger-Automator\chrome-debug-profile" ^
  "https://www.blogger.com/"
```

Validar:

```bat
curl http://127.0.0.1:9222/json/version
```

O perfil `chrome-debug-profile` deve ser separado do perfil normal do Chrome.

### 2. Iniciar o runner local

O runner exige `BLOGGER_RUNNER_TOKEN` com pelo menos 32 caracteres. O valor é segredo operacional e **não deve ser commitado**.

Exemplo de boot da versão v0.5:

```bat
cd /d C:\Blogger-Automator\blogger_safe_automator_v0_3\tools\blogger_safe_automator_v0_2
set BLOGGER_RUNNER_TOKEN=<TOKEN_LOCAL_DE_32_OU_MAIS_CARACTERES>
.venv\Scripts\python.exe local_service_v05.py
```

Se a cópia local ainda não tiver `local_service_v05.py`, sincronizar somente os arquivos validados da branch `blogger-safe-ui-provisioning-v0-2` antes de iniciar.

### 3. Confirmar runner

- `GET http://127.0.0.1:8765/v1/health`
- depois `audit` via plugin/runner.

### 4. Autorizar/reconectar plugin se necessário

O gateway valida o token diretamente contra o runner. OAuth usa PKCE. O token local é recebido pela página de autorização e encapsulado nos tokens OAuth criptografados com `OAUTH_SECRET` no Worker; o valor de `OAUTH_SECRET` não está versionado.

### 5. Atualizar ferramentas do ChatGPT se o schema estiver antigo

`ChatGPT → Plugins → Blogger Local Runner → Gerir aplicação → Atualizar ferramentas`

Se a conversa antiga continuar mostrando apenas seis tools, abrir uma nova conversa depois da atualização.

## Backup do gateway Cloudflare

Diretório:

`infrastructure/cloudflare/blogger-local-runner-gateway/`

Arquivos:

- `worker.js` — espelho normalizado do source de produção v7 (multipart removido/formatação normalizada; conteúdo lógico preservado).
- `worker-metadata.json` — script ID, versão, ETag, compatibility date, bindings e rotas sem valores de secrets.

Produção no snapshot:

- URL/base: `https://blogger-local-runner-gateway.comercebem-ar.workers.dev`
- MCP resource: `https://blogger-local-runner-gateway.comercebem-ar.workers.dev/mcp`
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

### Mapeamento MCP → runner

- `health` → `GET /v1/health`
- `audit` → `POST /v1/audit`
- `preflight_blog` → `POST /v1/preflight`
- `create_blog` → `POST /v1/create-blog`
- `preflight_settings` → `POST /v1/preflight/settings-profile`
- `configure_settings` → `POST /v1/configure-settings`
- `adopt_model_v20` → `POST /v1/adopt-model-v20`

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

## Recuperação resumida

1. iniciar Chrome oficial com CDP loopback;
2. confirmar `/json/version` em `127.0.0.1:9222`;
3. iniciar/confirmar runner em `127.0.0.1:8765`;
4. rodar `health` e `audit`;
5. se a tool `adopt_model_v20` não aparecer no ChatGPT, atualizar ferramentas do plugin;
6. conferir gateway v7 / `tools/list`;
7. somente depois executar escrita.

Consulte também `CHECKPOINT_ATUAL.md` e os dois checkpoints mestre na raiz.
