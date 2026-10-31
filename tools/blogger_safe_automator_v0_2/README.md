# Blogger Safe Automator — estado validado v0.7

Automação segura do Blogger usando **Google Chrome oficial via CDP loopback**, Blogger Local Runner e plugin privado do ChatGPT.

> Checkpoint canônico completo: `docs/BLOGGER_AUTOMATION_V20_CHECKPOINT_2026-10-30.md`

## Estado atual

Validado em 30/10/2026:

- Chrome oficial + CDP loopback;
- auto-start do Chrome e runner no Windows;
- Blogger Local Runner v0.7;
- plugin privado com 8 ferramentas;
- criação segura de blog;
- configurações/SEO;
- fuso GMT-03 / São Paulo;
- TEMA MODELO V20 canônico;
- adoção V20 em blog existente sem apagar posts;
- provisionamento V20 de blog novo;
- manifesto das 5 páginas institucionais;
- publicação/validação das páginas via Blogger Bridge V2;
- blog novo validado com 0 posts e 0 drafts.

## Arquitetura

```text
ChatGPT
  -> Blogger Local Runner plugin / MCP gateway
    -> http://127.0.0.1:8765
      -> Chrome oficial via CDP http://127.0.0.1:9222
        -> painel Blogger

ChatGPT
  -> Blogger Bridge V2
    -> posts e páginas pela API Blogger
```

## Segurança mantida

- nenhuma exclusão automática de posts;
- login/senha Google nunca são automatizados nem armazenados;
- CDP somente em loopback (`127.0.0.1:9222`);
- runner somente em loopback (`127.0.0.1:8765`);
- Bearer token obrigatório;
- CDP remoto bloqueado;
- operações de navegador serializadas;
- confirmação literal para ações de escrita;
- Blog ID validado antes de settings/tema;
- seletores fail-closed;
- robots personalizados permanecem intocados;
- checkpoints de falha parcial;
- sucesso somente após validação posterior.

## Runner v0.7

Arquivo:

```text
local_service_v07.py
```

Health:

```json
{
  "ok": true,
  "service": "blogger-local-runner",
  "version": "0.7",
  "bind": "loopback",
  "capabilities": ["create", "settings", "v20", "provision-new-blog-v20"]
}
```

## Ferramentas do plugin

1. `health`
2. `audit`
3. `preflight_blog`
4. `create_blog`
5. `preflight_settings`
6. `configure_settings`
7. `adopt_model_v20`
8. `provision_new_blog_v20`

Confirmações:

```text
CREATE BLOG
APPLY SETTINGS
ADOPT MODEL V20
PROVISION BLOG V20
```

## Auto-start Windows

Diretório:

```text
windows_autostart_v07/
```

Task Scheduler:

```text
BloggerAutomationV20
```

Log:

```text
C:\Blogger-Automator\logs\autostart\blogger_automation_v07.log
```

Bootstrap saudável:

```text
Chrome CDP OK.
Iniciando runner v0.7.
BOOTSTRAP_OK runner=0.7 cdp=9222
```

## Settings/SEO canônicos

- visibilidade de pesquisa: ON;
- HTTPS redirect: ON;
- lazy images: ON;
- WebP: ON;
- descrição de pesquisa: ON;
- fuso: `(GMT-03:00) Horário Padrão de Brasília – São Paulo`;
- robots.txt personalizado: UNCHANGED;
- headers robots personalizados: UNCHANGED.

## TEMA MODELO V20

Arquivos centrais:

```text
../../themes/blogger_modelo_v20/theme.xml.tpl
../../themes/blogger_modelo_v20/pages.json
```

Marker:

```text
emporio-revisao-visual-20-modelo-final
```

O modelo não incorpora posts (`inherit_posts=false`).

Paletas:

```text
auto, blue, emerald, plum, terracotta, teal, burgundy, indigo, amber
```

## Provisionamento de blog novo

Arquivo:

```text
provision_new_blog_v20.py
```

Fluxo central:

```text
criar blog
-> validar Blog ID/URL
-> settings/SEO
-> TEMA MODELO V20
-> renderizar manifesto das 5 páginas
-> checkpoint
```

Sucesso:

```text
BLOGGER_NEW_BLOG_V20_CORE_PROVISIONED
```

A publicação das páginas é concluída pelo Blogger Bridge V2. Essa arquitetura foi validada ponta a ponta.

## Páginas canônicas

1. Termos de Uso
2. Política de Privacidade
3. Contato
4. Aviso de Afiliados
5. Sobre

## Teste final de referência

```text
Título: Laboratório Final V20
Blog ID: 985207980854401026
URL: https://labv20-final-1030-1629.blogspot.com/
```

Validado:

```text
settings/SEO PASS
GMT-03 São Paulo PASS
tema V20 PASS
5 páginas LIVE
0 posts LIVE
0 drafts
robots intocados
```

## Diagnósticos e checkpoints

```text
logs/browser_diagnostics/
logs/provisioning/
```

O provisionador salva:

```text
logs/provisioning/provision-v20-YYYYMMDDTHHMMSSZ.json
```

## Recuperação do bootstrap

```bat
cd /d C:\Blogger-Automator\blogger_safe_automator_v0_3
powershell -NoProfile -ExecutionPolicy Bypass -Command "$c=Get-NetTCPConnection -LocalPort 9222 -State Listen -ErrorAction SilentlyContinue; if($c){Stop-Process -Id $c.OwningProcess -Force}; $p=Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'python.exe' -and $_.CommandLine -like '*local_service_v07.py*' }; $p | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }; Start-Sleep -Seconds 2; Start-ScheduledTask -TaskName 'BloggerAutomationV20'; Start-Sleep -Seconds 8; Get-Content 'C:\Blogger-Automator\logs\autostart\blogger_automation_v07.log' -Tail 12"
```

## Regra de manutenção

Não voltar a tratar o projeto como v0.3/v0.6 apenas porque nomes históricos de diretório ainda existem. O estado operacional validado é **runner v0.7 + V20 canônico**.

Para detalhes, hashes, backups, histórico de promoção do tema, arquitetura do plugin e regras de retomada, consultar:

```text
docs/BLOGGER_AUTOMATION_V20_CHECKPOINT_2026-10-30.md
```
