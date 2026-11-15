# V31 — Reconstrução com acesso de leitura ao Runner Windows e ao plugin

**Estado:** LAB / não instalado no Windows / ferramentas MCP não adicionadas ao plugin atual.

## Diagnóstico de arquitetura

- Repositório conectado: `adelrib27/blogger-automation1`; branch default `main`, em evolução por workflows autônomos.
- Runtime Windows conectado: Blogger Local Runner `0.9-v31-r52-candidate`, porta loopback/autenticação já implementadas. O plugin não possui ferramentas genéricas de leitura de arquivos.
- Plugin privado Blogger Local Runner: release `1.0.0`; expõe 8 ações: `health`, `audit`, `preflight_blog`, `create_blog`, `preflight_settings`, `configure_settings`, `adopt_model_v31_exact`, `provision_new_blog_v31`.
- Runner anuncia `resume-provision-new-blog-v31`, mas o plugin não expõe essa operação. **Não executar resume** no checkpoint R52 de criação não validada.
- O manifesto do plugin disponível à edição contém principalmente metadados da App. A exposição de novas ferramentas depende também da implementação/registro do servidor MCP associado. Não declarar plugin atualizado ao mudar só o manifesto.
- ZIP Windows anterior incluiu 26 scripts, não a árvore completa; fontes indisponíveis e configurações privadas não devem ser presumidas.

## Proposta implementada nesta branch

`lab_v31_runner_inspection/runner_source_inspector_v31.py`: inventário de 34 nomes de módulos Python permitidos, tamanho e SHA-256; leitura de **um** arquivo por vez condicionada a nome exato, digest esperado, confirmação literal e varredura conservadora de conteúdo sensível. Rejeita arquivos acima de 128 KiB, symlinks, traversal, código inválido e possíveis credenciais. Nenhuma função de escrita ou execução remota.

`lab_v31_runner_inspection/runner_source_http_v31.py`: adaptador somente leitura para duas rotas HTTP, reutilizando `_require_auth` e `_send` do Handler atual. As rotas ficam **desabilitadas por padrão**. Mesmo com o adaptador instalado, só responderiam se `BLOGGER_V31_SOURCE_INSPECTION_ENABLED=true` for explicitamente configurado. Nenhum serviço novo em rede ou porta adicional.

| Futuro tool MCP | HTTP | Escopo |
|---|---|---|
| `source_manifest_v31()` | GET `/v1/source-manifest-v31` | Lista nomes permitidos, tamanhos e hashes, sem conteúdo |
| `read_source_v31(name, expected_sha256, confirm)` | POST `/v1/source-read-v31` | Lê somente um `.py` autorizado, confirmação `READ V31 SOURCE` |

**NÃO** criar `run_shell`, `read_any_file`, `execute_python`, `list_cookies`, `read_credentials` ou acesso irrestrito ao PC. Esses endpoints não inspecionam qualquer pasta Windows: a expansão do escopo deve ser revisada caso a caso.

## Ponto de integração futuro (não aplicar automaticamente)

Após conferir hashes e diff da instalação Windows, copiar os dois módulos aprovados ao diretório real de `local_service_v31.py`. Adicionar import `runner_source_http_v31 as source_http` e, **no começo** dos métodos existentes:

```python
# dentro de Handler.do_GET, antes das rotas existentes
if source_http.handle_get(self):
    return
# dentro de Handler.do_POST, antes das rotas existentes
if source_http.handle_post(self):
    return
```

Isto é uma instrução de diff mínimo, **não** um arquivo completo de substituição. Preservar as rotas originais, locks, autenticação, confirmações, CDP e políticas V31.

O plugin requer atualização coordenada do **servidor MCP original**, mantendo as oito ferramentas existentes e adicionando apenas as duas ações READ_ONLY. A versão App 1.0.0 não prova sincronização. As ferramentas novas precisam ser descobertas/inspecionadas ao vivo após implantação e testar negativas/positivas.

## Testes e gates

- Offline: 18 testes unitários da ponte e adaptador PASS.
- Contra o ZIP Windows coletado: 26/26 fontes permitidas puderam ser lidas em teste com hashes correspondentes. O ZIP tem conteúdo sanitizado; não comprova todos os arquivos ao vivo.
- **Não executado:** integração real no serviço Windows, chamadas de endpoints reais, atualização do MCP, restart, ou publicação Blogger. Nenhuma implementação LIVE validada.
- Gates antes de produção: hash atual do Runner, backup, revisão do código MCP e segredo de autenticação, diff minimizado, regressões originais, bloqueios de permissões, teste de regressão via Runner sem Blogger writes, confirmação de não exposição de secrets, plano de rollback.

## Orquestração futura da reconstrução

1. Ler os scripts e metadados do Runner com o acesso controlado, e comparar hashes dos módulos com a branch GitHub correta.
2. Catalogar herança HTTP `local_service_v05...v31`, fluxo CDP, checkpoints, tema, configuração SEO, arquivos auxiliares.
3. Resolver em LAB as incompatibilidades já vistas: slug alternativo vs alvo exato; primeira aba Blogger vs aba ativa; estados da caixa de seleção; falhas na etapa Settings.
4. Criar regressões que falham antes da correção, implementar somente os diffs necessários e testar em SAFE.
5. Sincronizar o registro de ferramentas do plugin com o contrato HTTP **sem** abrir operações de escrita arbitrárias.
6. Só aplicar no Windows/produção após autorização, com backup, verificação ao vivo e rollback.

**Atenção:** scanners não garantem remover todo segredo de um script. Mesmo com arquivos allowlistados, revisar os fontes reais antes de permitir uma nova ferramenta remota. Nenhuma branch LAB equivale a sistema implantado.
