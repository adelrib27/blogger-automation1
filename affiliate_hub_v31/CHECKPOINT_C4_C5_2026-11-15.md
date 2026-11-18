# C4 + C5 — Conversão afiliada real e pautas originais em dois blogs (15/11/2026)

**Código C4:** `V31-EDITORIAL-C4-CONVERSAO-REAL-PASS-20261115`  
**Código C5 (continuar por aqui):** `V31-EDITORIAL-C5-ORIGINALIDADE-REAL-PASS-20261115`

## Escopo

Projeto V31 Hub Editorial Shopee — **Blogger e WordPress**, sem Pinterest.
Repositório `adelrib27/blogger-automation1`; branch isolada `feature/v31-affiliate-hub-c1-safe-20261115`, [PR #52](https://github.com/adelrib27/blogger-automation1/pull/52) draft.

## C4 — Piloto REAL de conversão da Shopee

- [Run 43771181969](https://github.com/adelrib27/blogger-automation1/actions/runs/43771181969), **SUCCESS**; log sanitizado `V31_C4_ONE_LINK_REAL_PASS`.
- Antes da execução real, **69/69 testes automatizados offline passaram**.
- Uma única mutation `generateShortLink` do produto aprovado do nicho **cozinha/air_fryers** para a campanha `airfryers`.
- **1 link afiliado gerado e salvo** no cache privado do catálogo SQLite/R2.
- Segundo acesso ao mesmo produto e campanha reutilizou o cache, sem nova mutation.
- Snapshot R2 gravado, restaurado e conferido, **retenção sem pendências** (`RETENTION_PENDING=False`).
- **O link real, as credenciais, o título e o identificador do produto não foram exibidos nos logs ou no repositório.**
- O workflow temporário `.github/workflows/v31_editorial_conversion_once.yml` foi excluído após PASS.

## C5 — Pautas diferenciadas usando o mesmo produto REAL

- [Run 43771386845](https://github.com/adelrib27/blogger-automation1/actions/runs/43771386845), **SUCCESS**; log `V31_C5_EDITORIAL_REUSE_REAL_PASS`.
- O mesmo produto já presente no R2 foi reservado para **dois blogs Blogger diferentes** (`blogger_air_fryers` e `blogger_cozinha_sem_complicacao`).
- **2 títulos e 2 abordagens distintos**, preservando a palavra-chave principal `air fryer`.
- Todas as pautas possuem status **`REVIEW_REQUIRED`**. Nenhum artigo foi gerado nem enviado para o Blogger.
- Histórico das duas pautas persistido, restaurado e validado no R2.
- Retenção real dos snapshots concluída sem pendência.
- O workflow temporário `.github/workflows/v31_editorial_briefs_once.yml` foi excluído após PASS.
- Não confundir a **originalidade da pauta/título** com originalidade do texto completo: esta depende de geração editorial, fontes e auditoria humana antes de publicar.

## Decisões de arquitetura confirmadas

- Reutilização de produtos comerciais é permitida; a regra de exclusividade opera por **assunto/intenção/ângulo/título**, preservando keywords estratégicas.
- URLs de imagens da Shopee serão referenciadas, não armazenadas no R2. Verificar disponibilidade e licença de uso quando os artigos forem criados.
- R2 deve conservar **no máximo dois snapshots**, atual e anterior, com `retention_pending` visível em relatórios se a limpeza falhar. Nenhum backup ilimitado.
- 50 blogs × 1–2 artigos/dia é a **meta**, não o estado atual. Somente **20 rotas** estão cadastradas (18 Blogger + 2 WordPress).
- Não ativar publicação automática em produção até validar credenciais de publicação, controle de qualidade e reconciliação de conteúdos remotos por blog.
- GitHub Environment `v31-editorial-safe` ainda foi visto com `Deployment branches and tags: No restriction`; restringir antes da liberação LIVE.
- Uma Shopee App Secret apareceu em uma captura anterior; **rotação ainda não comprovada**. Coordenar substituição sem interromper outros projetos dependentes.

## Próxima etapa C6

- Criar fluxo de geração/revisão de texto completo, baseado em informações verificáveis dos produtos e sem afirmações comerciais inventadas.
- Implementar criação de **rascunhos reais** via adaptadores Blogger e WordPress com credenciais e permissões específicas, sem publicação ao vivo inicialmente.
- Fazer testes de postagem por blog, reconciliação e títulos diferentes, agendamentos desativados por padrão e habilitação gradual após aceitação.
- Expandir mapeamento para os 50 blogs **apenas com IDs/URLs reais fornecidos ou descobertos em contas conectadas**; não inventar blogs.
- Garantir orçamentos, monitoramento de erros e operação idempotente na nuvem.

**Não fazer merge automático do PR #52 nem ativar jobs LIVE sem revisão de segurança.**
