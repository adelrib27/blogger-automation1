# V31 — Incidente de inicialização R28 e auditoria SAFE (13/11/2026)

**Estado:** auditoria documental/LAB; recuperação Windows pendente. Nenhuma alteração em Blogger, Cloudflare, secrets, agendador, temas ou workflows.

## Evidências fornecidas pelo operador

- A tarefa Windows BloggerAutomationV20 retornou código 1 em 13/11/2026 às 11:05.
- Portas locais 8765 (Runner) e 9222 (Chrome CDP) sem listener.
- Autostart: BOOTSTRAP_R28_FAIL_CLOSED Arquivo Mestre V31 divergente; abortando sem iniciar processos.
- Gateway: "Token do runner inválido ou runner indisponível". Esse erro não prova revogação; Runner offline já explica indisponibilidade.
- Atualização local de 13/11 alterou quatro módulos: local_service_v31.py, provision_new_blog_v31.py, install_modelo_v31_adoption.py e v31_handoff_safe.py. Criou backup, sem reinício nem validação E2E.
- O modelo theme.xml.tpl foi previamente confirmado com SHA-256 e99121de968a858315f642217bb4725cb3b3dfe3adeb45834a504063d79fd415.

## Causa ainda não demonstrada

O script R28 do backup de 07/11 verifica cinco **outros** arquivos: local_service_v08.py, apply_universal_v31.py, v31_master_policy.py, v31_master_acceptance.py, v31_master_approved_labs.json. O log não identifica qual divergiu. Não atribuir causalidade à troca dos quatro módulos V31 antes de identificar o hash conflitante e a ação real do agendador.

## Ferramenta exclusivamente de leitura

tools/v31_bootstrap_integrity_audit.py lê o script R28 instalado, extrai os hashes dos cinco arquivos permitidos e compara com as cópias locais. Em caso de estrutura inesperada, retorna BOOTSTRAP_AUDIT_FAIL_CLOSED. Nunca acessa token, rede ou Blogger, nem altera hashes, arquivos ou processos.

Comando Windows, após baixar apenas o arquivo auditor da branch LAB para uma pasta de trabalho fora da instalação:

    $python = 'C:\Blogger-Automator\blogger_safe_automator_v0_3\tools\blogger_safe_automator_v0_2\.venv\Scripts\python.exe'
    & $python .\v31_bootstrap_integrity_audit.py

É necessário verificar separadamente qual script o agendador executa; a auditoria sozinha não prova isso. Não é necessário instalar a branch no Runner.

## Recuperação recomendada

1. Comparar os hashes e a ação da tarefa agendada.
2. Identificar arquivo divergente, origem, backup e alteração concorrente.
3. Após autorização expressa, preparar reconciliação ou rollback guardado com comparação SHA.
4. Validar o autostart, Chrome CDP e health; só então investigar token/gateway.
5. Não desativar fail-closed, atualizar hashes à força ou editar secrets.

## Evolução V31 já existente

Reutilizar a engenharia de v31_master/autoevolution na branch lab/v31-autoevolucao-safe-20261112; não duplicar workflows, memória ou gerador de candidatos. Este PR propõe apenas ferramenta de observabilidade complementar. Nenhuma mudança em produção.

## Regressões

Executar: python -m unittest discover -s tools/tests -p test_v31_bootstrap_integrity_audit.py -v

Testes sintéticos não comprovam recuperação do Runner real.
