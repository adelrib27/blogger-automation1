# UPDATE DE CHECKPOINT — LABORATÓRIO + V20 CANÔNICO

**Data:** 2026-10-30

Este arquivo complementa os checkpoints mestres anteriores e deve ser lido junto com `CHECKPOINT_ATUAL.md`.

## 1. Runner local v0.6 validado

O runner local foi atualizado operacionalmente para `local_service_v06.py` e validado pela própria ponte ChatGPT → Cloudflare → VPC → PC:

```json
{"ok":true,"service":"blogger-local-runner","version":"0.6","bind":"loopback"}
```

Arquivos novos na branch `blogger-safe-ui-provisioning-v0-2`:

- `tools/blogger_safe_automator_v0_2/browser_resilience_v06.py`
- `tools/blogger_safe_automator_v0_2/local_service_v06.py`

A v0.6 adiciona retry controlado apenas na descoberta do seletor `Novo blog`, preservando as travas anteriores de criação, Blog ID, endereço e validação pública.

## 2. Blog de laboratório criado para provar a reconstrução do projeto

### Identidade

- Título: `Laboratório Achados V20`
- Blog ID: `4937056944831075547`
- URL: `https://laboratorio-achados-v20-20261030.blogspot.com/`
- Endereço solicitado aceito na primeira tentativa.
- URL pública validada com HTTP 200.

### Configurações essenciais aplicadas e revalidadas

- descrição: aplicada;
- visibilidade para mecanismos de pesquisa: ativa;
- redirecionamento HTTPS: ativo;
- lazy loading de imagens: ativo;
- WebP: ativo;
- descrição de pesquisa: ativa;
- fuso: `(GMT-03:00) Horário Padrão de Brasília – São Paulo`;
- custom robots TXT: `UNCHANGED`;
- custom robots headers: `UNCHANGED`.

## 3. V20 instalado no laboratório

Resultado da tool `adopt_model_v20`:

- status: `BLOGGER_MODELO_V20_ADOPTED`;
- Blog ID confirmado: `4937056944831075547`;
- marker público esperado: `emporio-revisao-visual-20-modelo-final`;
- `existing_posts_policy`: `PRESERVE_ALL`;
- `posts_deleted`: `false`;
- `posts_copied_from_reference`: `false`.

Render local:

`C:\Blogger-Automator\blogger_safe_automator_v0_3\themes\blogger_modelo_v20\rendered\4937056944831075547\theme.xml`

Backup do tema anterior:

`C:\Blogger-Automator\backups\blogger\4937056944831075547\theme-before-modelo-v20-adoption.xml`

## 4. Estado editorial do laboratório

Validação por Blogger API:

- posts LIVE: `0`;
- drafts: `0`;
- páginas institucionais LIVE: `5`.

Páginas criadas:

1. Termos de Uso — ID `4176292188461234078`
2. Política de Privacidade — ID `6327901344218459907`
3. Contato — ID `1568559644741563523`
4. Aviso de Afiliados — ID `6683299981942594865`
5. Sobre — ID `5543285250478725415`

### Achado importante

A operação atual `adopt_model_v20` instala o tema, mas **não cria automaticamente as 5 páginas institucionais**. No laboratório elas foram criadas em etapa separada via `Blogger_Bridge_V2`, usando como fonte operacional as páginas já validadas do Conecta Achados e adaptando o nome do blog.

Portanto, o provisionamento completo de blog novo ainda deve ser aprimorado para incorporar as 5 páginas na mesma automação.

## 5. Promoção do tema V20 canônico

Foi executado localmente:

`tools/blogger_safe_automator_v0_2/promote_validated_model_v20.py --confirm "PROMOTE VALIDATED V20"`

Resultado final:

`BLOGGER_MODELO_V20_CANONICAL_PROMOTED`

### Fonte validada

- Blog fonte: Conecta Achados
- Blog ID: `1719259388907013414`
- Fonte local validada: `themes\blogger_modelo_v20\rendered\1719259388907013414\theme.xml`
- SHA256 validado: `DF6A3B40003FE64889157F60A6C00A1E05D85DC5CF02425C12091E8738D6F21D`

### Template canônico

- Arquivo: `themes\blogger_modelo_v20\theme.xml.tpl`
- SHA256: `D83B0E1F1750739F0801458F985DCBB3721D506140127EC30CB4EAEC2A2AF565`
- XML válido: `true`
- marker V20 presente: `true`
- marker de paleta renderizada no canônico: `false`
- token `__BLOG_TITLE__`: presente
- token `__BLOG_URL__`: presente

### Prova round-trip

O candidato canônico foi renderizado novamente para:

- título: `Conecta Achados`;
- URL: `https://conectaachados.blogspot.com/`;
- paleta: `emerald`.

O resultado reconstruído teve SHA256:

`DF6A3B40003FE64889157F60A6C00A1E05D85DC5CF02425C12091E8738D6F21D`

Ou seja:

`roundtrip_exact_match = true`

### Descoberta importante

O template anterior já possuía exatamente o mesmo SHA256 do candidato promovido:

`D83B0E1F1750739F0801458F985DCBB3721D506140127EC30CB4EAEC2A2AF565`

Portanto, **não houve mudança de bytes no template canônico**. A operação serviu para provar formalmente que o template existente já correspondia à versão validada do tema e para gerar backup antes da promoção.

### Backup criado antes da promoção

`C:\Blogger-Automator\backups\blogger-modelo-v20-canonical\20261030T161301Z\theme.xml.tpl.before`

Round-trip salvo em:

`C:\Blogger-Automator\backups\blogger-modelo-v20-canonical\20261030T161301Z\theme.roundtrip.xml`

## 6. Regra canônica a partir deste ponto

O `TEMA MODELO V20` oficial é o template canônico cujo SHA256 é:

`D83B0E1F1750739F0801458F985DCBB3721D506140127EC30CB4EAEC2A2AF565`

Quando renderizado para Conecta Achados + paleta emerald, ele deve produzir exatamente:

`DF6A3B40003FE64889157F60A6C00A1E05D85DC5CF02425C12091E8738D6F21D`

Qualquer alteração futura no template deve preservar versionamento, backup e nova prova round-trip antes de ser considerada canônica.

## 7. Pendências reais após esta validação

1. Automatizar o start do Chrome oficial com CDP + runner local, eliminando a etapa manual.
2. Incorporar a criação/validação das 5 páginas institucionais ao provisionamento automático de blog novo.
3. Manter o runner v0.6 como versão operacional até nova versão explicitamente validada.
4. Os módulos locais `apply_theme_safe.py` e `backup_theme_safe.py` continuam existentes e validados no PC; continuam sem cópia-fonte versionada no GitHub.
