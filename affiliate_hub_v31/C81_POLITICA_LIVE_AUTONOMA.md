# Política operacional V31 para publicação LIVE

**Estado atual: proposta, com LIVE automático desativado.** A política LIVE individual existente segue vigente durante a homologação.

## Pré-requisitos para a autorização única

1. Homologar cada rota em DRAFT. Confirmar o estado, o título e o HTML por leitura autenticada e demonstrar que uma repetição não cria outro post.
2. Observar o agendamento em DRAFT por sete dias consecutivos. Incluir pelo menos três novos rascunhos por plataforma, recuperação de uma falha transitória e interrupção comprovada diante de falha ambígua. Uma rota sem volume ou evidência suficientes permanece em DRAFT.
3. O proprietário aprova a versão da política, os blogs e seus limites de frequência e custo. A ativação exige a configuração protegida com o SHA-256 exato da política. Qualquer mudança no arquivo exige nova autorização da política.
4. Aplicar a migração do registro de tentativas somente ao D1 oficial depois da aprovação. O trabalho recorrente será configurado em projeto isolado. Nenhuma implantação ou migração está prevista neste PR.

## Controles propostos

- **Revisão e originalidade.** Fontes autorizadas são consultadas pelo verificador. Cada fato precisa corresponder à identidade do SKU e a uma extração objetiva. O HTML usa texto de uma receita editorial confiável, próprio da categoria. O gerador só propõe o produto; não tem acesso ao processo de assinatura. Sem prova externa, o candidato é bloqueado.
- **Rota e integridade.** O publicador exige o manifesto do verificador autônomo, identifica site e campanha, confere catálogo, imagem e destino Shopee, relê o estado do CMS, valida título e bytes do HTML e exige evidência fresca no D1. A versão inicial exige no mínimo 350 palavras em LIVE.
- **Limites iniciais.** Uma tentativa LIVE por blog e por dia UTC, com pelo menos 24 horas entre tentativas. DRAFT tem limite separado. As pesquisas pagas têm orçamento de tentativas por blog e tipo. Em caso de 429, a pesquisa entra em pausa persistente.
- **Deduplicação e recuperação.** A reserva atômica D1 bloqueia o mesmo fingerprint ou ID de post. Uma resposta ambígua mantém a rota interrompida. A recuperação exige comprovar primeiro o estado remoto. A automação não repete um POST LIVE cujo resultado não foi confirmado.
- **Auditoria e alertas.** O registro D1 conserva loja, campanha, fingerprint, ID do post, hash da política, momento e resultado. Falhas de execução ficam nos registros do GitHub Actions. Antes da ativação, o painel operacional deve verificar a fila D1 e alertar sobre tentativas pendentes e falhas repetidas. As rotas só retomam após a reconciliação do estado remoto.
- **Desligamento.** Remover a autorização do hash ou impedir a execução do workflow interrompe novas publicações. Registros e conteúdo existente são preservados. O início do teste deve restringir-se aos blogs homologados.

A autorização se aplica apenas ao uso da política aprovada. Os artigos são liberados pelos controles automatizados.
