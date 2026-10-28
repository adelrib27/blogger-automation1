# Blogger Safe Automator v0.3 — Chrome oficial via CDP

Camada complementar ao Blogger Bridge/API para ações que a API Blogger v3 não expõe. Esta versão **não inicia o Chromium do Playwright**: conecta ao **Google Chrome oficial já autenticado** via CDP.

## Segurança mantida

- nenhuma exclusão automática;
- login/senha Google nunca são automatizados nem armazenados;
- CDP fica em loopback por padrão (`127.0.0.1:9222`);
- `audit` é somente leitura;
- `create-blog` faz preflight por padrão;
- criação real exige confirmação explícita `CREATE BLOG`;
- seletores são fail-closed;
- sucesso só é retornado depois de detectar um Blog ID novo e validar a URL pública com HTTP 200;
- URLs gravadas em diagnóstico têm query/fragmento removidos;
- ao terminar, o script **não fecha o Chrome oficial**;
- CDP remoto é bloqueado por padrão.

## Instalação

```bat
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

**Não execute `playwright install chromium` para autenticar Google.**

## Iniciar o Chrome oficial com CDP

```bat
start "" "%ProgramFiles%\Google\Chrome\Application\chrome.exe" ^
  --remote-debugging-port=9222 ^
  --remote-debugging-address=127.0.0.1 ^
  --user-data-dir="C:\Blogger-Automator\chrome-debug-profile" ^
  "https://www.blogger.com/"
```

O perfil `chrome-debug-profile` deve continuar separado do perfil normal do Chrome.

Verificação:

```bat
curl http://127.0.0.1:9222/json/version
```

## Uso direto pela CLI

Auditoria:

```bat
.\.venv\Scripts\python.exe browser_provision.py audit
```

Preflight — não cria nada:

```bat
.\.venv\Scripts\python.exe browser_provision.py create-blog ^
  --title "TESTE BLOGGER AUTOMATION" ^
  --address "teste-blogger-automation"
```

Criação real, somente após o preflight:

```bat
.\.venv\Scripts\python.exe browser_provision.py create-blog ^
  --title "TESTE BLOGGER AUTOMATION" ^
  --address "teste-blogger-automation" ^
  --apply ^
  --confirm "CREATE BLOG"
```

## Serviço local para a futura ponte do ChatGPT

`local_service.py` expõe o automador apenas no próprio PC:

```text
http://127.0.0.1:8765
```

Ele **não escuta na rede local nem na internet** e exige um Bearer token de pelo menos 32 caracteres.

No Prompt de Comando, defina um token somente para a sessão atual e inicie:

```bat
set BLOGGER_RUNNER_TOKEN=COLOQUE_AQUI_UM_TOKEN_ALEATORIO_COM_32_OU_MAIS_CARACTERES
.\.venv\Scripts\python.exe local_service.py
```

Endpoints atuais:

- `GET /v1/health`
- `POST /v1/audit`
- `POST /v1/preflight`
- `POST /v1/create-blog`

O endpoint de criação continua exigindo `confirm = "CREATE BLOG"`. O serviço força `allow_remote_cdp = false` e serializa operações do navegador para evitar duas escritas simultâneas.

## Diagnósticos

Padrão:

```text
logs/browser_diagnostics/
```

Arquivos possíveis:

- `visible_controls.json`
- `blogger_panel.png`
- `preflight_controls.json`
- `after_create_blog.png`
- `failure_controls.json`
- `failure.png`

Screenshots do painel devem ser tratados como dados privados.

## Testes locais

```bat
.\.venv\Scripts\python.exe -m unittest test_browser_provision.py test_local_service.py
```

## Escopo atual

Incluído:

- Chrome oficial + CDP;
- auditoria do painel;
- preflight fail-closed;
- criação segura de blog;
- proteção contra confundir o Blog ID antigo com o novo;
- validação da URL pública;
- serviço HTTP local autenticado e restrito ao loopback;
- testes de regressão de segurança.

Ainda não incluído:

- Configurações;
- Layout;
- Tema;
- exposição segura da ponte externa;
- plugin privado do ChatGPT.

Essas etapas devem usar o mesmo Chrome oficial/CDP, sem voltar ao Chromium interno do Playwright.
