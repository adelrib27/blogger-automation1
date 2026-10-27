# Blogger Safe Automator v0.3 — Chrome oficial via CDP

Camada complementar ao Blogger Bridge/API para ações que a API Blogger v3 não expõe. Esta versão **não inicia o Chromium do Playwright**: conecta ao **Google Chrome oficial já autenticado** via CDP.

## Segurança mantida

- nenhuma exclusão automática;
- login/senha Google nunca são automatizados nem armazenados;
- CDP fica em loopback por padrão (`127.0.0.1:9222`);
- `audit` é somente leitura;
- `create-blog` faz preflight por padrão;
- criação real exige `--apply` + `--confirm "CREATE BLOG"`;
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

## Auditoria

```bat
.\.venv\Scripts\python.exe browser_provision.py audit
```

Resultado esperado:

```text
"AUDIT_OK"
```

## Preflight de criação — não cria nada

```bat
.\.venv\Scripts\python.exe browser_provision.py create-blog ^
  --title "TESTE BLOGGER AUTOMATION" ^
  --address "teste-blogger-automation"
```

Resultado esperado:

```text
"PREFLIGHT_OK_NO_CHANGES"
```

## Criação real

Somente após o preflight:

```bat
.\.venv\Scripts\python.exe browser_provision.py create-blog ^
  --title "TESTE BLOGGER AUTOMATION" ^
  --address "teste-blogger-automation" ^
  --apply ^
  --confirm "CREATE BLOG"
```

O comando só retorna `CREATE_BLOG_VALIDATED` depois de:

1. executar o fluxo `Novo blog`;
2. detectar um Blog ID diferente do blog de origem;
3. confirmar a URL pública com HTTP 200.

Se alguma validação falhar, o processo não registra sucesso.

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
.\.venv\Scripts\python.exe -m unittest test_browser_provision.py
```

## Escopo atual

Incluído:

- Chrome oficial + CDP;
- auditoria do painel;
- preflight fail-closed;
- criação segura de blog;
- proteção contra confundir o Blog ID antigo com o novo;
- validação da URL pública;
- testes de regressão de segurança.

Ainda não incluído:

- Configurações;
- Layout;
- Tema;
- ponte externa ChatGPT → runner;
- implantação Cloudflare Tunnel.

Essas etapas devem usar o mesmo Chrome oficial/CDP, sem voltar ao Chromium interno do Playwright.
