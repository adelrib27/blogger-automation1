# Blogger Automation V20 — Checkpoint canônico

**Data de consolidação:** 2026-10-30  
**Projeto:** blogger-automation1  
**Branch validada:** `blogger-safe-ui-provisioning-v0-2`  
**Estado geral:** **PASS — provisionamento V20 ponta a ponta validado**

Este arquivo é o checkpoint técnico para retomada em futuras conversas e manutenção. Ele descreve o estado efetivamente validado do sistema em 30/10/2026. Não contém senhas, tokens OAuth, cookies, credenciais Google ou chaves secretas.

---

## 1. Resultado final validado

O sistema está validado para:

1. iniciar automaticamente o Chrome oficial com CDP em loopback;
2. iniciar automaticamente o Blogger Local Runner v0.7;
3. expor o runner ao ChatGPT por plugin privado/MCP;
4. auditar e criar blogs com proteções fail-closed;
5. aplicar configurações/SEO essenciais;
6. selecionar e persistir o fuso `(GMT-03:00) Horário Padrão de Brasília – São Paulo`;
7. aplicar o TEMA MODELO V20 canônico com backup e validação pública;
8. manter blog novo com **zero posts**;
9. renderizar as 5 páginas institucionais canônicas;
10. publicar/validar essas páginas via Blogger Bridge V2;
11. operar sem depender do ChatGPT Work.

Status do teste final:

- Plugin com 8 ferramentas: **PASS**
- Chrome CDP loopback: **PASS**
- Runner v0.7: **PASS**
- `provision_new_blog_v20`: **PASS**
- criação de blog: **PASS**
- settings/SEO: **PASS**
- fuso GMT-03 / São Paulo: **PASS**
- TEMA MODELO V20: **PASS**
- 5 páginas institucionais: **PASS**
- 0 posts publicados: **PASS**
- 0 drafts: **PASS**
- robots personalizados preservados/intocados: **PASS**

---

## 2. Arquitetura final

Fluxo principal:

```text
ChatGPT
  -> Plugin privado "Blogger Local Runner"
    -> Cloudflare Worker / MCP gateway
      -> Blogger Local Runner v0.7 no PC (127.0.0.1:8765)
        -> Google Chrome oficial via CDP loopback (127.0.0.1:9222)
          -> painel Blogger

ChatGPT
  -> Blogger Bridge V2
    -> Blogger API para posts/páginas
```

Responsabilidades:

- **Runner v0.7:** ações de painel que a API Blogger não cobre bem: criação de blog, settings/SEO, tema, navegação segura e provisionamento central.
- **Blogger Bridge V2:** leitura/escrita de posts e páginas, incluindo publicação das 5 páginas institucionais devolvidas pelo provisionador.
- **Cloudflare Worker/MCP:** gateway do plugin. O Worker já anuncia as ferramentas novas; não é necessário alterar Cloudflare para o estado atual.

---

## 3. Ferramentas expostas pelo plugin

O plugin foi atualizado e, em nova sessão do ChatGPT, passou a expor **8 ferramentas**:

1. `health`
2. `audit`
3. `preflight_blog`
4. `create_blog`
5. `preflight_settings`
6. `configure_settings`
7. `adopt_model_v20`
8. `provision_new_blog_v20`

Confirmações literais de escrita continuam obrigatórias:

- criação: `CREATE BLOG`
- settings: `APPLY SETTINGS`
- adoção V20: `ADOPT MODEL V20`
- provisionamento V20: `PROVISION BLOG V20`

---

## 4. Runner local v0.7

Arquivo principal:

```text
tools/blogger_safe_automator_v0_2/local_service_v07.py
```

Health esperado:

```json
{
  "ok": true,
  "service": "blogger-local-runner",
  "version": "0.7",
  "bind": "loopback",
  "capabilities": ["create", "settings", "v20", "provision-new-blog-v20"]
}
```

Porta local:

```text
http://127.0.0.1:8765
```

CDP:

```text
http://127.0.0.1:9222
```

O runner v0.7 carrega por último as camadas de resiliência validadas para Blog ID e fuso horário, incluindo o clique físico final necessário para o radio de São Paulo.

---

## 5. Auto-start do Chrome + runner

Diretório canônico:

```text
tools/blogger_safe_automator_v0_2/windows_autostart_v07/
```

Arquivos:

```text
install_blogger_autostart_v07.ps1
start_blogger_automation_v07.ps1
uninstall_blogger_autostart_v07.ps1
```

Task Scheduler:

```text
BloggerAutomationV20
```

Token local armazenado com Windows DPAPI para o usuário atual:

```text
C:\Blogger-Automator\secrets\blogger_runner_token.dpapi
```

Fallback de inicialização:

```text
%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\BloggerAutomationV20.cmd
```

Log:

```text
C:\Blogger-Automator\logs\autostart\blogger_automation_v07.log
```

Sinal de bootstrap saudável:

```text
Chrome CDP OK.
Iniciando runner v0.7.
BOOTSTRAP_OK runner=0.7 cdp=9222
```

Comando de recuperação validado para reiniciar CDP + runner:

```bat
cd /d C:\Blogger-Automator\blogger_safe_automator_v0_3
powershell -NoProfile -ExecutionPolicy Bypass -Command "$c=Get-NetTCPConnection -LocalPort 9222 -State Listen -ErrorAction SilentlyContinue; if($c){Stop-Process -Id $c.OwningProcess -Force}; $p=Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'python.exe' -and $_.CommandLine -like '*local_service_v07.py*' }; $p | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }; Start-Sleep -Seconds 2; Start-ScheduledTask -TaskName 'BloggerAutomationV20'; Start-Sleep -Seconds 8; Get-Content 'C:\Blogger-Automator\logs\autostart\blogger_automation_v07.log' -Tail 12"
```

---

## 6. Proteções de segurança preservadas

Princípios que não devem ser removidos em refactors futuros:

- Chrome oficial; não voltar ao Chromium interno do Playwright para autenticação Google;
- CDP somente loopback;
- runner HTTP somente loopback;
- Bearer token obrigatório;
- nenhuma automação de senha/login Google;
- confirmação literal para toda escrita importante;
- operações do navegador serializadas/exclusivas;
- fail-closed quando Blog ID não corresponde ao esperado;
- seleção explícita pelo Blog ID antes de settings/tema;
- nenhuma exclusão automática de posts;
- robots personalizados ficam `UNCHANGED`;
- falha parcial gera checkpoint local;
- não declarar sucesso antes de validação posterior.

Durante a correção do fuso, várias tentativas foram bloqueadas ao detectar blog errado; nenhuma escrita foi feita nesses casos. Essa proteção é considerada parte essencial do sistema.

---

## 7. Settings/SEO canônicos

Perfil validado para blogs novos:

- visibilidade para mecanismos de pesquisa: **ON**;
- redirecionamento HTTPS: **ON**;
- lazy loading de imagens: **ON**;
- servir imagens em WebP: **ON**;
- descrição de pesquisa: **ON**;
- descrição do blog: configurada pelo provisionamento;
- fuso: **`(GMT-03:00) Horário Padrão de Brasília – São Paulo`**;
- robots.txt personalizado: **não alterar**;
- cabeçalhos robots personalizados: **não alterar**.

A validação final do fuso exige leitura independente com:

```text
matches_target: true
```

A solução final para o componente de fuso do Blogger usa localização da opção São Paulo e clique físico via `page.mouse`, porque o componente não persistiu corretamente com cliques DOM sintéticos nas tentativas anteriores.

---

## 8. TEMA MODELO V20 canônico

Template canônico:

```text
themes/blogger_modelo_v20/theme.xml.tpl
```

Marker público:

```text
emporio-revisao-visual-20-modelo-final
```

Propriedade fundamental:

```text
inherit_posts = false
```

O modelo **não incorpora posts** do blog de referência.

Fonte validada que originou a promoção canônica:

- Blog: **Conecta Achados**
- Blog ID: `1719259388907013414`
- URL: `https://conectaachados.blogspot.com/`
- paleta validada: `emerald`

Hashes registrados na promoção canônica:

```text
validated rendered theme SHA256:
DF6A3B40003FE64889157F60A6C00A1E05D85DC5CF02425C12091E8738D6F21D

canonical template SHA256:
D83B0E1F1750739F0801458F985DCBB3721D506140127EC30CB4EAEC2A2AF565
```

Round-trip da promoção:

```text
roundtrip_exact_match = true
```

Backup do template anterior na promoção:

```text
C:\Blogger-Automator\backups\blogger-modelo-v20-canonical\20261030T161301Z\theme.xml.tpl.before
```

O sistema aceita identidade visual por paleta:

```text
auto, blue, emerald, plum, terracotta, teal, burgundy, indigo, amber
```

`auto` escolhe a identidade visual para o blog sem alterar a estrutura canônica.

---

## 9. Adoção do V20 em blog existente

Ferramenta:

```text
adopt_model_v20
```

Semântica validada:

- preserva posts existentes;
- não copia posts do blog-modelo;
- gera tema renderizado individual por Blog ID;
- salva backup do tema atual;
- aplica o V20;
- valida marker publicamente;
- usa proteção de Blog ID.

Teste real de adoção validado no **Conecta Achados**.

---

## 10. Provisionamento de blog novo

Arquivo:

```text
tools/blogger_safe_automator_v0_2/provision_new_blog_v20.py
```

Ferramenta do plugin:

```text
provision_new_blog_v20
```

Fluxo central executado numa única chamada:

```text
preflight de entrada
-> criação segura do blog
-> validação do novo Blog ID / URL
-> settings/SEO
-> adoção do TEMA MODELO V20
-> renderização das 5 páginas institucionais
-> checkpoint
```

Retorno de sucesso central:

```text
BLOGGER_NEW_BLOG_V20_CORE_PROVISIONED
```

A ferramenta devolve:

```text
pages_to_publish
next_action = PUBLISH_AND_VALIDATE_V20_PAGES_VIA_BLOGGER_BRIDGE
```

Importante: no estado validado em 30/10/2026, criação + settings + tema são feitos pela tool única. A publicação das 5 páginas é a segunda camada automática, feita pelo Blogger Bridge V2. O fluxo completo está validado ponta a ponta, mas tecnicamente ainda são essas duas camadas.

Em qualquer falha parcial:

```text
PROVISION_PARTIAL_FAILURE
```

O arquivo de checkpoint fica em:

```text
logs/provisioning/provision-v20-YYYYMMDDTHHMMSSZ.json
```

---

## 11. Páginas institucionais canônicas

Fonte:

```text
themes/blogger_modelo_v20/pages.json
```

O manifesto exige exatamente 5 páginas e `inherit_posts=false`:

1. `Termos de Uso` -> `/p/termos-de-uso.html`
2. `Política de Privacidade` -> `/p/politica-de-privacidade.html`
3. `Contato` -> `/p/contato.html`
4. `Aviso de Afiliados` -> `/p/aviso-de-afiliados.html`
5. `Sobre` -> `/p/sobre.html`

A página Contato usa o runtime/formulário compatível com o tema V20.

---

## 12. Teste final ponta a ponta — PASS

Blog criado exclusivamente para validação final:

```text
Título: Laboratório Final V20
Blog ID: 985207980854401026
URL: https://labv20-final-1030-1629.blogspot.com/
```

Resultado da `provision_new_blog_v20`:

```text
status = BLOGGER_NEW_BLOG_V20_CORE_PROVISIONED
settings_validated = true
robots_untouched = true
theme_adopted = true
theme_marker = emporio-revisao-visual-20-modelo-final
posts_deleted = false
posts_copied_from_reference = false
expected_page_count = 5
expected_new_blog_posts = 0
```

Páginas publicadas e validadas:

```text
Termos de Uso
Política de Privacidade
Contato
Aviso de Afiliados
Sobre
```

Validação final pelo Blogger Bridge V2:

```text
5 páginas LIVE
0 posts LIVE
0 drafts
```

Validação independente final de settings:

```text
search_visibility = true
https_redirect = true
lazy_images = true
webp_images = true
search_description = true
custom_robots_txt = false / untouched
custom_robots_headers = false / untouched
timezone = (GMT-03:00) Horário Padrão de Brasília – São Paulo
matches_target = true
```

Checkpoint gerado pelo provisionador no teste final:

```text
C:\Blogger-Automator\blogger_safe_automator_v0_3\logs\provisioning\provision-v20-20261030T193159Z.json
```

---

## 13. Plugin / MCP / Cloudflare

Plugin: **Blogger Local Runner**.

Após atualização das ferramentas, uma nova conversa do ChatGPT passou a enxergar corretamente as 8 tools. A conversa antiga continuava com snapshot de 6 tools, portanto atualização de schema pode exigir **nova conversa/sessão**.

O Worker/MCP já anunciava as ferramentas novas; o problema era cache/snapshot da conversa, não ausência do endpoint no Worker.

Não alterar Cloudflare apenas para “forçar” schema se o Worker já listar as tools. Primeiro abrir nova conversa e redescobrir o plugin.

---

## 14. Conteúdo, posts e Shopee — contexto preservado

O provisionamento V20 é deliberadamente separado da automação editorial de posts.

Regra central:

- tema/modelo não deve carregar posts do blog de referência;
- blogs novos começam com zero posts;
- posts são criados depois pelo fluxo editorial/afiliado apropriado.

Identificador informado para a integração Shopee no projeto:

```text
Shopee AppID: 18352820579
```

Requisitos editoriais estabelecidos para posts afiliados:

- artigos longos e ricos, não descrições curtas;
- conteúdo mais completo que os primeiros posts do Conecta Achados;
- CTA/botão para o produto Shopee já na parte inicial do artigo, incluindo o bloco logo após o segundo parágrafo;
- CTA adicional quando apropriado;
- transparência de link de afiliado;
- não inventar preço/estoque/benefícios não confirmados;
- otimizar também posts antigos ao aplicar o padrão editorial.

Este checkpoint não inclui segredos da API Shopee nem tokens.

---

## 15. Regras para futuras conversas/manutenções

Ao retomar o projeto:

1. considerar V20 como modelo canônico atual;
2. não reconstruir o tema a partir de posts antigos;
3. não apagar posts existentes durante adoção;
4. não alterar robots personalizados sem pedido explícito;
5. usar Blog ID como proteção primária contra blog errado;
6. usar runner v0.7, não voltar para v0.6 salvo diagnóstico deliberado;
7. manter CDP em loopback;
8. validar fuso por leitura posterior, não apenas pelo clique;
9. validar tema por marker público;
10. validar páginas via Bridge;
11. blog novo deve terminar com zero posts antes do início editorial;
12. se o plugin mostrar apenas 6 tools, abrir nova conversa antes de alterar Worker/plugin;
13. preservar checkpoints locais de falhas parciais.

---

## 16. Comandos de sincronização/recovery

Branch validada:

```bat
cd /d C:\Blogger-Automator\blogger_safe_automator_v0_3
git fetch origin blogger-safe-ui-provisioning-v0-2
```

Para restaurar os componentes V20 a partir da branch validada, revisar primeiro o `git status` e então recuperar seletivamente os arquivos/diretórios necessários. Não fazer checkout destrutivo de todo o repositório sem revisar alterações locais.

Componentes centrais:

```text
tools/blogger_safe_automator_v0_2/local_service_v07.py
tools/blogger_safe_automator_v0_2/provision_new_blog_v20.py
tools/blogger_safe_automator_v0_2/settings_profile.py
tools/blogger_safe_automator_v0_2/apply_theme_auto.py
tools/blogger_safe_automator_v0_2/backup_theme_auto.py
tools/blogger_safe_automator_v0_2/install_modelo_v20_adoption.py
tools/blogger_safe_automator_v0_2/render_modelo_v20_theme.py
tools/blogger_safe_automator_v0_2/promote_validated_model_v20.py
tools/blogger_safe_automator_v0_2/windows_autostart_v07/
themes/blogger_modelo_v20/theme.xml.tpl
themes/blogger_modelo_v20/pages.json
```

Camadas de resiliência v0.7 carregadas pelo runner:

```text
blog_id_url_resilience_v07.py
timezone_resilience_v07.py
timezone_keyboard_resilience_v07.py
timezone_offscreen_resilience_v07.py
timezone_virtual_window_resilience_v07.py
timezone_physical_click_resilience_v07.py
```

---

## 17. Próxima manutenção recomendada

O sistema já está utilizável e validado. A próxima melhoria opcional, sem bloquear o uso, é transformar a publicação das 5 páginas em uma etapa embutida na própria operação `provision_new_blog_v20`, caso se queira literalmente **uma única chamada** do início ao fim. Hoje o fluxo é automático e validado, porém dividido em:

```text
1. provision_new_blog_v20 -> cria + settings + tema + renderiza páginas
2. Blogger Bridge V2 -> publica/valida as 5 páginas
```

Não tratar essa separação como falha do V20 atual.

---

## 18. Estado para retomada

**V20 CANÔNICO: PASS**  
**AUTO-START: PASS**  
**PLUGIN 8 TOOLS: PASS**  
**CREATE BLOG: PASS**  
**SETTINGS/SEO: PASS**  
**GMT-03 SÃO PAULO: PASS**  
**TEMA: PASS**  
**5 PÁGINAS: PASS**  
**ZERO POSTS/DRAFTS NO BLOG NOVO: PASS**  
**PROVISIONAMENTO PONTA A PONTA: PASS**

Este é o ponto correto para continuar o projeto.
