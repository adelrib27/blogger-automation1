# C81 — revisão independente antes do DRAFT

O gerador entrega um candidato privado. O revisor confere exatamente o HTML, as fontes, os fatos e o contexto SEO do candidato. O publicador recebe apenas a chave pública da assinatura de entrega.

## Fluxo

1. O produtor usa `python -m affiliate_hub_v31.independent_review submit --file candidato.json`. O processo normal do catálogo e as rotas V31 determinam site, SKU e campanha. A submissão valida a estrutura HTML, normaliza o JSON e retorna o site e o SHA-256. O R2 guarda o candidato privado em `v31/private-review/v1/` por site e digest com escrita condicional e leitura exata.
2. O revisor recupera os mesmos bytes com `python -m affiliate_hub_v31.independent_review export --site-key <site> --digest <sha256> --file candidato.json` em estação autorizada. Verifica que a foto, SKU, campanha e oferta são os exatos. Abre cada fonte, verifica identidade e atualidade, compara trechos com os fatos usados, revisa também o texto livre, a intenção e os links internos. Um resultado de pesquisa ou uma autodeclaração do gerador exige conferência independente.
3. Disparar [Revisão factual independente e DRAFT](../.github/workflows/v31_independent_review_draft.yml) na `main` para o site e digest. O revisor configurado só aprova o job protegido se o SHA-256 da execução corresponder ao pacote que conferiu. O código lê o histórico autenticado de aprovações do GitHub e compara aprovador, ambiente, site e digest com a execução. Ausência, rejeição ou divergência interrompem a etapa.
4. O job protegido restaura o catálogo oficial, verifica os fatos e executa o C77 sobre o HTML exato antes de persistir READY. A aprovação produz o HMAC C77 e uma assinatura Ed25519 do manifesto completo. O envelope R2 v2 é imutável. A emissão resgatável fica vinculada ao fingerprint e ao hash da evidência no D1.
5. Quando a entrada `create_draft` foi ativada para aquela execução, o job de entrega usa a chave pública Ed25519. Ele confere o envelope, o D1, o CMS e só então reivindica a tentativa de criação. A leitura autenticada do CMS precisa confirmar DRAFT, título e HTML exato. Replays conciliam o rascunho e não repetem o POST. Se USED não corresponder a um rascunho encontrado, preserve o job para investigar a resposta anterior.
6. A aprovação desta execução é editorial, para READY e DRAFT. Um LIVE exige a aprovação individual já separada do fluxo C81.

## Preparação do ambiente

- Usar o ambiente GitHub `v31-independent-review` com implantação exclusiva da `main` e revisor obrigatório. Definir `V31_PROTECTED_REVIEWER` com o login autorizado a aprovar. O aprovador precisa ser de fato separado do gerador.
- Os secrets `V31_READY_REVIEW_HMAC_KEY` e `V31_REVIEW_RELEASE_PRIVATE_KEY_HEX` ficam nesse ambiente. Ambos usam 32 bytes aleatórios codificados em hex. O segundo é uma semente de Ed25519. Definir `V31_REVIEW_RELEASE_PUBLIC_KEY_HEX` com os 32 bytes públicos brutos em hex, visível aos dois ambientes. Evitar rotação até concluir os jobs assinados com a chave anterior.
- Autorizar o runner revisor a ler o catálogo oficial e o candidato, persistir o envelope e acessar o D1 oficial. Seu ambiente recebe os identificadores V31 oficiais e os secrets `V31_EDITORIAL_R2_ACCESS_KEY_ID`, `V31_EDITORIAL_R2_SECRET_ACCESS_KEY` e `V31_D1_API_TOKEN` de acesso ao V31. O job revisor não possui credenciais CMS. O gerador e o publicador não recebem os segredos de assinatura.
- O workflow tem disparo manual e `create_draft` começa desmarcado. O código protege a rota registrada e não muda os agendamentos atuais.

O contrato do candidato é `ARTICLE_FIELDS` em `independent_review.py`. O pacote guarda o HTML final, SEO, fatos, URLs de fontes e links internos reais. Nenhuma saída do modelo concede autorização. O pacote deve ir ao R2 privado ou à estação do revisor, com logs públicos limitados ao digest, aos códigos de resultado e aos identificadores de execução.
