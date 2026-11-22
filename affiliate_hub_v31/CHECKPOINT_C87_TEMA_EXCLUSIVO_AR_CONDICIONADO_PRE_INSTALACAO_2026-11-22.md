# V31 C87 — Tema exclusivo Ar-Condicionado sem Dúvidas: preparado, não instalado

Data: 22/11/2026. **Aguardar instalação e homologação em etapa posterior, conforme ordem expressa do proprietário.**

## Identificação precisa
- Blog alvo autenticado pelo Blogger API v3: **Ar-Condicionado sem Dúvidas**, ID `2228849984262880811`, URL `https://ar-condicionado-sem-duvidas.blogspot.com/`, posts total **0**, pages total **0**.
- Fonte de código enviada pelo proprietário ao chat: `theme-8476663092477971560_R52_CONTATO_SAFE_NAO_APLICADO.xml`, 218.539 bytes. **O ID 8476663092477971560 identifica a origem LAB do XML, NÃO o blog alvo.**
- A API Blogger V2 conectada confirma o alvo como pertencente à conta; Runner Local lista 8476663092477971560 como destino autorizado de LAB, mas não autoriza implantação automática do XML C87 em 2228849984262880811. Não chamar `adopt_model_v31_exact` no alvo fora de allowlist.

## Artefato entregue ao proprietário — arquivo de conversa, não commitado no repositório
- **`TEMA_EXCLUSIVO_AR_CONDICIONADO_SEM_DUVIDAS_V31_C87.xml`**
- Tamanho **216.894 bytes**; SHA-256 `6d0bcab7cfc84c912ffac0dd8b187717b5258738434c447f88960354ac465019`.
- TXT equivalente (byte a byte): `TEMA_EXCLUSIVO_AR_CONDICIONADO_SEM_DUVIDAS_V31_C87_HTML_COMPLETO.txt`.
- Backup da base R52: `BACKUP_BASE_R52_ANTES_TEMA_AR_CONDICIONADO.xml`.
- Diff: `ALTERACOES_TEMA_AR_CONDICIONADO_V31_C87.patch`.
- Manifesto: `VALIDACAO_TEMA_AR_CONDICIONADO_V31_C87.json`.
- Relatório integral: `RELATORIO_TEMA_AR_CONDICIONADO_V31_C87.md`.
- **Não alegar que estes arquivos binários/grandes estão no GitHub**; os artefatos foram criados no contêiner da conversa e os links locais somente são válidos no mesmo chat. Este checkpoint descreve os arquivos e fingerprints para continuidade.

## Alterações verificadas no código
1. Removido o `<b:section id='featured_post'>` com gadget ativo `FeaturedPost1` que causava supressão do mais recente na grade Blogger; mantido `Blog1` como fonte única do carrossel `#ub-v21-featured` e da grade, com dedupe por URL e 5 slides. Duas condições obsoletas de exclusão de FeaturedPost removidas.
2. Novo tema visual especializado para ar-condicionado: paleta fixa `clima` azul técnico/ciano, marca com floco de neve, subtítulo editorial, introdução HOME com H1 do título Blogger e tópicos BTUs/Inverter/Consumo/Instalação, layout responsivo, cartões, carrossel e rodapé específicos.
3. Widget Header1 e URL da PageList desativada foram corrigidos para o novo blog; sem importação de dados de LAB.
4. Removido formulário FormSubmit do LAB que enviava dados a destinatário não autorizado. A página Contato do novo blog ainda deverá ser criada e um canal privado legítimo só pode ser habilitado com identificação/autorização do proprietário.
5. Estrutura Loja universal preservada; nenhum produto, oferta, preço ou link afiliado inventado. Outros gadgets mantidos, contagem original 13 -> final 12.

## Testes realizados
- `lxml` com parsing XML estrito e namespaces Blogger: **PASS**.
- `node --check` nos scripts JavaScript inline separáveis: **PASS**, preservados os scripts com expressões XML dinâmicas Blogger.
- `tinycss2` análise do CSS novo: **PASS**.
- `Blog1` único, carrossel ligado a `#Blog1 .post-wrapper`, destaque oculto ausente, URL LAB ausente, URL do destinatário LAB ausente, identificação C87 presente e H1 HOME único: **PASS**.
- Nenhum teste Blogger LIVE, Android/iOS mobile ou artigos reais foi feito (blog sem posts).

## Bloqueios e próxima etapa
1. **Não instalado ainda.** Quando o proprietário autorizar, obter backup do tema atual do blog alvo e aplicar somente nele o XML C87 fornecido; validar HOME pública, Layout, mobile, 5 slides quando existirem posts, grade completa e post individual.
2. Criar institucional com **slugs exatos** já presentes no menu: `/p/sobre.html`, `/p/loja.html`, `/p/contato.html`, `/p/politica-de-privacidade.html`, `/p/termos-de-uso.html`, `/p/aviso-de-afiliados.html`. O blog tinha **0 páginas** na auditoria; links do tema ainda não têm destino real.
3. Configurar e testar canal Contato privado real apenas após aprovação de destinatário e política apropriada. Não transferir FormSubmit LAB.
4. Sistema V31: **`V31_AUTOLIVE_ACTIVE=false` permanece**. Nada em R2, D1, conversor, CI ou outros blogs foi modificado nesta etapa.
