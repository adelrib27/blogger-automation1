# CHECKPOINT UPDATE — 2026-11-01 — POLICY, ANTI-REPETIÇÃO E COOKIES

**Projeto:** Blogger Automation sem ChatGPT Work  
**Repositório:** `adelrib27/blogger-automation1`  
**Status deste checkpoint:** estado validado até a conclusão da auditoria europeia de cookies em 2026-11-01.

## REGRA DE CONTINUIDADE

Este arquivo prevalece sobre checkpoints anteriores quando houver diferença de estado operacional. Não recomeçar diagnósticos já concluídos. Preservar os checkpoints de 2026-10-30 como histórico e base de recuperação.

## Runner / automação Blogger atual

- Blogger Local Runner validado e autenticado: **v0.8**.
- Chrome oficial/CDP conectado com sucesso.
- Capacidades reportadas pelo runner v0.8: `create`, `settings`, `v20`, `provision-new-blog-v20`, `v20-runtime-sync-guard`.
- A versão v0.8 supersede o registro operacional antigo de v0.6 no checkpoint de 2026-10-30.
- Conteúdo Blogger continua sendo operado pela integração `Blogger_Bridge_V2`.
- Não assumir operação manual do painel quando já existe comando validado no Local Runner.

## Rede Blogger atualmente conectada — 18 blogs

1. Eletroportáteis na Cozinha — `https://eletroportateis-na-cozinha.blogspot.com/`
2. Cabelos em Foco — `https://cabelos-em-foco.blogspot.com/`
3. Achados para Casa — `https://achadosparacasa2026.blogspot.com/`
4. Ventiladores em Foco — `https://ventiladores-em-foco.blogspot.com/`
5. Air Fryers em Foco — `https://air-fryers-em-foco.blogspot.com/`
6. Limpeza Inteligente — `https://limpeza-inteligente.blogspot.com/`
7. Conecta Achados — `https://conectaachados.blogspot.com/`
8. Estilo no Dia a Dia — `https://estilo-no-dia-a-dia-0071220800-2.blogspot.com/`
9. Casa em Ordem — `https://casa-em-ordem-pratica.blogspot.com/`
10. Escolha Certa Online — `https://escolha-certa-online.blogspot.com/`
11. Achados que Valem — `https://achados-que-valem.blogspot.com/`
12. Guia de Achados & Ofertas — `https://guia-de-achados-e-ofertas.blogspot.com/`
13. Vitrine Prática — `https://vitrine-pratica.blogspot.com/`
14. Moda e Ofertas — `https://moda-ofertas.blogspot.com/`
15. Achadinhos de Beleza — `https://canal-attitude.blogspot.com/`
16. Radar Tech BR — `https://portalradartechbr.blogspot.com/`
17. Cozinha Sem Complicação — `https://cozinha-sem-complicacao.blogspot.com/`
18. Liquidificadores em Foco — `https://liquidificadores-em-foco.blogspot.com/`

### IDs críticos confirmados

- Conecta Achados — Blog ID `1719259388907013414`.
- Achados para Casa — Blog ID `1426630233929943394`.
- Ventiladores em Foco — Blog ID `4473989735719981382`.
- Air Fryers em Foco — Blog ID `9113728635217260884`.
- Limpeza Inteligente — Blog ID `7757953554206491487`.
- Cabelos em Foco — Blog ID `6319734511998091378`.
- Liquidificadores em Foco — Blog ID `5271798990390532475`.
- Eletroportáteis na Cozinha — Blog ID `8658632621591002634`.

## Regra permanente de identidade dos blogs

Blogs não devem mais usar como identidade principal o nome de um único produto. As identidades de nicho já adotadas e que devem ser preservadas são:

- Ventiladores em Foco
- Air Fryers em Foco
- Limpeza Inteligente
- Cabelos em Foco
- Liquidificadores em Foco
- Eletroportáteis na Cozinha

Nomes legados de produtos podem permanecer apenas em posts antigos/conteúdo, nunca como identidade principal do blog ou domínio ativo.

## Lojas Shopee por nicho — estado validado

As seis lojas de nicho usam arquitetura isolada: **1 motor + N configs + N históricos independentes**. Não voltar a um único `store_last_selection.json` compartilhado entre blogs.

Fluxo canônico validado:

`Shopee API → Blogger Policy Guard → filtro semântico de nicho → dedup/rotação → SAFE → LIVE → hero 12 → validação pública → persistência`

Contrato atual das lojas:

- **20 produtos** por loja.
- **12 produtos** no hero.
- Persistência de rotação/histórico somente após validação pública bem-sucedida.
- Fail-closed: se qualquer estágio crítico falhar, preservar a loja anterior.

Categorias atuais:

### Ventiladores em Foco
- Mesa & Coluna
- Torre
- Teto
- Parede
- Circuladores & Climatização

### Air Fryers em Foco
- Air Fryers
- Grandes/Família
- Formas
- Grelhas/Cestos
- Utensílios

### Limpeza Inteligente
- Robôs Aspiradores
- Aspiradores Verticais
- Aspiradores Portáteis
- Mops & Limpeza
- Acessórios de Limpeza

### Cabelos em Foco
- Máscaras & Tratamentos Cosméticos
- Shampoo & Condicionamento
- Finalização
- Secadores & Escovas
- Pentes & Acessórios

### Liquidificadores em Foco
- Liquidificadores
- Mixers
- Processadores
- Trituradores
- Complementos de Cozinha

### Eletroportáteis na Cozinha
- Air Fryers
- Liquidificadores & Mixers
- Processadores
- Batedeiras
- Cafeteiras & Outros Eletros

## Correções visuais de LOJA que NÃO devem ser refeitas

A correção final de Store já foi validada em Vitrine Prática e aplicada/validada em Ventiladores em Foco:

- `.centered-bottom` em uma coluna.
- coluna lateral antiga de 300 px removida.
- `.main-container` em 100% de largura.
- sidebar oculta apenas na página Loja.
- “Postagens mais visitadas” oculto apenas na página Loja.
- `.bls-page` centralizada.
- 20 cards + 12 hero preservados.
- domínio/nome legado removido do cloner de Ventiladores em Foco.

Não repetir essa correção sem regressão comprovada.

## Blogger Policy Guard — estado atual

Arquivos centrais:

- `POLICY_BASELINE_BLOGGER_GOOGLE_2026.md`
- `config/blogger_policy_guard.json`
- `src/blogger_policy_guard.py`

O baseline atual está datado de 2026-11-01 e registra a política Blogger futura com vigência indicada para 2026-12-16.

O guard cobre, entre outros pontos:

- produtos regulados/proibidos;
- links afiliados apenas em hosts Shopee aprovados;
- imagens de origem Shopee;
- frases enganosas/urgência inventada/garantias falsas;
- aviso de afiliados;
- `nofollow sponsored noopener`;
- tentativas de esconder/desativar aviso nativo de cookies do Blogger;
- contrato de Store 20 produtos + 12 hero.

### Seis pipelines de nicho

O `BLOGGER_POLICY_GUARD` está integrado nos seis pipelines de nicho tanto em SAFE quanto na validação pública LIVE. A seleção/rotação só é persistida depois de PASS público.

### Auditoria permanente de política

Já existe auditoria independente do repositório para impedir regressões como:

- remoção do Policy Guard dos seis pipelines;
- ocultação/desativação do aviso nativo de cookies;
- reintrodução de domínios legados de blogs-produto em workflows ativos;
- pipeline LIVE sem validação pública 20 + 12.

O falso positivo inicial de domínio legado foi corrigido; a execução subsequente passou 100%.

## Gate anti-repetição editorial — CONCLUÍDO

Arquivos novos:

- `config/editorial_cross_blog_guard.json`
- `src/editorial_cross_blog_guard.py`
- `src/editorial_cross_blog_guard_self_test.py`
- `.github/workflows/editorial_cross_blog_guard_safe.yml`

Escopo atual do gate: fluxos editoriais automatizados de **Casa & Decoração, Oficina & Garagem e Radar Tech BR**.

Regras principais:

- compara `editorial_html`, não o `content_html` completo;
- ignora na prática CTA, aviso de afiliado, rodapé/legal/layout compartilhado;
- usa múltiplos sinais: título, sequência, cosseno de tokens e shingles;
- bloqueia cópia idêntica e near-duplicate de alta confiança;
- bloqueia somente o candidato conflitante (`BLOCKED`), mantendo os demais disponíveis;
- erros de configuração/operação falham a execução;
- produz relatório auditável.

Validação SAFE:

- workflow: `Editorial — Gate Anti-Repetição Entre Blogs SAFE`;
- execução validada: run ID `41358905465`;
- resultado: **SUCCESS**;
- autotestes: cópia idêntica BLOCKED, near-duplicate BLOCKED, conteúdo realmente diferente PASS, CTA/legal compartilhado sem falso positivo.

## Auditoria europeia de cookies Blogger — CONCLUÍDA

Arquivos novos:

- `src/blogger_eu_cookie_audit.py`
- `.github/workflows/blogger_eu_cookie_audit_safe.yml`

Método:

- navegador Chromium/Playwright;
- contexto limpo por blog;
- locale `fr-FR`;
- timezone `Europe/Paris`;
- `Accept-Language` francês;
- URL testada com `?gl=fr`;
- screenshot antes e depois;
- detecção visual/DOM do banner;
- detecção do botão;
- clique real;
- confirmação de que o banner desaparece.

Resultado final da versão otimizada:

- workflow: `Blogger — Auditoria SAFE do aviso europeu de cookies`;
- run ID `41359632797`;
- **18/18 PASS**;
- **0 FAIL**;
- todos retornaram HTTP 200;
- todos mostraram o aviso francês;
- todos apresentaram botão de consentimento;
- em todos o clique removeu o aviso corretamente;
- evidências em screenshots e `report.json` foram salvas como artifact do GitHub Actions.

Conclusão operacional: não adicionar outro banner manual ao tema enquanto esse mecanismo nativo continuar passando a auditoria. `?gl=fr` é mecanismo prático de teste regional, não deve ser tratado isoladamente como certificação jurídica completa de conformidade europeia.

## Próximo bloco de trabalho

Retomar a implantação/expansão da **página LOJA Blogger + Shopee em destaque na rede**, reutilizando o motor, Policy Guard, filtros, rotação, contrato 20 + 12 e validação pública já existentes. Não reconstruir a arquitetura do zero.

Objetivo de continuidade:

`Blogger + automação local + APIs + tema/SEO + páginas institucionais + afiliados + Shopee + LOJA destacada + atualização automática`

## Regras de retomada

- Não refazer validações já concluídas sem sinal concreto de regressão.
- Não pedir operação manual quando o Local Runner já possui comando validado.
- Confirmar Blog ID antes de qualquer escrita.
- Preservar a regra de identidade por nicho.
- Preservar Store 20 + 12, fail-closed e histórico independente por blog.
- Preservar Policy Guard SAFE/LIVE e validação pública antes da persistência.
- Preservar o gate anti-repetição editorial nos fluxos já protegidos.
- Preservar o aviso nativo de cookies do Blogger; não ocultar via tema/CSS.
- Não armazenar secrets no repositório.
- Não declarar sucesso sem validação concreta.

## Pendências históricas ainda documentadas

Os gaps locais antigos `apply_theme_safe.py` e `backup_theme_safe.py` continuam documentados no backup de 2026-10-30 como arquivos executados/validados localmente mas sem bytes-fonte preservados no GitHub naquele snapshot. Não declarar esse gap resolvido sem confirmação concreta.
