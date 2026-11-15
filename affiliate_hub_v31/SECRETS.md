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

### C1.2 — checagem da API (preparada, execução real PENDENTE)

A captura de tela de 15/11/2026 confirma dois nomes em **Environment secrets** e nenhum segredo em **Environment variables**. **Isso prova somente o cadastro/posicionamento, não a validade dos valores.**

O App Secret anterior foi exposto em uma captura. Antes de qualquer execução autenticada, substituí-lo na Shopee (e sincronizar os outros fluxos que eventualmente compartilhem a credencial). O workflow manual exige a confirmação explícita dessa rotação:

- `.github/workflows/v31_editorial_shopee_api_probe_safe.yml`
- `affiliate_hub_v31/shopee_probe.py`
- Executa **uma** chamada assinada de leitura `productOfferV2` com limite de 1, sem publicar e sem gravar produtos.
- Bloqueado para todas as refs exceto `refs/heads/main`, com input `credential_rotated=true`.
- Não pode ser acionado pelo botão Actions até estar na branch padrão, após a revisão do PR. **Não fazer merge automaticamente.**
- Não imprime valores de secrets, links, conteúdo dos produtos ou detalhes livres da resposta da API.
- Apenas status sanitizado `V31_SHOPEE_API_PASS` confirma que a consulta foi aceita; outros estados exigem análise controlada.

**Proteção adicional no GitHub Environment:** em `Deployment branches and tags`, substituir `No restriction` por regra de branches selecionadas, permitindo inicialmente apenas `main` (quando o workflow for aprovado e integrado). Isso reduz o risco de outro workflow em branch livre acessar os segredos. A regra do workflow é adicional, não substitui essa restrição. Se usar `Required reviewers`, conferir que a conta/nível do repositório suporta a regra; não presumir que self-approval será permitido.

### C1.3 — autenticação real Shopee validada (15/11/2026)

- **Prova concreta:** GitHub Actions [run 43725343531](https://github.com/adelrib27/blogger-automation1/actions/runs/43725343531), job `uma-consulta-sem-publicacao`, status **SUCCESS**.
- Resposta registrada (sem dados sensíveis): `V31_SHOPEE_API_PASS`.
- Escopo: **uma única consulta assinada read-only** `productOfferV2` (`limit: 1`) usando os secrets `V31_EDITORIAL_SHOPEE_APP_ID` e `V31_EDITORIAL_SHOPEE_APP_SECRET` do Environment. Nenhum blog ou WordPress foi alterado.
- Foi utilizado um gatilho temporário de branch para execução controlada; o arquivo `.github/workflows/v31_editorial_shopee_api_probe_once.yml` **foi removido imediatamente após o PASS**. O workflow manual de produção continua não executado.
- Os testes offline do módulo, catálogo e nomenclatura de credenciais seguem independentes. **Não confundir:** autenticação validada NÃO implica conversão de links, ingestão de feeds, persistência cloud ou publicação.
- **Segurança:** não foi comprovado que a chave exposta anteriormente foi rotacionada. Sua rotação continua obrigatória, com sincronização dos outros fluxos que a compartilhem. O GitHub Environment deve ter proteção de branches antes de qualquer etapa LIVE.

**Código de continuidade:** `V31-EDITORIAL-C1-API-REAL-PASS-20261115`.

### C2 — Feeds e R2 (pendentes de cadastro real)

Para processamento dos CSVs **sem computador ligado**, seguir [CHECKPOINT_C2_2026-11-15.md](CHECKPOINT_C2_2026-11-15.md). São necessários os dois Secrets `V31_EDITORIAL_DATAFEED_URL_1` e `V31_EDITORIAL_DATAFEED_URL_2`, duas chaves R2 dedicadas (`V31_EDITORIAL_R2_ACCESS_KEY_ID`, `V31_EDITORIAL_R2_SECRET_ACCESS_KEY`) e duas Variables (`V31_EDITORIAL_R2_ACCOUNT_ID`, `V31_EDITORIAL_R2_BUCKET`). Nenhum desses valores foi cadastrado por esta sessão.

O workflow de importação `v31_editorial_ingest_r2_safe.yml` é manual e exclusivo da `main` revisada, utiliza `concurrency: v31-editorial-catalog-single-writer` e exige `confirm_private_storage=true`. Na PRIMEIRA execução com bucket vazio, informar também `initialize_new_catalog=true`; em execução normal com catálogo existente, manter `false`. Isso impede substituição silenciosa de catálogo histórico quando o ponteiro remoto desaparece.

### Código de continuidade

`V31-EDITORIAL-C1-API-PROBE-20261115-SAFE` — credenciais agora aparecem em Secrets segundo captura, teste automático de autenticação preparado, mas não executado e aguardando rotação da chave e proteção do Environment.
