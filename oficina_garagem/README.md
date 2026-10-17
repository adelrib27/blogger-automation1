# Oficina & Garagem

Destino exclusivo: https://oficina.radartechbr.com.br

## Estado atual

- WordPress tradicional independente ativo em HTTPS.
- Tema filho **Oficina & Garagem Editorial** ativo e aprovado, baseado no padrão visual validado do Casa e Decoração, com identidade própria e carrossel de 5 segundos.
- Categorias: Ferramentas, Manutenção, Acessórios Automotivos, Organização de Garagem, Limpeza e Conservação, Segurança e Proteção.
- AIOSEO, WPVibe e Easy MCP AI instalados.
- Páginas publicadas: Sobre, Política editorial e Transparência e afiliados.
- Contato, Privacidade, Cookies e Termos permanecem em draft até completar dados reais e revisão final.
- Posts demonstrativos permanecem em draft.
- Search Console ainda pendente.

## Automação editorial

O projeto possui estrutura isolada em `oficina_garagem/` e não reutiliza filas, credenciais ou dados de Radar Tech BR/Casa e Decoração.

Implementado:

1. descoberta Shopee usando o scanner v2.3 existente do repositório, mas com configuração, categorias, regras semânticas e regressões próprias do Oficina;
2. builder de fila editorial a partir do `intent_report.json`;
3. quality/safety gate específico para ferramentas e automotivo;
4. bloqueio de alegações de teste próprio, especificações numéricas não confirmadas, compatibilidade universal e instruções procedimentais de alto risco;
5. revisão humana obrigatória para Segurança e Proteção e termos de maior risco;
6. geração por Workers AI implementada, mas **desativada por padrão**;
7. sincronização com WordPress implementada **somente em draft** e desativada por padrão;
8. auditoria de candidatos sem qualquer ação de publicação ao vivo;
9. testes automatizados dos gates.

## Segurança operacional

- `publishing_allowed=false`.
- Não existe rotina de publicação ao vivo no pipeline Oficina neste estágio.
- Geração depende de `OFICINA_GENERATION_ENABLED=true` e credenciais próprias de Cloudflare.
- Sincronização WordPress depende de `OFICINA_DRAFT_SYNC_ENABLED=true` e credenciais próprias do WordPress; o status enviado é fixo como `draft`.
- Conteúdo sobre freios, direção, suspensão, airbag, elevação de veículo, corte, solda, bateria/eletricidade, torque e EPI exige tratamento conservador e/ou revisão humana.

## Workflows

- `.github/workflows/oficina_shopee_oportunidades.yml`: descoberta + regressões + fila; não gera nem publica artigo.
- `.github/workflows/oficina_editorial_safe.yml`: valida o pipeline draft-only; geração e sync ficam desligados até liberação específica.

O projeto deve permanecer separado dos outros blogs e qualquer futura publicação automática exige nova validação explícita.
