# CHECKPOINT OPERACIONAL V31 — Violão do Começo — 08/11/2026

> Estado real auditado nesta execução. Hierarquia: live API/HTML público > arquitetura V31 validada > checkpoint > histórico. O antigo `CHECKPOINT_V31_CRIACAO_2026-11-08.md` descreve uma etapa intermediária, superada pelo estado abaixo. **Não repetir provisionamento nem instalar o tema via Runner**; o usuário fez a instalação manualmente e solicitou preservá-la.

## Identidade e etapa inicial
- Blog ID exato (string): `370856880185231084`
- Nome: **Violão do Começo — Acordes e Cuidados**
- URL: https://violao-do-comeco-acordes.blogspot.com/
- Nicho: aprendizagem inicial de violão, afinação, escolha do instrumento, cordas, capotrastes, conservação e acessórios.
- Inventário inicial da criação: 26 blogs, anticlonagem aplicada; novo blog criado na conta após chamada parcial do Runner, com SEO validado. **Não criar outro blog para o mesmo endereço.**
- Tema universal V31: **instalado manualmente pelo usuário**. Firecrawl público da home retornou HTTP 200, título correto, `ub-header`/`ub-footer`, menu para Início/Sobre/Loja/Contato. Não houve leitura integral do XML/template, logo não afirmar equivalência byte a byte à versão R52.

## Estado de publicação (Blogger Bridge V2)
**8 páginas LIVE:**
1. Mensagem enviada: `5268810886379481544`, https://violao-do-comeco-acordes.blogspot.com/p/mensagem-enviada.html
2. Sobre: `5814314898328211032`, https://violao-do-comeco-acordes.blogspot.com/p/sobre.html
3. Política de Privacidade: `3114696112517100423`, https://violao-do-comeco-acordes.blogspot.com/p/politica-de-privacidade.html
4. Termos de Uso: `1568130325946995438`, https://violao-do-comeco-acordes.blogspot.com/p/termos-de-uso.html
5. Política de Cookies: `4639907286224257162`, https://violao-do-comeco-acordes.blogspot.com/p/politica-de-cookies.html
6. Aviso de Afiliados: `4294125077079519626`, https://violao-do-comeco-acordes.blogspot.com/p/aviso-de-afiliados.html
7. Contato: `1746256944168826772`, https://violao-do-comeco-acordes.blogspot.com/p/contato.html
8. LOJA: `8853351638771820335`, https://violao-do-comeco-acordes.blogspot.com/p/loja.html

**3 artigos LIVE, exclusivos, com 2 imagens Shopee e 2 CTAs afiliados cada:**
1. `4639395596795413595` — [Primeiro violão: como escolher entre nylon e aço, tamanho e conforto](https://violao-do-comeco-acordes.blogspot.com/2026/11/primeiro-violao-como-escolher-entre.html)
2. `634645461240454735` — [Como afinar o violão para iniciantes](https://violao-do-comeco-acordes.blogspot.com/2026/11/como-afinar-o-violao-para-iniciantes.html)
3. `5305810004310304820` — [Capotraste, capa e cuidados do violão](https://violao-do-comeco-acordes.blogspot.com/2026/11/capotraste-capa-e-cuidados-do-violao.html)

- Os três começaram em rascunho com pré-validação SAFE, foram publicados individualmente e tiveram readback API. Cada HTML contém alt e `rel="nofollow sponsored noopener noreferrer"` nos links Shopee, disclosure comercial, sem prometer experiência própria de teste.
- Links internos relacionados entre os três artigos e para `/p/loja.html` foram inseridos com marcador único `VDC31_INTERNAL_LINKS_20261108`, conferidos por readback.

## Shopee Affiliate API e Loja
- PR laboratório SAFE **#36**: https://github.com/adelrib27/blogger-automation1/pull/36 — catálogo autenticado em `violao_do_comeco/shopee_catalog_safe.py` e workflow `.github/workflows/violao_do_comeco_shopee_catalog_safe.yml`. **DRAFT / não integrar sem revisão.**
- GitHub Actions execução SAFE `42516276271`: **SUCCESS**, 16 IDs diferentes, 4 produtos por categoria, imagens HTTPS e links comerciais reais, checagem `blogger_policy_guard`. Primeira execução `42516174032` encontrou erro GraphQL transitório e falhou; script ganhou espera e retry limitado, sem contornar limites.
- Loja LIVE Page ID `8853351638771820335`: quatro grupos (Cordas de Violão, Afinadores, Capotrastes, Capas para Violão) × quatro ofertas = **16 IDs únicos, 16 imagens HTML, 16 links afiliados**. Os nomes de categorias de vitrine foram ajustados para corresponder aos produtos efetivamente selecionados: os grupos SAFE `Capotrastes e Palhetas` e `Capas e Suportes` continham apenas capotrastes e capas. Alinhar eventual gerador futuro a estes nomes reais.
- Região automatizável protegida pelos marcadores `UNIVERSAL_V31_STORE_AUTO_START/END`, CSS responsivo e navegação horizontal de categorias. Data exibida da consulta real: 08/11/2026, 16h41 Recife; valores somente referências daquela captura, não preços em tempo real.
- **Nenhuma rotação agendada/LIVE ativada** para este blog. Os produtos são o snapshot inicial; scripts e agenda de rotação precisam de trabalho específico, SAFE, isolamento, teste e autorização antes de integração.

## Auditorias públicas executadas
- Firecrawl live `maxAge:0`: **HTTP 200** home, Loja, três artigos, Contato, Sobre e Mensagem enviada.
- Home: título, meta description específica, canonical HTTPS, viewport, `ub-header`, `ub-footer` e navegação presentes.
- Três artigos: títulos corretos, HTML público com duas imagens de anúncios Shopee e dois CTAs afiliados, disclosure e links internos.
- Loja: 16 `data-item-id` únicos, 16 imagens de anúncios e 16 links Shopee distintos no HTML público; captura mobile retornada por serviço externo. **Não equiparar presença de URL da imagem à confirmação da carga visual efetiva de cada uma das 16 imagens**.
- Teste móvel superficial: captura da Loja e de um artigo, HTTP 200; inspeção detalhada de layout visual completo em diversos tamanhos/desktop e verificação de carregamento `naturalWidth` ainda não provadas.

## Pendências e bloqueios fail-closed
**Contato público:** a página Contato salva na API contém formulário FormSubmit com `_subject`, `_next=https://violao-do-comeco-acordes.blogspot.com/p/mensagem-enviada.html` e honeypot. Foi reutilizado exclusivamente o destino já configurado nos blogs anteriores, sem expor e-mail. **Porém o tema manual renderiza formulário público próprio `ub-contact-form` sem o campo `_next`.** A página de retorno existe, mas o redirecionamento real não é comprovado. Ativação/entrega FormSubmit para este blog não foi testada. **Não alterar tema instalado sem inspeção e procedimento autorizado.** Correção deve ser pontual no template que gera o formulário público, com readback e envio E2E consentido.
**SEO de posts:** HTML público dos artigos não apresentou meta description específica em `<head>`; há canonical e título. Ajuste a ser auditado por fluxo seguro de SEO/tema, sem sobrepor o tema manual.
**Imagens:** URL de 16 imagens presente e captura mobile gerada, mas carga visual individual não aferida.
**Conteúdo editorial:** além de três posts iniciais, pilares e clusters do mapa ainda **não publicados**.
**Autoridade:** planejamento ético documentado; nenhum backlink adquirido ou inventado.
**Automações:** não criar nem ativar execução LIVE de rotador/editorial sem gate SAFE, Blog ID + Loja Page ID + ETag/concorrência + readback e QA público; não copiar cron de outro blog.

## Próximas ações
1. Corrigir a geração do formulário público `ub-contact-form` para incluir `_next` real e validar processamento/entrega separadamente. Não reinstalar tema.
2. Completar QA visual mobile/desktop da Loja, imagens individuais e menus, e revisão das metadescrições de posts.
3. Produzir pilares e clusters originais conforme `MAPA_EDITORIAL_V31.md`, com SEO, links internos, CTAs Shopee contextuais e verificação pública.
4. Preparar rotação diária da Loja isolada por `370856880185231084` e `8853351638771820335`, distinguindo SAFE e LIVE. Conferir fonte Shopee e mudanças do catálogo em tempo real antes de ativar.
5. Só marcar etapa 15 de finalização plena quando todas as pendências tiverem evidência real, inclusive schedule recorrente.
