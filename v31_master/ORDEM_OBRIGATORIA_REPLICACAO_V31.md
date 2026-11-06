# Blogger Automation V31 — ordem obrigatória de replicação

Versão: R58-CORRECAO-SEQUENCIA, 2026-11-06
Escopo: novos blogs e laboratórios V31. Esta ordem é **bloqueante**.

## Contrato de execução

| Fase | Operação | Requisito para liberar a próxima |
|---|---|---|
| 01 | PREFLIGHT e **CRIAR BLOG** | Blog ID/URL exatos, criação única, HTTP público e registro de identidade |
| 02 | **BACKUP DO TEMA PADRÃO + INSTALAR TEMA V31/R52** | XML íntegro com hash, instalação única, readback real e prova pública do marcador V31 e da navegação |
| 03 | **CONFIGURAR SEO** | Apenas após Fase 02 validada; HTTPS, descrições, visibilidade, WebP, lazy-load, fuso e leitura posterior |
| 04 | **PUBLICAR PÁGINAS** | Apenas após Fase 03 validada; cinco páginas institucionais e validação de URL e conteúdo |
| 05 | **COLETAR PRODUTOS SHOPEE, PUBLICAR 3 ARTIGOS** | API autenticada e SAFE, IDs/links/imagens válidos, disclosure, readback e publicação pública |
| 06 | **PUBLICAR LOJA INTEGRADA** | Page estável, links dos três artigos, 16 itens únicos, links patrocinados, readback/API e HTTP |
| 07 | **ROTAÇÃO SAFE → LIVE ÚNICA → AGENDAMENTO DE TESTE** | Somente após Fases 01–06, backups, uma tentativa, validação pública, persistência pós-PASS; nunca habilitar cron por antecipação |

## Guardas

1. **Fase 02 é obrigatoriamente anterior às Fases 03, 04, 05, 06 e 07.** Instalação pendente ou marcador público ausente: parar. Não publicar SEO, páginas, artigos ou LOJA.
2. Se houver timeout/falha/incerteza na instalação V31, NÃO repetir automaticamente nem recorrer ao V20. Auditar instalação real antes de avançar.
3. O Tema V31 deve ser adaptado a nome, endereço e Blog ID novos, sem copiar identidade de outro blog.
4. Rotação de 15 minutos é experimento EXCLUSIVO R58 e não define o padrão de produção.
5. Nunca alterar hashes assinados, inicializador, DPAPI ou políticas R49 por atalho. Nunca alterar outros blogs.
6. **Evidência de execução** precisa conter marcador público do tema e cronologia real das fases. Checkpoint, plano, XML preparado ou relatório offline não substituem execução validada.
7. Em blogs já criados, não apagar nem recriar para falsificar a ordem; marcar o teste como fora de sequência e concluir o que falta com rastreabilidade.

## Caso R58 real

O LAB R58 (5999019959932264006) foi criado e teve SEO, páginas, 3 artigos e LOJA publicados **antes** da instalação do V31. Foi uma execução fora da sequência exigida; não é admissível classificá-lo como replicação E2E **sequencial** aprovada.

Preservar publicações atuais. Instalar V31 apenas com tentativa única e confirmação pública. Validar os componentes já existentes após o tema. Em uma nova replicação futura, seguir a sequência 01→02→03→04→05→06→07 sem exceções.
