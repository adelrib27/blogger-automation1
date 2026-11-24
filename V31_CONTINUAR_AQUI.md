# V31 — Índice operacional

**Fonte mestre única:** [SYSTEM_MASTER.md](SYSTEM_MASTER.md).  
**Estado operacional legível por máquina:** [CONTINUIDADE_ESTADO.json](affiliate_hub_v31/CONTINUIDADE_ESTADO.json).  
**Repositório:** `adelrib27/blogger-automation1`, branch `main`.  
**Estado de publicação:** SAFE/DRAFT controlado. LIVE automático permanece desativado (`activation=pending_policy_approval`).

## Fonte de decisão

Leia `SYSTEM_MASTER.md` antes de qualquer execução. Em seguida, confira os arquivos de política, rotas e estado vivo do serviço envolvido. O conteúdo deste índice é apenas um atalho operacional; não substitui o documento mestre, a implementação ou os estados reais de R2, D1, Shopee e CMS.

## Portfólio habilitável

O motor universal possui **7 rotas editoriais cadastradas**: quatro Blogger (Móveis para Cada Canto, Limpeza Inteligente, Estilo no Dia a Dia e Acessórios, Cozinha Sem Complicação) e três WordPress (Casa e Decoração, Oficina & Garagem, Radar Tech BR). **Vida Pet Prática** é um blog Blogger ativo, identificado como `8052455848487624244`, mas depende de confirmação de rota e campanha V31 antes de receber DRAFT. **Ar-Condicionado sem Dúvidas** está fora do rollout.

Os **24 IDs indisponíveis** descritos em `affiliate_hub_v31/EDITORIAL_DELETED_BLOGGER_TOMBSTONES_C143.json` permanecem bloqueados. O sistema não tenta reativá-los nem recriar seus writers, crons ou campanhas.

## Próxima operação segura

1. Confirmar a `main` e os workflows recentes, verificando novos commits antes de mutações.
2. Confirmar a identidade, campanha, SKU, imagem, fontes independentes, SEO e duplicidade de cada candidato.
3. Rodar 50 simulações offline por ciclo crítico; em DRAFT real, confirmar ID/status/hash por GET autenticado.
4. Reconciliar colisões READY/CMS sem repetir POST; diagnosticar indisponibilidade Shopee sem forçar ofertas.
5. Manter o limite diário por site, o catálogo cumulativo, o escopo exclusivo Blogger/WordPress e LIVE desativado até autorização expressa.

**Preservação:** o mecanismo de continuidade mantém o estado atual no JSON e um checkpoint técnico verificável enquanto necessário. Arquivos de relatório desnecessários não determinam autorização operacional. Consulte `SYSTEM_MASTER.md` para o contrato completo.
