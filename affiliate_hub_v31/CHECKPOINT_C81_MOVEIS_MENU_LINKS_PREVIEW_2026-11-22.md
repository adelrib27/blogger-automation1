# V31 C81 — Blogger Móveis: correção de links fixos de menu — pré-mutação

Data: 22/11/2026. Blog ID `1439741542627895062`, URL https://moveisparacadacanto.blogspot.com/.

## Evidência de leitura de página real
O navegador conectado retornou os hyperlinks do tema:
- Cabeçalho/rodapé `Sobre`: `/p/sobre.html`
- Cabeçalho/rodapé `Contato`: `/p/contato.html`
- Cabeçalho/rodapé `Loja`: `/p/loja.html`
- Rodapé `Termos de Uso`: `/p/termos-de-uso.html`
- Rodapé `Aviso de Afiliados`: `/p/aviso-de-afiliados.html`
- Rodapé `Política de Privacidade`: `/p/politica-de-privacidade.html` (existente e operante).

O Blogger API v3 retornou somente três páginas publicadas: `/p/sobre-o-moveis-para-cada-canto.html`, `/p/transparencia-comercial-e-links-de.html` e `/p/politica-de-privacidade.html`. Portanto as cinco URLs restantes do tema não correspondem aos paths existentes. A criação de uma página não modifica o tema nem seus hyperlinks hardcoded.

## Correção planejada
- Criar páginas intituladas exatamente `Sobre`, `Contato`, `Loja`, `Termos de Uso`, `Aviso de Afiliados` com permalinks gerados e verificar que coincidem com os paths fixos do tema.
- Sobre e Aviso: páginas-resumo úteis, com links às páginas editoriais completas existentes, sem excluir/redirecionar cegamente.
- Contato: não inventar e-mail ou expor conta pessoal; orientar sobre comentários públicos e reconhecer que canal privado depende de decisão do proprietário.
- Loja: não inventar produtos/preços; direcionar a guias publicados.
- Termos: texto geral proporcional às atividades observadas; sem afirmação de aconselhamento jurídico.
- Ler cada página criada por GET; checar via navegador quando disponível.
- Nada de alterações em artigos comerciais, DRAFT, LIVE policy, secrets, D1, R2, catálogo ou outros blogs.
