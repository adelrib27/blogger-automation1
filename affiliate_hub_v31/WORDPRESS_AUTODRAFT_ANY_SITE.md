# V31 C60 — WordPress universal, rascunhos por pedido real (não só três sites)

O V31 deve aceitar QUALQUER blog WordPress registrado em `site_routes.json` ou `sites.d/<site_key>.json`, com rota real `platform=wordpress`, domínio HTTPS, campanha Shopee exclusiva e `publish_enabled=false`.

## Solicitação/autorização

O proprietário indica nome/tema/plataforma/quantidade. Após existir o WordPress REAL, criar `site_requests.d/<site_key>.json` no esquema que o V31 já usa:
```json
{"site_key":"wordpress_site_real","topic":"assunto solicitado","platform":"wordpress","articles":null,"enabled":true}
```

**Este é um EXEMPLO, não uma solicitação real nem um site já cadastrado.** Não adicionar a pasta sem site real do usuário. Desde a C61, `articles:null` significa **rascunhos contínuos, sem limite total**; `articles` inteiro entre 1 e 24 continua disponível para pedidos com quantidade finita. Cada execução cria no máximo **um novo rascunho**, com anti-duplicação por identidade do produto e pelo prefixo `v31-<hash-da-rota>-`. Isso não substitui nem sobrescreve os artigos legados de qualquer WordPress já existente. Publicação LIVE exige autorização e fluxo separados.

## Credenciais WordPress (separadas por site)

O GitHub Actions deve ter em segredo `V31_WORDPRESS_SITE_CREDENTIALS_JSON` um objeto JSON privado:
```json
{
 "wordpress_site_real": {
   "username": "usuario-editor-da-instalacao",
   "application_password": "SENHA-DE-APLICATIVO-CRIADA-NO-WORDPRESS"
 }
}
```

**Não** colocar credenciais no repo, em arquivos checkpoint, logs ou no chat. Essa estrutura é ilustrativa, sem segredos reais. As credenciais da ferramenta WordPress conectada no ChatGPT **não são automaticamente transferidas** para o GitHub Actions. Cada site novo deve ter credenciais realmente autorizadas antes de habilitar criação. O script só acessa a identidade HTTPS de `sites()`, nunca um domínio passado livremente.

## Fluxo técnico automático

1. Ler apenas pedidos `enabled=true` e rotas registradas, sem nichos fixados em Python.
2. Restaurar R2, verificar catálogo e selecionar SKU aprovado por tema/site; exige link afiliado convertido para a campanha EXATA e foto original Shopee.
3. Conferir postagens WordPress por REST; links internos só de posts publicados **no mesmo host**, bloquear repetição por link/slug/SKU e limitar totais pelo prefixo exclusivo de autoria V31.
4. Criar texto novo (Workers AI suportado JSON), montar HTML escapado com foto do próprio produto, link patrocinado na palavra-chave, CTA e disclosure, links internos se houver posts prévios. Sem posts antigos, primeiro artigo pode legitimamente ter 0 links internos.
5. Reconsultar o histórico para evitar concorrência, escrever WordPress REST com **status: draft** e validar novamente por GET status/ID/slug/conteúdo. Nunca publicar LIVE, alterar posts legados nem converter Shopee nesse escritor.
6. Se faltar pedido, foto, aprovação, link, credencial, identidade ou resposta confirmada, **falha fechada** sem publicação.

## Agendamento seguro e controles

- `.github/workflows/v31_universal_wordpress_autodraft_daily.yml`: cron 09:41 Recife. **C65:** quando existe pedido real `enabled:true`, o cron normal pode criar **somente 1 DRAFT por execução**; a variável GitHub `V31_UNIVERSAL_WORDPRESS_AUTODRAFT_ENABLED=false` pausa o agendamento em modo prévia. Independentemente dessa variável, sem pedido real, identidade, SKU/afiliado e credenciais corretas, a publicação não ocorre. `workflow_dispatch` continua exigindo `execute_draft=true`. O fluxo LIVE é separado e exige aprovação por post.
- Rascunho é etapa de revisão, não publicação automática. A aprovação e a publicação futura exigem gate/publisher específico, identidade WordPress e autorização apropriada.
- O sistema continua universal para Blogger pelo C55 e WordPress pelo C60, mas o cron WordPress **não pode provar uma nova publicação/draft REAL em site sem pedido e credencial**, e isso deve constar no checkpoint até existir essa demanda.
- Para testar sem alterar blog, usar `--site-key wordpress_casa_decoracao --topic "decoração"` (é preview, nunca autorização para novo artigo) e verificar JSON agregado com 0 posts.

**Nunca afirmar que o primeiro cron futuro já ocorreu só porque está presente em main.** 

## C65 — piloto WordPress Casa real, sem antecipar outros blogs

- O piloto já existente `wordpress_casa_decoracao` recebeu o pedido persistente `site_requests.d/wordpress_casa_decoracao.json` com assunto correspondente à sua rota cadastrada (`vaso decorativo`) e `articles:null`, sem teto total. O R2 real mostrou 12 candidatos aprovados para o tema, com 1 link da campanha em cache e 11 aguardando conversão, antes de verificar duplicação contra todo o histórico WordPress. Isso não aprova produtos sob REVIEW.
- O cron V31 WordPress usa prioritariamente o segredo universal `V31_WORDPRESS_SITE_CREDENTIALS_JSON`. Somente para o Casa já autenticado pela C62, existe ponte das credenciais **já presentes** no GitHub Environment `CASA_WORDPRESS_USERNAME`/`CASA_WORDPRESS_APP_PASSWORD`; nenhum outro WordPress herda esse login.
- `V31_UNIVERSAL_WORDPRESS_AUTODRAFT_ENABLED=false` é o botão de pausa de criação; o modo padrão permite DRAFT apenas para pedidos habilitados. Não usar essa variável para autorização de LIVE.
- O canário de cron C65 usa horário extra separado e modo DRY_RUN, não deve criar rascunhos; deve ser removido após o teste.
