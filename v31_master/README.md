# Blogger Automation — V31 Mestre R56 (LAB R2)

**Estado:** LAB R2 validado publicamente para a primeira LOJA Shopee; código de replicação preparado em branch de laboratório. **Ainda não integrado ao Runner local R49** e **não habilita agendamento de rotação**.

## Alvo exclusivo

- Blog ID: `8476663092477971560`
- URL: `https://lab-v31-r2-replicacao-limpa-20261105.blogspot.com/`
- Page LOJA já existente: `7313055886747196118` (`/p/loja.html`).
- Não tocar nos outros blogs, na branch `main`, no inicializador R49, no CDP, no DPAPI, nem no Tema V31/R52.

## Comprovantes obtidos em 2026-11-06

- Runner R49: saúde OK, três LABs autorizados, Chrome/CDP `AUDIT_OK`.
- R52 CSS responsivo: HTML público detectado; sem reinstalação.
- R55 SEO: descrição de busca, WebP, lazy images, HTTPS, visibilidade e fuso Brasília validados, robots intocados.
- Páginas institucionais: cinco LIVE, rotas canônicas, sem títulos `h2` duplicados.
- Shopee: GitHub Actions SAFE `42264864219` concluiu com sucesso, usando secrets do repositório sem expor credenciais.
- Primeira publicação de LOJA autorizada pelo usuário: Blogger Page ID **igual**, status LIVE; 16 produtos únicos; 4 categorias x 4; 32 links com `nofollow sponsored noopener`; URL pública HTTP 200. Home sem produtos/post técnico.
- Segunda consulta SAFE `42265395587` falhou fechada (sem Blogger writes). Não confundir com a primeira seleção, que foi validada.
- Rotação automática, schedule e Writer do LAB R2: **DESATIVADOS**.

## Arquivos neste escopo

- `profiles/lab_r2_v31_r52_r55.json`: perfil explícito, referências da R52, SEO R55, cinco páginas, Page LOJA, checks R56.
- `replication_safe.py`: gate read-only para validar um perfil por Blog ID/URL, SEO, páginas, LOJA e proteções. NÃO cria blog, não instala tema, não reinicia Runner, não publica nada.
- `shopee_r2_safe.py`: usa os secrets `SHOPEE_APP_ID` e `SHOPEE_SECRET` apenas via ambiente de GitHub Actions para obter ofertas `productOfferV2`, valida categoria, domínio, preço, item único e HTML. NÃO escreve no Blogger.
- `.github/workflows/v31_lab_r2_shopee_safe.yml`: workflow SAFE isolado da V20, `contents: read`, sem cron, sem publicação automática.

## Contrato para replicação futura (não executar sem preflight)

1. Alvo: Blog ID e URL exatos; verificar que não existe outra automação/Writer para o mesmo blog.
2. SEO: descrição adaptada ao nicho; fuso Brasília, lazy/WebP/HTTPS, busca e robots preservados.
3. Tema: V31/R52 validado; backup XML obrigatório; nenhuma instalação repetida, nenhuma troca de tema por inferência.
4. Institucionais: criar apenas páginas inexistentes, com títulos Sobre, Contato, Política de Privacidade, Termos de Uso, Aviso de Afiliados. Conteúdos legais/contato exigem adaptação por blog; nunca copiar o texto do laboratório como texto definitivo.
5. LOJA: Page estável `/p/loja.html` e ID original preservado; não criar post `Loja` duplicado.
6. Shopee: SAFE com ofertas atuais da API; curadoria semântica do nicho, links oficiais, deduplicação, `rel` patrocinado, preços como retornados pela API, disclosure, varredura contra scripts/injeção.
7. Publicar somente no LAB autorizado, após backup e preflight. Exigir readback da API, HTTP 200 público, 16 cards e 32 `rel`; falhar fechado em 429/timeout.
8. Persistir estado de rotação apenas após PASS público. Agendamento somente depois de teste de primeira rotação, idempotência, rollback e ausência de Writer concorrente.

## Dependência pendente no Runner local

O registro histórico `v31_master_policy.py` / `v31_master_approved_labs.json` do R49 ainda possuía `store_mode=empty` para o LAB R2. A LOJA agora contém 16 produtos. **Não executar novamente qualquer instalador/Apply V31 nem auditor que exija LOJA vazia**. Antes de habilitar futuras ações automáticas, introduzir uma transição de política para `populated_verified_manual`, com backup, hashes e testes LAB sem reiniciar arbitrariamente o Runner. A validação de saúde do Runner não prova que esse contrato de LOJA esteja atualizado.

## Testes offline

```bash
python v31_master/replication_safe.py --profile v31_master/profiles/lab_r2_v31_r52_r55.json
python v31_master/shopee_r2_safe.py --self-test
```

A branch é somente para integração incremental. Não fazer merge na `main` nem ativar schedules/writers sem validação e autorização de publicação para os demais blogs.
