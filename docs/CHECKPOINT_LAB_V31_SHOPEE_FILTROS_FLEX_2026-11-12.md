# CHECKPOINT V31 — FLEXIBILIZACAO DE FILTROS SHOPEE — 2026-11-12

## Escopo e estados

- SOMENTE LAB — branch `lab/v31-shopee-filtros-flex-safe-20261112`.
- Base: `lab/v31-r57-rotacao-safe-lab-r2` em `fef15ad0f3f5fe0f5f85fe576f18967b182a0efa`.
- `main` permaneceu em `2286726c6353fc2bfc454fd8b54bd7207cd36aec` após o experimento.
- Nenhuma escrita no Blogger, nenhum tema alterado, nenhum merge, nenhuma rotação LIVE.
- Código fonte alterado isoladamente: `v31_master/shopee_r2_safe.py`. NÃO está em produção.
- Workflows criados com gatilhos somente na branch LAB e sem Blogger API write.

## Filtros de CANDIDATOS relaxados

- Título mínimo de 12 para 8 caracteres; máximo de 190 preservado.
- Nota mínima de 4,0 para 3,5. Notas acima de 5 e dados inválidos rejeitados.
- Categoria: tolerância a acentos, plurais e sufixos em começo de palavra; categoria incompatível ainda rejeitada.
- Diversificação: limite de 2 para 4 itens por loja/vendedor na seleção de 16.
- Preservados: item ID numérico, link HTTPS Shopee em domínio permitido, imagem HTTPS válida em domínio permitido, preço numérico entre 1 e 100000, produtos distintos, 4 por categoria e 16 no total, marcadores e links patrocinados, lock por blog/page e bloqueio de escrita no SAFE.
- Sem fallback inventado quando a Shopee não responde. O gate GraphQL original permanece.

## Evidência de testes

1. GitHub Actions offline: run `43224569435` — PASS nos testes iniciais.
2. GitHub Actions offline: run `43225144206` — PASS, 17 testes dos filtros e simulação + 14 testes existentes do policy guard = 31 PASS.
3. Fixtures SINTÉTICAS em LAB: a seleção rígida selecionou 0/16 por critérios rígidos; a flexibilizada 16/16, IDs únicos, quatro categorias. Não são produtos reais.
4. Simulação com duas vitrines sintéticas: `R57_CANDIDATE_SAFE_NOT_AUTHORIZED`, `writes=false`, 16 novos itens. Identidade: `R57_NO_CHANGE`, `writes=false`.
5. Sonda Shopee: run `43224900760`, exatamente UMA consulta de `productOfferV2` para `mouse`. O programa retornou `API_BLOCKED_NO_UPDATE` com 0 seleção, `writes_blogger=false`. O run GitHub teve `success` porque foi capaz de registrar o bloqueio; isto NÃO é sucesso da API. O código específico do erro upstream não foi registrado nessa sonda, mas logs anteriores mostraram GraphQL `10000`.
6. NENHUM produto real obtido pela sonda; nenhuma alteração em lojas; rotação real segue NAO VALIDADA.

## Próximo trabalho recomendado

1. Diagnosticar por que `productOfferV2` retorna erro com uma chamada mínima, redigindo somente HTTP e code GraphQL; comparar assinatura, argumentos e permissão sem expor secrets.
2. Se a API retornar ofertas: medir quantitativos aceitos por filtros rígidos versus flexibilizados com amostra real, comparar semântica, vendedores e qualidade.
3. Só então testar rotação real em LAB em modo SAFE/readback. Sem aprovação de produção até passar.
4. Preservar a configuração atual e `r57_store_policy.py` intactos até haver evidência e autorização explícita de promoção para blogs existentes.

## Links

- Branch: https://github.com/adelrib27/blogger-automation1/tree/lab/v31-shopee-filtros-flex-safe-20261112
- Offline PASS: https://github.com/adelrib27/blogger-automation1/actions/runs/43225144206
- Sonda REAL bloqueada: https://github.com/adelrib27/blogger-automation1/actions/runs/43224900760

## Adendo P0 - Diagnóstico diferencial GraphQL (12/11/2026)

**Estado:** causa-raiz AINDA NÃO DETERMINADA. Houve respostas reais bem-sucedidas e falhas `10000` em consultas consecutivas. O resultado contradiz a hipótese de indisponibilidade total da API, mas não prova rate limit nem erro específico nos parâmetros.

### Evidências ao vivo (somente LAB, chamadas POST GraphQL de leitura)

1. Run [43227286424](https://github.com/adelrib27/blogger-automation1/actions/runs/43227286424): `__typename` raiz HTTP 200 / PASS; `productOfferV2` com `nodes { __typename }` `10000`; `productOfferV2` com `nodes { itemId productName }` **PASS, 1 oferta real**; com `listType:2`, `sortType:2` `10000`. 9 testes offline PASS no mesmo workflow.
2. Run [43227603848](https://github.com/adelrib27/blogger-automation1/actions/runs/43227603848): sem filtros opcionais e com campos úteis (link/imagem/preço/ID/avaliação) **PASS, 1 oferta real**; consultas posteriores com `sortType:2`, `listType:2`, `sortType:1` e até consulta básica repetida deram `10000`. Portanto não isolar como defeito determinístico de `sortType` ou `listType`.
3. Run [43227975705](https://github.com/adelrib27/blogger-automation1/actions/runs/43227975705): uma única consulta até 20 nós, sem filtros opcionais, devolveu HTTP 200 + GraphQL `10000`. **Nenhuma amostra válida para comparar filtros rígidos e flexibilizados neste run**.
4. Nenhuma mutação Shopee, nenhuma escrita Blogger, nenhum produto/identificador real/secret persistido ou impresso no diagnóstico. O status GitHub `success` significa execução do DIAGNÓSTICO, não sucesso da API de ofertas.

### Correção candidata, somente branch LAB

- Em `v31_master/shopee_r2_safe.py`, a query passou a usar apenas `productOfferV2(keyword, page:1, limit:20)` e os campos essenciais `itemId productName offerLink imageUrl priceMin shopId ratingStar sales`.
- Mantidos como guardas: `GateError` quando existem `errors` GraphQL, 16 produtos distintos, 4 por categoria, HTTPS e whitelists para produto/imagem, preço válido, lock e `r57_store_policy.py` não modificado.
- Esta mudança não foi comprovada como solução; **a query reduzida também foi vista falhar esporadicamente** no ambiente da Shopee.
- Run [43228442713](https://github.com/adelrib27/blogger-automation1/actions/runs/43228442713): **36 testes offline PASS** (17 seleção/rotação simulada + 5 gateway mínimo + 14 policy guard). Nenhuma chamada externa nesse workflow.
- `main` / workflows produtivos / blogs / temas / Lojas: não alterados pelo diagnóstico.

### Próximo gate

- **Não repetir consultas continuamente** quando Shopee retorna `10000`. Considerar cooldown e 1 sonda por janela, com observação do code HTTP/GraphQL, sem usar dados antigos como novos.
- Esperar retorno real não vazio e estável para coletar contagens de candidatos aceitos sob ambos filtros `estrito` e `flexível`, sem logar dados comerciais nem publicá-los.
- Em seguida rodar a seleção 16/16 e somente uma simulação de rotação; antes de uma publicação LAB, exigir preflight de blog/page, diff, autorização de escopo, readback e HTTP público.
- Não promover a `main` ou produção sem evidência adicional e autorização específica.
