# Instruções de engenharia para agentes — Blogger Automation V31

> Escopo: **branch LAB `lab/v31-autoevolucao-safe-20261112`**. Este arquivo orienta agentes que o leem; NÃO altera os pesos de um modelo e NÃO garante que conversas externas leiam automaticamente o conteúdo.

## Prioridade de confiança

1. Estado ao vivo validado na execução (Blogger/GitHub/Runner/Cloudflare).
2. Código V31 validado e contratos de teste do repositório correto.
3. Última evidência cumulativa em `v31_master/autoevolution/knowledge/state.json` e relatórios em `v31_master/autoevolution/reports/`.
4. Checkpoints/backup recentes.
5. Histórico antigo apenas como contexto.

Nunca substituir código V31 funcional por precedente legado sem comparar implementação e testes.

## Ciclo de autoevolução por estágio

1. **OBSERVE:** identificar repositório, blog, branch, workflow, página/post e estado; ler resultados e métricas somente no repositório do projeto. Verificar produção ao vivo antes de mudanças.
2. **CLASSIFY:** classificar falhas por camada sem inventar causa raiz. Em GraphQL `10000`, não concluir estoque zero nem ausência comercial definitiva.
3. **LEARN:** anexar evidências sanitizadas e deduplicadas na memória técnica local ao repositório. Logs brutos, credenciais, IDs secretos e respostas HTTP sensíveis não entram na memória.
4. **HYPOTHESIZE:** gerar hipótese técnica e proposta de experimento com critérios de sucesso e rollback.
5. **SAFE:** criar branch LAB isolada; nunca alterar tema, páginas, workflow ou blog produtivo por inferência. Editar somente depois de ler o arquivo real e comparar o SHA.
6. **VERIFY:** executar testes do componente e todas as regressões V31 relevantes. Falha bloqueia promoção. Validar visual, API readback e HTTP público quando pertinente.
7. **REVIEW:** produzir PR de revisão para mudanças funcionais e explicar diffs, riscos e evidências. Nunca auto-merge para `main` nem LIVE sem autorização explícita.
8. **PROMOTE:** apenas após aprovação, aplicação controlada por blog com snapshot/backup, diff de região gerenciada, Blogger/WordPress readback, QA público, métricas e rollback.
9. **REPEAT:** resultados da nova etapa alimentam o próximo ciclo. Aprimorar regras e testes conforme evidências, não por tentativa aleatória.

## Contratos inegociáveis

- `productOfferV2`: ausência na pesquisa, campo inexistente, erro `10000`, HTTP inválido ou resposta parcial = **UNKNOWN** para estoque; nenhuma rotação por suposto esgotamento.
- Estoque `CONFIRMED_OUT_OF_STOCK` exige fonte autorizada de inventário e verificações independentes. Esta fonte **ainda não foi homologada**; não simular como LIVE.
- Comissão afiliada: positiva e verificável para a conta, **sem percentual mínimo**, sem comissão extra obrigatória; não somar percentuais sem contrato API.
- Rotação: não trocar itens apenas para simular novidade; manter itens relevantes e preservar o catálogo bom se API/filtros falharem.
- Blog/URL/Page/Post ID, tema, arquivos de estado, escopo de credenciais e workflow são exclusivos do projeto. Não compartilhar tokens nem cotas supostamente independentes com a mesma aplicação Shopee.
- Os guardas de `r57_store_policy.py` e as regressões de Loja V31 devem permanecer aprovados.
- Nem o modelo de IA nem este workflow têm autorização geral para alterar produção. O observador escreve somente relatórios e memória após os testes. O workflow de candidatos pode criar branches `lab/jarvis-candidate-*` e PRs rascunho para LAB, após baseline, regressão vermelha e suíte verde em sandbox. Não pode promover ou editar seus próprios guardas. Resultados sanitizados ficam em `v31_master/autoevolution/experiments/`.

## Motor piloto instalado e evidências

- Coletor: `v31_master/autoevolution/engine.py`; usa somente metadados GitHub Actions, sem baixar logs ou executar texto não confiável.
- Memória cumulativa deduplicada: `v31_master/autoevolution/knowledge.py`.
- Workflow: `.github/workflows/v31_lab_autoevolucao_safe.yml`, disparado automaticamente em push na branch LAB, com testes antes de gravar evidência.
- Nenhum autopatch do código da Loja, nenhuma escrita Blogger, nenhum merge ou promoção de produção.
- Como o GitHub só garante agendamentos `schedule` a partir do branch default, **esta branch LAB opera por eventos de push**, não como cron global contínuo.
- Histórico limitado: 50.000 observações de tentativas por estado, com alerta aos 80%. Ao atingir o limite, parar e arquivar/revalidar, nunca descartar silenciosamente.

## Protocolo para um novo blog em repositório próprio

1. Criar/identificar repositório do blog, conexão de publicação, identidade visual, estado de Loja, conta OAuth e secrets próprios **com autorização**.
2. Replicar a engenharia (engine, knowledge, testes e workflow) alterando allowlist de repositório e branch; não copiar IDs, nomes, URLs, secrets ou estado cumulativo de outro blog.
3. Iniciar em LAB com `contents:read` até passar a suíte e comprovar a autorização de gravação apenas de relatórios; depois habilitar escrita apenas de evidência no LAB.
4. Revisar sinais e relatórios daquele repositório, não de outro. A aplicação Shopee compartilhada permanece sujeita à mesma cota.
5. Usar PRs revisáveis para atualizar código da Loja; habilitar LIVE só após testes próprios daquele blog e aprovação do responsável.

## Limites honestos

Este é **aprendizado operacional persistido no GitHub**, não retreinamento automático do ChatGPT. O modelo só usa essas lições se um agente/código consultar os arquivos. A evolução automática segura atual observa e registra; mudanças de código são propostas e validadas antes de promoção. Não declarar 100% E2E sem evidência de laboratório e produção.

## Extensão v2 — contrato do candidato

Leia `v31_master/autoevolution/README.md` antes de operar o motor. A geração paga por IA
requer chave exclusiva, modelo e habilitação explícita nas configurações do repositório.
Sem isso, o estado é BLOCKED_MODEL_CONFIGURATION, nunca declarar IA ativa.
Não confundir smoke sintético com melhoria real. Nunca executar candidato com tokens,
rede ou acesso a `.git`. Preservar regressões existentes e registrar resultados verificáveis.
A base observada antes desta revisão foi `cdbe7bba122ae3130cdc25b5bd410f492bf387fc`;
a main observada foi `2286726c6353fc2bfc454fd8b54bd7207cd36aec`. Estes SHAs são
referências de auditoria, não autorização de promoção nem substitutos de nova leitura ao vivo.
