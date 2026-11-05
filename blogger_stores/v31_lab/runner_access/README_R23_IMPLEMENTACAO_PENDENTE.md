# R23 — Autorização V31 restrita ao novo LAB (código SAFE, **não instalado**)

O usuário autorizou corrigir a restrição para instalar **somente o tema atual
TEMA_BLOGGER_UNIVERSAL_V31_R1_PLAY_REFINADO_LAB** no novo laboratório
`https://lab-v31-loja-20261105.blogspot.com/`.

## Identificadores exatos

- LAB anterior: Blog `4739187376492839837`, Page `2446067640331732447`.
- Novo LAB: Blog `1625257710858445955`, Page `8266917849571219350`.

A função `authorize_v31_lab_theme` recusa qualquer outro ID, URL ou Page ID,
inclusive blogs existentes como Vida Pet Prática. Requer operação
`ADOPT_CURRENT_UNIVERSAL_V31` e confirmação com ID exato.
NÃO existem wildcards, modo all blogs, fallback V20, nem escalada de permissões.

## Importante: status correto

**CÓDIGO PREPARADO/TESTÁVEL EM LAB, NÃO APLICADO NO SERVIÇO WINDOWS.**
O serviço `blogger-local-runner/0.8-v31r1-lab` vivo anunciou
`universal_v31_allowed_blog_id=4739187376492839837` e
`v31_enabled_for_new_blogs=false`. Suas 8 ações remotas não incluem
gerenciar allowlist nem aplicar tema V31 em novos blogs. O arquivo Python exato
do serviço 0.8-v31r1-lab em execução no Windows não foi fornecido e não existe
na branch do repositório lida nesta auditoria. Por isso, não usar o provisionador
V20, não substituir o serviço por uma versão histórica nem afirmar que a
allowlist ao vivo já foi alterada.

## Para aplicar no Runner real (ainda pendente)

1. Obter a versão ATUAL do handler Python e do instalador V31 do computador,
   confirmar hash e fazer backup.
2. Integrar `authorize_v31_lab_theme` ANTES de qualquer backup/editação de
   tema; revalidar blog ID+URL lidos AO VIVO do painel Blogger.
3. Preservar a permissão do LAB antigo e introduzir somente o novo ID; nunca
   definir `v31_enabled_for_new_blogs=true` globalmente.
4. Fazer backup canônico do tema atual do NOVO blog (hoje padrão Blogger),
   confirmar o SHA do arquivo `TEMA_BLOGGER_UNIVERSAL_V31_R1_PLAY_REFINADO_LAB.xml`
   e testar instalador apenas para este Blog ID com confirmação explícita.
5. Confirmar resposta `health` com allowlist dos dois IDs, verificar por
   GET público / API que as seis páginas e seus IDs continuam intactos.
6. Somente depois proceder à publicação da LOJA Shopee, com autorização
   específica e todos os gates de publicação V31.
7. Se o serviço retornar estado inesperado, bloquear a ação e preservar tema.

O teste SAFE deste módulo é:
`python -m unittest discover -s blogger_stores/v31_lab/runner_access -p test_*.py -v`.

Esta correção isolada não modifica produção nem executa chamadas ao Blogger.
