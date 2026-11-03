# UPDATE DE CHECKPOINT — RUNNER V0.6 APOSENTADO

**Data:** 2026-11-02  
**Projeto:** Blogger Automation — Sistema Mestre V20

## Estado canônico

O **Blogger Local Runner v0.8** permanece como runner operacional validado.

O runner v0.6 foi retirado da cadeia ativa versionada. O checkpoint de 2026-10-30 que registra a v0.6 continua preservado exclusivamente como evidência histórica da evolução do sistema e **não deve ser usado como instrução operacional atual**.

## Evidência ao vivo antes/depois da limpeza

- `health`: `version=0.8`;
- capabilities: `create`, `settings`, `v20`, `provision-new-blog-v20`, `v20-runtime-sync-guard`;
- `audit`: `AUDIT_OK`;
- Chrome oficial/CDP loopback conectado;
- `new_blog_available=true`.

Nenhum conteúdo Blogger foi alterado durante esta manutenção.

## Refatoração da branch de tooling

Branch:

`blogger-safe-ui-provisioning-v0-2`

Commit:

`caf3e8475548e2fa4739e1fff7c45142b4df90cb`

Mensagem:

`Retirar runner v0.6 da cadeia ativa do Local Runner`

Alterações:

1. removido `tools/blogger_safe_automator_v0_2/local_service_v06.py`;
2. removido `tools/blogger_safe_automator_v0_2/browser_resilience_v06.py`;
3. preservada a resiliência útil do seletor `Novo blog...` em `new_blog_selector_resilience.py`, sem identidade de versão antiga;
4. `local_service_v07.py` deixou de herdar/importar `local_service_v06` e passa a usar `local_service_v05` diretamente, instalando a resiliência canônica do seletor;
5. `local_service_v08.py` deixou de acessar `v07.v06.v05` e passa a acessar `v07.v05`;
6. cadeia ativa versionada resultante: `v0.8 -> v0.7 -> v0.5/base`, sem runner v0.6.

## Validação

Antes do commit, a refatoração foi testada localmente em cópia isolada do pacote unificado:

- `py_compile`: PASS;
- busca por referências Python ativas a `local_service_v06`, `browser_resilience_v06`, `v07.v06` e `v06.v05`: nenhuma ocorrência.

Após o commit:

- `local_service_v06.py`: 404 na branch;
- `browser_resilience_v06.py`: 404 na branch;
- `local_service_v08.py`: confirmado usando `v07.v05`;
- check GitHub Actions `validate-runtime`: **SUCCESS**;
- run `41550742420`;
- job `125637408622`.

## Limite operacional ainda não declarado como concluído

O processo v0.8 no PC já estava iniciado antes desta refatoração. A conexão disponível ao ChatGPT não oferece operação arbitrária de filesystem nem restart do serviço local.

Portanto:

- a v0.6 está **aposentada e removida da cadeia ativa versionada**;
- o runtime ao vivo continua sendo **v0.8 saudável**;
- **não declarar ainda** que os arquivos antigos foram fisicamente apagados do disco `C:\Blogger-Automator` sem uma verificação local correspondente;
- no próximo ciclo controlado de sincronização/restart do runner, confirmar que o processo carregado usa a cadeia nova e que nenhum arquivo v0.6 permanece como dependência operacional.

Essa ressalva é fail-closed e evita transformar uma remoção comprovada no GitHub em uma afirmação não comprovada sobre o filesystem local.

## Regra de retomada

Para qualquer operação futura:

1. considerar v0.8 como versão operacional;
2. nunca iniciar `local_service_v06.py`;
3. nunca restaurar `local_service_v06.py` apenas por aparecer em checkpoint histórico ou backup;
4. preservar a lógica útil de resiliência já absorvida pelo módulo neutro atual;
5. se houver conflito entre o checkpoint histórico de 30/10 e este update/estado ao vivo, prevalece o estado ao vivo + v0.8.
