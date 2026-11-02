# CHECKPOINT — Pacote portátil final Blogger Automation

Data: 2026-11-02
Projeto: `blogger-automation1 Teste Laboratório sem Work`
Pacote: `Blogger_Automation_Unificado_2026-11-02_FINAL.zip`

## Fonte congelada

- repositório: `adelrib27/blogger-automation1`
- main usado na build validada: `f2da8e441ac474b0faf731e6000783b9f3bd07d0`
- runner branch: `blogger-safe-ui-provisioning-v0-2`
- runner commit: `249f766ee20e34782de2505ac9c302523a840507`
- construtor portátil: `portable/build_portable_package.py`

## Integridade do pacote interno

- arquivos: `769`
- SHA-256: `4d9716928d4999d3c439385dd8d5eabe54e16ed3d012378841bf2a0565505b6f`
- `unzip -t`: PASS
- `compileall`: PASS
- secret scan: PASS
- credenciais reais incluídas: **não**

## Build de validação

GitHub Actions:
- run: `41502067306`
- job: `125471784527`
- artifact: `13168937243`
- conclusão: `SUCCESS`

Validações executadas na build:
- instalação do `requirements.txt` do próprio pacote: PASS
- imports externos: googleapiclient, google.auth, google_auth_oauthlib, google.genai, requests, cloudinary, PIL, playwright: PASS
- `blogger_policy_guard_self_test`: **13/13 OK**
- imports críticos do runner: `apply_theme_safe`, `apply_theme_auto`, `backup_theme_auto`, `run_with_cdp_resilience_v08`, `provision_new_blog_v20`, `local_service_v08`: PASS

## Gap histórico do runner fechado

Foi versionado em `blogger-safe-ui-provisioning-v0-2`:
- `tools/blogger_safe_automator_v0_2/apply_theme_safe.py`

O backup atual já é autocontido em `backup_theme_auto.py` + resiliência v0.8. Portanto o caminho V20 não depende mais do arquivo local ausente documentado no snapshot antigo.

## Casa Prática Lab — referência visual final

Antes do empacotamento foi concluído e validado:
- Page LOJA 20+12;
- layout amplo;
- carousel real;
- share card branco + ícone verde + Web Share/clipboard fallback;
- Store Post técnico fora da home;
- 3/3 artigos editoriais com imagem;
- Policy Guard;
- retry HTTP 429;
- writer permanente reaplicando/verificando share card.

Run de fechamento do share card:
- run `41500419347`
- job `125466150980`
- `CASA_PRATICA_LAB_PUBLIC_E2E_PAGE_MATURE_PASS`

## Conteúdo portátil principal

- `run.py` — entrada unificada
- `requirements.txt`
- `instrucoes.txt`
- `LEIA-ME-PRIMEIRO.txt`
- `.env.example`
- `scripts/oauth_blogger_setup.py`
- `scripts/blogger_api_smoke.py`
- `scripts/publish_v20_pages.py`
- `instalar_windows.bat`
- `iniciar_chrome_blogger.bat`
- `src/`
- `blogger_stores/`
- stores específicos da rede
- `config/`
- `themes/` e `blogger_themes/`
- `local_runner/` v0.8
- `infrastructure/` Cloudflare/ChatGPT sem secrets
- workflows permanentes
- `MANIFEST.json`
- `SHA256SUMS.txt`

## Credenciais intencionalmente ausentes

Devem ser recriadas na máquina/conta nova:
- Blogger OAuth client secret/refresh token;
- Shopee Secret;
- `BLOGGER_RUNNER_TOKEN`;
- Cloudflare `OAUTH_SECRET`;
- login/cookies/perfil do Chrome;
- tokens/conexão do plugin privado da conta antiga do ChatGPT.

A instalação e recriação estão documentadas em `instrucoes.txt`.
