# Blogger Automation V20 — CURRENT

Checkpoint operacional atual do projeto.

**Estado geral:** PASS  
**Runner:** v0.7  
**Tema:** BLOGGER_MODELO_V20 canônico  
**Provisionamento ponta a ponta:** validado em 2026-10-30  
**Auto-start após reboot sem CMD manual:** PASS  
**Fluxo editorial Shopee real:** PASS nos 3 blogs reais

Documento canônico técnico detalhado:

```text
docs/BLOGGER_AUTOMATION_V20_CHECKPOINT_2026-10-30.md
```

## Estado técnico validado

```text
plugin 8 tools: PASS
Chrome CDP: PASS
runner v0.7: PASS
create blog: PASS
settings/SEO: PASS
GMT-03 São Paulo: PASS
tema V20: PASS
5 páginas institucionais: PASS
robots intocados: PASS
auto-start após reiniciar Windows: PASS
ChatGPT acessando runner sem CMD manual: PASS
```

## Blogs reais — estado editorial final em 2026-10-30

### 1. Vitrine Prática

- Blog ID: `9144338307944682868`
- URL: https://vitrine-pratica.blogspot.com/
- 5 páginas institucionais LIVE
- 5 posts afiliados LIVE
- 0 drafts
- produtos reais da Shopee Affiliate API
- CTA afiliado no segundo parágrafo: PASS
- segundo CTA perto do fim: PASS
- linkagem interna: PASS
- Arquitetura de Silos: PASS

Silos:

```text
Organização & Rotina
- Organizador de guarda-roupa com zíper
- Potes herméticos de vidro com tampa de bambu

Conforto & Ambientes
- Travesseiro 50x70 anunciado como pluma de ganso
- Tapete geométrico aveludado e antiderrapante
- Luminária solar com sensor de movimento
```

Backups:

```text
# snapshot original
backups/blogger-content/2026-10-30/vitrine-pratica/manifest.md
backups/blogger-content/2026-10-30/vitrine-pratica/01-organizador-guarda-roupa.html
backups/blogger-content/2026-10-30/vitrine-pratica/02-luminaria-solar.html
backups/blogger-content/2026-10-30/vitrine-pratica/03-travesseiro-50x70.html
backups/blogger-content/2026-10-30/vitrine-pratica/04-tapete-geometrico.html
backups/blogger-content/2026-10-30/vitrine-pratica/05-potes-hermeticos.html

# snapshot após retrofit das regras v2
backups/blogger-content/2026-10-30/vitrine-pratica-rules-v2/manifest.md
backups/blogger-content/2026-10-30/vitrine-pratica-rules-v2/posts-full.html
```

### 2. Achados que Valem

- Blog ID: `7527651041649593600`
- URL: https://achados-que-valem.blogspot.com/
- 5 páginas institucionais LIVE
- 5 posts afiliados LIVE
- 0 drafts
- Posicionamento editorial: oportunidades e custo-benefício
- CTA afiliado no segundo parágrafo: PASS
- segundo CTA perto do fim: PASS
- linkagem interna: PASS
- Arquitetura de Silos: PASS

Silos:

```text
Tecnologia & Lazer
- Smartwatch barato com chamadas Bluetooth
- Caixa de som Bluetooth com 2 microfones

Casa & Utilidades
- Organizador de banheiro barato
- Escorredor de louças de aço
- Parafusadeira 25V com maleta
```

Backup:

```text
backups/blogger-content/2026-10-30/achados-que-valem/manifest.md
backups/blogger-content/2026-10-30/achados-que-valem/posts-full.html
```

### 3. Escolha Certa Online

- Blog ID: `5151950717041967683`
- URL: https://escolha-certa-online.blogspot.com/
- 5 páginas institucionais LIVE
- 5 posts afiliados LIVE
- 0 drafts
- Posicionamento editorial: guias comparativos e decisão de compra
- CTA afiliado no segundo parágrafo: PASS
- segundo CTA perto do fim: PASS
- linkagem interna: PASS
- Arquitetura de Silos: PASS

Silos:

```text
Cama & Banho
- Lençol 400 fios
- Tapete de banheiro antiderrapante
- Kit de acessórios para banheiro em inox

Jardim & Decoração
- Pedra dolomita branca
- Suporte de madeira para vaso
```

Backup:

```text
backups/blogger-content/2026-10-30/escolha-certa-online/manifest.md
backups/blogger-content/2026-10-30/escolha-certa-online/posts-full.html
```

## Totais do ciclo editorial real

```text
3 blogs reais
15 posts afiliados LIVE
0 drafts após validação final em cada blog
15 produtos/ofertas trabalhados no ciclo
2 CTAs por post: PASS nos 3 blogs
linkagem interna: PASS nos 3 blogs
Arquitetura de Silos: PASS nos 3 blogs
```

## Padrão editorial obrigatório vigente

Cada novo post deve conter:

- artigo rico e útil, não uma descrição curta de produto;
- produto real vindo da Shopee Affiliate API;
- nenhuma invenção de preço, estoque, benefício ou especificação;
- imagem real da oferta quando disponível;
- transparência de afiliado;
- primeiro CTA afiliado no segundo parágrafo;
- segundo CTA afiliado antes ou depois do penúltimo parágrafo;
- links comerciais com `rel="nofollow sponsored noopener"`;
- dados comerciais apresentados como retrato da coleta quando aplicável;
- SEO natural;
- linkagem interna contextual;
- Arquitetura de Silos planejada por conjunto de posts;
- âncoras internas descritivas e naturais;
- validação final no Blogger após publicação;
- backup versionado depois de cada lote concluído.

## Próximo estado

Os três blogs reais estão provisionados e com o primeiro lote editorial concluído sob o mesmo padrão editorial vigente. O próximo trabalho pode ser expansão de conteúdo, aprofundamento dos silos existentes, criação de novos silos ou automação contínua de novos lotes.

Ao iniciar uma nova conversa, usar este arquivo como ponte para o checkpoint técnico completo e para o estado editorial atual. Não recomeçar o projeto a partir de documentação antiga.
