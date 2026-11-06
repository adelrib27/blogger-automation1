# R57 — LOJA Shopee LAB R2, política separada do Runner R49

Estado: LAB_SAFE. Não é LIVE_ROTATION_VALIDATED.

## Imutabilidade do R49

O bootstrap do R49 verifica hashes exatos de local_service_v08.py,
apply_universal_v31.py, v31_master_policy.py, v31_master_acceptance.py e
v31_master_approved_labs.json. A política anterior exigia store_mode=empty no
LAB R2, mas a LOJA publicada já contém 16 ofertas. Alterar os arquivos diretamente
quebraria a inicialização. A R57 NÃO modifica esses arquivos, o DPAPI, o tema ou o
inicializador. O Runner continua com daily_store_updates_enabled_by_runner=false.

O módulo r57_store_policy.py é uma política comercial SEPARADA, exclusiva do
Blog ID 8476663092477971560 e Page ID 7313055886747196118. Não substitui
os arquivos assinados da R49.

## Provas

- R56 API SAFE: GitHub run 42264864219 PASS, 16 ofertas em quatro categorias.
- R57 offline: GitHub run 42269667429 PASS, 21 regressões offline.
- R57 readback autenticado: run 42269447018 PASS, R57_NO_CHANGE, writes=0.
- R57 consulta Shopee posterior: run 42269020510 falhou fechada, antes de escrever
  no Blogger. Não há autorização para interpretar o resultado parcial como catálogo.
- LOJA LIVE do LAB R2 preservada com 16 produtos e 32 links afiliados.

## Writer e proteção

O writer r57_rotate_store.py faz dry-run por padrão. Um LIVE exige ambos:
1) rotation_enabled=true E allow_auto_write=true no estado;
2) variável de confirmação exata exclusiva do LAB R2.
Antes de escrever: confere IDs, status publicado, URL, hash da região existente,
16 produtos, 32 links e ausência de alterações concorrentes; faz backup.
Executa no máximo uma tentativa de PUT. Se houver erro ou timeout, não repete.
Somente após readback API e PASS público produz R57_ROTATION_STATE_NEXT.json
para persistência. Workflows não recriam Posts/Pages, não mexem em outros blogs.

## Próximo gate (ainda pendente)

A API Shopee deve concluir um SAFE novo; é preciso revisar as ofertas e executar
o primeiro LIVE supervisionado. Só depois habilitar schedule diário na main.
A branch R57 permanece SAFE: rotation_enabled=false, allow_auto_write=false;
nenhum schedule ou writer automático está habilitado. Não forçar R49.

Os arquivos operacionais no Windows e o pacote R54/R56 devem continuar guardados.
