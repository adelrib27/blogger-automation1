# V31 Hub Editorial Shopee — Blogger & WordPress

## Escopo canônico (15/11/2026)

Este projeto opera **exclusivamente para blogs Blogger e WordPress**. Pinterest e redes sociais têm projetos separados e **não fazem parte** deste módulo.

Repositório: `adelrib27/blogger-automation1`. A implantação reside em uma branch isolada. Nenhuma automação de produção foi modificada.

### Secrets e variáveis do Hub (centralizado)

**Registro oficial de nomes e instruções:** [SECRETS.md](SECRETS.md)  
**Manifesto legível por máquina:** [credentials_registry.json](credentials_registry.json)  
**Verificação sem revelar valores:** `python -m affiliate_hub_v31.credentials --profile manifest`  
**Workflow manual SAFE:** `.github/workflows/v31_editorial_secret_inventory_safe.yml` (disponível para execução manual após inclusão na branch padrão).

Namespace isolado: `V31_EDITORIAL_...`. Nenhuma credencial real é versionada aqui, e os workflows comerciais existentes permanecem intactos. O cadastro efetivo dos secrets/variables no GitHub Environment `v31-editorial-safe` ainda é obrigatório e não foi executado.

### Objetivo

1. Receber os dois feeds CSV da Shopee em área privada de armazenamento. A contagem histórica relatada é de 100.000 + 10.000 linhas **antes** da deduplicação; esta branch ainda não baixou os arquivos atuais.
2. Importar, normalizar, deduplicar e classificar produtos para revisão editorial antes de publicar.
3. Reutilizar links afiliados já validados por produto/campanha. Para links faltantes, chamar a Shopee Affiliate Open API com autenticação assinada, limites e registro de tentativas.
4. Expor candidatos a adaptadores separados: **Blogger** e **WordPress**, preservando IDs, filtros, HTML comercial e política de cada site.
5. Agendar rotinas de ingestão e publicação na nuvem somente após testes e aprovação do fluxo LIVE.

### Limites de segurança

- Feeds privados, App Secret, tokens, arquivos de catálogo e métricas comerciais não entram no repositório público nem nos logs.
- Github Actions não oferece disco persistente entre execuções: é necessário provisionar backup/estado persistente privado antes de executar de verdade (p.ex. R2 ou banco gerenciado).
- Nunca concluir que URL de produto tem atribuição de afiliado: armazenar somente retorno validado da API ou importação legada verificada.
- Nenhuma integração com Pinterest. Não apagar fluxos Pinterest preexistentes de outros projetos.
- Modo padrão: **SAFE**, sem publicar, sem editar posts, sem ativar schedules e sem emitir links em massa.
- Live Blogger e WordPress exigirão validadores próprios, idempotência, fila de revisão, proteção contra duplicados e opção de rollback.
- Link Shopee pode expirar/mudar; revisão de validade deve preceder publicação.
- Política editorial: não publicar indiscriminadamente produtos não revisados, alegações não confirmadas ou páginas duplicadas.

### O que existe nesta etapa

- `affiliate_hub_v31/catalog.py`: banco SQLite local e importador CSV, deduplicação, revisão básica, cache por campanha, consultas.
- `affiliate_hub_v31/__init__.py`: pacote Python.
- **Testes SAFE:** 14/14 passaram no GitHub Actions (push `8370a2d`, run `43722692312`), sem acesso a APIs reais nem secrets. **Ainda falta:** workflow de ingestão real, esquema real dos dois CSVs, estado persistente remoto, cadastro dos secrets, conversor Open API funcional, adaptadores Blogger/WordPress, agendamento e execução LIVE.

### Próximo marco de validação

`V31-EDITORIAL-C1-20261115-SAFE`

Testes unitários sintéticos **14/14 PASS** em CI após correção de allowlist de encurtadores. Próximo passo: validar o esquema CSV real e os secrets do Environment; depois preparar ingestão em nuvem com persistência privada. Não tratar simulação como implantação concluída.

## Separação operacional

```
Feeds Shopee (privados)
    → catálogo/deduplicação/revisão (privado)
    → links afiliados validados pela Open API (cache privado)
    → seleção editorial e política por site
          ├── adaptador Blogger → SAFE → aprovação LIVE → Blogger
          └── adaptador WordPress → SAFE → aprovação LIVE → WordPress

Pinterest: fora deste projeto.
```
