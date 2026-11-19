# C66 — WordPress Casa #305: revisão antes de publicar LIVE

**ESTADO: PRONTO PARA APROVAÇÃO INDIVIDUAL; NÃO PUBLICADO.** Este documento é evidência de revisão técnica/editorial preliminar, **não substitui** consentimento do proprietário nem confirma preço, estoque ou qualidade comercial do item.

## Identidade e versão revisada
- Blog WordPress real: `https://casaedecoracao.radartechbr.com.br/`; rota V31 `wordpress_casa_decoracao`.
- Post ID **305**, status CMS `draft` após edição e após o teste do workflow LIVE. Título: **Como escolher um vaso decorativo âmbar para sua sala**. Slug de proteção de duplicação preservado `v31-31856a8a43a1-58259898640`.
- Conteúdo editorial revisado manualmente: 8 seções, **753 palavras**, correspondência direta H2/texto, linguagem prudente sobre material/dimensões/estoque. O título comercial informa **30 cm**, mas o artigo manda conferir medidas completas com o vendedor, sem afirmar especificação adicional não verificada.
- Exemplo comercial inalterado: produto `shopee:1718605288:58259898640`, imagem `https://cf.shopee.com.br/file/br-11134207-820lh-mnods1an1ipw39`, URL de afiliado `https://s.shopee.com.br/8pnOgLent4` na campanha específica `casaedecoracaowp` registrada no R2. 3 ocorrências do mesmo link, CTA, divulgação de comissão. O HTML de oferta foi mantido **exatamente como no DRAFT anterior**, nenhuma reconversão ou preço declarado.
- Dois URLs internos são de posts já publicados no **mesmo WordPress**: `/como-escolher-a-cadeira-ideal-para-sua-varanda/` (WP ID **298**) e `/como-organizar-alimentos-em-pequenas-quantidades/` (WP ID **295**).
- [Workflow PERMANENTE LIVE read-only #44577760603](https://github.com/adelrib27/blogger-automation1/actions/runs/44577760603) **SUCCESS** após [PR #94](https://github.com/adelrib27/blogger-automation1/pull/94), 46 testes isolados PASS, `approved_sku:true`, `exact_campaign:true`, `sections:8`, `publication_calls:0`, `owner_approval_loaded:false`, `AWAITING_OWNER_APPROVAL`.
- **SHA256 de aprovação C66**, formato SHA256 UTF-8 de `título decodificado + "\\n" + HTML bruto`: `ccc848b143a51235dba21b89be4b5dad92c538300678b9b8854347a5297d9b63`. Valores C65 e da primeira prévia C66 de HTML isolado **não são válidos** depois da revisão e do PR94. Qualquer edição posterior de título ou HTML exige nova revisão e SHA.

## Revisão que ainda depende do proprietário
1. **Revisão editorial final:** examinar conteúdo exibido no editor WordPress #305, apresentação da imagem e do CTA na versão móvel, legibilidade, coerência SEO e adequação à voz do blog. A IA não comprova experiência própria de uso.
2. **Oferta comercial atual:** a biblioteca R2 comprova link na campanha correta, foto original do CSV e elegibilidade; **a página externa da Shopee não pôde ser acessada de modo independente na auditoria web de 19/11**. Por isso confirmar no próprio anúncio se SKU, fotografia, anúncio atual, comissão, vendedor, envio e disponibilidade continuam corretos. Não alegar avaliações ou preço verificado.
3. **Autorização estrita:** somente a aprovação explícita do proprietário do **post WordPress Casa ID 305**, após esta revisão, permite criar manifesto `affiliate_hub_v31/live_approvals.d/wordpress_casa_decoracao__305.json` com `owner_authorized:true`, `editorial_reviewed:true`, `commercial_reviewed:true` e hash atualizado. Isso não libera nenhuma outra publicação.
4. **Teste LIVE real:** com manifesto válido e confirmação manual literal `PUBLISH:wordpress_casa_decoracao:305`, usar workflow separado [v31_manual_live_release.yml](../.github/workflows/v31_manual_live_release.yml) e revalidar GET/status/hash; após falha ou resultado incerto, NÃO repetir POST até confirmar CMS.

### Evidências independentes
- C66 edição API do DRAFT, [checkpoint C66](CHECKPOINT_C66_REVISAO_REAL_LIVE_2026-11-19.md).
- [PR #93](https://github.com/adelrib27/blogger-automation1/pull/93) corrigiu cabeçalhos para Blogger e WordPress, CI405 PASS.
- [PR #94](https://github.com/adelrib27/blogger-automation1/pull/94) vinculou título+HTML e verificou identidade WP, CI407 PASS.
- Segundo preflight LIVE autenticado [#44577760603](https://github.com/adelrib27/blogger-automation1/actions/runs/44577760603) **não publicou nada**.
- API WordPress após testes: **43 LIVE +59 DRAFT**, #305 ainda `draft`; nenhum manifesto de aprovação real na `main`.

**Ação pendente:** obter consentimento sobre este artigo individual; **não inferir aprovação da ordem genérica “pode avançar”**.
