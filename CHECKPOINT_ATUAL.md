# CHECKPOINT ATUAL — BLOGGER AUTOMATION

**Última atualização:** 2026-10-30  
**Projeto:** Blogger Automation sem ChatGPT Work

## LEIA PRIMEIRO

Antes de qualquer operação Blogger neste projeto, leia integralmente:

1. `CHECKPOINT_BLOGGER_AUTOMATION_MASTER_2026-10-30.md`
2. `CHECKPOINT_BLOGGER_AUTOMATION_MASTER_2026-10-30.json`
3. `infrastructure/README.md`
4. `BACKUP_MANIFEST_BLOGGER_AUTOMATION_2026-10-30.json`

Esses arquivos são a fonte persistente de continuidade entre conversas.

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

`apply_theme_safe.py` e `backup_theme_safe.py` foram validados em execução no PC, mas seus bytes-fonte não estão no GitHub e não puderam ser lidos pela conexão atual. Preservar a cópia local. Ver `infrastructure/README.md` e o manifesto de backup.

## IDs que nunca podem ser confundidos

- **Conecta Achados** — Blog ID `1719259388907013414` — `https://conectaachados.blogspot.com/`
- **Achados para Casa** — Blog ID `1426630233929943394` — NÃO usar quando o alvo for Conecta Achados.

## Estado principal validado

- Conecta Achados: TEMA MODELO V20 instalado e publicamente validado.
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
- HEAD validado da branch: `6420a44e43d411d2d3837363f7564c30f4bae4a1`.

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

Se este arquivo for encontrado, NÃO recomece o diagnóstico do zero. Carregue os dois checkpoints mestre, o mapa de infraestrutura e o manifesto do backup, confirme o estado vivo e continue a partir deles. Se houver divergência entre o checkpoint e o sistema vivo, valide a divergência e atualize o checkpoint depois.
