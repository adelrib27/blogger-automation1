# R58 — Teste Blogger V31 + Shopee de ponta a ponta, LAB isolado

> **CORREÇÃO DE ORDEM OBRIGATÓRIA (06/11/2026):** o fluxo correto é criação do blog → instalação e validação pública do Tema V31 → configuração SEO → páginas institucionais → artigos → LOJA → rotação. A execução R58 já feita publicou SEO/páginas/artigos/LOJA antes do tema, contrariando essa ordem. Esses recursos permanecem preservados, mas o R58 NÃO é um teste E2E sequencial válido. Documento normativo: ORDEM_OBRIGATORIA_REPLICACAO_V31.md. NÃO criar novo blog nem remover conteúdo para disfarçar a ordem.\n\n**Estado em 2026-11-06:** BLOG_CRIADO + SEO + 6 PÁGINAS + 3 POSTS + LOJA 16
PUBLICADOS. TEMA V31 PREPARADO, AINDA NÃO INSTALADO.
ROTAÇÃO DE 15 MINUTOS IMPLEMENTADA E VALIDADA EM DRY-RUN,
MAS AINDA DESATIVADA POR GATE.

## Identidade exata

Blog ID 5999019959932264006
URL https://lab-v31-r58-shopee-e2e-20261106.blogspot.com/
Page LOJA ID 7680030566642713590
Timezone America/Recife, Blogger (GMT-03:00) São Paulo
Robots personalizados intocados. HTTPS, SEO, WebP e lazy-load ativos.

## Publicação existente

Cinco páginas institucionais: Sobre 4330493101782559572;
Contato 8642485791986631414; Política 223485400474715031;
Termos 2862183582058934423; Aviso Afiliados 6443676382450783375.
LOJA 7680030566642713590: 16 produtos Shopee de coleta R56 em 6/11/2026,
32 links rel nofollow sponsored noopener, quatro categorias.
LOJA inclui links para 3 posts.

Posts LIVE:
- Sapateira modular 3893198167585505550 (item Shopee 21797631048)
- Mixer elétrico 8886363878493152260 (item Shopee 22392992790)
- Mouse sem fio 1086696355631937197 (item Shopee 22597307453)

Dez URLs públicas responderam HTTP 200. Marcador V31 R58 ainda ausente
na auditoria pública; por isso NÃO afirmar tema instalado.

## Código

Branch: lab/v31-r58-novo-blog-shopee-e2e-15min
Partiu de branch R57 de testes; NÃO alterar ou mesclar main sem revisão.
v31_master/profiles/lab_r58_v31_e2e.json contém o escopo.
v31_master/state/lab_r58_rotation.json contém hash inicial da LOJA
4bb2ac7d5b4e7faee622aa3dbf5bf9b6d363d6ea9f6b70151607afbff7f9840b.
rotation_enabled e allow_auto_write seguem false.

Shopee API SAFE R58 GitHub run 42277216118: PASS, 16 itens,
sete diferentes da LOJA inicial. SHA256 catálogo HTML:
1d24434ac79be436672d3f5061744e3851294dd8c81a9f1289f6fc892a8fa6ce.
Dry-run autenticado GitHub run 42277536917: PASS,
R58_DRY_RUN_PASS_NO_WRITES, new_items=7.
21+ regressões e inventário autenticado: run 42277085051 PASS.
Revisões de HTML público grande passaram em run 42277850453.

## Tema

O XML V31 R52 foi adaptado offline ao R58, SHA256
9d59f34aa0a2c6e03a1e59206c4d27dbcb98f2bcbbc1c8b21e728ab63a4d7d81.
Está no pacote BLOGGER_R58_TEMA_V31_CDP_INSTALACAO_ISOLADA.zip.
A API Blogger v3 pública não tem operação de upload de tema.
O conector local expõe somente instalação V20; não utilizá-la.
É preciso executar o CMD único pelo Chrome/CDP do Windows:
01_INSTALAR_TEMA_R58_UNICA_VEZ.cmd.
Após a trava de tentativa não repetir, mesmo se incerto.
Não reiniciar R49 nem editar seus arquivos assinados.

## Rotação experimental 15 minutos

Workflow .github/workflows/v31_lab_r58_rotation_15min.yml contém cron
"*/15 * * * *" e stop_after_utc=2026-11-07T21:00:00Z.
Schedules GitHub Actions rodam a partir da branch padrão; este arquivo está
somente em branch LAB. O cron ainda NÃO está rodando.
Gates obrigatórios: XML V31 R58 visível, estado habilitado exclusivamente
R58, API Shopee sem erro, 16 ofertas válidas, seleção diferente, backup,
uma única tentativa de PUT para a Page exata, readback API, prova pública e
persistência de estado APENAS após PASS. Erro de API não altera LOJA.
Sem envio de secrets a logs. A configuração atual impede LIVE.

## Próximos gates (não executados)

1. Instalar tema V31 via CMD do pacote no Windows do usuário, validar público
   e navegação/celular.
2. Revalidar a Page e os três posts após tema.
3. Atualizar flags R58 por revisão, repetir prévia SAFE, fazer um LIVE único
   com catálogo novo (se ainda válido).
4. Verificar 16 produtos, links, tema e homepage públicos e estado persistido.
5. Somente depois integrar workflow R58 à main e habilitar cron de 15 min
   limitado ao prazo de teste, sem modificar workflows/temas de outros blogs.

**R49 continua intacto e opera somente nos 3 LABs anteriores.**
