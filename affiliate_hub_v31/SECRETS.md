# V31 Hub Editorial Shopee — Cadastro e identificação dos Secrets

**Escopo exclusivo:** Blogger e WordPress. **Não inclui Pinterest.**

**Fonte de verdade dos NOMES:** [`credentials_registry.json`](credentials_registry.json).  
**Validador (somente presença):** `python -m affiliate_hub_v31.credentials --profile manifest`.  
**Repositório:** `adelrib27/blogger-automation1` — PR draft #52, sem alterar a produção.

## Local central no GitHub

Criar/configurar o **Environment** `v31-editorial-safe` em:

`GitHub → blogger-automation1 → Settings → Environments → New environment`

Cadastrar dentro desse Environment os secrets e variables descritos abaixo. O Environment isola as referências dos workflows antigos, **mas não substitui controles de permissão e revisão de código**. Recomenda-se restringir branches aceitas e habilitar aprovação manual nos ambientes LIVE. **NÃO criar ambiente LIVE nem autorizar publicação neste marco.**

> O GitHub não permite recuperar o valor de um Secret depois de salvo. Este projeto não tem acesso aos valores atuais, não testa sua validade na API e não criou valores de segredos reais.

| Nome EXATO | GitHub | Grupo | Função |
| --- | --- | --- | --- |
| `V31_EDITORIAL_SHOPEE_APP_ID` | Environment **secret** | shopee | Identificador do App da Shopee Affiliate Open API |
| `V31_EDITORIAL_SHOPEE_APP_SECRET` | Environment **secret** | shopee | Chave de assinatura da Shopee |
| `V31_EDITORIAL_DATAFEED_URL_1` | Environment **secret** | feeds | URL privada do primeiro CSV |
| `V31_EDITORIAL_DATAFEED_URL_2` | Environment **secret** | feeds | URL privada do segundo CSV |
| `V31_EDITORIAL_R2_ACCESS_KEY_ID` | Environment **secret** | storage | Chave R2 S3 compatível, limitada ao bucket do hub |
| `V31_EDITORIAL_R2_SECRET_ACCESS_KEY` | Environment **secret** | storage | Segredo R2 S3 compatível |
| `V31_EDITORIAL_R2_ACCOUNT_ID` | Environment **variable** | storage | Conta Cloudflare (não é segredo) |
| `V31_EDITORIAL_R2_BUCKET` | Environment **variable** | storage | Bucket privado, EXCLUSIVO deste hub |

**Nunca salvar os valores** em README, JSON, `.env` versionado, issues, Pull Requests, logs, mensagens ou anexos. Os dois links de download contêm identificadores de acesso e devem ser tratados como segredos. Se já foram publicados em um ambiente aberto, solicitar/regerar links quando possível.

### Compatibilidade com os blogs existentes

Alguns workflows existentes usam `SHOPEE_APP_ID` + `SHOPEE_SECRET`; outros usam `BLOGGER_CLIENT_ID`, `BLOGGER_CLIENT_SECRET`, `BLOGGER_REFRESH_TOKEN` e `WORDPRESS_USERNAME` + `WORDPRESS_APP_PASSWORD`.

**Não renomear, apagar nem substituir** essas credenciais antigas. O novo namespace `V31_EDITORIAL_...` identifica apenas este hub. Ele **não significa que a Shopee forneceu um novo App ID/Secret**: caso seja necessário reutilizar as mesmas credenciais, a replicação segura deverá ser feita pelo proprietário no GitHub, com plano de rotação e sem expor valores ao código. Quando possível, obter credenciais com escopo próprio para o hub.

Na futura integração de cada blog, documentar em um inventário próprio: plataforma, site/Blog ID, identificador do adaptador, Environment de execução, segredo de autenticação e responsável. Preferir **segredos de publicação por blog/ambiente**, separando SAFE (consulta, sem escrita) de LIVE (escrita, aprovação humana), e não compartilhar um usuário WordPress com todos os sites sem necessidade.

**Outros diretórios/projetos no mesmo repositório** poderão consultar este manifesto e referenciar as mesmas credenciais *apenas* quando seu workflow selecionar o Environment `v31-editorial-safe` e tiver autorização. **Outros repositórios GitHub não herdam Environment Secrets**; devem receber acesso explicitamente por GitHub Organization Secrets restritos a repositórios autorizados ou por um gerenciador de segredos externo. **Nenhum workflow de publicação recebe secrets do hub automaticamente.**

### Como verificar após cadastro (sem expor conteúdo)

1. Adicionar os seis **secrets** e duas **variables** no Environment `v31-editorial-safe`.
2. Após o workflow `.github/workflows/v31_editorial_secret_inventory_safe.yml` existir na branch padrão, abrir **Actions → V31 Editorial - Inventario de Secrets SAFE → Run workflow**.
3. Escolher `manifest` (estrutura), `shopee`, `feeds`, `storage` ou `all`. O diagnóstico informa somente **PRESENTE/AUSENTE** e nunca imprime os valores.
4. Resultado `READY` **não comprova autenticidade**, permissão na Shopee, validade dos links ou acesso R2. Essas provas dependerão de verificações SAFE específicas e com limites.

**Importante:** o workflow de inspeção foi criado em uma branch de PR draft. Em regra, o botão manual do GitHub Actions só fica disponível quando o arquivo existir na branch padrão. Não fazer merge somente para executar esse diagnóstico; concluir CI e revisão primeiro.

### Exemplo de referência por outros workflows autorizados

```yaml
jobs:
  consulta-editorial:
    runs-on: ubuntu-latest
    environment: v31-editorial-safe
    permissions:
      contents: read
    steps:
      - name: Exemplo de nomes (não imprime valores)
        env:
          SHOPEE_APP_ID: ${{ secrets.V31_EDITORIAL_SHOPEE_APP_ID }}
          SHOPEE_SECRET: ${{ secrets.V31_EDITORIAL_SHOPEE_APP_SECRET }}
          CATALOG_BUCKET: ${{ vars.V31_EDITORIAL_R2_BUCKET }}
        run: |
          test -n "$SHOPEE_APP_ID"
          test -n "$SHOPEE_SECRET"
          test -n "$CATALOG_BUCKET"
```

Esse exemplo não foi conectado a workflows comerciais existentes. **Não presumir que um nome cadastrado corresponde a uma credencial válida ou que outros projetos tenham acesso.**

### Código de continuidade

`V31-EDITORIAL-C1-SECRETS-20261115-SAFE` — manifesto e verificador criados, valores reais pendentes do proprietário, sem publicação e sem Pinterest.
