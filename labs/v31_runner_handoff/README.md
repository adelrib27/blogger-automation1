# V31 Runner — retomada segura de blog novo (LAB / NÃO INSTALAR DIRETAMENTE)

**Data:** 2026-11-12 · **Escopo:** Blog ID `2228849984262880811`, Ar-Condicionado sem Dúvidas.  
**Estado:** patch candidato separado do Runner Windows ativo; não é um endpoint operacional nem autorização para publicação.

## Problema confirmado

O fluxo de provisionamento V31 criou o blog e interrompeu-se antes de completar SEO + Tema V31. SEO foi corrigido separadamente; o instalador de tema ainda exige `SETTINGS_VALIDATED_AWAIT_THEME` no checkpoint de criação. Configurar SEO fora do provisionamento não restaura automaticamente este estado.

**A ordem SEO → Tema é correta.** O defeito está na retomada após a interrupção. Os `universal_v31_allowed_blog_ids` do `health` são de operações universais, não substituem o checkpoint de autorização exata do tema.

## Implementação candidata

O módulo `v31_handoff_safe.py` implementa `resume_exact` com entrada explícita e uma única tentativa:
- confirma ID, título e URL do blog, checkpoint de criação, status parcial e histórico;
- rejeita ausência de checkpoint, destino divergente, tema já iniciado, latch, resultado ou preflight de tema existente;
- valida HTTP público e nome antes de mexer no SEO;
- registra início da retomada e nunca tenta novamente automaticamente;
- reconfigura e valida SEO, em seguida grava autorização de tema específica do checkpoint;
- delega **uma única vez** ao instalador V31 existente, exigindo validação pública dele;
- não recria blog, não edita listas históricas, não edita Blogger diretamente.

**Importante:** este módulo não cria o endpoint `resume-provision-v31` por si. O pacote de handoff `BLOGGER_V31_HANDOFF_SEO_TEMA_RECUPERACAO_SAFE_2026-11-12.zip` contém os três diffs para `local_service_v31.py`, `provision_new_blog_v31.py` e `install_modelo_v31_adoption.py` e **29 testes offline**. Esses diffs foram produzidos a partir de backups de 07/11 e 10/11, **não** do filesystem Windows atual. Devem ser reconciliados antes de uso.

## Plano de implantação segura

1. Verificar arquivos ativos, processos e checkpoints no Windows; fazer backup atual. Não utilizar uma cópia antiga do Runner para sobrescrever arquivos mais recentes.
2. Examinar o checkpoint `logs/provisioning/v31/ar-condicionado-sem-duvidas.json`. Exigir Blog ID `2228849984262880811`, título/URL corretos, `created=true`, `PROVISION_V31_PARTIAL_STOP`, `theme_install_started=false`.
3. Verificar que não existem latch/result/preflight de upload de tema e que o HTML público ainda não possui Tema V31. Se algum indicador existir, parar para inspeção humana.
4. Reconcilie e aplique diffs **somente no Runner LAB local**, nunca em produção por cópia cega. Executar 29 regressões originais, smoke tests e validar contrato do endpoint.
5. Só depois de autorizar a retomada exata, executar a operação `RESUME BLOG V31` uma vez, validar Tema V31 publicamente e checkpoint. Não criar o blog de novo.
6. Publicar páginas institucionais, conteúdo e Loja por contratos próprios, em etapas separadas, após aprovação dos gates.

## Separação de projetos

- Branch de trabalho: `lab/v31-runner-resume-exact-safe-20261112`.
- Não altera `main`, `lab/v31-autoevolucao-safe-20261112`, outras branches do Work nem blogs existentes.
- Sem permissões para escrever arquivos no Windows ou fazer restart do Runner nesta conexão. Portanto instalação LIVE não confirmada.
- Não apagar checkpoints/logs/autorizações legadas: eliminar seu uso como autorização **de novos blogs**, não o histórico necessário a auditoria e rollback.

## Critérios de aceitação

- Testes sintáticos e unidade offline PASS.
- Destino errado, tema pré-existente, checkpoint inválido, SEO falho ou repetição de tentativa ⇒ fail-closed.
- Comparação com código Windows ativo e backup ⇒ PASS.
- Uma execução LIVE controlada ⇒ Tema V31 e páginas verificadas por Blogger/HTTP, sem duplicação.
