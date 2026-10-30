# CHECKPOINT ATUAL — BLOGGER AUTOMATION

**Última atualização:** 2026-10-30  
**Projeto:** Blogger Automation sem ChatGPT Work

## LEIA PRIMEIRO

Antes de qualquer operação Blogger neste projeto, leia integralmente:

1. `CHECKPOINT_UPDATE_2026-10-30_LAB_CANONICAL_V20.md`
2. `CHECKPOINT_BLOGGER_AUTOMATION_MASTER_2026-10-30.md`
3. `CHECKPOINT_BLOGGER_AUTOMATION_MASTER_2026-10-30.json`
4. `infrastructure/README.md`
5. `BACKUP_MANIFEST_BLOGGER_AUTOMATION_2026-10-30.json`

Esses arquivos são a fonte persistente de continuidade entre conversas. O arquivo `CHECKPOINT_UPDATE_2026-10-30_LAB_CANONICAL_V20.md` contém as validações mais recentes e prevalece quando houver diferença em relação aos checkpoints anteriores.

## Estado mais recente validado

- Runner operacional atual: **v0.6** (`local_service_v06.py`).
- O health v0.6 foi confirmado pela própria ponte ChatGPT → Cloudflare → VPC → PC.
- Blog de teste criado: **Laboratório Achados V20**.
- Blog ID: `4937056944831075547`.
- URL: `https://laboratorio-achados-v20-20261030.blogspot.com/`.
- Configurações essenciais/SEO aplicadas e revalidadas; robots personalizados permaneceram intocados.
- V20 instalado no laboratório.
- Laboratório validado com **0 posts LIVE, 0 drafts e 5 páginas institucionais LIVE**.
- Achado: `adopt_model_v20` aplica o tema, mas ainda não cria automaticamente as 5 páginas; isso deve ser incorporado ao provisionamento completo de blog novo.

## TEMA MODELO V20 canônico — promovido e provado

Fonte final validada do Conecta Achados:

`DF6A3B40003FE64889157F60A6C00A1E05D85DC5CF02425C12091E8738D6F21D`

Template canônico oficial:

`themes/blogger_modelo_v20/theme.xml.tpl`

SHA256 do template canônico:

`D83B0E1F1750739F0801458F985DCBB3721D506140127EC30CB4EAEC2A2AF565`

A promoção passou com:

- `BLOGGER_MODELO_V20_CANONICAL_PROMOTED`
- `roundtrip_exact_match = true`
- XML válido
- marker V20 presente
- `__BLOG_TITLE__` presente
- `__BLOG_URL__` presente
- identidade/paleta renderizada ausente do template canônico

Ao renderizar o template canônico para **Conecta Achados + emerald**, o resultado volta exatamente ao SHA256 validado `DF6A3B...`.

Importante: o template anterior já tinha o mesmo SHA256 `D83B0E...`; portanto a promoção não mudou seus bytes. Ela formalizou e provou que o template existente já era exatamente a fonte canônica correspondente ao tema validado, além de gerar backup antes da promoção.

Backup da promoção:

`C:\Blogger-Automator\backups\blogger-modelo-v20-canonical\20261030T161301Z\theme.xml.tpl.before`

## Backups de infraestrutura anexos

### Gateway Cloudflare

`infrastructure/cloudflare/blogger-local-runner-gateway/`

- `worker.js` — espelho normalizado do Worker de produção v7.
- `worker-metadata.json` — versão, ETag, bindings e rotas sem valores de secrets.

### Plugin privado ChatGPT

`infrastructure/chatgpt/blogger-local-runner/`

- `.app.json`
- `plugin.json`
- `plugin-metadata.json`

### Gap local explicitamente documentado

`apply_theme_safe.py` e `backup_theme_safe.py` foram validados em execução no PC, mas seus bytes-fonte não estão no GitHub. Eles não impedem o funcionamento atual: o robô local já os utilizou com sucesso. Preservar a cópia local.

## IDs que nunca podem ser confundidos

- **Conecta Achados** — Blog ID `1719259388907013414` — `https://conectaachados.blogspot.com/`
- **Laboratório Achados V20** — Blog ID `4937056944831075547` — `https://laboratorio-achados-v20-20261030.blogspot.com/`
- **Achados para Casa** — Blog ID `1426630233929943394` — NÃO usar quando o alvo for Conecta Achados.

## Estado principal validado do Conecta Achados

- TEMA MODELO V20 instalado e publicamente validado.
- Paleta: `emerald` (`#0F8A5F`, `#F2FBF7`, `#12372A`).
- Marker V20: `emporio-revisao-visual-20-modelo-final`.
- 11 posts LIVE.
- 5 páginas institucionais LIVE.
- Todos os 11 posts estão no padrão editorial longo.
- CTA Shopee obrigatório após o segundo parágrafo + segundo CTA mais abaixo.
- Shopee AppID canônico fornecido pelo proprietário: `18352820579`.
- `SHOPEE_SECRET` e demais Secrets NÃO ficam neste repositório; somente os nomes dos bindings estão documentados.
- Workflow padrão do Conecta cria RASCUNHO (`CONECTA_PUBLISH_MODE=draft`).
- Automação atual: `conecta_achados/src/automation_rich_cta.py`.
- Workflow: `.github/workflows/conecta_achados_shopee.yml`.

## Automação do Blogger sem Work

- Conteúdo: `Blogger_Bridge_V2`.
- Criação/configuração/tema via painel: `Blogger Local Runner` no PC + Chrome oficial/CDP.
- Runner local: `127.0.0.1:8765`.
- Chrome CDP: `127.0.0.1:9222`.
- Gateway: Cloudflare Worker `blogger-local-runner-gateway`.
- Produção do gateway no snapshot: versão 7, version ID `0258427f-fb22-4aa8-afae-b1fe8c83c5c9`.
- Branch do automador: `blogger-safe-ui-provisioning-v0-2`.

## Pendências reais agora

1. Fazer Chrome oficial com CDP + runner subirem automaticamente, sem comando manual.
2. Incorporar a criação e validação das 5 páginas institucionais ao provisionamento automático de blog novo.
3. Manter v0.6 como runner operacional até nova versão explicitamente validada.

## Regras essenciais

- Confirmar Blog ID antes de escrever.
- Backup antes de aplicar tema.
- Arquivo de tema para upload deve se chamar exatamente `theme.xml`.
- Nunca copiar posts do blog de referência `Guia de Achados & Ofertas`.
- Blog novo termina o provisionamento com zero posts.
- Adoção V20 em blog existente preserva posts/páginas.
- Custom robots não são tocados por padrão.
- Não inventar especificações de produtos.
- Não publicar produto Shopee já existente em `state.json`.
- Não depender de ChatGPT Work.
- Não declarar sucesso sem validação concreta.

## Instrução para futura conversa

Se este arquivo for encontrado, NÃO recomece o diagnóstico do zero. Leia primeiro `CHECKPOINT_UPDATE_2026-10-30_LAB_CANONICAL_V20.md`, depois os checkpoints mestre. Confirme o estado vivo e continue a partir deles. Se houver divergência entre checkpoint e sistema vivo, valide a divergência e atualize o checkpoint depois.
