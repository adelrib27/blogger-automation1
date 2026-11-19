# Autorizações individuais LIVE — V31 C65

**Nenhum arquivo de aprovação real existe por padrão.** O gerador Blogger C55 e o WordPress C60 produzem somente DRAFTs. Publicar exige uma revisão humana de UM post específico, o manifesto de aprovação neste diretório e disparo manual separado do workflow `.github/workflows/v31_manual_live_release.yml`. Essa pasta não deve ser preenchida pela IA com `owner_authorized:true` sem autorização explícita de conteúdo. O GitHub CI nunca executa publicação.

Formato `<site_key>__<post_id>.json` (EXEMPLO INVÁLIDO ATÉ QUE SEJA INSPECIONADO E APROVADO):

```json
{
  "site_key": "site_real_cadastrado",
  "platform": "blogger",
  "post_id": "123456789",
  "content_sha256": "0000000000000000000000000000000000000000000000000000000000000000",
  "approved_utc": "2026-11-19T00:00:00Z",
  "owner_authorized": false,
  "editorial_reviewed": false,
  "commercial_reviewed": false
}
```

A pessoa responsável precisa conferir título, texto integral, factualidade, produto/imagem, disclosure, link convertido na campanha EXATA, URLs internas e limites de nicho. O SHA256 deve corresponder ao HTML bruto recuperado por API autenticada no momento da aprovação. Definir as três revisões verdadeiras, só depois de sua realização. Alterar o DRAFT depois invalida o manifesto. No workflow, informar `site_key`, `post_id`, marcar `execute_live` e digitar exatamente `PUBLISH:<site_key>:<post_id>`. Sem manifesto aprovado, tudo é DRY_RUN ou BLOQUEADO.

A publicação LIVE não é um cron diário, não altera `publish_enabled=false` no cadastro V31 nem habilita publicações em massa. O escritor continua produzindo apenas rascunhos. Um erro após a tentativa de publicação exige leitura remota manual antes de tentar novamente.
