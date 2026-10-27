# Blogger Safe Automator v0.2 — UI Provisioning

Camada local complementar ao Blogger Bridge/API. Objetivo: cobrir ações que a API Blogger v3 não expõe, começando pela criação segura de um novo blog no painel do Blogger.

## Princípios de segurança

- sessão Playwright persistente e visível;
- não automatiza login/senha Google;
- `audit` é somente leitura;
- `create-blog` faz apenas pré-validação por padrão;
- criação real exige `--apply` **e** `--confirm "CREATE BLOG"`;
- se o seletor de blogs, campos ou botões não forem identificados com segurança, a execução falha sem clicar em alternativas genéricas;
- salva diagnóstico local (`json` + screenshot) para ajuste de seletores;
- não contém rotinas de exclusão;
- não altera blogs existentes.

## Instalação no Windows

```bat
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m playwright install chromium
```

## 1. Auditoria do painel

```bat
.\.venv\Scripts\python.exe browser_provision.py audit
```

Na primeira execução, se a sessão persistente ainda não estiver autenticada, faça o login manualmente no Chromium aberto pelo Playwright e execute o comando novamente.

O perfil padrão fica em:

```text
.blogger-playwright-profile
```

Para reaproveitar outro perfil persistente já existente:

```bat
.\.venv\Scripts\python.exe browser_provision.py --profile-dir "CAMINHO_DO_PERFIL" audit
```

## 2. Pré-validação de um novo blog — não cria nada

```bat
.\.venv\Scripts\python.exe browser_provision.py create-blog ^
  --title "Nome do Produto" ^
  --address "nome-do-produto"
```

Resultado esperado:

```text
PREFLIGHT_OK_NO_CHANGES
```

## 3. Criação real

Somente depois de a auditoria/pré-validação estar correta:

```bat
.\.venv\Scripts\python.exe browser_provision.py create-blog ^
  --title "Nome do Produto" ^
  --address "nome-do-produto" ^
  --apply ^
  --confirm "CREATE BLOG"
```

O fluxo segue a sequência documentada oficialmente pelo Blogger:

1. abrir o seletor de blogs;
2. `Novo blog`;
3. preencher o nome;
4. `Próxima`;
5. preencher o endereço;
6. `Salvar`.

## Diagnósticos

Por padrão:

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

Esses arquivos não devem conter senhas; ainda assim, trate screenshots do painel como dados privados.

## Escopo desta v0.2

Incluído:
- auditoria do painel;
- criação segura de blog via UI.

Ainda não incluído:
- instalação/edição de tema XML;
- alterações de Configurações;
- exclusão de blog;
- automação de login Google.

Essas etapas devem ser adicionadas somente depois de validar o fluxo de criação em sessão real.
